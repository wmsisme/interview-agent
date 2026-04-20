<template>
  <div class="qwen-interview-view">
    <div class="header">
      <el-page-header @back="goBack">
        <template #content>
          <div class="header-content">
            <span class="position">{{ positionName }}</span>
            <el-tag v-if="currentRound" type="primary">第{{ currentRound }}轮</el-tag>
            <el-tag v-if="qwenConnected" type="success" class="qwen-status-tag">
              <el-icon><Connection /></el-icon>
              Qwen-Omni已连接
            </el-tag>
            <el-tag v-else type="warning" class="qwen-status-tag">
              <el-icon><Close /></el-icon>
              Qwen-Omni未连接
            </el-tag>
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
          <QwenMessageBubble 
            :message="message" 
            @play-audio="playAudio"
            @retry-audio="retryAudio"
          />
        </div>
        <div v-if="loading" class="loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>AI正在思考...</span>
        </div>
        
        <!-- 实时音频播放状态 -->
        <div v-if="isPlayingAudio" class="audio-playing-status">
          <el-icon class="playing-icon"><VideoPlay /></el-icon>
          <span>正在播放面试官语音...</span>
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
              <el-radio-button value="image" :disabled="!cameraSupported">
                <el-icon><Camera /></el-icon>
                <span>图像输入</span>
              </el-radio-button>
            </el-radio-group>
          </div>

          <!-- 文本输入 -->
          <div v-if="inputMode === 'text'" class="text-input">
            <el-input
              v-model="textInput"
              type="textarea"
              :rows="3"
              placeholder="请输入您的回答..."
              :disabled="loading || !qwenConnected"
              @keyup.enter.exact.prevent="submitTextAnswer"
            />
            <el-button
              type="primary"
              :loading="loading"
              :disabled="!textInput.trim() || !qwenConnected"
              @click="submitTextAnswer"
              class="send-button"
            >
              发送回答
            </el-button>
          </div>

          <!-- 语音输入 -->
          <div v-else-if="inputMode === 'voice'" class="voice-input">
            <QwenAudioRecorder
              :disabled="loading || !qwenConnected"
              @recording-start="onRecordingStart"
              @recording-stop="onRecordingStop"
              @audio-chunk="onAudioChunk"
              @audio-ready="onAudioReady"
            />
            
            <div v-if="qwenConnected" class="voice-hint">
              <el-icon><InfoFilled /></el-icon>
              <span>Qwen-Omni支持实时语音交互，请直接说话</span>
            </div>
          </div>

          <!-- 图像输入 -->
          <div v-else-if="inputMode === 'image'" class="image-input">
            <div class="camera-container" v-if="showCamera">
              <video ref="cameraVideo" class="camera-video" autoplay></video>
              <div class="camera-controls">
                <el-button type="primary" @click="captureImage" :disabled="loading">
                  <el-icon><CameraFilled /></el-icon>
                  拍摄图像
                </el-button>
                <el-button @click="toggleCamera">
                  <el-icon><Refresh /></el-icon>
                  切换摄像头
                </el-button>
              </div>
            </div>
            
            <div v-else class="camera-placeholder">
              <el-button type="primary" @click="startCamera">
                <el-icon><VideoCamera /></el-icon>
                开启摄像头
              </el-button>
            </div>
            
            <div v-if="capturedImage" class="captured-image">
              <img :src="capturedImage" alt="已拍摄的图像" class="preview-image" />
              <div class="image-controls">
                <el-button type="success" @click="sendImage" :loading="loading">
                  发送图像
                </el-button>
                <el-button @click="retryCapture">
                  重新拍摄
                </el-button>
              </div>
            </div>
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
import { ref, computed, onMounted, nextTick, watch, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  EditPen, Microphone, Loading, Connection, Close,
  Camera, CameraFilled, VideoCamera, Refresh, InfoFilled,
  VideoPlay
} from '@element-plus/icons-vue'
import QwenMessageBubble from '@/components/QwenMessageBubble.vue'
import QwenAudioRecorder from '@/components/QwenAudioRecorder.vue'
import { useQwenInterviewStore } from '@/stores/qwen_interview'

const route = useRoute()
const router = useRouter()
const interviewStore = useQwenInterviewStore()

const loading = ref(false)
const inputMode = ref<'text' | 'voice' | 'image'>('voice')
const textInput = ref('')
const chatArea = ref<HTMLElement>()
const isPlayingAudio = ref(false)
const cameraSupported = ref('mediaDevices' in navigator)
const showCamera = ref(false)
const cameraVideo = ref<HTMLVideoElement>()
const capturedImage = ref<string | null>(null)
const cameraStream = ref<MediaStream | null>(null)
const currentCameraFacingMode = ref<'user' | 'environment'>('user')

const positionName = computed(() => {
  const positions: Record<string, string> = {
    'java_backend': 'Java后端开发工程师',
    'web_frontend': 'Web前端开发工程师',
    'fullstack': '全栈开发工程师',
    'bigdata': '大数据工程师'
  }
  return positions[interviewStore.position || ''] || interviewStore.position || '未知岗位'
})

const messages = computed(() => interviewStore.messages)
const finished = computed(() => interviewStore.finished)
const qwenConnected = computed(() => interviewStore.isQwenConnected)
const currentRound = computed(() => interviewStore.currentRound)

const scrollToBottom = () => {
  nextTick(() => {
    if (chatArea.value) {
      chatArea.value.scrollTop = chatArea.value.scrollHeight
    }
  })
}

watch(messages, scrollToBottom, { deep: true })

const goBack = () => {
  if (!finished.value && interviewStore.messages.length > 0) {
    ElMessageBox.confirm('确定要离开吗？未完成的面试将不会被保存。', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      if (window.history.length > 1) {
        router.go(-1)
      } else {
        router.push('/')
      }
    }).catch(() => {
      // 用户取消离开
    })
  } else {
    if (window.history.length > 1) {
      router.go(-1)
    } else {
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
  router.push('/')
}

const endInterview = async () => {
  try {
    loading.value = true
    await interviewStore.endInterview()
  } catch (error) {
    console.error('结束面试失败:', error)
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
  // 可以在这里添加录音开始的UI反馈
}

const onRecordingStop = () => {
  console.log('停止录音')
  // 可以在这里添加录音停止的UI反馈
}

const onAudioChunk = (pcmBuffer: ArrayBuffer) => {
  // 实时发送音频块到Qwen-Omni
  interviewStore.sendAudioChunk(pcmBuffer)
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

const playAudio = async (audioBase64: string) => {
  try {
    isPlayingAudio.value = true
    await interviewStore.audioProcessor.playPCMBase64(audioBase64)
  } catch (error) {
    console.error('播放音频失败:', error)
    ElMessage.error('播放音频失败')
  } finally {
    isPlayingAudio.value = false
  }
}

const retryAudio = (messageId: number) => {
  const message = interviewStore.messages.find(m => m.id === messageId)
  if (message?.audioBase64) {
    playAudio(message.audioBase64)
  }
}

// 摄像头相关功能
const startCamera = async () => {
  if (!cameraSupported.value) {
    ElMessage.error('您的设备不支持摄像头')
    return
  }
  
  try {
    cameraStream.value = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: 'user', // 前置摄像头
        width: { ideal: 1280 },
        height: { ideal: 720 }
      }
    })
    
    // 更新当前摄像头方向
    currentCameraFacingMode.value = 'user'
    
    if (cameraVideo.value) {
      cameraVideo.value.srcObject = cameraStream.value
      showCamera.value = true
    }
  } catch (error) {
    console.error('开启摄像头失败:', error)
    ElMessage.error('开启摄像头失败，请检查权限')
  }
}

const toggleCamera = async () => {
  if (cameraStream.value) {
    cameraStream.value.getTracks().forEach(track => track.stop())
    cameraStream.value = null
  }
  
  try {
    // 切换摄像头方向
    const newFacingMode = currentCameraFacingMode.value === 'user' ? 'environment' : 'user'
    
    cameraStream.value = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: newFacingMode,
        width: { ideal: 1280 },
        height: { ideal: 720 }
      }
    })
    
    // 更新当前摄像头方向
    currentCameraFacingMode.value = newFacingMode
    
    if (cameraVideo.value) {
      cameraVideo.value.srcObject = cameraStream.value
    }
  } catch (error) {
    console.error('切换摄像头失败:', error)
    ElMessage.error('切换摄像头失败')
  }
}

const captureImage = () => {
  if (!cameraVideo.value) return
  
  const canvas = document.createElement('canvas')
  canvas.width = cameraVideo.value.videoWidth
  canvas.height = cameraVideo.value.videoHeight
  
  const ctx = canvas.getContext('2d')
  if (ctx) {
    ctx.drawImage(cameraVideo.value, 0, 0, canvas.width, canvas.height)
    capturedImage.value = canvas.toDataURL('image/jpeg', 0.8)
    
    // 关闭摄像头预览
    if (cameraStream.value) {
      cameraStream.value.getTracks().forEach(track => track.stop())
      cameraStream.value = null
      showCamera.value = false
    }
  }
}

const sendImage = async () => {
  if (!capturedImage.value) return
  
  try {
    loading.value = true
    // 移除数据URL前缀
    const base64Data = capturedImage.value.replace(/^data:image\/\w+;base64,/, '')
    await interviewStore.sendImage(base64Data)
    capturedImage.value = null
    ElMessage.success('图像已发送')
  } catch (error) {
    console.error('发送图像失败:', error)
    ElMessage.error('发送图像失败')
  } finally {
    loading.value = false
  }
}

const retryCapture = () => {
  capturedImage.value = null
  startCamera()
}

onMounted(() => {
  // 如果还没有开始面试，跳转回首页
  if (!interviewStore.interviewId) {
    router.push('/')
    return
  }
  
  // 自动选择语音输入模式（推荐）
  inputMode.value = 'voice'
})

onUnmounted(() => {
  // 清理摄像头流
  if (cameraStream.value) {
    cameraStream.value.getTracks().forEach(track => track.stop())
    cameraStream.value = null
  }
  
  // 清理面试状态
  if (finished.value) {
    interviewStore.cleanup()
  }
})
</script>

<style scoped>
.qwen-interview-view {
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

.qwen-status-tag {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.interview-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  background: var(--background-color);
}

.audio-playing-status {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  color: var(--primary-color);
  background: rgba(var(--primary-rgb), 0.1);
  border-radius: 8px;
  margin-top: 1rem;
}

.playing-icon {
  margin-right: 0.5rem;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.input-area {
  padding: 1.5rem;
  background: white;
  border-top: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
}

.input-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.input-mode-toggle {
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
  min-width: 120px;
}

.voice-input {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.voice-hint {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: var(--info-bg-color);
  border-radius: 8px;
  color: var(--info-color);
  font-size: 0.875rem;
}

.image-input {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.camera-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.camera-video {
  width: 100%;
  max-height: 300px;
  border-radius: 8px;
  background: #000;
}

.camera-controls {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.camera-placeholder {
  display: flex;
  justify-content: center;
  padding: 2rem;
  background: var(--background-color);
  border-radius: 8px;
  border: 2px dashed var(--border-color);
}

.captured-image {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.preview-image {
  width: 100%;
  max-height: 300px;
  object-fit: contain;
  border-radius: 8px;
  background: var(--background-color);
}

.image-controls {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.interview-finished {
  padding: 2rem;
}

.message-wrapper {
  margin-bottom: 1rem;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  color: var(--text-secondary-color);
}

.is-loading {
  margin-right: 0.5rem;
  animation: rotate 1.5s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>