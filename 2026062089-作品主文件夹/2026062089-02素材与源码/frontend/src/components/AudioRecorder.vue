<template>
  <div class="audio-recorder">
    <div class="recorder-container">
      <!-- 录音按钮 -->
      <div class="recorder-button-container">
        <el-button
          class="recorder-button"
          :class="{ 'recording': isRecording, 'disabled': disabled }"
          :type="isRecording ? 'danger' : 'primary'"
          :size="'large'"
          :circle="true"
          @click="toggleRecording"
          :disabled="disabled"
        >
          <template #icon>
            <el-icon v-if="!isRecording"><Microphone /></el-icon>
            <el-icon v-else class="pulse-animation"><Microphone /></el-icon>
          </template>
        </el-button>
      </div>

      <!-- 录音状态显示 -->
      <div class="recorder-status">
        <div v-if="isRecording" class="recording-status">
          <div class="recording-indicator">
            <span class="pulse-dot"></span>
            <span class="recording-text">录音中...</span>
          </div>
          <div class="recording-time">
            <el-icon><Clock /></el-icon>
            <span>{{ formattedTime }}</span>
          </div>
        </div>
        <div v-else class="idle-status">
          <span class="idle-text">长按按钮开始录音</span>
          <span class="hint-text">松开按钮结束录音</span>
        </div>
      </div>

      <!-- 波形显示 -->
      <div v-if="isRecording" class="waveform-container">
        <canvas ref="waveformCanvas" class="waveform-canvas"></canvas>
      </div>

      <!-- 实时识别文本 -->
      <div v-if="partialText && !showEdit" class="partial-text">
        <div class="partial-text-label">实时识别：</div>
        <div class="partial-text-content">{{ partialText }}</div>
      </div>

      <!-- 文本编辑区域 -->
      <div v-if="showEdit && editedText" class="text-edit-area">
        <div class="edit-label">编辑识别文本：</div>
        <el-input
          v-model="editedText"
          type="textarea"
          :rows="3"
          placeholder="请编辑或确认识别文本..."
          :disabled="disabled"
          class="text-edit-input"
        />
        <div class="edit-buttons">
          <el-button
            type="primary"
            size="small"
            @click="submitEditedText"
            :loading="submitting"
            :disabled="!editedText.trim()"
          >
            提交文本
          </el-button>
          <el-button
            type="warning"
            size="small"
            @click="reRecord"
            :disabled="disabled"
          >
            重新录音
          </el-button>
          <el-button
            type="info"
            size="small"
            @click="cancelEdit"
            :disabled="disabled"
          >
            取消编辑
          </el-button>
        </div>
      </div>

      <!-- 控制按钮 -->
      <div class="control-buttons">
        <el-button
          v-if="isRecording"
          type="danger"
          size="small"
          @click="cancelRecording"
          :disabled="disabled"
        >
          取消录音
        </el-button>
        <el-button
          v-if="!isRecording && audioBlob && !showEdit"
          type="primary"
          size="small"
          @click="playRecording"
          :disabled="disabled"
        >
          试听录音
        </el-button>
        <el-button
          v-if="!isRecording && audioBlob && !showEdit"
          type="success"
          size="small"
          @click="submitRecording"
          :loading="submitting"
          :disabled="disabled"
        >
          提交录音
        </el-button>
      </div>
    </div>

    <!-- 音频播放器（隐藏） -->
    <audio ref="audioPlayer" class="audio-player"></audio>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Microphone, Clock } from '@element-plus/icons-vue'
import { AudioRecorder as AudioRecorderUtil, createAudioWaveformCanvas } from '@/utils/audio'
import VoiceWebSocket from '@/api/websocket'

interface Props {
  disabled?: boolean
  interviewId?: number
  questionId?: number
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  interviewId: 0,
  questionId: 0
})

const emit = defineEmits<{
  'recording-start': []
  'recording-stop': []
  'audio-ready': [blob: Blob]
  'text-ready': [text: string]
  'partial-text': [text: string]
}>()

// 状态
const isRecording = ref(false)
const recordingTime = ref(0)
const timer = ref<number | null>(null)
const audioRecorder = ref<AudioRecorderUtil | null>(null)
const audioBlob = ref<Blob | null>(null)
const submitting = ref(false)
const partialText = ref('')
const editedText = ref('')
const showEdit = ref(false)
const voiceWebSocket = ref<VoiceWebSocket | null>(null)

// 引用
const waveformCanvas = ref<HTMLCanvasElement>()
const audioPlayer = ref<HTMLAudioElement>()

// 计算属性
const formattedTime = computed(() => {
  const minutes = Math.floor(recordingTime.value / 60)
  const seconds = recordingTime.value % 60
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
})

// 切换录音状态
const toggleRecording = async () => {
  if (props.disabled) return
  
  if (isRecording.value) {
    // 如果正在录音，则停止录音
    await stopRecording()
  } else {
    // 如果未录音，则开始录音
    await startRecording()
  }
}

// 开始录音
const startRecording = async () => {
  if (props.disabled || isRecording.value) return
  
  try {
    isRecording.value = true
    recordingTime.value = 0
    audioBlob.value = null
    partialText.value = ''
    editedText.value = ''
    showEdit.value = false
    
    // 创建录音器
    audioRecorder.value = new AudioRecorderUtil()
    await audioRecorder.value.startRecording()
    
    // 启动计时器
    timer.value = setInterval(() => {
      recordingTime.value++
      // 更新波形
      updateWaveform()
    }, 1000)
    
    // 连接WebSocket进行实时语音识别
    if (props.interviewId && props.questionId) {
      voiceWebSocket.value = new VoiceWebSocket()
      voiceWebSocket.value.connectAndStart(
        props.interviewId,
        props.questionId,
        {
          onPartialText: (text) => {
            partialText.value = text
            emit('partial-text', text)
          },
          onFinalText: (text) => {
            partialText.value = text
            emit('partial-text', text)
          },
          onError: (error) => {
            console.error('WebSocket错误:', error)
            ElMessage.warning('实时语音识别连接失败，将使用普通录音模式')
          },
          onStarted: (sessionId) => {
            console.log('WebSocket会话已启动:', sessionId)
            // WebSocket连接成功后，设置音频数据回调
            if (audioRecorder.value) {
              audioRecorder.value.setOnDataAvailable(async (audioBlob: Blob) => {
                try {
                  // 将WebM Blob转换为ArrayBuffer并发送到WebSocket
                  const arrayBuffer = await audioBlob.arrayBuffer()
                  voiceWebSocket.value?.sendAudioData(arrayBuffer)
                } catch (error) {
                  console.error('发送音频数据到WebSocket失败:', error)
                }
              })
            }
          }
        }
      )
    } else {
      // 如果没有WebSocket连接，仍然设置一个简单的回调以收集数据
      if (audioRecorder.value) {
        audioRecorder.value.setOnDataAvailable((audioBlob: Blob) => {
          // 仅收集数据，不发送到WebSocket
          console.debug('音频数据块:', audioBlob.size, 'bytes')
        })
      }
    }
    
    emit('recording-start')
    ElMessage.success('开始录音')
  } catch (error) {
    console.error('开始录音失败:', error)
    ElMessage.error('无法访问麦克风，请检查权限')
    stopRecording()
  }
}

// 停止录音
const stopRecording = async () => {
  if (!isRecording.value || !audioRecorder.value) return
  
  try {
    // 停止计时器
    if (timer.value) {
      clearInterval(timer.value)
      timer.value = null
    }
    
    // 停止录音
    const blob = await audioRecorder.value.stopRecording()
    audioBlob.value = blob
    
    // 停止WebSocket
    if (voiceWebSocket.value) {
      voiceWebSocket.value.stop()
      voiceWebSocket.value = null
    }
    
    emit('recording-stop')
    ElMessage.success(`录音完成，时长: ${formattedTime.value}`)
  } catch (error) {
    console.error('停止录音失败:', error)
    ElMessage.error('录音失败')
  } finally {
    isRecording.value = false
    // 设置编辑文本为识别结果
    editedText.value = partialText.value || ''
    showEdit.value = true
  }
}

// 取消录音
const cancelRecording = () => {
  if (audioRecorder.value) {
    audioRecorder.value.cancelRecording()
  }
  
  if (timer.value) {
    clearInterval(timer.value)
    timer.value = null
  }
  
  if (voiceWebSocket.value) {
    voiceWebSocket.value.close()
    voiceWebSocket.value = null
  }
  
  isRecording.value = false
  recordingTime.value = 0
  audioBlob.value = null
  partialText.value = ''
  editedText.value = ''
  showEdit.value = false
  
  ElMessage.info('已取消录音')
}

// 更新波形
const updateWaveform = () => {
  if (!waveformCanvas.value || !isRecording.value) return
  
  // 模拟波形数据（实际项目中应该从音频分析器获取）
  const ctx = waveformCanvas.value.getContext('2d')
  if (!ctx) return
  
  const width = waveformCanvas.value.width
  const height = waveformCanvas.value.height
  
  ctx.clearRect(0, 0, width, height)
  ctx.fillStyle = '#3b82f6'
  
  // 生成随机波形
  const barCount = 50
  const barWidth = width / barCount
  
  for (let i = 0; i < barCount; i++) {
    const barHeight = Math.random() * height * 0.8 + height * 0.1
    ctx.fillRect(i * barWidth, height - barHeight, barWidth - 2, barHeight)
  }
}

// 试听录音
const playRecording = () => {
  if (!audioBlob.value || !audioPlayer.value) return
  
  const audioUrl = URL.createObjectURL(audioBlob.value)
  audioPlayer.value.src = audioUrl
  audioPlayer.value.play().catch(error => {
    console.error('播放录音失败:', error)
    ElMessage.error('播放录音失败')
  })
}

// 提交录音
const submitRecording = () => {
  if (!audioBlob.value) {
    ElMessage.warning('没有可提交的录音')
    return
  }
  
  submitting.value = true
  try {
    emit('audio-ready', audioBlob.value)
    ElMessage.success('录音已提交')
  } catch (error) {
    console.error('提交录音失败:', error)
    ElMessage.error('提交录音失败')
  } finally {
    submitting.value = false
  }
}

// 提交编辑文本
const submitEditedText = () => {
  if (!editedText.value.trim()) {
    ElMessage.warning('请输入文本内容')
    return
  }
  
  submitting.value = true
  try {
    emit('text-ready', editedText.value.trim())
    ElMessage.success('文本已提交')
    // 清空状态
    editedText.value = ''
    showEdit.value = false
    audioBlob.value = null
    partialText.value = ''
  } catch (error) {
    console.error('提交文本失败:', error)
    ElMessage.error('提交文本失败')
  } finally {
    submitting.value = false
  }
}

// 重新录音
const reRecord = () => {
  editedText.value = ''
  showEdit.value = false
  audioBlob.value = null
  partialText.value = ''
  ElMessage.info('可以重新开始录音')
}

// 取消编辑
const cancelEdit = () => {
  editedText.value = ''
  showEdit.value = false
  ElMessage.info('已取消编辑')
}

// 发送音频数据到WebSocket（用于实时识别）
const sendAudioToWebSocket = (audioData: ArrayBuffer) => {
  if (voiceWebSocket.value && isRecording.value) {
    voiceWebSocket.value.sendAudioData(audioData)
  }
}

// 生命周期
onMounted(() => {
  // 初始化波形画布
  if (waveformCanvas.value) {
    waveformCanvas.value.width = waveformCanvas.value.clientWidth
    waveformCanvas.value.height = 60
  }
})

onUnmounted(() => {
  // 清理资源
  if (timer.value) {
    clearInterval(timer.value)
  }
  
  if (voiceWebSocket.value) {
    voiceWebSocket.value.close()
  }
  
  if (audioBlob.value) {
    URL.revokeObjectURL(URL.createObjectURL(audioBlob.value))
  }
})

// 暴露方法给父组件
defineExpose({
  startRecording,
  stopRecording,
  cancelRecording,
  toggleRecording,
  submitEditedText,
  reRecord,
  cancelEdit
})
</script>

<style scoped>
.audio-recorder {
  width: 100%;
}

.recorder-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  background: white;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.recorder-button-container {
  margin-bottom: 1rem;
}

.recorder-button {
  width: 80px;
  height: 80px;
  font-size: 1.5rem;
  transition: all 0.3s ease;
}

.recorder-button:hover:not(.disabled) {
  transform: scale(1.05);
}

.recorder-button.recording {
  animation: pulse 1.5s infinite;
}

.recorder-button.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pulse-animation {
  animation: pulse-icon 0.5s infinite alternate;
}

.recorder-status {
  text-align: center;
  min-height: 40px;
}

.recording-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.recording-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--danger-color);
  font-weight: 600;
}

.pulse-dot {
  width: 10px;
  height: 10px;
  background-color: var(--danger-color);
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

.recording-text {
  font-size: 0.875rem;
}

.recording-time {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.idle-status {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.idle-text {
  font-weight: 600;
  color: var(--text-primary);
}

.hint-text {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.waveform-container {
  width: 100%;
  height: 60px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.waveform-canvas {
  width: 100%;
  height: 100%;
}

.partial-text {
  width: 100%;
  padding: 0.75rem;
  background: var(--background-color);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}

.partial-text-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: 0.25rem;
}

.partial-text-content {
  font-size: 0.875rem;
  color: var(--text-primary);
  line-height: 1.4;
  min-height: 1.2em;
}

.control-buttons {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  justify-content: center;
}

.audio-player {
  display: none;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(239, 68, 68, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0);
  }
}

@keyframes pulse-icon {
  0% {
    transform: scale(1);
  }
  100% {
    transform: scale(1.2);
  }
}

@media (max-width: 640px) {
  .recorder-button {
    width: 70px;
    height: 70px;
  }
  
  .control-buttons {
    flex-direction: column;
    width: 100%;
  }
  
  .control-buttons .el-button {
    width: 100%;
  }
}

/* 文本编辑区域样式 */
.text-edit-area {
  width: 100%;
  padding: 1rem;
  background: var(--background-color);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
}

.edit-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.text-edit-input {
  margin-bottom: 1rem;
}

.text-edit-input :deep(.el-textarea__inner) {
  font-family: inherit;
  font-size: 0.875rem;
  line-height: 1.5;
  resize: vertical;
  min-height: 80px;
}

.edit-buttons {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

.edit-buttons .el-button {
  min-width: 80px;
}
</style>