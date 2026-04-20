<template>
  <div class="qwen-message-bubble" :class="[roleClass, { 'has-scores': showScores, 'has-audio': hasAudio }]">
    <div class="message-header">
      <div class="avatar">
        <div v-if="message.role === 'ai'" class="avatar-ai">
          <el-icon><ChatDotRound /></el-icon>
        </div>
        <div v-else class="avatar-user">
          <el-icon><User /></el-icon>
        </div>
      </div>
      <div class="message-meta">
        <div class="sender-info">
          <span class="sender">{{ senderName }}</span>
          <el-tag v-if="message.role === 'ai'" size="small" type="info" class="qwen-tag">
            Qwen-Omni
          </el-tag>
        </div>
        <span class="timestamp">{{ formattedTime }}</span>
      </div>
    </div>
    
    <div class="message-content">
      <!-- 实时文本显示（AI消息可能会有增量更新） -->
      <div class="content-text">{{ displayText }}</div>
      
      <!-- 音频控制 -->
      <div v-if="hasAudio" class="audio-controls">
        <div class="audio-info">
          <el-icon><Phone /></el-icon>
          <span>包含语音回复</span>
        </div>
        <div class="audio-buttons">
          <el-button
            type="primary"
            text
            :icon="isPlayingAudio ? VideoPause : VideoPlay"
            @click="toggleAudio"
            :loading="audioLoading"
            size="small"
          >
            {{ isPlayingAudio ? '暂停' : '播放' }}
          </el-button>
          <el-button
            type="warning"
            text
            :icon="RefreshRight"
            @click="$emit('retry-audio', message.id)"
            size="small"
          >
            重播
          </el-button>
        </div>
      </div>
      
      <!-- 音频播放进度 -->
      <div v-if="isPlayingAudio && hasAudio" class="audio-progress">
        <el-progress
          :percentage="audioProgress"
          :stroke-width="6"
          :show-text="false"
          :color="getProgressColor(audioProgress)"
        />
        <span class="progress-time">{{ formatProgressTime(audioProgress) }}</span>
      </div>
      
      <!-- 评分显示 -->
      <div v-if="showScores && message.scores" class="score-display">
        <div class="score-title">回答评分：</div>
        <div class="score-bars">
          <div class="score-item">
            <span class="score-label">技术正确性</span>
            <el-progress
              :percentage="message.scores.tech * 10"
              :stroke-width="8"
              :show-text="false"
              :color="getScoreColor(message.scores.tech)"
            />
            <span class="score-value">{{ message.scores.tech.toFixed(1) }}/10</span>
          </div>
          <div class="score-item">
            <span class="score-label">知识深度</span>
            <el-progress
              :percentage="message.scores.depth * 10"
              :stroke-width="8"
              :show-text="false"
              :color="getScoreColor(message.scores.depth)"
            />
            <span class="score-value">{{ message.scores.depth.toFixed(1) }}/10</span>
          </div>
          <div class="score-item">
            <span class="score-label">逻辑清晰度</span>
            <el-progress
              :percentage="message.scores.logic * 10"
              :stroke-width="8"
              :show-text="false"
              :color="getScoreColor(message.scores.logic)"
            />
            <span class="score-value">{{ message.scores.logic.toFixed(1) }}/10</span>
          </div>
          <div class="score-item">
            <span class="score-label">岗位匹配度</span>
            <el-progress
              :percentage="message.scores.match * 10"
              :stroke-width="8"
              :show-text="false"
              :color="getScoreColor(message.scores.match)"
            />
            <span class="score-value">{{ message.scores.match.toFixed(1) }}/10</span>
          </div>
        </div>
        
        <!-- 总分显示 -->
        <div v-if="showScores" class="total-score">
          <span class="total-label">综合评分：</span>
          <el-rate
            v-model="averageScore"
            disabled
            show-score
            text-color="#ff9900"
            score-template="{value}"
            class="total-rate"
          />
        </div>
      </div>
      
      <!-- 多模态指示器 -->
      <div v-if="message.role === 'ai' && hasAudio" class="multimodal-indicator">
        <el-tag size="small" type="success" class="multimodal-tag">
          <el-icon><VideoCamera /></el-icon>
          语音+文本
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onUnmounted } from 'vue'
import { 
  ChatDotRound, User, VideoPlay, VideoPause, Phone, 
  RefreshRight, VideoCamera 
} from '@element-plus/icons-vue'
import { getQwenAudioProcessor } from '@/utils/qwen_audio'
import type { QwenInterviewMessage } from '@/stores/qwen_interview'

interface Props {
  message: QwenInterviewMessage
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'play-audio': [audioBase64: string]
  'retry-audio': [messageId: number]
}>()

const audioLoading = ref(false)
const isPlayingAudio = ref(false)
const audioProgress = ref(0)
const audioProcessor = ref(getQwenAudioProcessor())
const audioInterval = ref<number | null>(null)

// 计算属性
const roleClass = computed(() => {
  return props.message.role === 'ai' ? 'ai-message' : 'user-message'
})

const senderName = computed(() => {
  return props.message.role === 'ai' ? 'AI面试官' : '您'
})

const formattedTime = computed(() => {
  const date = props.message.timestamp
  if (!(date instanceof Date)) return ''
  
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${hours}:${minutes}`
})

const displayText = computed(() => {
  return props.message.content || ''
})

const hasAudio = computed(() => {
  return !!props.message.audioBase64
})

const showScores = computed(() => {
  return props.message.scores !== undefined && props.message.role === 'user'
})

const averageScore = computed(() => {
  if (!props.message.scores) return 0
  
  const { tech, depth, logic, match } = props.message.scores
  const total = tech + depth + logic + match
  return Math.round(total / 4 * 2) / 2 // 转换为0-5的评分（步长0.5）
})

// 监听消息内容变化（用于实时文本更新）
watch(() => props.message.content, (newContent) => {
  // 可以在这里添加文本变化的动画效果
  console.log('消息内容更新:', newContent.substring(0, 50))
})

// 音频播放控制
const toggleAudio = async () => {
  if (!hasAudio.value || !props.message.audioBase64) return
  
  try {
    if (isPlayingAudio.value) {
      // 暂停音频
      // 注意：当前实现不支持暂停，需要改进
      stopAudioProgress()
    } else {
      // 播放音频
      audioLoading.value = true
      await playAudio(props.message.audioBase64)
      audioLoading.value = false
    }
  } catch (error) {
    console.error('音频播放失败:', error)
    audioLoading.value = false
    isPlayingAudio.value = false
  }
}

const playAudio = async (audioBase64: string) => {
  try {
    isPlayingAudio.value = true
    audioProgress.value = 0
    
    // 模拟播放进度
    startAudioProgress()
    
    // 实际播放音频
    await audioProcessor.value.playPCMBase64(audioBase64)
    
    // 播放完成
    stopAudioProgress()
    isPlayingAudio.value = false
    audioProgress.value = 100
    
    // 1秒后重置进度
    setTimeout(() => {
      audioProgress.value = 0
    }, 1000)
    
  } catch (error) {
    console.error('播放音频失败:', error)
    stopAudioProgress()
    isPlayingAudio.value = false
    throw error
  }
}

const startAudioProgress = () => {
  if (audioInterval.value) {
    clearInterval(audioInterval.value)
  }
  
  // 模拟播放进度（实际应根据音频时长调整）
  const duration = 5000 // 假设5秒音频
  const step = 100 / (duration / 100)
  
  audioInterval.value = window.setInterval(() => {
    audioProgress.value = Math.min(100, audioProgress.value + step)
  }, 100)
}

const stopAudioProgress = () => {
  if (audioInterval.value) {
    clearInterval(audioInterval.value)
    audioInterval.value = null
  }
}

const formatProgressTime = (progress: number) => {
  const totalSeconds = 5 // 假设5秒音频
  const currentSeconds = Math.floor(totalSeconds * progress / 100)
  const remainingSeconds = totalSeconds - currentSeconds
  
  return `${currentSeconds}s / ${totalSeconds}s`
}

// 颜色工具函数
const getScoreColor = (score: number): string => {
  if (score >= 8) return '#67c23a' // 优秀 - 绿色
  if (score >= 6) return '#e6a23c' // 良好 - 黄色
  if (score >= 4) return '#f56c6c' // 一般 - 红色
  return '#909399' // 较差 - 灰色
}

const getProgressColor = (progress: number): string => {
  if (progress >= 80) return '#67c23a'
  if (progress >= 50) return '#e6a23c'
  return '#409eff'
}

// 组件卸载时清理
onUnmounted(() => {
  stopAudioProgress()
})
</script>

<style scoped>
.qwen-message-bubble {
  max-width: 85%;
  margin: 1rem auto;
  padding: 1.25rem;
  border-radius: 16px;
  background: white;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.qwen-message-bubble:hover {
  box-shadow: 0 6px 25px rgba(0, 0, 0, 0.12);
  border-color: #e0e0e0;
}

.qwen-message-bubble.ai-message {
  margin-left: 0;
  margin-right: auto;
  background: linear-gradient(135deg, #f0f9ff 0%, #e6f7ff 100%);
  border-color: #bae0ff;
}

.qwen-message-bubble.user-message {
  margin-left: auto;
  margin-right: 0;
  background: linear-gradient(135deg, #f6ffed 0%, #f0ffe6 100%);
  border-color: #b7eb8f;
}

.qwen-message-bubble.has-audio {
  border-left-width: 4px;
}

.ai-message.has-audio {
  border-left-color: #409eff;
}

.user-message.has-audio {
  border-left-color: #67c23a;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.avatar {
  flex-shrink: 0;
}

.avatar-ai, .avatar-user {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
}

.avatar-ai {
  background: linear-gradient(135deg, #409eff, #1677ff);
  color: white;
}

.avatar-user {
  background: linear-gradient(135deg, #67c23a, #52c41a);
  color: white;
}

.message-meta {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sender-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.sender {
  font-weight: 600;
  font-size: 1rem;
}

.qwen-tag {
  font-size: 0.7rem;
  padding: 0 0.5rem;
  height: 20px;
  line-height: 18px;
}

.timestamp {
  font-size: 0.8rem;
  color: #909399;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.content-text {
  font-size: 1rem;
  line-height: 1.6;
  color: #303133;
  white-space: pre-wrap;
  word-break: break-word;
  min-height: 1.5em;
}

.audio-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 10px;
  border: 1px solid #e8e8e8;
}

.audio-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #409eff;
  font-weight: 500;
}

.audio-buttons {
  display: flex;
  gap: 0.5rem;
}

.audio-progress {
  margin-top: -0.5rem;
  padding: 0 0.5rem;
}

.progress-time {
  display: block;
  text-align: center;
  font-size: 0.8rem;
  color: #606266;
  margin-top: 0.25rem;
}

.score-display {
  padding: 1rem;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 10px;
  border: 1px solid #f0f0f0;
}

.score-title {
  font-weight: 600;
  margin-bottom: 0.75rem;
  color: #303133;
  font-size: 0.95rem;
}

.score-bars {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.score-item {
  display: grid;
  grid-template-columns: 80px 1fr 50px;
  align-items: center;
  gap: 0.75rem;
}

.score-label {
  font-size: 0.85rem;
  color: #606266;
  text-align: right;
}

.score-value {
  font-size: 0.85rem;
  font-weight: 600;
  color: #303133;
  text-align: right;
}

.total-score {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px dashed #e0e0e0;
}

.total-label {
  font-weight: 600;
  color: #303133;
}

.total-rate {
  font-size: 1.2rem;
}

.multimodal-indicator {
  display: flex;
  justify-content: flex-end;
  margin-top: 0.5rem;
}

.multimodal-tag {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .qwen-message-bubble {
    max-width: 95%;
    padding: 1rem;
  }
  
  .score-item {
    grid-template-columns: 70px 1fr 45px;
    gap: 0.5rem;
  }
  
  .audio-controls {
    flex-direction: column;
    gap: 0.75rem;
    align-items: stretch;
  }
  
  .audio-buttons {
    justify-content: center;
  }
}
</style>