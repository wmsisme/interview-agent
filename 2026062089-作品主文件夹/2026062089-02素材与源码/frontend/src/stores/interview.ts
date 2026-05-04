import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import type { EvaluationResult, StartInterviewResponse } from '@/api/interview'
import * as interviewApi from '@/api/interview'
import { playTTS } from '@/api/voice'
import { calculateAverageScore } from '@/utils/format'

export interface InterviewMessage {
  id: number
  role: 'ai' | 'user'
  content: string
  audioUrl?: string
  scores?: {
    tech: number
    depth: number
    logic: number
    match: number
  }
  timestamp: Date
}

export const useInterviewStore = defineStore('interview', () => {
  // 状态
  const interviewId = ref<number | null>(null)
  const position = ref<string>('')
  const messages = ref<InterviewMessage[]>([])
  const currentQuestion = ref<string>('')
  const currentQuestionId = ref<number | null>(null)
  const isLoading = ref(false)
  const isRecording = ref(false)
  const finished = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const currentRound = computed(() => messages.value.filter(m => m.role === 'ai').length)
  const lastMessage = computed(() => messages.value[messages.value.length - 1])
  const totalScore = computed(() => {
    const scores = messages.value
      .filter(m => m.scores)
      .map(m => {
        const s = m.scores!
        return (s.tech + s.depth + s.logic + s.match) / 4
      })
    return calculateAverageScore(scores)
  })

  // 动作
  const startInterview = async (positionParam: string, isVideo: boolean = true) => {
    try {
      // 清除之前的面试状态
      clearInterview()
      
      isLoading.value = true
      error.value = null
      
      // 调用API开始面试
      const response = await interviewApi.startInterview(positionParam)
      const responseData = response as unknown as StartInterviewResponse
      
      interviewId.value = responseData.interviewId
      position.value = positionParam
      finished.value = false
      
      // 对于视频面试，不添加首条AI消息（由视频聊天处理）
      if (!isVideo) {
        // 添加首条AI消息（传统面试）
        addMessage({
          id: 1,
          role: 'ai',
          content: responseData.firstQuestion,
          timestamp: new Date()
        })
        
        currentQuestion.value = responseData.firstQuestion
        currentQuestionId.value = responseData.firstQuestionId
        
        // 注意：首条问题的TTS播放将在InterviewView.vue页面加载完成后进行
        // 这确保了页面跳转完成后再播放语音，避免页面切换期间的音频中断
      }
      
      return response
    } catch (err) {
      error.value = '开始面试失败'
      ElMessage.error('开始面试失败')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const sendAnswer = async (answerText: string) => {
    if (!interviewId.value || !currentQuestionId.value || isLoading.value) {
      throw new Error('面试未开始或正在处理中')
    }

    try {
      isLoading.value = true
      error.value = null
      
      // 添加用户消息
      const userMessageId = messages.value.length + 1
      addMessage({
        id: userMessageId,
        role: 'user',
        content: answerText,
        timestamp: new Date()
      })
      
      // 提交回答
      const result = await interviewApi.submitAnswer(
        interviewId.value,
        currentQuestionId.value,
        answerText
      )
      const resultData = result as unknown as EvaluationResult
      
      // 处理评估结果
      await processEvaluationResult(resultData)
      
    } catch (err) {
      error.value = '提交回答失败'
      ElMessage.error('提交回答失败')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const sendAudioAnswer = async (audioBlob: Blob) => {
    if (!interviewId.value || !currentQuestionId.value || isLoading.value) {
      throw new Error('面试未开始或正在处理中')
    }

    try {
      isLoading.value = true
      error.value = null
      
      // 添加用户消息（临时占位）
      const userMessageId = messages.value.length + 1
      addMessage({
        id: userMessageId,
        role: 'user',
        content: '语音回答处理中...',
        timestamp: new Date()
      })
      
      // 提交音频回答
      const result = await interviewApi.submitAudioAnswer(
        interviewId.value,
        currentQuestionId.value,
        audioBlob
      )
      const resultData = result as unknown as EvaluationResult
      
      // 更新用户消息内容为识别文本（如果有的话）
      // 这里简化处理，实际应该使用语音识别结果
      const lastUserMessage = messages.value[messages.value.length - 1]
      if (lastUserMessage && lastUserMessage.role === 'user') {
        lastUserMessage.content = '语音回答已提交'
      }
      
      // 处理评估结果
      await processEvaluationResult(resultData)
      
    } catch (err) {
      error.value = '提交音频回答失败'
      ElMessage.error('提交音频回答失败')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const processEvaluationResult = async (result: EvaluationResult) => {
    // 添加AI反馈消息
    const feedbackMessageId = messages.value.length + 1
    addMessage({
      id: feedbackMessageId,
      role: 'ai',
      content: result.feedback || '面试官正在评估您的回答...',
      timestamp: new Date(),
      scores: {
        tech: result.techScore,
        depth: result.depthScore,
        logic: result.logicScore,
        match: result.matchScore
      }
    })
    
    // 播放反馈语音
    try {
      await playTTS(result.feedback)
    } catch (error) {
      console.error('播放反馈语音失败:', error)
    }
    
    // 更新用户消息的评分（如果有）
    const userMessages = messages.value.filter(m => m.role === 'user')
    const lastUserMessage = userMessages.length > 0 ? userMessages[userMessages.length - 1] : undefined
    if (lastUserMessage) {
      lastUserMessage.scores = {
        tech: result.techScore,
        depth: result.depthScore,
        logic: result.logicScore,
        match: result.matchScore
      }
    }
    
    // 检查是否结束面试
    if (result.endInterview || !result.nextQuestion) {
      finished.value = true
      ElMessage.success({ message: '面试已完成', duration: 3000 })
    } else {
      // 添加下一轮问题
      const questionMessageId = messages.value.length + 1
      addMessage({
        id: questionMessageId,
        role: 'ai',
        content: result.nextQuestion,
        timestamp: new Date()
      })
      
      currentQuestion.value = result.nextQuestion
      // 使用后端返回的数据库问题ID，如果没有则使用前端生成的消息ID
      currentQuestionId.value = result.nextQuestionId || questionMessageId
      
      // 播放下一问题的语音
      try {
        await playTTS(result.nextQuestion)
      } catch (error) {
        console.error('播放下一问题语音失败:', error)
      }
    }
  }

  const endInterview = async (conversation?: { role: string; content: string }[]) => {
    if (!interviewId.value) {
      throw new Error('没有活跃的面试')
    }

    try {
      isLoading.value = true
      console.log(`正在结束面试 ${interviewId.value}...`)
      const result = await interviewApi.endInterview(interviewId.value, conversation)
      console.log('结束面试API调用成功:', result)
      finished.value = true
      return result
    } catch (err) {
      console.error('结束面试API调用失败:', err)
      error.value = '结束面试失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const addMessage = (message: InterviewMessage) => {
    messages.value.push(message)
  }

  const clearInterview = () => {
    interviewId.value = null
    position.value = ''
    messages.value = []
    currentQuestion.value = ''
    currentQuestionId.value = null
    isLoading.value = false
    isRecording.value = false
    finished.value = false
    error.value = null
  }

  const setRecording = (recording: boolean) => {
    isRecording.value = recording
  }

  return {
    // 状态
    interviewId,
    position,
    messages,
    currentQuestion,
    currentQuestionId,
    isLoading,
    isRecording,
    finished,
    error,
    
    // 计算属性
    currentRound,
    lastMessage,
    totalScore,
    
    // 动作
    startInterview,
    sendAnswer,
    sendAudioAnswer,
    endInterview,
    clearInterview,
    setRecording,
    addMessage
  }
})