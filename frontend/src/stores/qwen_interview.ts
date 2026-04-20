import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import QwenWebSocket from '@/api/qwen_websocket'
import { getQwenAudioProcessor } from '@/utils/qwen_audio'
import type { EvaluationResult, StartInterviewResponse } from '@/api/interview'
import * as interviewApi from '@/api/interview'

export interface QwenInterviewMessage {
  id: number
  role: 'ai' | 'user'
  content: string
  audioBase64?: string // 存储Base64音频数据，用于播放
  scores?: {
    tech: number
    depth: number
    logic: number
    match: number
  }
  timestamp: Date
}

export const useQwenInterviewStore = defineStore('qwen_interview', () => {
  // 状态
  const interviewId = ref<number | null>(null)
  const position = ref<string>('')
  const messages = ref<QwenInterviewMessage[]>([])
  const currentQuestion = ref<string>('')
  const isLoading = ref(false)
  const isRecording = ref(false)
  const finished = ref(false)
  const error = ref<string | null>(null)
  
  // Qwen-Omni相关状态
  const qwenWebSocket = ref<QwenWebSocket | null>(null)
  const qwenSessionId = ref<string>('')
  const isQwenConnected = ref(false)
  const audioProcessor = ref(getQwenAudioProcessor())
  
  // 当前接收的音频数据
  const currentAudioChunks = ref<string[]>([])
  const currentTextChunks = ref<string[]>([])
  
  // 计算属性
  const currentRound = computed(() => messages.value.filter(m => m.role === 'ai').length)
  const lastMessage = computed(() => messages.value[messages.value.length - 1])
  
  // Qwen-Omni WebSocket处理
  const connectToQwen = () => {
    if (!interviewId.value || !position.value) {
      throw new Error('面试未开始')
    }
    
    const sessionId = `qwen_${interviewId.value}_${Date.now()}`
    qwenSessionId.value = sessionId
    
    qwenWebSocket.value = new QwenWebSocket()
    
    qwenWebSocket.value.connect(
      sessionId,
      interviewId.value.toString(),
      position.value,
      {
        onAudio: handleQwenAudio,
        onText: handleQwenText,
        onStarted: handleQwenStarted,
        onStopped: handleQwenStopped,
        onError: handleQwenError,
        onRagResults: handleRagResults
      }
    )
  }
  
  const handleQwenAudio = (audioBase64: string) => {
    // 收集音频块
    currentAudioChunks.value.push(audioBase64)
    
    // 实时播放音频
    try {
      audioProcessor.value.playPCMBase64(audioBase64).catch(err => {
        console.warn('播放音频块失败:', err)
      })
    } catch (error) {
      console.error('播放音频块错误:', error)
    }
  }
  
  const handleQwenText = (textChunk: string) => {
    // 收集文本块
    currentTextChunks.value.push(textChunk)
    
    // 更新最后一条AI消息的内容（如果有）
    const aiMessages = messages.value.filter(m => m.role === 'ai')
    if (aiMessages.length > 0) {
      const lastAIMessage = aiMessages[aiMessages.length - 1]
      lastAIMessage!.content = currentTextChunks.value.join('')
    }
  }
  
  const handleQwenStarted = (sessionId: string) => {
    console.log('Qwen-Omni会话已开始:', sessionId)
    isQwenConnected.value = true
    qwenSessionId.value = sessionId
    
    // 清除之前的音频和文本块
    currentAudioChunks.value = []
    currentTextChunks.value = []
  }
  
  const handleQwenStopped = (sessionId: string) => {
    console.log('Qwen-Omni会话已停止:', sessionId)
    isQwenConnected.value = false
    
    // 将收集到的音频和文本保存到最后一条AI消息
    if (currentAudioChunks.value.length > 0 || currentTextChunks.value.length > 0) {
      const aiMessages = messages.value.filter(m => m.role === 'ai')
      if (aiMessages.length > 0) {
        const lastAIMessage = aiMessages[aiMessages.length - 1]
        
        if (currentAudioChunks.value.length > 0) {
          // 将所有音频块合并为一个Base64字符串
          lastAIMessage!.audioBase64 = currentAudioChunks.value.join('')
        }
        
        if (currentTextChunks.value.length > 0) {
          lastAIMessage!.content = currentTextChunks.value.join('')
        }
      }
    }
  }
  
  const handleQwenError = (errorMsg: string) => {
    console.error('Qwen-Omni错误详情:', {
      message: errorMsg,
      timestamp: new Date().toISOString(),
      sessionId: qwenSessionId.value,
      isConnected: isQwenConnected.value,
      interviewId: interviewId.value,
      position: position.value
    })
    error.value = errorMsg
    ElMessage.error(`Qwen-Omni错误: ${errorMsg}`)
  }
  
  const handleRagResults = (query: string, results: any[]) => {
    console.log('RAG搜索结果:', query, results)
    // 这里可以处理RAG结果，例如显示相关知识点
  }
  
  // 动作
  const startInterview = async (positionParam: string) => {
    try {
      // 清除之前的面试状态
      clearInterview()
      
      isLoading.value = true
      error.value = null
      
      // 调用API开始面试（保持原有的面试记录逻辑）
      const response = await interviewApi.startInterview(positionParam)
      const responseData = response as unknown as StartInterviewResponse
      
      interviewId.value = responseData.interviewId
      position.value = positionParam
      finished.value = false
      
      // 添加首条AI消息（占位）
      addMessage({
        id: 1,
        role: 'ai',
        content: '面试官正在初始化...',
        timestamp: new Date()
      })
      
      currentQuestion.value = responseData.firstQuestion
      
      // 连接到Qwen-Omni
      connectToQwen()
      
      // 使用Qwen-Omni的文本替换占位消息
      setTimeout(() => {
        if (messages.value.length > 0 && messages.value[0]!.role === 'ai') {
          messages.value[0]!.content = responseData.firstQuestion
          // 如果需要，可以在这里发送RAG查询来增强面试官的知识
          if (qwenWebSocket.value?.isConnected()) {
            qwenWebSocket.value.sendRagQuery(responseData.firstQuestion, positionParam)
          }
        }
      }, 1000)
      
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
    if (!interviewId.value || isLoading.value) {
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
      
      // 通过WebSocket发送文本给Qwen-Omni
      if (qwenWebSocket.value?.isConnected()) {
        // 这里需要将文本转换为音频发送，但Qwen-Omni也支持文本输入
        // 暂时先发送一个空的音频，让面试官继续说话
        // 在实际应用中，可以调用TTS服务将文本转换为语音
        console.log('发送文本回答:', answerText)
        
        // 发送RAG查询以获取相关知识点
        qwenWebSocket.value.sendRagQuery(answerText, position.value)
      }
      
      // 仍然调用原有的评估API以保持评分功能
      // 注意：这里简化处理，实际上可能需要调整
      const result = await interviewApi.submitAnswer(
        interviewId.value,
        0, // 问题ID（简化处理）
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
    if (!interviewId.value || isLoading.value) {
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
      
      // 转换为PCM格式
      const pcmBuffer = await audioProcessor.value.convertToPCM(audioBlob)
      
      // 验证PCM格式
      const isValid = audioProcessor.value.validatePCM(pcmBuffer)
      if (!isValid) {
        throw new Error('音频格式验证失败')
      }
      
      const audioBase64 = audioProcessor.value.pcmToBase64(pcmBuffer)
      
      // 通过WebSocket发送音频给Qwen-Omni
      if (qwenWebSocket.value?.isConnected()) {
        qwenWebSocket.value.sendAudio(audioBase64)
        
        // 更新用户消息内容
        const lastUserMessage = messages.value[messages.value.length - 1]
        if (lastUserMessage && lastUserMessage.role === 'user') {
          lastUserMessage.content = '语音回答已发送'
        }
      }
      
    } catch (err) {
      error.value = '提交音频回答失败'
      ElMessage.error('提交音频回答失败')
      throw err
    } finally {
      isLoading.value = false
    }
  }
  
  const sendAudioChunk = async (pcmBuffer: ArrayBuffer) => {
    if (!interviewId.value || !qwenWebSocket.value?.isConnected()) {
      return
    }
    
    try {
      // 验证PCM格式
      const isValid = audioProcessor.value.validatePCM(pcmBuffer)
      if (!isValid) {
        console.error('音频块格式验证失败')
        return
      }
      
      const audioBase64 = audioProcessor.value.pcmToBase64(pcmBuffer)
      qwenWebSocket.value.sendAudio(audioBase64)
    } catch (err) {
      console.error('发送音频块失败:', err)
    }
  }
  
  const sendImage = async (imageBase64: string) => {
    if (!interviewId.value || !qwenWebSocket.value?.isConnected()) {
      return
    }
    
    try {
      qwenWebSocket.value.sendImage(imageBase64)
    } catch (err) {
      console.error('发送图像失败:', err)
    }
  }
  
  const processEvaluationResult = async (result: EvaluationResult) => {
    // 添加AI反馈消息（占位）
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
      disconnectFromQwen()
      ElMessage.success({ message: '面试已完成', duration: 3000 })
    } else {
      // 添加下一轮问题（占位）
      const questionMessageId = messages.value.length + 1
      addMessage({
        id: questionMessageId,
        role: 'ai',
        content: result.nextQuestion,
        timestamp: new Date()
      })
      
      currentQuestion.value = result.nextQuestion
      
      // 发送RAG查询以增强面试官的知识
      if (qwenWebSocket.value?.isConnected()) {
        qwenWebSocket.value.sendRagQuery(result.nextQuestion, position.value)
      }
    }
  }
  
  const endInterview = async () => {
    if (!interviewId.value) {
      throw new Error('没有活跃的面试')
    }

    try {
      isLoading.value = true
      
      // 断开Qwen-Omni连接
      disconnectFromQwen()
      
      // 调用原有的结束面试API
      const result = await interviewApi.endInterview(interviewId.value)
      
      finished.value = true
      ElMessage.success('面试已结束')
      
      return result
    } catch (err) {
      error.value = '结束面试失败'
      ElMessage.error('结束面试失败')
      throw err
    } finally {
      isLoading.value = false
    }
  }
  
  const disconnectFromQwen = () => {
    if (qwenWebSocket.value) {
      qwenWebSocket.value.disconnect()
      qwenWebSocket.value = null
    }
    isQwenConnected.value = false
    qwenSessionId.value = ''
  }
  
  const addMessage = (message: QwenInterviewMessage) => {
    messages.value.push(message)
  }
  
  const clearInterview = () => {
    interviewId.value = null
    position.value = ''
    messages.value = []
    currentQuestion.value = ''
    isLoading.value = false
    isRecording.value = false
    finished.value = false
    error.value = null
    
    disconnectFromQwen()
    currentAudioChunks.value = []
    currentTextChunks.value = []
  }
  
  const setRecording = (recording: boolean) => {
    isRecording.value = recording
  }
  
  // 清理
  const cleanup = () => {
    disconnectFromQwen()
    audioProcessor.value.destroy()
  }

  return {
    // 状态
    interviewId,
    position,
    messages,
    currentQuestion,
    isLoading,
    isRecording,
    finished,
    error,
    
    // Qwen-Omni状态
    qwenWebSocket,
    qwenSessionId,
    isQwenConnected,
    audioProcessor,
    currentAudioChunks,
    currentTextChunks,
    
    // 计算属性
    currentRound,
    lastMessage,
    
    // 动作
    startInterview,
    sendAnswer,
    sendAudioAnswer,
    sendAudioChunk,
    sendImage,
    endInterview,
    connectToQwen,
    disconnectFromQwen,
    addMessage,
    clearInterview,
    setRecording,
    cleanup
  }
})