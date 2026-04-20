<template>
  <div class="video-interview-view">
    <div class="header">
      <el-page-header @back="goBack">
        <template #content>
          <div class="header-content">
            <span class="position">{{ positionName }}</span>
            <el-tag v-if="currentRound" type="primary">第{{ currentRound }}轮</el-tag>
            <el-tag v-if="videoConnected" type="success" class="video-status-tag">
              <el-icon><Connection /></el-icon>
              视频面试已连接
            </el-tag>
            <el-tag v-else type="warning" class="video-status-tag">
              <el-icon><Close /></el-icon>
              视频面试未连接
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

    <div class="video-interview-container">
      <!-- 视频区域 -->
      <div class="video-area">
        <div class="video-preview">
          <h3>您的摄像头预览</h3>
          <video ref="localVideo" autoplay muted class="local-video"></video>
          
          <!-- 设备选择 -->
          <div v-if="!cameraActive" class="device-selection">
            <div class="device-selector">
              <span class="device-label">摄像头:</span>
              <div v-if="videoDevices.length > 0" class="device-dropdown">
                <el-select 
                  v-model="selectedVideoDeviceId" 
                  placeholder="选择摄像头"
                  size="small"
                  style="width: 200px"
                >
                  <el-option
                  v-for="device in videoDevices"
                  :key="device.deviceId"
                  :label="device.displayLabel"
                  :value="device.deviceId"
                  :class="device.isVirtual ? 'virtual-camera-option' : ''"
                />
                </el-select>
              </div>
              <div v-else class="device-empty">
                <span class="empty-text">未检测到摄像头设备</span>
                <el-button link size="small" @click="enumerateDevices">刷新</el-button>
              </div>
            </div>
            <div class="device-selector">
              <span class="device-label">麦克风:</span>
              <div v-if="audioDevices.length > 0" class="device-dropdown">
                <el-select 
                  v-model="selectedAudioDeviceId" 
                  placeholder="选择麦克风"
                  size="small"
                  style="width: 200px"
                >
                  <el-option
                  v-for="device in audioDevices"
                  :key="device.deviceId"
                  :label="device.displayLabel"
                  :value="device.deviceId"
                />
                </el-select>
              </div>
              <div v-else class="device-empty">
                <span class="empty-text">未检测到麦克风设备</span>
                <el-button link size="small" @click="enumerateDevices">刷新</el-button>
              </div>
            </div>
          </div>
          
          <div class="video-controls">
            <el-button 
              v-if="!cameraActive" 
              type="primary" 
              @click="startCamera"
              :loading="cameraLoading"
            >
              <el-icon><VideoCamera /></el-icon>
              开启摄像头
            </el-button>
            <el-button 
              v-else 
              type="warning" 
              @click="stopCamera"
            >
              <el-icon><VideoCameraFilled /></el-icon>
              关闭摄像头
            </el-button>
            <el-button 
              :type="microphoneActive ? 'warning' : 'primary'" 
              @click="toggleMicrophone"
            >
              <el-icon><Microphone /></el-icon>
              {{ microphoneActive ? '关闭麦克风' : '开启麦克风' }}
            </el-button>
            <div class="audio-hint" v-if="microphoneActive">
              <el-icon><InfoFilled /></el-icon>
              <span>建议使用耳机以避免回音</span>
            </div>
          </div>
        </div>

        <div class="video-status">
          <h3>面试状态</h3>
          <div class="status-indicators">
            <div class="status-item">
              <el-icon :color="cameraActive ? '#67c23a' : '#909399'"><VideoCamera /></el-icon>
              <span>摄像头 {{ cameraActive ? '已开启' : '已关闭' }}</span>
            </div>
            <div class="status-item">
              <el-icon :color="microphoneActive ? '#67c23a' : '#909399'"><Microphone /></el-icon>
              <span>麦克风 {{ microphoneActive ? '已开启' : '已关闭' }}</span>
            </div>
            <div class="status-item">
              <el-icon :color="videoConnected ? '#67c23a' : '#909399'"><Connection /></el-icon>
              <span>视频连接 {{ videoConnected ? '已建立' : '未连接' }}</span>
            </div>
            <div class="status-item">
              <el-icon :color="isPlayingAudio ? '#e6a23c' : '#909399'"><VideoPlay /></el-icon>
              <span>AI语音 {{ isPlayingAudio ? '播放中' : '静音' }}</span>
            </div>
          </div>

          <!-- 字幕显示 -->
          <div v-if="currentSubtitle" class="subtitle-display">
            <h4>面试官发言</h4>
            <div class="subtitle-text">{{ currentSubtitle }}</div>
          </div>
        </div>
      </div>

      <!-- 对话历史区域 -->
      <div class="chat-history">
        <h3>对话历史</h3>
        <div class="messages-container">
          <div v-for="(message, index) in messages" :key="index" class="message-item">
            <div class="message-sender">{{ message.role === 'ai' ? '面试官' : '您' }}</div>
            <div class="message-content">{{ message.content }}</div>
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>
          <div v-if="messages.length === 0" class="empty-messages">
            <el-empty description="对话尚未开始，请开启摄像头和麦克风后开始面试" />
          </div>
        </div>
      </div>
    </div>

    <!-- 开始面试按钮 -->
    <div v-if="!interviewStarted" class="start-interview-section">
      <el-button 
        type="success" 
        size="large" 
        @click="startVideoInterview"
        :disabled="!cameraActive || !microphoneActive || loading"
        :loading="loading"
      >
        <el-icon><VideoPlay /></el-icon>
        开始视频面试
      </el-button>
      <p class="start-hint">请确保摄像头和麦克风已开启，然后点击开始面试</p>
    </div>

    <!-- 音频播放器（隐藏） -->
    <audio ref="audioPlayer" @ended="onAudioEnded"></audio>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Connection, Close, VideoCamera, VideoCameraFilled, 
  Microphone, VideoPlay, InfoFilled 
} from '@element-plus/icons-vue'
import { useInterviewStore } from '@/stores/interview'
import { useUserStore } from '@/stores/user'
import type { InterviewMessage } from '@/stores/interview'
import { io, Socket } from 'socket.io-client'

// 自定义设备类型，扩展MediaDeviceInfo
interface ExtendedMediaDeviceInfo extends MediaDeviceInfo {
  displayLabel: string
  isVirtual?: boolean
  isWebcam?: boolean
  hasDetailedLabel?: boolean
  unavailable?: boolean
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

// 媒体状态
const cameraActive = ref(false)
const microphoneActive = ref(false)
const cameraLoading = ref(false)
const videoConnected = ref(false)
const isPlayingAudio = ref(false)
const hasCameraPermission = ref(false)
const hasMicrophonePermission = ref(false)
const isFirstCameraRequest = ref(true)

// 数据
const currentSubtitle = ref('')
const messages = ref<InterviewMessage[]>([])
const currentRound = ref(1)

// 媒体流
let localStream: MediaStream | null = null
let videoSocket: Socket | null = null
let videoInterval: number | null = null

// 音频处理
let audioContext: AudioContext | null = null
let audioSource: MediaStreamAudioSourceNode | null = null
let audioProcessor: ScriptProcessorNode | null = null
let audioInterval: number | null = null
const AUDIO_SAMPLE_RATE = 16000
const AUDIO_CHUNK_SIZE = 800
const AUDIO_CHUNK_SAMPLES = AUDIO_CHUNK_SIZE / 2 // 400 samples (800 bytes / 2 bytes per sample)
let audioBuffer = new Int16Array(0)

// 设备枚举
const videoDevices = ref<ExtendedMediaDeviceInfo[]>([])
const audioDevices = ref<ExtendedMediaDeviceInfo[]>([])
const selectedVideoDeviceId = ref<string>('')
const selectedAudioDeviceId = ref<string>('')

// 不可用设备跟踪
const unavailableDeviceIds = ref<Set<string>>(new Set())

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
  // 枚举设备
  enumerateDevices()
  // 检查设备权限
  checkMediaPermissions()
})

onUnmounted(() => {
  cleanup()
})

// 方法
const markDeviceAsUnavailable = (deviceId: string) => {
  if (deviceId) {
    unavailableDeviceIds.value.add(deviceId)
    console.warn(`设备标记为不可用: ${deviceId}`)
  }
}

const enumerateDevices = async () => {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices()
    
    // 处理视频设备
    const videoInputs = devices.filter(device => device.kind === 'videoinput')
    videoDevices.value = videoInputs.map((device, index) => {
      // 检测是否为虚拟摄像头或不可用设备
      const label = device.label || ''
      const lowerLabel = label.toLowerCase()
      
      // 扩展的虚拟摄像头检测关键词
      const virtualKeywords = [
        'virtual', '虚拟', 'xiaomi', 'obs', 'manycam', 'vcam', 'screen', 'mirror',
        'droidcam', 'ivcam', 'epoccam', 'camo', 'webcamoid', 'yawcam',
        '虚拟相机', '虚拟摄像头', '屏幕捕获', '屏幕录制', 'desktop', 'monitor',
        'capture', 'recorder', 'mirroring', 'simulated', 'fake', 'dummy'
      ]
      
      // 网络摄像头常见标识（可能断开连接）
      const webcamKeywords = [
        'webcam', 'usb camera', 'usb video', 'integrated camera', 'built-in camera',
        '网络摄像头', 'usb摄像', '摄像头', 'camera', 'hd camera', '720p', '1080p'
      ]
      
      // 检测是否为虚拟摄像头
      let isVirtual = false
      for (const keyword of virtualKeywords) {
        if (lowerLabel.includes(keyword.toLowerCase())) {
          isVirtual = true
          break
        }
      }
      
      // 检测是否为网络摄像头（可能断开连接）
      let isWebcam = false
      for (const keyword of webcamKeywords) {
        if (lowerLabel.includes(keyword.toLowerCase())) {
          isWebcam = true
          break
        }
      }
      
      // 特殊处理：如果标签为空或只有默认标签，可能是权限未授予的设备
      const hasDetailedLabel = Boolean(device.label && device.label.trim() !== '' && 
                              !device.label.toLowerCase().includes('camera') &&
                              !device.label.toLowerCase().includes('摄像头'))
      
      // 确保deviceId有值
      const deviceId = device.deviceId || `video-device-${index}`
      
      // 构建显示标签
      let displayLabel = ''
      if (device.label && device.label.trim() !== '') {
        displayLabel = device.label
        if (isVirtual) {
          displayLabel += ' (虚拟摄像头)'
        } else if (isWebcam) {
          displayLabel += ' (网络摄像头)'
        }
      } else {
        displayLabel = `摄像头 ${index + 1}`
        if (isVirtual) {
          displayLabel += ' (虚拟摄像头)'
        } else if (isWebcam) {
          displayLabel += ' (网络摄像头)'
        }
      }
      
      return {
        ...device,
        deviceId: deviceId,
        label: device.label || `摄像头 ${index + 1}`,
        isVirtual: isVirtual,
        isWebcam: isWebcam,
        hasDetailedLabel: hasDetailedLabel,
        unavailable: unavailableDeviceIds.value.has(deviceId),
        displayLabel: displayLabel
      }
    })
    
    // 处理音频设备
    const audioInputs = devices.filter(device => device.kind === 'audioinput')
    audioDevices.value = audioInputs.map((device, index) => {
      // 确保deviceId有值
      const deviceId = device.deviceId || `audio-device-${index}`
      
      return {
        ...device,
        deviceId: deviceId,
        label: device.label || `麦克风 ${index + 1}`,
        displayLabel: device.label || `麦克风 ${index + 1}`
      }
    })
    
    // 智能选择摄像头设备
    if (videoDevices.value.length > 0) {
      const currentVideoSelected = selectedVideoDeviceId.value
      const videoDeviceExists = videoDevices.value.some(device => device.deviceId === currentVideoSelected)
      
      if (!currentVideoSelected || !videoDeviceExists) {
        // 按优先级选择最佳摄像头：
        // 1. 有详细标签的非虚拟摄像头（最可能可用）
        // 2. 有详细标签的摄像头
        // 3. 非虚拟摄像头
        // 4. 第一个可用的摄像头
        
        const preferredDevices = videoDevices.value.filter(device => 
          device.hasDetailedLabel && !device.isVirtual && !device.unavailable
        )
        
        if (preferredDevices.length > 0) {
          selectedVideoDeviceId.value = preferredDevices[0]?.deviceId || ''
          console.log('选择了有详细标签的非虚拟摄像头:', preferredDevices[0]?.label)
        } else {
          const detailedDevices = videoDevices.value.filter(device => device.hasDetailedLabel && !device.unavailable)
          if (detailedDevices.length > 0) {
            selectedVideoDeviceId.value = detailedDevices[0]?.deviceId || ''
            console.log('选择了有详细标签的摄像头:', detailedDevices[0]?.label)
          } else {
            const nonVirtualDevices = videoDevices.value.filter(device => !device.isVirtual && !device.unavailable)
            if (nonVirtualDevices.length > 0) {
              selectedVideoDeviceId.value = nonVirtualDevices[0]?.deviceId || ''
              console.log('选择了非虚拟摄像头:', nonVirtualDevices[0]?.label)
            } else {
              // 过滤可用设备（非不可用）
              const availableDevices = videoDevices.value.filter(device => !device.unavailable)
              if (availableDevices.length > 0) {
                selectedVideoDeviceId.value = availableDevices[0]?.deviceId || ''
                console.log('选择了第一个可用摄像头:', availableDevices[0]?.label)
              } else {
                selectedVideoDeviceId.value = ''
                console.warn('没有可用的摄像头设备')
              }
            }
          }
        }
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
    
    if (videoDevices.value.length > 0) {
      console.log('视频设备详情:')
      videoDevices.value.forEach((device, index) => {
        const deviceId = device.deviceId || ''
        const idDisplay = deviceId ? `${deviceId.substring(0, 20)}...` : '无ID'
        console.log(`  ${index + 1}. ${device.displayLabel}`)
        console.log(`     原始标签: "${device.label}"`)
        console.log(`     设备ID: ${idDisplay}`)
        console.log(`     虚拟摄像头: ${device.isVirtual ? '是' : '否'}`)
        console.log(`     网络摄像头: ${device.isWebcam ? '是' : '否'}`)
        console.log(`     详细标签: ${device.hasDetailedLabel ? '是' : '否'}`)
        console.log(`     不可用: ${device.unavailable ? '是' : '否'}`)
      })
    }
    
  } catch (error) {
    console.error('枚举设备失败:', error)
  }
}

const checkMediaPermissions = async () => {
  try {
    // 检查摄像头和麦克风权限（仅用于信息提示，不自动开启摄像头）
    const cameraPermission = await navigator.permissions.query({ name: 'camera' as PermissionName })
    const microphonePermission = await navigator.permissions.query({ name: 'microphone' as PermissionName })
    
    hasCameraPermission.value = cameraPermission.state === 'granted'
    hasMicrophonePermission.value = microphonePermission.state === 'granted'
    
    if (hasCameraPermission.value && hasMicrophonePermission.value) {
      console.log('摄像头和麦克风权限已授予，等待用户手动开启设备')
    } else if (cameraPermission.state === 'prompt' || microphonePermission.state === 'prompt') {
      ElMessage.info('请授予摄像头和麦克风权限以开始视频面试')
    }
  } catch (error) {
    console.warn('权限API不支持:', error)
  }
}

const startCamera = async () => {
  try {
    cameraLoading.value = true
    
    // 第一步：停止任何现有的摄像头流
    if (localStream) {
      console.log('停止现有的摄像头流...')
      localStream.getTracks().forEach(track => {
        console.log(`停止轨道: ${track.kind} (${track.id})`)
        track.stop()
      })
      localStream = null
    }
    
    console.log('开始摄像头请求，第一次请求状态:', isFirstCameraRequest.value)
    console.log('当前权限状态 - 摄像头:', hasCameraPermission.value, '麦克风:', hasMicrophonePermission.value)
    
    // 如果是第一次请求或没有权限，先请求基本权限
    if (isFirstCameraRequest.value || (!hasCameraPermission.value && !hasMicrophonePermission.value)) {
      console.log('第一次请求权限或权限未授予，使用基本约束请求权限')
      
      // 基本约束 - 不指定设备ID，只请求权限
      const basicConstraints: MediaStreamConstraints = {
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          frameRate: { ideal: 30 }
        },
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      }
      
      try {
        console.log('发送基本权限请求约束:', JSON.stringify(basicConstraints, null, 2))
        localStream = await navigator.mediaDevices.getUserMedia(basicConstraints)
        console.log('权限请求成功，获取到基本媒体流')
        
        // 更新权限状态
        hasCameraPermission.value = true
        hasMicrophonePermission.value = true
        isFirstCameraRequest.value = false
        
        // 立即停止这个临时流（我们只需要权限，不需要保持流开启）
        localStream.getTracks().forEach(track => {
          console.log(`停止临时权限获取轨道: ${track.kind} (${track.id})`)
          track.stop()
        })
        localStream = null
        
        // 重新枚举设备（现在有权限了，可以获取完整设备标签）
        await enumerateDevices()
        
        // 如果设备列表中有设备，自动选择第一个物理摄像头（如果有的话）
        if (videoDevices.value.length > 0) {
          // 优先选择物理摄像头
          const physicalCamera = videoDevices.value.find(device => !device.isVirtual)
          if (physicalCamera) {
            selectedVideoDeviceId.value = physicalCamera.deviceId
            console.log('自动选择第一个物理摄像头:', physicalCamera.label)
          } else {
            // 如果没有物理摄像头，选择第一个设备
            selectedVideoDeviceId.value = videoDevices.value[0]?.deviceId || ''
            console.log('自动选择第一个摄像头:', videoDevices.value[0]?.label)
          }
          
          ElMessage.success('摄像头权限已获取，请选择您要使用的摄像头设备')
        } else {
          ElMessage.success('摄像头权限已获取，但未检测到摄像头设备')
        }
        
        return // 第一次请求完成，等待用户选择设备
        
      } catch (permissionError) {
        console.error('获取摄像头权限失败:', permissionError)
        let errorMessage = '无法获取摄像头或麦克风权限'
        if (permissionError instanceof DOMException) {
          if (permissionError.name === 'NotAllowedError') {
            errorMessage = '用户拒绝了摄像头或麦克风权限'
          } else if (permissionError.name === 'NotFoundError') {
            errorMessage = '未找到摄像头或麦克风设备'
          }
        }
        ElMessage.error(errorMessage)
        return
      }
    }
    
    // 如果不是第一次请求（已经有权限），检查设备选择
    console.log('非第一次请求，检查设备选择...')
    console.log('选择的视频设备ID:', selectedVideoDeviceId.value)
    console.log('视频设备列表:', videoDevices.value)
    
    // 验证设备选择
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
    
    console.log('选中的摄像头设备:', selectedVideoDevice.label, (selectedVideoDevice.isVirtual ? '(虚拟摄像头)' : '(物理摄像头)'))
    
    // 构建视频约束 - 使用选择的设备
    const videoConstraints: MediaTrackConstraints = {
      width: { ideal: 640 },
      height: { ideal: 480 },
      frameRate: { ideal: 30 },
      deviceId: { exact: selectedVideoDeviceId.value }  // 强制使用精确匹配
    }
    
    // 构建音频约束
    const audioConstraints: MediaTrackConstraints = {
      sampleRate: 16000,
      channelCount: 1,
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true
    }
    
    // 如果选择了麦克风，则指定麦克风设备
    if (selectedAudioDeviceId.value) {
      audioConstraints.deviceId = { exact: selectedAudioDeviceId.value }
      console.log('使用指定的音频设备ID:', selectedAudioDeviceId.value)
    }
    
    const constraints: MediaStreamConstraints = {
      video: videoConstraints,
      audio: audioConstraints
    }
    
    console.log('发送的媒体约束（使用选择的设备）:', JSON.stringify(constraints, null, 2))
    
    // 获取指定设备的媒体流
    localStream = await navigator.mediaDevices.getUserMedia(constraints)
    
    console.log('成功获取指定设备的媒体流:')
    localStream.getTracks().forEach(track => {
      console.log(`轨道: ${track.kind}, id: ${track.id}, enabled: ${track.enabled}, readyState: ${track.readyState}`)
      console.log('轨道设置:', track.getSettings())
    })
    
    // 验证只获取了一个视频轨道
    const videoTracks = localStream.getVideoTracks()
    if (videoTracks.length === 0) {
      console.warn('警告：媒体流中没有视频轨道')
      ElMessage.warning('摄像头已开启，但未检测到视频数据')
    } else if (videoTracks.length > 1) {
      console.warn(`警告：获取了${videoTracks.length}个视频轨道，可能开启了多个摄像头`)
      // 如果意外获取了多个视频轨道，只保留第一个，停止其他的
      for (let i = 1; i < videoTracks.length; i++) {
        const extraTrack = videoTracks[i]
        if (extraTrack) {
          console.log(`停止多余视频轨道: ${extraTrack.id}`)
          extraTrack.stop()
        }
      }
    } else {
      const mainVideoTrack = videoTracks[0]
      if (mainVideoTrack) {
        const settings = mainVideoTrack.getSettings()
        console.log('成功获取单个视频轨道，设备ID:', settings?.deviceId || '未知')
      }
    }
    
    if (localVideo.value) {
      localVideo.value.srcObject = localStream
      console.log('视频元素已设置媒体流')
    }
    
    cameraActive.value = true
    microphoneActive.value = true
    
    // 检查视频轨道是否真的有数据
    if (videoTracks.length > 0) {
      const track = videoTracks[0]
      if (track) {
        console.log('视频轨道状态:', {
          readyState: track.readyState,
          enabled: track.enabled,
          muted: track.muted,
          settings: track.getSettings()
        })
      }
    }
    
    ElMessage.success('摄像头和麦克风已开启')
    
  } catch (error) {
    console.error('无法访问摄像头/麦克风:', error)
    // 显示更详细的错误信息
    let errorMessage = '无法访问摄像头或麦克风，请检查设备权限'
    if (error instanceof DOMException) {
      errorMessage = `设备访问错误: ${error.name} - ${error.message}`
      if (error.name === 'NotFoundError') {
        errorMessage = `未找到摄像头设备: ${selectedVideoDeviceId.value}`
        // 标记设备为不可用并清除选择
        markDeviceAsUnavailable(selectedVideoDeviceId.value)
        selectedVideoDeviceId.value = ''
        // 重新枚举设备以更新列表
        setTimeout(() => enumerateDevices(), 100)
      } else if (error.name === 'NotAllowedError') {
        errorMessage = '用户拒绝了摄像头或麦克风权限'
      } else if (error.name === 'NotReadableError') {
        errorMessage = '摄像头或麦克风正被其他程序占用'
      } else if (error.name === 'OverconstrainedError') {
        errorMessage = `无法满足摄像头要求。设备ID: ${selectedVideoDeviceId.value}`
        // 标记设备为不可用并清除选择
        markDeviceAsUnavailable(selectedVideoDeviceId.value)
        selectedVideoDeviceId.value = ''
        // 重新枚举设备以更新列表
        setTimeout(() => enumerateDevices(), 100)
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
  
  ElMessage.info('摄像头和麦克风已关闭')
}

const toggleMicrophone = () => {
  if (localStream) {
    const audioTracks = localStream.getAudioTracks()
    audioTracks.forEach(track => {
      track.enabled = !track.enabled
    })
    microphoneActive.value = audioTracks[0]?.enabled || false
    ElMessage.info(`麦克风已${microphoneActive.value ? '开启' : '关闭'}`)
  }
}

// 音频流处理函数
const startAudioStreaming = () => {
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
    
    // 创建ScriptProcessorNode用于处理音频数据
    audioProcessor = audioContext.createScriptProcessor(4096, 1, 1)
    
    // 音频处理回调
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
        const sample = Math.max(-32768, Math.min(32767, Math.floor(input[i] * 32768)))
        int16Array[i] = sample
        if (sample !== 0) {
          hasValidData = true
        }
      }
      
      if (hasValidData) {
        // 追加到缓冲区
        const newBuffer = new Int16Array(audioBuffer.length + int16Array.length)
        newBuffer.set(audioBuffer)
        newBuffer.set(int16Array, audioBuffer.length)
        audioBuffer = newBuffer
        
        // 调试日志：每10次回调记录一次
        if (Math.random() < 0.1) {  // 10%概率记录，避免日志过多
          console.log(`音频数据接收: ${input.length}个float32样本, 转换为${int16Array.length}个int16样本, 缓冲区总计: ${audioBuffer.length}样本`)
        }
      } else {
        // 静音数据，可以发送静音帧或忽略
        console.log('收到静音音频数据，忽略或发送静音帧')
      }
    }
    
    // 连接音频节点
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

const sendAudioData = () => {
  if (!videoSocket || !videoSocket.connected) {
    return
  }
  
  // 如果缓冲区有足够的数据，发送一个音频块
  if (audioBuffer.length >= AUDIO_CHUNK_SAMPLES) {
    // 提取一个音频块 (AUDIO_CHUNK_SAMPLES个样本)
    const chunk = audioBuffer.slice(0, AUDIO_CHUNK_SAMPLES)
    
    // 正确提取切片对应的缓冲区部分
    const sliceBuffer = chunk.buffer.slice(chunk.byteOffset, chunk.byteOffset + chunk.byteLength)
    const byteArray = new Uint8Array(sliceBuffer)
    
    console.log(`发送音频数据: ${byteArray.length}字节, 缓冲区剩余: ${audioBuffer.length - AUDIO_CHUNK_SAMPLES}样本`)
    
    // 发送音频数据到WebSocket - 发送Uint8Array的缓冲区数据
    videoSocket.emit('audio', byteArray.buffer)
    
    // 从缓冲区移除已发送的数据
    audioBuffer = audioBuffer.slice(AUDIO_CHUNK_SAMPLES)
  } else {
    // 缓冲区不足，发送静音帧以保持连接活跃
    // 800字节的静音帧 (25ms @ 16kHz, 16-bit mono)
    const silentFrame = new Uint8Array(AUDIO_CHUNK_SIZE).fill(0)
    console.log(`发送静音帧: ${silentFrame.length}字节 (缓冲区不足: ${audioBuffer.length}/${AUDIO_CHUNK_SAMPLES}样本)`)
    
    // 发送静音帧
    videoSocket.emit('audio', silentFrame.buffer)
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
    
    // 检查socket连接状态
    if (!videoSocket?.connected) {
      throw new Error('WebSocket连接未建立')
    }
    
    console.log('开始发送视频帧...')
    // 开始发送视频帧
    startVideoStreaming()
    
    console.log('开始采集和发送音频流...')
    // 开始采集和发送音频流（VAD模式需要）
    startAudioStreaming()
    
    interviewStarted.value = true
    videoConnected.value = true
    
    console.log('视频面试已开始，界面状态已更新')
    ElMessage.success('视频面试已开始，请开始对话')
    
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
    const wsBaseUrl = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8083'
    // Socket.IO需要完整的WebSocket URL，命名空间作为URL的一部分
    videoSocket = io(wsBaseUrl + '/ws/video', {
      path: '/socket.io',
      transports: ['websocket'],
      reconnection: false
    })
    
    let connected = false
    let timeoutId: number | null = null
    
    // 设置超时，避免无限等待
    timeoutId = window.setTimeout(() => {
      if (!connected) {
        console.warn('Socket.IO连接超时')
        reject(new Error('连接超时'))
      }
    }, 10000) // 10秒超时
    
    videoSocket.on('connect', () => {
      console.log('视频WebSocket连接已建立')
      console.log('socket namespace:', videoSocket?.nsp, 'socket id:', videoSocket?.id)
      
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
    
    videoSocket.on('started', (data: any) => {
      handleSocketMessage({ type: 'started' })
    })
    
    videoSocket.on('stopped', (data: any) => {
      handleSocketMessage({ type: 'stopped' })
    })
    
    videoSocket.on('error', (data: any) => {
      handleSocketMessage({ type: 'error', message: data.message })
    })
    
    videoSocket.on('connect_error', (error: Error) => {
      console.error('Socket.IO连接错误:', error)
      reject(error)
    })
    
    videoSocket.on('disconnect', () => {
      console.log('Socket.IO连接断开')
      videoConnected.value = false
    })
  })
}

const handleSocketMessage = (data: any) => {
  const type = data.type
  
  switch (type) {
    case 'audio':
      // 处理AI音频回复
      playAIAudio(data.data)
      break
    case 'text':
      // 处理AI文本回复（字幕）
      currentSubtitle.value += data.data
      break
    case 'response_done':
      // AI响应完成
      currentSubtitle.value = ''
      isPlayingAudio.value = false
      break
    case 'started':
      // 面试已开始
      addMessage('ai', '您好，我是面试官。请简要介绍一下自己。')
      break
    case 'stopped':
      // 面试已结束
      finished.value = true
      interviewStarted.value = false
      ElMessage.success('视频面试已结束')
      break
    case 'error':
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
  if (!audioPlayer.value) return
  
  try {
    const audioData = atob(audioBase64)
    const arrayBuffer = new ArrayBuffer(audioData.length)
    const uint8Array = new Uint8Array(arrayBuffer)
    
    for (let i = 0; i < audioData.length; i++) {
      uint8Array[i] = audioData.charCodeAt(i)
    }
    
    const blob = new Blob([arrayBuffer], { type: 'audio/wav' })
    const url = URL.createObjectURL(blob)
    
    audioPlayer.value.src = url
    audioPlayer.value.play()
    isPlayingAudio.value = true
    
  } catch (error) {
    console.error('播放AI音频失败:', error)
  }
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
    console.log('正在结束视频面试，清理资源...')
    
    // 发送停止消息
    if (videoSocket && videoSocket.connected) {
      videoSocket.emit('stop_interview', {})
      console.log('已发送stop_interview事件')
    }
    
    // 立即停止音频和视频流
    stopAudioStreaming()
    
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
    
    // 更新面试记录
    if (interviewStore.interviewId) {
      await interviewStore.endInterview()
    }
    
    finished.value = true
    interviewStarted.value = false
    videoConnected.value = false
    
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
  
  stopAudioStreaming()
  stopCamera()
}
</script>

<style scoped>
.video-interview-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.header {
  background: rgba(255, 255, 255, 0.95);
  padding: 16px 24px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.video-interview-container {
  flex: 1;
  display: flex;
  padding: 24px;
  gap: 24px;
  overflow: hidden;
}

.video-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.video-preview {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.video-preview h3 {
  margin-bottom: 16px;
  color: #333;
}

.local-video {
  width: 100%;
  max-height: 360px;
  border-radius: 8px;
  background: #000;
  margin-bottom: 16px;
}

.video-controls {
  display: flex;
  gap: 12px;
  justify-content: center;
  align-items: center;
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

.device-selection {
  margin-bottom: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.device-selector {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.device-selector:last-child {
  margin-bottom: 0;
}

.device-label {
  min-width: 80px;
  font-weight: 500;
  color: #495057;
}

.device-dropdown {
  flex: 1;
}

.device-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  color: #6c757d;
  font-size: 14px;
}

.empty-text {
  color: #6c757d;
}

/* 虚拟摄像头选项样式 */
:deep(.virtual-camera-option) .el-select-dropdown__item {
  color: #f56c6c !important;
  font-style: italic;
}

:deep(.virtual-camera-option) .el-select-dropdown__item:hover {
  background-color: #fef0f0 !important;
}

.video-status {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.status-indicators {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.subtitle-display {
  background: #f0f9ff;
  border: 1px solid #91caff;
  border-radius: 8px;
  padding: 16px;
  margin-top: 16px;
}

.subtitle-display h4 {
  margin-bottom: 8px;
  color: #409eff;
}

.subtitle-text {
  font-size: 16px;
  line-height: 1.5;
  color: #333;
  min-height: 24px;
}

.chat-history {
  width: 400px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

.chat-history h3 {
  margin-bottom: 16px;
  color: #333;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding-right: 8px;
}

.message-item {
  padding: 12px;
  margin-bottom: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.message-sender {
  font-weight: bold;
  color: #409eff;
  margin-bottom: 4px;
}

.message-content {
  color: #333;
  line-height: 1.5;
}

.message-time {
  font-size: 12px;
  color: #999;
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
  padding: 40px;
  background: rgba(255, 255, 255, 0.95);
  margin: 24px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.start-hint {
  margin-top: 16px;
  color: #666;
  font-size: 14px;
}
</style>