<template>
  <div class="message-bubble" :class="[roleClass, { 'has-scores': showScores }]">
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
        <span class="sender">{{ senderName }}</span>
        <span class="timestamp">{{ formattedTime }}</span>
      </div>
    </div>
    
    <div class="message-content">
      <div class="content-text">{{ message.content }}</div>
      
      <div v-if="message.audioUrl" class="audio-controls">
        <el-button
          type="primary"
          text
          :icon="VideoPlay"
          @click="playAudio"
          :loading="audioLoading"
        >
          播放语音
        </el-button>
      </div>
      
      <div v-if="showScores && message.scores" class="score-display">
        <div class="score-title">回答评分：</div>
        <div class="score-bars">
          <div class="score-item">
            <span class="score-label">技术</span>
            <el-progress
              :percentage="message.scores.tech * 10"
              :stroke-width="8"
              :show-text="false"
              :color="getScoreColor(message.scores.tech)"
            />
            <span class="score-value">{{ message.scores.tech.toFixed(1) }}/10</span>
          </div>
          <div class="score-item">
            <span class="score-label">深度</span>
            <el-progress
              :percentage="message.scores.depth * 10"
              :stroke-width="8"
              :show-text="false"
              :color="getScoreColor(message.scores.depth)"
            />
            <span class="score-value">{{ message.scores.depth.toFixed(1) }}/10</span>
          </div>
          <div class="score-item">
            <span class="score-label">逻辑</span>
            <el-progress
              :percentage="message.scores.logic * 10"
              :stroke-width="8"
              :show-text="false"
              :color="getScoreColor(message.scores.logic)"
            />
            <span class="score-value">{{ message.scores.logic.toFixed(1) }}/10</span>
          </div>
          <div class="score-item">
            <span class="score-label">匹配</span>
            <el-progress
              :percentage="message.scores.match * 10"
              :stroke-width="8"
              :show-text="false"
              :color="getScoreColor(message.scores.match)"
            />
            <span class="score-value">{{ message.scores.match.toFixed(1) }}/10</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatDotRound, User, VideoPlay } from '@element-plus/icons-vue'
import type { InterviewMessage } from '@/stores/interview'

interface Props {
  message: InterviewMessage
}

const props = defineProps<Props>()
const emit = defineEmits<{
  playAudio: [url: string]
}>()

const audioLoading = ref(false)

const roleClass = computed(() => {
  return props.message.role === 'ai' ? 'ai-message' : 'user-message'
})

const senderName = computed(() => {
  return props.message.role === 'ai' ? 'AI面试官' : '我'
})

const formattedTime = computed(() => {
  const date = new Date(props.message.timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
})

const showScores = computed(() => {
  return props.message.scores !== undefined
})

const getScoreColor = (score: number) => {
  if (score >= 9) return '#10b981'
  if (score >= 7) return '#3b82f6'
  if (score >= 5) return '#f59e0b'
  return '#ef4444'
}

const playAudio = async () => {
  if (!props.message.audioUrl) return
  
  try {
    audioLoading.value = true
    emit('playAudio', props.message.audioUrl)
  } catch (error) {
    ElMessage.error('播放音频失败')
  } finally {
    audioLoading.value = false
  }
}
</script>

<style scoped>
.message-bubble {
  margin-bottom: 1.5rem;
  border-radius: var(--radius-xl);
  padding: 1.125rem;
  max-width: 80%;
  position: relative;
  transition: all var(--transition-base);
  animation: fadeInUp 0.4s ease both;
}

.message-bubble:hover {
  box-shadow: var(--shadow-md);
}

.ai-message {
  background-color: white;
  border: 1px solid var(--border-color);
  align-self: flex-start;
  margin-right: auto;
}

.user-message {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  color: white;
  align-self: flex-end;
  margin-left: auto;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.2);
}

.has-scores {
  border-left: 4px solid var(--primary-color);
}

.message-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-ai {
  background: linear-gradient(135deg, var(--accent-color), var(--accent-dark));
  color: white;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.25);
}

.avatar-user {
  background: linear-gradient(135deg, var(--secondary-color), var(--secondary-dark));
  color: white;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.25);
}

.message-meta {
  display: flex;
  flex-direction: column;
}

.sender {
  font-weight: 700;
  font-size: 0.85rem;
}

.user-message .sender {
  color: rgba(255, 255, 255, 0.95);
}

.timestamp {
  font-size: 0.7rem;
  opacity: 0.6;
}

.user-message .timestamp {
  color: rgba(255, 255, 255, 0.65);
}

.message-content {
  line-height: 1.6;
}

.content-text {
  white-space: pre-wrap;
  word-break: break-word;
  margin-bottom: 1rem;
  font-size: 0.925rem;
}

.ai-message .content-text {
  color: var(--text-primary);
}

.user-message .content-text {
  color: white;
}

.audio-controls {
  margin-top: 0.5rem;
  display: flex;
  align-items: center;
}

.score-display {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-color);
}

.user-message .score-display {
  border-top-color: rgba(255, 255, 255, 0.2);
}

.score-title {
  font-weight: 700;
  margin-bottom: 0.75rem;
  font-size: 0.85rem;
}

.user-message .score-title {
  color: rgba(255, 255, 255, 0.9);
}

.score-bars {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.score-item {
  display: grid;
  grid-template-columns: 55px 1fr 55px;
  align-items: center;
  gap: 0.75rem;
}

.score-label {
  font-size: 0.8rem;
  color: var(--text-secondary);
  text-align: right;
  font-weight: 500;
}

.user-message .score-label {
  color: rgba(255, 255, 255, 0.75);
}

.score-value {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-primary);
  text-align: center;
}

.user-message .score-value {
  color: white;
}

:deep(.el-progress-bar__outer) {
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
}

.user-message :deep(.el-progress-bar__outer) {
  background-color: rgba(255, 255, 255, 0.2);
}

@media (max-width: 640px) {
  .message-bubble {
    max-width: 90%;
  }

  .score-item {
    grid-template-columns: 45px 1fr 45px;
    gap: 0.5rem;
  }
}
</style>