<template>
  <div class="video-interview-view">
    <div class="header">
      <div class="header-inner">
        <div class="header-left">
          <el-button text @click="goBack" class="back-btn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
          </el-button>
          <div class="header-title-group">
            <span class="position">{{ positionName }}</span>
            <div class="header-tags">
              <el-tag v-if="currentRound" type="primary" size="small" round>第{{ currentRound }}轮</el-tag>
              <div v-if="videoConnected" class="status-badge connected">
                <span class="status-dot"></span>
                视频面试已连接
              </div>
              <div v-else class="status-badge disconnected">
                <span class="status-dot"></span>
                视频面试未连接
              </div>
            </div>
          </div>
        </div>
        <div class="header-right">
          <el-button v-if="!finished" type="danger" plain round @click="endInterview" :loading="loading">
            结束面试
          </el-button>
          <el-button v-else type="primary" round @click="goToReport">
            查看报告
          </el-button>
        </div>
      </div>
    </div>

    <div class="video-interview-container">
      <div class="video-area">
        <div class="video-preview">
          <div class="section-head">
            <div>
              <div class="section-eyebrow">摄像头预览</div>
              <h3>您的画面</h3>
            </div>
            <div class="section-actions">
              <el-button plain size="small" round @click="showDebugPanel = !showDebugPanel">
                {{ showDebugPanel ? '收起控制面板' : '展开控制面板' }}
              </el-button>
            </div>
          </div>
          <div v-if="mediaWarningText" class="media-warning">
            <el-alert :title="mediaWarningText" type="warning" :closable="false" show-icon />
          </div>
          <div v-if="!cameraActive" class="permission-actions">
            <el-button type="primary" plain round @click="requestPermissionsAndRefresh" :loading="cameraLoading">
              重新检测设备
            </el-button>
            <span class="permission-hint">页面会自动请求权限，如列表未刷新可点击重试</span>
          </div>
          <div class="video-wrapper">
            <video ref="localVideo" autoplay muted playsinline class="local-video"></video>
            <div v-if="!cameraActive" class="video-placeholder">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.3"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
              <span>摄像头未开启</span>
            </div>
          </div>

          <div v-if="!cameraActive" class="device-selection">
            <div class="device-selector">
              <span class="device-label">摄像头</span>
              <div v-if="videoDevices.length > 0" class="device-dropdown">
                <el-select v-model="selectedVideoDeviceId" placeholder="选择摄像头" size="small" style="width: 200px">
                  <el-option v-for="device in videoDevices" :key="device.deviceId" :label="device.displayLabel" :value="device.deviceId" />
                </el-select>
              </div>
              <div v-else class="device-empty">
                <span class="empty-text">未检测到摄像头</span>
                <el-button link size="small" @click="requestPermissionsAndRefresh">检测刷新</el-button>
              </div>
            </div>
            <div class="device-selector">
              <span class="device-label">麦克风</span>
              <div v-if="audioDevices.length > 0" class="device-dropdown">
                <el-select v-model="selectedAudioDeviceId" placeholder="选择麦克风" size="small" style="width: 200px">
                  <el-option v-for="device in audioDevices" :key="device.deviceId" :label="device.displayLabel" :value="device.deviceId" />
                </el-select>
              </div>
              <div v-else class="device-empty">
                <span class="empty-text">未检测到麦克风</span>
                <el-button link size="small" @click="requestPermissionsAndRefresh">检测刷新</el-button>
              </div>
            </div>
          </div>

          <div class="video-controls">
            <el-button v-if="!cameraActive" type="primary" round @click="startCamera" :loading="cameraLoading" class="control-btn">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
              开启摄像头
            </el-button>
            <el-button v-else type="warning" round @click="stopCamera" class="control-btn">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
              关闭摄像头
            </el-button>
          </div>

          <div v-if="showDebugPanel" class="debug-panel">
            <div class="debug-header">调试信息</div>
            <div class="debug-grid">
              <div>安全上下文: {{ debugState.isSecureContext ? '是' : '否' }}</div>
              <div>协议: {{ debugState.protocol }}</div>
              <div>摄像头权限: {{ debugState.cameraPermission }}</div>
              <div>麦克风权限: {{ debugState.microphonePermission }}</div>
              <div>视频设备数: {{ videoDevices.length }}</div>
              <div>音频设备数: {{ audioDevices.length }}</div>
              <div>videoWidth: {{ debugState.videoWidth }}</div>
              <div>videoHeight: {{ debugState.videoHeight }}</div>
              <div>video readyState: {{ debugState.videoReadyState }}</div>
              <div>流轨道: {{ debugState.trackSummary || '无' }}</div>
              <div>模型状态: {{ modelStatusText }}</div>
            </div>
            <div class="debug-devices" v-if="videoDevices.length || audioDevices.length">
              <div v-for="device in rawDeviceDebug" :key="`${device.kind}-${device.deviceId}`" class="debug-device-row">
                {{ device.kind }} | {{ device.label || '(empty)' }} | {{ device.deviceId }}
              </div>
            </div>
            <div class="debug-log">
              <div v-for="(entry, index) in debugLogs" :key="index" class="debug-log-line">{{ entry }}</div>
            </div>
          </div>
        </div>

        <div class="video-status">
          <div class="section-head">
            <div>
              <div class="section-eyebrow">面试状态</div>
              <h3>实时监控</h3>
            </div>
          </div>
          <div class="status-indicators">
            <div class="status-item" :class="{ active: cameraActive }">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
              <span>摄像头 {{ cameraActive ? '已开启' : '已关闭' }}</span>
            </div>
            <div class="status-item" :class="{ active: microphoneActive }">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
              <span>麦克风 {{ microphoneActive ? '已开启' : '已关闭' }}</span>
            </div>
            <div class="status-item" :class="{ active: videoConnected }">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
              <span>连接 {{ videoConnected ? '已建立' : '未连接' }}</span>
            </div>
            <div class="status-item" :class="{ active: isPlayingAudio }">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
              <span>AI语音 {{ isPlayingAudio ? '播放中' : '静音' }}</span>
            </div>
          </div>

          <div v-if="currentSubtitle" class="subtitle-display">
            <div class="subtitle-label">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/></svg>
              面试官正在发言
            </div>
            <div class="subtitle-text">{{ currentSubtitle }}</div>
          </div>
        </div>
      </div>

      <div class="chat-history">
        <div class="section-head">
          <div>
            <div class="section-eyebrow">对话记录</div>
            <h3>对话历史</h3>
          </div>
          <el-tag type="info" effect="plain" size="small" round>{{ messages.length }} 条消息</el-tag>
        </div>
        <div class="messages-container">
          <div v-for="(message, index) in messages" :key="index" class="message-item" :class="message.role === 'ai' ? 'ai-msg' : 'user-msg'">
            <div class="message-sender">{{ message.role === 'ai' ? '🤖 面试官' : '👤 您' }}</div>
            <div class="message-content">{{ message.content }}</div>
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>
          <div v-if="messages.length === 0" class="empty-messages">
            <el-empty description="对话尚未开始，请先开启摄像头与麦克风" />
          </div>
        </div>
      </div>
    </div>

    <div v-if="!interviewStarted" class="start-interview-section">
      <div class="start-card">
        <div class="start-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        </div>
        <h3>准备开始面试</h3>
        <p>请确保摄像头和麦克风已开启</p>
        <el-button type="primary" size="large" round @click="startVideoInterview" :disabled="!cameraActive || !microphoneActive || loading" :loading="loading" class="start-interview-btn">
          开始视频面试
        </el-button>
      </div>
    </div>

    <audio ref="audioPlayer" @ended="onAudioEnded"></audio>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Connection, Close, VideoCamera, VideoCameraFilled, 
  Microphone, VideoPlay
} from '@element-plus/icons-vue'
import { useInterviewStore } from '@/stores/interview'
import { useUserStore } from '@/stores/user'
import type { InterviewMessage } from '@/stores/interview'
import * as interviewApi from '@/api/interview'
import { io, Socket } from 'socket.io-client'
import { SOCKET_HTTP_BASE_URL } from '@/config/runtime'
import { getQwenAudioProcessor } from '@/utils/qwen_audio'

// 自定义设备类型，扩展MediaDeviceInfo
interface ExtendedMediaDeviceInfo extends MediaDeviceInfo {
  displayLabel: string
}

const router = useRouter()
const route = useRoute()
const interviewStore = useInterviewStore()
const userStore = useUserStore()

// Refs
const localVideo = ref<HTMLVideoElement>()
const audioPlayer = ref<HTMLAudioElement>()
const loading = ref(false)
const finished = ref(false)
const interviewStarted = ref(false)
const showDebugPanel = ref(false)

// 媒体状态
const cameraActive = ref(false)
const microphoneActive = ref(false)
const cameraLoading = ref(false)
const videoConnected = ref(false)
const isPlayingAudio = ref(false)

// 数据
const currentSubtitle = ref('')
const modelStatusText = ref('未开始')
const messages = ref<InterviewMessage[]>([])
const currentRound = ref(1)
const debugLogs = ref<string[]>([])
const debugState = ref({
  isSecureContext: false,
  protocol: '',
  cameraPermission: 'unknown',
  microphonePermission: 'unknown',
  videoWidth: 0,
  videoHeight: 0,
  videoReadyState: 0,
  trackSummary: ''
})
const mediaWarningText = computed(() => {
  if (!window.isSecureContext) {
    return '当前页面不是安全上下文。手机浏览器中的摄像头和麦克风通常需要 HTTPS。'
  }

  if (!('mediaDevices' in navigator) || !navigator.mediaDevices?.getUserMedia) {
    return '当前浏览器不支持媒体设备接口。'
  }

  if (!videoDevices.value.length && !audioDevices.value.length) {
    return '浏览器尚未暴露设备列表。页面会自动请求权限并刷新设备。'
  }

  return ''
})
const rawDeviceDebug = computed(() => [
  ...videoDevices.value.map(device => ({
    kind: device.kind,
    label: device.label,
    deviceId: device.deviceId
  })),
  ...audioDevices.value.map(device => ({
    kind: device.kind,
    label: device.label,
    deviceId: device.deviceId
  }))
])

// 媒体流
let localStream: MediaStream | null = null
let videoSocket: Socket | null = null
let videoInterval: number | null = null
let mediaStreamingStarted = false

// 音频处理
let audioContext: AudioContext | null = null
let audioSource: MediaStreamAudioSourceNode | null = null
let audioProcessor: ScriptProcessorNode | AudioWorkletNode | null = null
let audioInterval: number | null = null
const aiAudioProcessor = getQwenAudioProcessor()
const AUDIO_SAMPLE_RATE = 16000
const AUDIO_CHUNK_SIZE = 800
const AUDIO_CHUNK_SAMPLES = AUDIO_CHUNK_SIZE / 2 // 400 samples (800 bytes / 2 bytes per sample)
let audioBuffer = new Int16Array(0)
let pendingAiTranscript = ''
let aiSpeechBlockUntil = 0

// 设备枚举
const videoDevices = ref<ExtendedMediaDeviceInfo[]>([])
const audioDevices = ref<ExtendedMediaDeviceInfo[]>([])
const selectedVideoDeviceId = ref<string>('')
const selectedAudioDeviceId = ref<string>('')

// 计算属性
const positionName = computed(() => {
  const position = interviewStore.position || 'java_backend'
  const positionMap: Record<string, string> = {
    'java_backend': 'Java后端开发',
    'web_frontend': 'Web前端开发', 
    'fullstack_engineer': '全栈工程师',
    'bigdata_engineer': '大数据工程师'
  }
  return positionMap[position] || '技术面试'
})

// 生命周期
onMounted(() => {
  updateDebugState()
  // 枚举设备
  enumerateDevices()
  // 检查设备权限
  checkMediaPermissions()
  // 在安全上下文中，自动按 WebRTC sample 的方式请求权限后再刷新设备列表
  if (window.isSecureContext && navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === 'function') {
    requestPermissionsAndRefresh(true)
  }

  if (localVideo.value) {
    localVideo.value.onloadedmetadata = () => {
      pushDebugLog(`video loadedmetadata ${localVideo.value?.videoWidth}x${localVideo.value?.videoHeight}`)
      updateVideoDebug()
    }
    localVideo.value.oncanplay = () => {
      pushDebugLog('video canplay')
      updateVideoDebug()
    }
    localVideo.value.onplaying = () => {
      pushDebugLog('video playing')
      updateVideoDebug()
    }
    localVideo.value.onerror = () => {
      pushDebugLog('video element error')
      updateVideoDebug()
    }
  }
})

onUnmounted(() => {
  cleanup()
})

const pushDebugLog = (message: string) => {
  const timestamp = new Date().toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
  debugLogs.value.unshift(`[${timestamp}] ${message}`)
  debugLogs.value = debugLogs.value.slice(0, 20)
}

const updateVideoDebug = () => {
  debugState.value.videoWidth = localVideo.value?.videoWidth || 0
  debugState.value.videoHeight = localVideo.value?.videoHeight || 0
  debugState.value.videoReadyState = localVideo.value?.readyState || 0
}

const updateDebugState = () => {
  debugState.value.isSecureContext = window.isSecureContext
  debugState.value.protocol = window.location.protocol
  updateVideoDebug()
}

const enumerateDevices = async () => {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices()
    pushDebugLog(`enumerateDevices returned ${devices.length} items`)
    
    const videoInputs = devices.filter(device => device.kind === 'videoinput')
    videoDevices.value = videoInputs.map((device, index) => {
      const deviceId = device.deviceId || `video-device-${index}`
      
      return {
        ...device,
        deviceId: deviceId,
        label: device.label || `摄像头 ${index + 1}`,
        displayLabel: device.label || `摄像头 ${index + 1}`
      }
    })
    
    const audioInputs = devices.filter(device => device.kind === 'audioinput')
    audioDevices.value = audioInputs.map((device, index) => {
      const deviceId = device.deviceId || `audio-device-${index}`
      
      return {
        ...device,
        deviceId: deviceId,
        label: device.label || `麦克风 ${index + 1}`,
        displayLabel: device.label || `麦克风 ${index + 1}`
      }
    })
    
    if (videoDevices.value.length > 0) {
      const videoDeviceExists = videoDevices.value.some(device => device.deviceId === selectedVideoDeviceId.value)
      if (!selectedVideoDeviceId.value || !videoDeviceExists) {
        selectedVideoDeviceId.value = videoDevices.value[0]?.deviceId || ''
      }
    } else {
      selectedVideoDeviceId.value = ''
    }
    
    if (audioDevices.value.length > 0) {
      const currentAudioSelected = selectedAudioDeviceId.value
      const audioDeviceExists = audioDevices.value.some(device => device.deviceId === currentAudioSelected)
      if (!currentAudioSelected || !audioDeviceExists) {
        selectedAudioDeviceId.value = audioDevices.value[0]?.deviceId || ''
      }
    } else {
      selectedAudioDeviceId.value = ''
    }
    
    console.log('枚举到的视频设备:', videoDevices.value)
    console.log('枚举到的音频设备:', audioDevices.value)
  } catch (error) {
    console.error('枚举设备失败:', error)
    pushDebugLog(`enumerateDevices failed: ${error instanceof Error ? error.message : String(error)}`)
  }
}

const checkMediaPermissions = async () => {
  try {
    const cameraPermission = await navigator.permissions.query({ name: 'camera' as PermissionName })
    const microphonePermission = await navigator.permissions.query({ name: 'microphone' as PermissionName })
    debugState.value.cameraPermission = cameraPermission.state
    debugState.value.microphonePermission = microphonePermission.state
    pushDebugLog(`permissions camera=${cameraPermission.state} microphone=${microphonePermission.state}`)

    if (cameraPermission.state === 'prompt' || microphonePermission.state === 'prompt') {
      ElMessage.info('请授予摄像头和麦克风权限以开始视频面试')
    }
  } catch (error) {
    console.warn('权限API不支持:', error)
  }
}

const requestPermissionsAndRefresh = async (silent = false) => {
  if (cameraLoading.value) {
    return
  }

  if (!window.isSecureContext) {
    if (!silent) {
      ElMessage.warning('当前页面不是 HTTPS，浏览器可能不会暴露摄像头和麦克风')
    }
    await enumerateDevices()
    return
  }

  if (!navigator.mediaDevices?.getUserMedia) {
    if (!silent) {
      ElMessage.error('当前浏览器不支持媒体设备访问')
    }
    return
  }

  try {
    cameraLoading.value = true
    pushDebugLog('requestPermissionsAndRefresh started')
    const getUserMediaWithTimeout = async (constraints: MediaStreamConstraints, label: string) => {
      return await Promise.race([
        navigator.mediaDevices.getUserMedia(constraints),
        new Promise<never>((_, reject) => {
          window.setTimeout(() => reject(new Error(`${label}权限请求超时`)), 10000)
        })
      ])
    }

    const stopStream = (stream: MediaStream | null) => {
      stream?.getTracks().forEach(track => track.stop())
    }

    try {
      const videoStream = await getUserMediaWithTimeout({ video: true }, '摄像头')
      pushDebugLog(`camera permission stream ok, tracks=${videoStream.getTracks().length}`)
      stopStream(videoStream)
    } finally {
    }

    try {
      const audioStream = await getUserMediaWithTimeout({ audio: true }, '麦克风')
      pushDebugLog(`microphone permission stream ok, tracks=${audioStream.getTracks().length}`)
      stopStream(audioStream)
    } finally {
    }

    await enumerateDevices()

    if (videoDevices.value.length || audioDevices.value.length) {
      if (!silent) {
        ElMessage.success('设备权限已获取，列表已刷新')
      }
    } else {
      if (!silent) {
        ElMessage.warning('已获取权限，但浏览器仍未返回设备列表')
      }
    }
  } catch (error) {
    console.error('检测并授权设备失败:', error)
    pushDebugLog(`requestPermissionsAndRefresh failed: ${error instanceof Error ? error.message : String(error)}`)
    let errorMessage = '无法获取摄像头和麦克风权限'
    if (error instanceof DOMException) {
      if (error.name === 'NotAllowedError') {
        errorMessage = '浏览器拒绝了摄像头或麦克风权限'
      } else if (error.name === 'NotFoundError') {
        errorMessage = '浏览器没有找到可用的摄像头或麦克风'
      } else {
        errorMessage = `${error.name}: ${error.message}`
      }
    } else if (error instanceof Error) {
      errorMessage = error.message
    }
    if (!silent) {
      ElMessage.error(errorMessage)
    }
  } finally {
    cameraLoading.value = false
  }
}

const startCamera = async () => {
  try {
    cameraLoading.value = true
    pushDebugLog(`startCamera selected video=${selectedVideoDeviceId.value || 'none'} audio=${selectedAudioDeviceId.value || 'none'}`)

    if (localStream) {
      localStream.getTracks().forEach(track => {
        track.stop()
      })
      localStream = null
    }

    if (!selectedVideoDeviceId.value) {
      ElMessage.warning('请先选择摄像头设备')
      return
    }
    
    // 查找选中的设备信息
    const selectedVideoDevice = videoDevices.value.find(device => device.deviceId === selectedVideoDeviceId.value)
    if (!selectedVideoDevice) {
      ElMessage.error('选择的摄像头设备不存在，请重新选择')
      return
    }

    const videoConstraints: MediaTrackConstraints = {
      width: { ideal: 640 },
      height: { ideal: 480 },
      frameRate: { ideal: 30 }
    }

    if (selectedVideoDeviceId.value) {
      videoConstraints.deviceId = { exact: selectedVideoDeviceId.value }
    }

    const audioConstraints: MediaTrackConstraints = {
      sampleRate: 16000,
      channelCount: 1,
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true
    }

    if (selectedAudioDeviceId.value) {
      audioConstraints.deviceId = { exact: selectedAudioDeviceId.value }
    }

    const constraints: MediaStreamConstraints = {
      video: videoConstraints,
      audio: audioConstraints
    }

    localStream = await navigator.mediaDevices.getUserMedia(constraints)
    debugState.value.trackSummary = localStream.getTracks()
      .map(track => `${track.kind}:${track.readyState}:${track.enabled ? 'on' : 'off'}`)
      .join(', ')
    pushDebugLog(`getUserMedia success ${debugState.value.trackSummary}`)

    if (localVideo.value) {
      localVideo.value.srcObject = localStream
      localVideo.value.muted = true
      localVideo.value.playsInline = true
      const playResult = localVideo.value.play()
      if (playResult && typeof playResult.catch === 'function') {
        playResult.catch((error: unknown) => {
          pushDebugLog(`video.play failed: ${error instanceof Error ? error.message : String(error)}`)
        })
      }
    }
    
    cameraActive.value = true
    microphoneActive.value = true
    updateVideoDebug()
    ElMessage.success('摄像头和麦克风已开启')
    
  } catch (error) {
    console.error('无法访问摄像头/麦克风:', error)
    pushDebugLog(`startCamera failed: ${error instanceof Error ? error.message : String(error)}`)
    let errorMessage = '无法访问摄像头或麦克风，请检查设备权限'
    if (error instanceof DOMException) {
      errorMessage = `设备访问错误: ${error.name} - ${error.message}`
      if (error.name === 'NotFoundError') {
        errorMessage = `未找到摄像头设备: ${selectedVideoDeviceId.value || '未指定'}`
      } else if (error.name === 'NotAllowedError') {
        errorMessage = '用户拒绝了摄像头或麦克风权限'
      } else if (error.name === 'NotReadableError') {
        errorMessage = '摄像头或麦克风正被其他程序占用'
      } else if (error.name === 'OverconstrainedError') {
        errorMessage = `无法满足摄像头要求。设备ID: ${selectedVideoDeviceId.value || '未指定'}`
      }
    }
    ElMessage.error(errorMessage)
  } finally {
    cameraLoading.value = false
  }
}

const stopCamera = () => {
  if (localStream) {
    localStream.getTracks().forEach(track => track.stop())
    localStream = null
  }
  cameraActive.value = false
  microphoneActive.value = false
  
  if (localVideo.value) {
    localVideo.value.srcObject = null
  }
  debugState.value.trackSummary = ''
  updateVideoDebug()
  
  ElMessage.info('摄像头和麦克风已关闭')
}

// 音频流处理函数
const startAudioStreaming = async () => {
  if (!localStream || !videoSocket) {
    console.error('无法启动音频流：localStream或videoSocket不存在')
    return
  }
  
  try {
    console.log('正在启动音频流采集...')
    
    // 检查本地流是否有音频轨道
    const audioTracks = localStream.getAudioTracks()
    console.log(`本地流音频轨道: ${audioTracks.length}个，第一个轨道状态:`, audioTracks[0]?.enabled ? '启用' : '禁用', audioTracks[0]?.readyState)
    
    if (audioTracks.length === 0) {
      console.error('本地流没有音频轨道，无法采集音频')
      return
    }
    
    // 停止现有的音频处理
    stopAudioStreaming()
    
    // 创建AudioContext
    audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
      sampleRate: AUDIO_SAMPLE_RATE
    })
    
    console.log(`AudioContext创建成功，采样率: ${audioContext.sampleRate}Hz，状态: ${audioContext.state}`)
    
    // 创建音频源节点
    audioSource = audioContext.createMediaStreamSource(localStream)
    
    // 检查是否支持AudioWorklet
    if (audioContext.audioWorklet) {
      try {
        console.log('使用AudioWorkletNode处理音频数据')
        
        // 创建内联的AudioWorklet处理器
        const workletCode = `
          class AudioProcessor extends AudioWorkletProcessor {
            constructor() {
              super()
              this.port.onmessage = this.handleMessage.bind(this)
            }
            
            handleMessage(event) {
              // 可以接收配置消息
            }
            
            process(inputs, outputs, parameters) {
              const input = inputs[0]
              if (!input || input.length === 0) {
                return true
              }
              
              const channelData = input[0]
              const int16Array = new Int16Array(channelData.length)
              let hasValidData = false
              
              for (let i = 0; i < channelData.length; i++) {
                const sample = Math.max(-32768, Math.min(32767, Math.floor(channelData[i] * 32768)))
                int16Array[i] = sample
                if (sample !== 0) {
                  hasValidData = true
                }
              }
              
              if (hasValidData) {
                this.port.postMessage({
                  type: 'audioData',
                  data: int16Array.buffer,
                  length: int16Array.length
                }, [int16Array.buffer])
              }
              
              return true
            }
          }
          
          registerProcessor('audio-processor', AudioProcessor)
        `
        
        // 创建Blob URL并加载worklet
        const blob = new Blob([workletCode], { type: 'application/javascript' })
        const url = URL.createObjectURL(blob)
        await audioContext.audioWorklet.addModule(url)
        URL.revokeObjectURL(url)
        
        // 创建AudioWorkletNode
        const workletNode = new AudioWorkletNode(audioContext, 'audio-processor', {
          numberOfInputs: 1,
          numberOfOutputs: 1,
          outputChannelCount: [1],
          processorOptions: {
            bufferSize: 4096
          }
        })
        
        // 处理来自worklet的音频数据
        workletNode.port.onmessage = (event: MessageEvent) => {
          if (event.data.type === 'audioData') {
            const int16Array = new Int16Array(event.data.data)
            
            // 限制缓冲区大小，避免延迟累积
            processAudioChunk(int16Array, 'AudioWorklet')
          }
        }
        
        audioProcessor = workletNode
        
        console.log('AudioWorkletNode创建成功')
        
      } catch (error) {
        console.warn('AudioWorklet加载失败，回退到ScriptProcessorNode:', error)
        // 回退到ScriptProcessorNode
        createScriptProcessorNode()
      }
    } else {
      console.warn('浏览器不支持AudioWorklet，使用ScriptProcessorNode（已弃用）')
      createScriptProcessorNode()
    }
    
    // ScriptProcessorNode回退实现
    function createScriptProcessorNode() {
      if (!audioContext) {
        console.error('audioContext未初始化')
        return
      }
      audioProcessor = audioContext.createScriptProcessor(4096, 1, 1)
      
      audioProcessor.onaudioprocess = (event: AudioProcessingEvent) => {
        const input = event.inputBuffer.getChannelData(0)
        
        // 检查输入数据是否有效
        if (input.length === 0) {
          console.warn('音频输入数据为空')
          return
        }
        
        // 转换为Int16Array
        const int16Array = new Int16Array(input.length)
        let hasValidData = false
        for (let i = 0; i < input.length; i++) {
          const inputSample = input[i] ?? 0
          const sample = Math.max(-32768, Math.min(32767, Math.floor(inputSample * 32768)))
          int16Array[i] = sample
          if (sample !== 0) {
            hasValidData = true
          }
        }
        
        if (hasValidData) {
          // 限制缓冲区大小，避免延迟累积
          processAudioChunk(int16Array, 'ScriptProcessor')
        } else {
          // 静音数据，可以发送静音帧或忽略
          console.log('收到静音音频数据，忽略或发送静音帧')
        }
      }
    }
    
    // 连接音频节点
    if (!audioSource || !audioProcessor || !audioContext) {
      console.error('无法连接音频节点：音频节点未正确初始化')
      return
    }
    audioSource.connect(audioProcessor)
    audioProcessor.connect(audioContext.destination)
    
    console.log('音频节点连接完成，开始采集音频数据...')
    console.log(`音频处理配置: 采样率${AUDIO_SAMPLE_RATE}Hz, 块大小${AUDIO_CHUNK_SIZE}字节(${AUDIO_CHUNK_SAMPLES}样本, 25ms), 发送间隔50ms`)
    
    // 启动定时发送音频数据
    audioInterval = window.setInterval(() => {
      sendAudioData()
    }, 50) // 每50ms发送一次音频数据
    
    console.log('音频流采集已启动，开始发送音频数据...')
  } catch (error) {
    console.error('启动音频流失败:', error)
  }
}

// 音频缓冲区溢出警告节流
let lastBufferWarnTime = 0

// 处理音频块，限制缓冲区大小避免延迟累积
const processAudioChunk = (int16Array: Int16Array, source: string) => {
  const MAX_BUFFER_SAMPLES = AUDIO_CHUNK_SAMPLES * 25
  
  if (audioBuffer.length > MAX_BUFFER_SAMPLES) {
    const excessSamples = audioBuffer.length - MAX_BUFFER_SAMPLES
    audioBuffer = audioBuffer.slice(excessSamples)
    const now = Date.now()
    if (now - lastBufferWarnTime > 30000 && excessSamples > AUDIO_CHUNK_SAMPLES) {
      lastBufferWarnTime = now
      console.warn(`音频缓冲区过大(${audioBuffer.length + excessSamples}样本)，丢弃${excessSamples}个旧样本`)
    }
  }
  
  // 追加新数据到缓冲区
  const newBuffer = new Int16Array(audioBuffer.length + int16Array.length)
  newBuffer.set(audioBuffer)
  newBuffer.set(int16Array, audioBuffer.length)
  audioBuffer = newBuffer
  
  // 循环排空可发送的音频块，避免数据累积
  while (audioBuffer.length >= AUDIO_CHUNK_SAMPLES && videoSocket?.connected) {
    if (isPlayingAudio.value || Date.now() < aiSpeechBlockUntil) {
      break
    }
    const chunk = audioBuffer.slice(0, AUDIO_CHUNK_SAMPLES)
    const sliceBuffer = chunk.buffer.slice(chunk.byteOffset, chunk.byteOffset + chunk.byteLength)
    const byteArray = new Uint8Array(sliceBuffer)
    
    try {
      videoSocket.emit('audio', byteArray.buffer)
      audioBuffer = audioBuffer.slice(AUDIO_CHUNK_SAMPLES)
    } catch (error) {
      console.warn(`实时发送音频失败(${source})，连接可能已关闭:`, error)
      break
    }
  }
  
  // 调试日志：每10次回调记录一次
  if (Math.random() < 0.1) {
    console.log(`${source}音频数据: ${int16Array.length}个int16样本, 缓冲区总计: ${audioBuffer.length}样本`)
  }
}

const sendAudioData = () => {
  if (!videoSocket || !videoSocket.connected) {
    return
  }

  // AI说话时以及刚说完的一小段时间内都发静音，避免扬声器回采
  if (isPlayingAudio.value || Date.now() < aiSpeechBlockUntil) {
    const silentFrame = new Uint8Array(AUDIO_CHUNK_SIZE).fill(0)
    try {
      videoSocket.emit('audio', silentFrame.buffer)
      console.log(`发送静音帧: AI说话中或刚说完，保持连接`)
    } catch (error) {
      console.warn('发送静音帧失败，连接可能已关闭:', error)
      handleSocketError()
    }
    return
  }
  
  // 如果缓冲区有足够的数据且没有在AI说话期间，发送一个音频块
  if (audioBuffer.length >= AUDIO_CHUNK_SAMPLES) {
    // 提取一个音频块 (AUDIO_CHUNK_SAMPLES个样本)
    const chunk = audioBuffer.slice(0, AUDIO_CHUNK_SAMPLES)
    
    // 正确提取切片对应的缓冲区部分
    const sliceBuffer = chunk.buffer.slice(chunk.byteOffset, chunk.byteOffset + chunk.byteLength)
    const byteArray = new Uint8Array(sliceBuffer)
    
    console.log(`定时器发送音频数据: ${byteArray.length}字节, 缓冲区剩余: ${audioBuffer.length - AUDIO_CHUNK_SAMPLES}样本`)
    
    try {
      // 发送音频数据到WebSocket - 发送Uint8Array的缓冲区数据
      videoSocket.emit('audio', byteArray.buffer)
      // 从缓冲区移除已发送的数据
      audioBuffer = audioBuffer.slice(AUDIO_CHUNK_SAMPLES)
    } catch (error) {
      console.warn('发送音频数据失败，连接可能已关闭:', error)
      handleSocketError()
    }
  } else {
    // 缓冲区不足，发送静音帧以保持连接活跃
    // 800字节的静音帧 (25ms @ 16kHz, 16-bit mono)
    const silentFrame = new Uint8Array(AUDIO_CHUNK_SIZE).fill(0)
    console.log(`发送静音帧: ${silentFrame.length}字节 (缓冲区不足: ${audioBuffer.length}/${AUDIO_CHUNK_SAMPLES}样本，保持连接活跃)`)
    
    try {
      // 发送静音帧
      videoSocket.emit('audio', silentFrame.buffer)
    } catch (error) {
      console.warn('发送静音帧失败，连接可能已关闭:', error)
      handleSocketError()
    }
  }
}

const stopAudioStreaming = () => {
  console.log('停止音频流采集...')
  
  // 清除定时器
  if (audioInterval) {
    clearInterval(audioInterval)
    audioInterval = null
  }
  
  // 断开音频节点连接
  if (audioProcessor) {
    // 如果是AudioWorkletNode，关闭端口
    if (audioProcessor instanceof AudioWorkletNode) {
      audioProcessor.port.close()
    }
    audioProcessor.disconnect()
    audioProcessor = null
  }
  
  if (audioSource) {
    audioSource.disconnect()
    audioSource = null
  }
  
  if (audioContext) {
    audioContext.close().catch(console.error)
    audioContext = null
  }
  
  // 清空音频缓冲区
  audioBuffer = new Int16Array(0)
  
  console.log('音频流采集已停止')
}

const startVideoInterview = async () => {
  if (!localStream) {
    ElMessage.warning('请先开启摄像头和麦克风')
    return
  }

  try {
    loading.value = true
    console.log('开始视频面试...')
    pendingAiTranscript = ''
    currentSubtitle.value = ''

    // 在用户点击手势内提前解锁音频上下文，避免移动端拦截后续AI音频播放
    await aiAudioProcessor.init()
    pushDebugLog('ai audio context unlocked')
    
    // 获取面试ID（应该已在store中设置）
    let interviewId = interviewStore.interviewId
    
    // 如果store中没有interviewId，则创建一个（后备方案）
    if (!interviewId) {
      console.log('store中没有interviewId，创建新的面试记录...')
      // 使用现有API创建面试记录（视频模式）
      const response = await interviewStore.startInterview(interviewStore.position || 'java_backend', true)
      interviewId = interviewStore.interviewId
      console.log('创建面试记录完成，interviewId:', interviewId)
    }
    
    console.log('连接到视频WebSocket，interviewId:', interviewId)
    // 连接到视频WebSocket（确保interviewId是字符串）
    await connectVideoSocket(interviewId?.toString() || '')
    
    console.log('视频WebSocket连接成功，videoSocket状态:', videoSocket?.connected)
    pushDebugLog('socket connected, waiting for backend started event')
    
  } catch (error) {
    console.error('开始视频面试失败:', error)
    ElMessage.error('开始视频面试失败，请重试: ' + (error as Error).message)
  } finally {
    console.log('finally块执行，设置loading.value = false')
    loading.value = false
  }
}

const connectVideoSocket = (interviewId: string): Promise<void> => {
  return new Promise((resolve, reject) => {
    if (videoSocket) {
      console.log('清理旧的Socket.IO连接')
      videoSocket.removeAllListeners()
      videoSocket.disconnect()
      videoSocket = null
    }
    
    videoSocket = io(SOCKET_HTTP_BASE_URL + '/ws/video', {
      path: '/socket.io',
      transports: ['polling'],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 500,
      reconnectionDelayMax: 3000,
      timeout: 30000,
      upgrade: false
    })
    
    let connected = false
    let timeoutId: number | null = null
    
    // 设置超时，避免无限等待
    timeoutId = window.setTimeout(() => {
      if (!connected) {
        console.warn('Socket.IO连接超时')
        reject(new Error('连接超时'))
      }
    }, 20000)
    
    videoSocket.on('connect', () => {
      console.log('视频WebSocket连接已建立')
      console.log('socket id:', videoSocket?.id)
      
      // 立即resolve，让按钮停止转圈
      if (!connected) {
        connected = true
        if (timeoutId) window.clearTimeout(timeoutId)
        resolve()
      }
      
      // 发送开始面试消息
      console.log('发送start_interview事件，interviewId:', interviewId, 'position:', interviewStore.position || 'java_backend')
      videoSocket!.emit('start_interview', {
        interviewId,
        position: interviewStore.position || 'java_backend'
      })
      pushDebugLog('start_interview emitted')
      console.log('start_interview事件已发送')
    })
    
    videoSocket.on('connected', () => {
      console.log('视频WebSocket命名空间已连接')
      if (!connected) {
        connected = true
        if (timeoutId) window.clearTimeout(timeoutId)
        resolve()
      }
    })
    
    videoSocket.on('audio', (data: any) => {
      handleSocketMessage({ type: 'audio', data: data.data })
    })
    
    videoSocket.on('text', (data: any) => {
      handleSocketMessage({ type: 'text', data: data.data })
    })
    
    videoSocket.on('response_done', (data: any) => {
      handleSocketMessage({ type: 'response_done' })
    })

    videoSocket.on('user_text', (data: any) => {
      handleSocketMessage({ type: 'user_text', data: data.data })
    })
    
    videoSocket.on('started', (data: any) => {
      handleSocketMessage({ type: 'started' })
    })
    
    videoSocket.on('stopped', (data: any) => {
      handleSocketMessage({ type: 'stopped' })
    })
    
    videoSocket.on('error', (data: any) => {
      handleSocketMessage({ type: 'error', message: data.message })
    })
    
    videoSocket.on('connect_error', (error: Error & { description?: any; context?: any; type?: string }) => {
      console.warn('Socket.IO connect_error:', error.message || error)
      if (error.description) console.warn('  描述:', error.description)
      if (error.context) console.warn('  上下文:', error.context)
      if (error.type) console.warn('  类型:', error.type)
      console.warn('  连接目标:', SOCKET_HTTP_BASE_URL + '/ws/video')
    })
    
    videoSocket.on('disconnect', (reason: string) => {
      console.log(`Socket.IO连接断开: ${reason}`)
      videoConnected.value = false
      mediaStreamingStarted = false
      
      // 停止媒体流，避免继续发送数据到已关闭的连接
      stopAudioStreaming()
      if (videoInterval) {
        clearInterval(videoInterval)
        videoInterval = null
      }
      // 停止AI音频播放
      isPlayingAudio.value = false
      aiAudioProcessor.destroy()
      
      // 显示断开连接通知
      ElMessage.warning(`连接已断开: ${reason}`)
    })
    
    videoSocket.on('reconnect', (attemptNumber: number) => {
      console.log(`Socket.IO重新连接成功，尝试次数: ${attemptNumber}`)
      // 重新连接后，可能需要重新发送start_interview事件
      if (videoSocket?.connected && interviewStarted.value) {
        console.log('重新连接后重新发送start_interview事件')
        videoSocket.emit('start_interview', {
          interviewId,
          position: interviewStore.position || 'java_backend'
        })
      }
    })
    
    videoSocket.on('reconnect_error', (error: Error) => {
      console.error('Socket.IO重新连接失败:', error)
    })
    
    videoSocket.on('reconnect_failed', () => {
      console.error('Socket.IO重新连接完全失败')
      ElMessage.error('连接断开且无法重新连接，请刷新页面重试')
    })

    videoSocket.onAny((eventName: string, ...args: any[]) => {
      const preview = args.length > 0 ? JSON.stringify(args[0]).slice(0, 120) : ''
      pushDebugLog(`socket event ${eventName}${preview ? ` ${preview}` : ''}`)
    })
  })
}

const handleSocketMessage = (data: any) => {
  const type = data.type
  
  switch (type) {
    case 'audio':
      // 处理AI音频回复
      // 如果面试已结束，忽略音频数据
      if (finished.value) {
        pushDebugLog(`忽略面试结束后的AI音频数据`)
        break
      }
      modelStatusText.value = '已收到AI音频'
      aiSpeechBlockUntil = Date.now() + 2000
      isPlayingAudio.value = true
      pushDebugLog(`received ai audio chunk length=${(data.data || '').length}`)
      playAIAudio(data.data)
      break
    case 'text':
      // 处理AI文本回复（字幕）
      modelStatusText.value = '已收到AI文本'
      pushDebugLog(`received ai text: ${String(data.data || '').slice(0, 30)}`)
      pendingAiTranscript += data.data || ''
      currentSubtitle.value += data.data
      break
    case 'response_done':
      // AI响应完成
      modelStatusText.value = '本轮响应完成'
      aiSpeechBlockUntil = Date.now() + 3000
      if (pendingAiTranscript.trim()) {
        addMessage('ai', pendingAiTranscript.trim())
        currentSubtitle.value = pendingAiTranscript.trim()
      }
      pendingAiTranscript = ''
      setTimeout(() => {
        if (Date.now() >= aiSpeechBlockUntil) {
          isPlayingAudio.value = false
        }
      }, 3000)
      break
    case 'user_text':
      pushDebugLog(`received user text: ${String(data.data || '').slice(0, 30)}`)
      if (String(data.data || '').trim()) {
        addMessage('user', String(data.data).trim())
      }
      break
    case 'started':
      // 以后端 started 作为真正的可推流信号，避免会话未激活时前端抢跑
      if (!mediaStreamingStarted) {
        mediaStreamingStarted = true
        interviewStarted.value = true
        videoConnected.value = true
        modelStatusText.value = '后端会话已启动，等待模型首句'
        pushDebugLog('backend started received, begin media streaming')
        startVideoStreaming()
        startAudioStreaming()
        ElMessage.success('视频面试已开始，请开始对话')
      }
      break
    case 'stopped':
      // 面试已结束
      modelStatusText.value = '会话已结束'
      finished.value = true
      interviewStarted.value = false
      // 停止AI音频播放
      isPlayingAudio.value = false
      aiAudioProcessor.destroy()
      ElMessage.success('视频面试已结束')
      break
    case 'error':
      modelStatusText.value = `错误: ${data.message || '未知错误'}`
      pushDebugLog(`socket error: ${data.message || 'unknown error'}`)
      ElMessage.error(data.message || '视频面试发生错误')
      break
  }
}

const startVideoStreaming = () => {
  if (!localStream || !videoSocket) return
  
  // 每秒发送1帧视频
  videoInterval = window.setInterval(() => {
    if (videoSocket?.connected) {
      captureAndSendVideoFrame()
    }
  }, 1000) // 1 FPS
  
  // 开始发送音频（简化版本，实际应使用AudioWorklet或MediaRecorder）
  // 这里省略音频流发送的实现
}

const captureAndSendVideoFrame = () => {
  if (!localVideo.value || !videoSocket) return
  
  const video = localVideo.value
  const canvas = document.createElement('canvas')
  canvas.width = video.videoWidth || 640
  canvas.height = video.videoHeight || 480
  
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
  
  canvas.toBlob((blob) => {
    if (blob && videoSocket?.connected) {
      const reader = new FileReader()
      reader.onload = () => {
        const base64Data = (reader.result as string).split(',')[1]
        if (videoSocket) {
          videoSocket.emit('image', base64Data)  // 直接发送base64字符串
        }
      }
      reader.readAsDataURL(blob)
    }
  }, 'image/jpeg', 0.8)
}

const playAIAudio = (audioBase64: string) => {
  isPlayingAudio.value = true
  aiAudioProcessor.playPCMBase64(audioBase64)
    .catch((error) => {
      console.error('播放AI音频失败:', error)
      pushDebugLog(`play ai audio failed: ${error instanceof Error ? error.message : String(error)}`)
    })
    .finally(() => {
      isPlayingAudio.value = false
    })
}

const onAudioEnded = () => {
  isPlayingAudio.value = false
}

const addMessage = (sender: 'ai' | 'user', content: string) => {
  messages.value.push({
    id: Date.now(),
    role: sender,
    content,
    timestamp: new Date(),
    audioUrl: undefined,
    scores: undefined
  })
  
  // 自动滚动到底部
  nextTick(() => {
    const container = document.querySelector('.messages-container')
    if (container) {
      container.scrollTop = container.scrollHeight
    }
  })
}

const formatTime = (timestamp: Date | string) => {
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp
  return date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit',
    second: '2-digit'
  })
}

const endInterview = async () => {
  try {
    await ElMessageBox.confirm('确定要结束视频面试吗？', '结束面试', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    loading.value = true
    finished.value = true
    interviewStarted.value = false
    videoConnected.value = false
    console.log('正在结束视频面试，清理资源...')
    
    // 发送停止消息（不等待响应）
    if (videoSocket && videoSocket.connected) {
      videoSocket.emit('stop_interview', {})
      console.log('已发送stop_interview事件')
    }
    
    // 立即停止音频和视频流（同步操作，不阻塞）
    mediaStreamingStarted = false
    stopAudioStreaming()
    isPlayingAudio.value = false
    aiAudioProcessor.destroy()
    
    if (videoInterval) {
      clearInterval(videoInterval)
      videoInterval = null
      console.log('已停止视频流')
    }
    
    // 关闭WebSocket连接
    if (videoSocket) {
      videoSocket.disconnect()
      videoSocket = null
      console.log('已断开WebSocket连接')
    }
    
    // 将对话数据和结束请求合并为一次API调用
    if (interviewStore.interviewId && messages.value.length > 0) {
      const conversationData = messages.value.map(m => ({
        role: m.role,
        content: m.content
      }))
      console.log('正在结束面试并保存对话记录，共', conversationData.length, '条')
      await interviewStore.endInterview(conversationData)
      console.log('面试结束完成')
    } else if (interviewStore.interviewId) {
      await interviewStore.endInterview()
    }
    
    ElMessage.success('视频面试已结束')
    console.log('视频面试资源清理完成')
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('结束面试失败:', error)
      ElMessage.error('结束面试失败')
    }
  } finally {
    loading.value = false
  }
}

const goToReport = () => {
  if (interviewStore.interviewId) {
    router.push(`/report/${interviewStore.interviewId}`)
  }
}

const goBack = () => {
  if (interviewStarted.value && !finished.value) {
    ElMessageBox.confirm('面试正在进行中，确定要离开吗？', '离开页面', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      router.push('/')
    }).catch(() => {})
  } else {
    router.push('/')
  }
}

const handleSocketError = () => {
  console.warn('处理WebSocket连接错误，停止音频流并清理资源')
  // 停止音频流
  stopAudioStreaming()
  // 清除视频间隔
  if (videoInterval) {
    clearInterval(videoInterval)
    videoInterval = null
  }
  // 停止AI音频播放
  isPlayingAudio.value = false
  aiAudioProcessor.destroy()
  // 标记连接已断开
  videoConnected.value = false
  mediaStreamingStarted = false
  // 显示错误提示
  ElMessage.warning('连接已断开，请重新开始面试')
}

const cleanup = () => {
  // 清理资源
  if (videoInterval) {
    clearInterval(videoInterval)
    videoInterval = null
  }
  
  if (videoSocket) {
    videoSocket.disconnect()
    videoSocket = null
  }
  
  mediaStreamingStarted = false
  stopAudioStreaming()
  // 停止AI音频播放
  isPlayingAudio.value = false
  aiAudioProcessor.destroy()
  stopCamera()
}
</script>

<style scoped>
.video-interview-view {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(circle at top left, rgba(255, 255, 255, 0.15), transparent 32%),
    linear-gradient(155deg, #0c1e3d 0%, #153677 35%, #1a5fa8 70%, #2980b9 100%);
}

.header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 4px 24px rgba(10, 31, 68, 0.1);
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  color: #475569;
  font-size: 1.25rem;
  padding: 8px;
  border-radius: var(--radius-lg);
  transition: all var(--transition-fast);
}

.back-btn:hover {
  background: rgba(0, 0, 0, 0.04);
  color: var(--text-primary);
}

.header-title-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-tags {
  display: flex;
  align-items: center;
  gap: 8px;
}

.position {
  font-size: 1.15rem;
  font-weight: 700;
  color: #0f172a;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 500;
}

.status-badge.connected {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(16, 185, 129, 0.06));
  color: #059669;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.status-badge.disconnected {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(245, 158, 11, 0.05));
  color: #d97706;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-badge.connected .status-dot {
  background: #10b981;
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.5);
}

.status-badge.disconnected .status-dot {
  background: #f59e0b;
  box-shadow: 0 0 6px rgba(245, 158, 11, 0.4);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.video-interview-container {
  flex: 1;
  display: flex;
  padding: 20px;
  gap: 20px;
  overflow: hidden;
}

.video-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
}

.video-preview {
  background: rgba(255, 255, 255, 0.95);
  border-radius: var(--radius-2xl);
  padding: 24px;
  box-shadow: 0 16px 48px rgba(10, 31, 68, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-eyebrow {
  margin-bottom: 2px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.video-preview h3,
.video-status h3,
.chat-history h3 {
  margin: 0;
  color: #0f172a;
  font-size: 1.05rem;
  font-weight: 700;
}

.media-warning {
  margin-bottom: 12px;
}

.permission-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.permission-hint {
  color: var(--text-tertiary);
  font-size: 0.8rem;
}

.video-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  margin-bottom: 14px;
}

.local-video {
  width: 100%;
  height: 100%;
  border-radius: var(--radius-xl);
  background: #0f172a;
  object-fit: contain;
}

.video-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: rgba(255, 255, 255, 0.4);
  background: #1e293b;
  border-radius: var(--radius-xl);
  font-size: 0.9rem;
}

.video-controls {
  display: flex;
  gap: 10px;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
}

.control-btn {
  font-weight: 600;
}

.audio-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #f0f9ff;
  border: 1px solid #91caff;
  border-radius: 6px;
  color: #409eff;
  font-size: 12px;
  margin-left: 12px;
}

.debug-panel {
  margin-top: 14px;
  padding: 14px;
  background: linear-gradient(180deg, #0f172a, #16233d);
  color: #e5e7eb;
  border-radius: var(--radius-lg);
  font-size: 12px;
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.debug-header {
  font-weight: 700;
  margin-bottom: 8px;
  color: #93c5fd;
}

.debug-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px 12px;
  margin-bottom: 10px;
}

.debug-devices {
  margin-bottom: 10px;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
}

.debug-device-row {
  word-break: break-all;
  margin-bottom: 4px;
  color: #cbd5e1;
}

.debug-log {
  max-height: 180px;
  overflow-y: auto;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
}

.debug-log-line {
  margin-bottom: 4px;
  word-break: break-word;
  color: #93c5fd;
}

.device-selection {
  margin-bottom: 16px;
  padding: 14px 16px;
  background: linear-gradient(180deg, #f8fbff, #f1f7ff);
  border-radius: var(--radius-lg);
  border: 1px solid #dbeafe;
}

.device-selector {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.device-selector:last-child {
  margin-bottom: 0;
}

.device-label {
  min-width: 72px;
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.device-dropdown {
  flex: 1;
}

.device-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: var(--radius-sm);
  color: #6c757d;
  font-size: 13px;
}

.empty-text {
  color: #6c757d;
  font-size: 0.85rem;
}

:deep(.virtual-camera-option) .el-select-dropdown__item {
  color: #f56c6c !important;
  font-style: italic;
}

:deep(.virtual-camera-option) .el-select-dropdown__item:hover {
  background-color: #fef0f0 !important;
}

.video-status {
  background: rgba(255, 255, 255, 0.95);
  border-radius: var(--radius-2xl);
  padding: 24px;
  box-shadow: 0 16px 48px rgba(10, 31, 68, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
}

.status-indicators {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 52px;
  padding: 12px 14px;
  background: linear-gradient(180deg, #f8fbff, #eef5ff);
  border-radius: var(--radius-lg);
  border: 1px solid #dbeafe;
  color: var(--text-tertiary);
  font-weight: 500;
  font-size: 0.85rem;
  transition: all var(--transition-base);
}

.status-item.active {
  color: #059669;
  background: linear-gradient(180deg, #ecfdf5, #d1fae5);
  border-color: #a7f3d0;
}

.status-item.active svg {
  color: #10b981;
}

.subtitle-display {
  background: linear-gradient(135deg, #f0f7ff, #f8fbff);
  border: 1px solid #bae6fd;
  border-radius: var(--radius-xl);
  padding: 16px;
  margin-top: 16px;
  animation: fadeInUp 0.4s ease;
}

.subtitle-label {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--primary-color);
}

.subtitle-text {
  font-size: 1rem;
  line-height: 1.6;
  color: var(--text-primary);
  min-height: 24px;
}

.chat-history {
  width: 400px;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.95);
  border-radius: var(--radius-2xl);
  padding: 24px;
  box-shadow: 0 16px 48px rgba(10, 31, 68, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
  min-height: 240px;
}

.message-item {
  padding: 12px 14px;
  margin-bottom: 10px;
  border-radius: var(--radius-lg);
  border: 1px solid #dbeafe;
  transition: all var(--transition-fast);
}

.message-item.ai-msg {
  background: linear-gradient(180deg, #f8fbff, #f2f7ff);
}

.message-item.user-msg {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.06), rgba(59, 130, 246, 0.03));
  border-color: rgba(59, 130, 246, 0.15);
}

.message-sender {
  font-weight: 700;
  font-size: 0.8rem;
  margin-bottom: 4px;
}

.ai-msg .message-sender {
  color: var(--primary-color);
}

.user-msg .message-sender {
  color: var(--text-primary);
}

.message-content {
  color: var(--text-primary);
  line-height: 1.55;
  font-size: 0.9rem;
}

.message-time {
  font-size: 0.7rem;
  color: var(--text-tertiary);
  margin-top: 4px;
  text-align: right;
}

.empty-messages {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
}

.start-interview-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: none;
  margin: 20px;
}

.start-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: var(--radius-2xl);
  padding: 40px 48px;
  box-shadow: 0 16px 48px rgba(10, 31, 68, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.start-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.12), rgba(139, 92, 246, 0.12));
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary-color);
  margin-bottom: 8px;
}

.start-card h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.start-card p {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin: 0;
}

.start-interview-btn {
  margin-top: 8px;
  padding: 12px 32px;
  font-size: 1rem;
  font-weight: 600;
}

.start-hint {
  margin-top: 16px;
  color: var(--text-secondary);
  font-size: 14px;
}

@media (max-width: 1200px) {
  .video-interview-container {
    flex-direction: column;
    overflow: auto;
  }

  .chat-history {
    width: 100%;
    min-height: 320px;
  }
}

@media (max-width: 768px) {
  .header-inner {
    padding: 10px 14px;
  }

  .header-title-group {
    flex-wrap: wrap;
    gap: 8px;
  }

  .position {
    font-size: 1rem;
  }

  .video-interview-container {
    padding: 12px;
    gap: 12px;
  }

  .video-preview,
  .video-status,
  .chat-history {
    padding: 16px;
    border-radius: var(--radius-xl);
  }

  .status-indicators {
    grid-template-columns: 1fr;
  }

  .device-selector {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .device-label {
    min-width: 0;
  }

  .section-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .local-video {
    aspect-ratio: 16/9;
    max-height: 280px;
  }

  .start-card {
    padding: 28px 20px;
  }
}
</style>
