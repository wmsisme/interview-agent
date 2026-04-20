<template>
  <div class="qwen-audio-recorder">
    <div class="recorder-container">
      <!-- 录音按钮 -->
      <div class="recorder-button-container">
        <el-button
          class="recorder-button"
          :class="{ 'recording': isRecording, 'disabled': disabled }"
          :type="isRecording ? 'danger' : 'primary'"
          :size="'large'"
          :circle="true"
          @mousedown="startRecording"
          @mouseup="stopRecording"
          @touchstart="handleTouchStart"
          @touchend="handleTouchEnd"
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
            <span class="recording-text">实时录音中...</span>
          </div>
          <div class="recording-time">
            <el-icon><Clock /></el-icon>
            <span>{{ formattedTime }}</span>
          </div>
        </div>
        <div v-else class="idle-status">
          <span class="idle-text">按住按钮说话</span>
          <span class="hint-text">Qwen-Omni支持实时语音交互</span>
        </div>
      </div>

      <!-- 波形显示 -->
      <div v-if="isRecording" class="waveform-container">
        <canvas ref="waveformCanvas" class="waveform-canvas"></canvas>
      </div>

      <!-- 音量指示器 -->
      <div v-if="isRecording" class="volume-indicator">
        <div class="volume-bar" :style="{ width: `${volumeLevel}%` }"></div>
        <div class="volume-label">音量: {{ Math.round(volumeLevel) }}%</div>
      </div>

      <!-- 音频预览（录制完成后） -->
      <div v-if="audioBlob && !isRecording" class="audio-preview">
        <div class="preview-label">录制完成</div>
        <div class="preview-controls">
          <el-button type="primary" size="small" @click="playRecording" :disabled="disabled">
            <el-icon><VideoPlay /></el-icon>
            试听
          </el-button>
          <el-button type="success" size="small" @click="submitRecording" :loading="submitting" :disabled="disabled">
            <el-icon><Upload /></el-icon>
            提交
          </el-button>
          <el-button type="warning" size="small" @click="reRecord" :disabled="disabled">
            <el-icon><Refresh /></el-icon>
            重录
          </el-button>
        </div>
      </div>

      <!-- 实时连接状态 -->
      <div class="connection-status">
        <el-tag :type="isConnected ? 'success' : 'warning'" size="small">
          <el-icon><Connection /></el-icon>
          {{ isConnected ? '实时连接已建立' : '等待连接...' }}
        </el-tag>
      </div>
    </div>

    <!-- 音频播放器（隐藏） -->
    <audio ref="audioPlayer" class="audio-player"></audio>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Microphone, Clock, VideoPlay, Upload, Refresh, Connection 
} from '@element-plus/icons-vue'
import { getQwenAudioProcessor } from '@/utils/qwen_audio'

interface Props {
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false
})

const emit = defineEmits<{
  'recording-start': []
  'recording-stop': []
  'audio-chunk': [pcmBuffer: ArrayBuffer]
  'audio-ready': [blob: Blob]
}>()

// 状态
const isRecording = ref(false)
const recordingTime = ref(0)
const timer = ref<number | null>(null)
const audioBlob = ref<Blob | null>(null)
const audioChunks = ref<Blob[]>([])
const submitting = ref(false)
const volumeLevel = ref(0)
const isConnected = ref(false)

// 引用
const waveformCanvas = ref<HTMLCanvasElement>()
const audioPlayer = ref<HTMLAudioElement>()

// 音频处理器
const audioProcessor = ref(getQwenAudioProcessor())
let cleanupStream: (() => void) | null = null

// 计算属性
const formattedTime = computed(() => {
  const minutes = Math.floor(recordingTime.value / 60)
  const seconds = recordingTime.value % 60
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
})

// 波形动画
let animationFrameId: number | null = null
const drawWaveform = () => {
  if (!waveformCanvas.value || !isRecording.value) return
  
  const canvas = waveformCanvas.value
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  const width = canvas.width
  const height = canvas.height
  
  // 清除画布
  ctx.clearRect(0, 0, width, height)
  
  // 绘制背景
  ctx.fillStyle = 'rgba(0, 150, 255, 0.1)'
  ctx.fillRect(0, 0, width, height)
  
  // 绘制波形
  ctx.strokeStyle = '#0066cc'
  ctx.lineWidth = 2
  ctx.beginPath()
  
  const segments = 50
  const segmentWidth = width / segments
  
  for (let i = 0; i < segments; i++) {
    const x = i * segmentWidth + segmentWidth / 2
    const noise = Math.random() * 0.5 + 0.5 // 0.5-1.0的随机值
    const amplitude = height * 0.4 * noise * (volumeLevel.value / 100)
    const y = height / 2 + Math.sin(Date.now() / 100 + i * 0.5) * amplitude
    
    if (i === 0) {
      ctx.moveTo(x, y)
    } else {
      ctx.lineTo(x, y)
    }
  }
  
  ctx.stroke()
  
  // 继续动画
  animationFrameId = requestAnimationFrame(drawWaveform)
}

// 触摸事件处理（防止移动端滚动）
const handleTouchStart = (event: TouchEvent) => {
  event.preventDefault()
  startRecording()
}

const handleTouchEnd = (event: TouchEvent) => {
  event.preventDefault()
  stopRecording()
}

// 开始录音
const startRecording = async () => {
  if (props.disabled || isRecording.value) return
  
  try {
    isRecording.value = true
    recordingTime.value = 0
    audioBlob.value = null
    audioChunks.value = []
    volumeLevel.value = 50
    
    // 开始计时
    timer.value = window.setInterval(() => {
      recordingTime.value++
      
      // 模拟音量变化
      volumeLevel.value = 30 + Math.sin(Date.now() / 300) * 30
    }, 1000)
    
    // 开始波形动画
    if (waveformCanvas.value) {
      drawWaveform()
    }
    
    // 获取麦克风流
    cleanupStream = await audioProcessor.value.getMicrophoneStream(
      async (pcmBuffer) => {
        // 实时发送音频块
        emit('audio-chunk', pcmBuffer)
        
        // 收集音频块（用于最后的完整录音）
        const blob = new Blob([pcmBuffer], { type: 'audio/pcm' })
        audioChunks.value.push(blob)
      },
      (error) => {
        console.error('麦克风流错误:', error)
        ElMessage.error('麦克风访问失败')
        stopRecording()
      }
    )
    
    isConnected.value = true
    emit('recording-start')
    
  } catch (error) {
    console.error('开始录音失败:', error)
    ElMessage.error('开始录音失败')
    stopRecording()
  }
}

// 停止录音
const stopRecording = async () => {
  if (!isRecording.value) return
  
  try {
    // 停止计时
    if (timer.value) {
      clearInterval(timer.value)
      timer.value = null
    }
    
    // 停止波形动画
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId)
      animationFrameId = null
    }
    
    // 清理麦克风流
    if (cleanupStream) {
      cleanupStream()
      cleanupStream = null
    }
    
    // 合并音频块
    if (audioChunks.value.length > 0) {
      audioBlob.value = new Blob(audioChunks.value, { type: 'audio/pcm' })
    }
    
    isRecording.value = false
    volumeLevel.value = 0
    isConnected.value = false
    
    emit('recording-stop')
    
    // 如果有录音，发送完整的录音
    if (audioBlob.value) {
      emit('audio-ready', audioBlob.value)
    }
    
  } catch (error) {
    console.error('停止录音失败:', error)
    ElMessage.error('停止录音失败')
  }
}

// 试听录音
const playRecording = async () => {
  if (!audioBlob.value) return
  
  try {
    // 将Blob转换为PCM然后播放
    const pcmBuffer = await audioProcessor.value.convertToPCM(audioBlob.value)
    const audioBase64 = audioProcessor.value.pcmToBase64(pcmBuffer)
    await audioProcessor.value.playPCMBase64(audioBase64)
  } catch (error) {
    console.error('播放录音失败:', error)
    ElMessage.error('播放录音失败')
  }
}

// 提交录音
const submitRecording = () => {
  if (!audioBlob.value) return
  
  submitting.value = true
  try {
    // 事件已经通过audio-ready发射，这里可以添加额外的处理
    ElMessage.success('录音已提交')
  } catch (error) {
    console.error('提交录音失败:', error)
    ElMessage.error('提交录音失败')
  } finally {
    submitting.value = false
  }
}

// 重新录音
const reRecord = () => {
  audioBlob.value = null
  audioChunks.value = []
  recordingTime.value = 0
}

// 组件生命周期
onMounted(() => {
  // 初始化音频处理器
  audioProcessor.value.init().catch(err => {
    console.warn('音频处理器初始化警告:', err)
  })
  
  // 初始化画布
  if (waveformCanvas.value) {
    const canvas = waveformCanvas.value
    const dpr = window.devicePixelRatio || 1
    canvas.width = canvas.clientWidth * dpr
    canvas.height = canvas.clientHeight * dpr
    
    const ctx = canvas.getContext('2d')
    if (ctx) {
      ctx.scale(dpr, dpr)
    }
  }
})

onUnmounted(() => {
  // 清理资源
  if (isRecording.value) {
    stopRecording()
  }
  
  if (cleanupStream) {
    cleanupStream()
    cleanupStream = null
  }
  
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
    animationFrameId = null
  }
})
</script>

<style scoped>
.qwen-audio-recorder {
  width: 100%;
}

.recorder-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  padding: 1.5rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.recorder-button-container {
  display: flex;
  justify-content: center;
}

.recorder-button {
  width: 80px;
  height: 80px;
  font-size: 1.5rem;
  transition: all 0.3s ease;
}

.recorder-button.recording {
  animation: pulse 1.5s infinite;
  box-shadow: 0 0 20px rgba(245, 108, 108, 0.6);
}

.recorder-button.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes pulse {
  0% { transform: scale(1); box-shadow: 0 0 20px rgba(245, 108, 108, 0.6); }
  50% { transform: scale(1.05); box-shadow: 0 0 30px rgba(245, 108, 108, 0.8); }
  100% { transform: scale(1); box-shadow: 0 0 20px rgba(245, 108, 108, 0.6); }
}

.pulse-animation {
  animation: mic-pulse 1s infinite;
}

@keyframes mic-pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.recorder-status {
  text-align: center;
  min-height: 3rem;
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
}

.pulse-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #f56c6c;
  animation: dot-pulse 1.5s infinite;
}

@keyframes dot-pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.5); opacity: 0.5; }
  100% { transform: scale(1); opacity: 1; }
}

.recording-text {
  font-weight: 600;
  color: #f56c6c;
}

.recording-time {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  color: #606266;
  font-size: 0.9rem;
}

.idle-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.idle-text {
  font-weight: 600;
  color: #409eff;
}

.hint-text {
  color: #909399;
  font-size: 0.85rem;
}

.waveform-container {
  width: 100%;
  height: 80px;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f7fa;
}

.waveform-canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.volume-indicator {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.volume-bar {
  height: 8px;
  background: linear-gradient(90deg, #67c23a, #e6a23c, #f56c6c);
  border-radius: 4px;
  transition: width 0.2s ease;
}

.volume-label {
  text-align: center;
  font-size: 0.85rem;
  color: #606266;
}

.audio-preview {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
  background: #f0f9ff;
  border-radius: 8px;
  border: 1px solid #bae0ff;
}

.preview-label {
  text-align: center;
  font-weight: 600;
  color: #409eff;
}

.preview-controls {
  display: flex;
  justify-content: center;
  gap: 0.75rem;
}

.connection-status {
  display: flex;
  justify-content: center;
}

.audio-player {
  display: none;
}
</style>