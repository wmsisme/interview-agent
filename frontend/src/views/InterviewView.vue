<template>
  <div class="interview-view">
    <div class="header">
      <el-page-header @back="goBack">
        <template #content>
          <div class="header-content">
            <span class="position">{{ positionName }}</span>
            <el-tag v-if="currentRound" type="primary">第{{ currentRound }}轮</el-tag>
          </div>
        </template>
        <template #extra>
          <el-button v-if="!finished" type="danger" @click="endInterview" :loading="loading">
            结束面试
          </el-button>
          <el-button v-else type="primary" @click="goToReport">
            查看报告
          </el-button>
        </template>
      </el-page-header>
    </div>

    <div class="interview-container">
      <!-- 对话区域 -->
      <div class="chat-area" ref="chatArea">
        <div v-for="(message, index) in messages" :key="index" class="message-wrapper">
          <MessageBubble :message="message" @play-audio="playAudio" />
        </div>
        <div v-if="loading" class="loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>AI正在思考...</span>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <div v-if="!finished" class="input-container">
          <div class="input-mode-toggle">
            <el-radio-group v-model="inputMode" size="large">
              <el-radio-button value="text">
                <el-icon><EditPen /></el-icon>
                <span>文本输入</span>
              </el-radio-button>
              <el-radio-button value="voice">
                <el-icon><Microphone /></el-icon>
                <span>语音输入</span>
              </el-radio-button>
            </el-radio-group>
          </div>

          <div v-if="inputMode === 'text'" class="text-input">
            <el-input
              v-model="textInput"
              type="textarea"
              :rows="3"
              placeholder="请输入您的回答..."
              :disabled="loading"
              @keyup.enter.exact.prevent="submitTextAnswer"
            />
            <el-button
              type="primary"
              :loading="loading"
              :disabled="!textInput.trim()"
              @click="submitTextAnswer"
              class="send-button"
            >
              发送回答
            </el-button>
          </div>

          <div v-else class="voice-input">
            <AudioRecorder
              :disabled="loading"
              @recording-start="onRecordingStart"
              @recording-stop="onRecordingStop"
              @audio-ready="onAudioReady"
              @text-ready="onTextReady"
              @partial-text="onPartialText"
            />
          </div>
        </div>

        <div v-else class="interview-finished">
          <el-result
            icon="success"
            title="面试已完成"
            sub-title="您可以查看详细的评估报告"
          >
            <template #extra>
              <el-button type="primary" @click="goToReport">查看报告</el-button>
              <el-button @click="goHome">返回首页</el-button>
            </template>
          </el-result>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { EditPen, Microphone, Loading } from '@element-plus/icons-vue'
import MessageBubble from '@/components/MessageBubble.vue'
import AudioRecorder from '@/components/AudioRecorder.vue'
import { useInterviewStore } from '@/stores/interview'
import { playTTS } from '@/api/voice'

const route = useRoute()
const router = useRouter()
const interviewStore = useInterviewStore()

const loading = ref(false)
const inputMode = ref<'text' | 'voice'>('text')
const textInput = ref('')
const chatArea = ref<HTMLElement>()
const initialTTSPlayed = ref(false)
const currentRound = computed(() => interviewStore.messages.filter(m => m.role === 'ai').length)

const positionName = computed(() => {
  const positions: Record<string, string> = {
    'java_backend': 'Java后端开发工程师',
    'web_frontend': 'Web前端开发工程师'
  }
  return positions[interviewStore.position || ''] || interviewStore.position || '未知岗位'
})

const messages = computed(() => interviewStore.messages)
const finished = computed(() => interviewStore.finished)

const scrollToBottom = () => {
  nextTick(() => {
    if (chatArea.value) {
      chatArea.value.scrollTop = chatArea.value.scrollHeight
    }
  })
}

watch(messages, scrollToBottom, { deep: true })

const goBack = () => {
  console.log('goBack called, finished:', finished.value, 'history length:', window.history.length)
  
  if (!finished.value && interviewStore.messages.length > 0) {
    ElMessageBox.confirm('确定要离开吗？未完成的面试将不会被保存。', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      console.log('User confirmed leaving interview')
      // 尝试返回上一页，如果失败则返回首页
      if (window.history.length > 1) {
        console.log('Navigating back with router.go(-1)')
        router.go(-1)
      } else {
        console.log('No history, navigating to home with router.push("/")')
        router.push('/')
      }
    }).catch(() => {
      console.log('User canceled leaving interview')
    })
  } else {
    console.log('Interview finished or no messages, navigating directly')
    // 面试已完成或没有消息，直接返回上一页
    if (window.history.length > 1) {
      console.log('Navigating back with router.go(-1)')
      router.go(-1)
    } else {
      console.log('No history, navigating to home with router.push("/")')
      router.push('/')
    }
  }
}

const goToReport = () => {
  if (interviewStore.interviewId) {
    router.push(`/report/${interviewStore.interviewId}`)
  }
}

const goHome = () => {
  console.log('InterviewView.goHome called, navigating to home')
  router.push('/')
}

const endInterview = async () => {
  try {
    console.log('用户点击结束面试按钮')
    loading.value = true
    await interviewStore.endInterview()
    // 注意：store中的endInterview已经显示成功消息
    // 这里不需要再显示，避免重复消息
  } catch (error) {
    console.error('结束面试捕获到错误:', error)
    // 注意：store中的endInterview已经显示错误消息
    // 这里不需要再显示，避免重复消息
  } finally {
    loading.value = false
  }
}

const submitTextAnswer = async () => {
  if (!textInput.value.trim() || loading.value) return
  
  try {
    loading.value = true
    await interviewStore.sendAnswer(textInput.value.trim())
    textInput.value = ''
  } catch (error) {
    ElMessage.error('提交回答失败')
  } finally {
    loading.value = false
  }
}

const onRecordingStart = () => {
  console.log('开始录音')
}

const onRecordingStop = () => {
  console.log('停止录音')
}

const onAudioReady = async (audioBlob: Blob) => {
  try {
    loading.value = true
    await interviewStore.sendAudioAnswer(audioBlob)
  } catch (error) {
    ElMessage.error('提交音频回答失败')
  } finally {
    loading.value = false
  }
}

const onTextReady = async (text: string) => {
  try {
    loading.value = true
    await interviewStore.sendAnswer(text)
  } catch (error) {
    ElMessage.error('提交文本回答失败')
  } finally {
    loading.value = false
  }
}

const onPartialText = (text: string) => {
  console.log('部分识别结果:', text)
}

const playAudio = (url: string) => {
  const audio = new Audio(url)
  audio.play()
}

onMounted(() => {
  // 如果还没有开始面试，跳转回首页
  if (!interviewStore.interviewId) {
    router.push('/')
    return
  }
  
  // 页面加载完成后播放首条问题的TTS
  // 使用setTimeout确保页面渲染完成后再播放
  setTimeout(() => {
    if (!initialTTSPlayed.value && interviewStore.messages.length > 0) {
      // 查找第一条AI消息
      const firstAIMessage = interviewStore.messages.find(msg => msg.role === 'ai')
      if (firstAIMessage && firstAIMessage.content) {
        console.log('播放首条问题的TTS:', firstAIMessage.content.substring(0, 50) + '...')
        playTTS(firstAIMessage.content).catch(error => {
          console.error('播放首条问题TTS失败:', error)
          // 静默失败，不影响面试流程
        })
        initialTTSPlayed.value = true
      }
    }
  }, 500) // 500ms延迟，确保页面完全加载
})
</script>

<style scoped>
.interview-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  padding: 1rem;
  background: white;
  border-bottom: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.position {
  font-size: 1.25rem;
  font-weight: 600;
}

.interview-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 1rem;
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
}

.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  background: white;
  border-radius: var(--radius-lg);
  margin-bottom: 1rem;
  box-shadow: var(--shadow-sm);
}

.message-wrapper {
  margin-bottom: 1rem;
}

.loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-secondary);
  padding: 1rem;
}

.input-area {
  background: white;
  border-radius: var(--radius-lg);
  padding: 1rem;
  box-shadow: var(--shadow-md);
}

.input-mode-toggle {
  margin-bottom: 1rem;
  display: flex;
  justify-content: center;
}

.text-input {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.send-button {
  align-self: flex-end;
}

.voice-input {
  display: flex;
  justify-content: center;
}

.interview-finished {
  padding: 2rem;
}
</style>