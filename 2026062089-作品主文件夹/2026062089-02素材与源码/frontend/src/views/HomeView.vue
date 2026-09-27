<template>
  <div class="home-view">
    <div class="hero-section">
      <div class="hero-bg">
        <div class="hero-orb orb-1"></div>
        <div class="hero-orb orb-2"></div>
        <div class="hero-orb orb-3"></div>
        <div class="hero-grid"></div>
      </div>
      <div class="container">
        <div class="hero-content">
          <div class="hero-badge animate-fade-in-up">
            <span class="badge-dot"></span>
            专为计算机专业学生打造
          </div>
          <h1 class="hero-title animate-fade-in-up delay-100">
            <span class="gradient-text">AI模拟面试教练</span>
          </h1>
          <p class="hero-subtitle animate-fade-in-up delay-200">
            与AI面试官实时对话，获取专业评估与改进建议<br>
            快速提升技术面试能力
          </p>
          <div class="hero-stats animate-fade-in-up delay-300">
            <div class="stat-item">
              <div class="stat-icon-wrapper">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              </div>
              <span class="stat-number">100+</span>
              <span class="stat-label">面试题库</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <div class="stat-icon-wrapper">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"/><line x1="12" y1="22" x2="12" y2="15.5"/><polyline points="22 8.5 12 15.5 2 8.5"/></svg>
              </div>
              <span class="stat-number">5维</span>
              <span class="stat-label">能力评估</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <div class="stat-icon-wrapper">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
              </div>
              <span class="stat-number">实时</span>
              <span class="stat-label">语音反馈</span>
            </div>
          </div>
          <div class="hero-cta animate-fade-in-up delay-400">
            <el-button type="primary" size="large" round class="hero-button" @click="scrollToPositions">
              立即开始
              <svg class="btn-arrow" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
            </el-button>
          </div>
        </div>
      </div>
      <div class="hero-wave">
        <svg viewBox="0 0 1440 120" fill="none" preserveAspectRatio="none">
          <path d="M0 60C240 100 480 0 720 40C960 80 1200 0 1440 60V120H0V60Z" fill="var(--background-color)"/>
        </svg>
      </div>
    </div>

    <div class="position-section" ref="positionSectionRef">
      <div class="container">
        <div class="section-header">
          <div class="section-badge">岗位选择</div>
          <h2>选择目标岗位</h2>
          <p>选择您想要练习的技术岗位，AI将根据岗位要求进行针对性面试</p>
        </div>

        <div class="position-cards">
          <div
            v-for="pos in positions"
            :key="pos.id"
            class="position-card"
            :class="{ 'selected': selectedPosition === pos.id }"
            @click="selectPosition(pos.id)"
          >
            <div class="card-accent" :style="{ background: pos.gradient }"></div>
            <div class="card-content">
              <div class="card-icon-wrapper">
                <div class="card-icon" :style="{ background: pos.gradient }">
                  <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path :d="pos.iconPath"/>
                  </svg>
                </div>
              </div>
              <div class="card-body">
                <h3>{{ pos.title }}</h3>
                <p class="card-description">{{ pos.description }}</p>
                <div class="card-tech">
                  <el-tag
                    v-for="tech in pos.techs"
                    :key="tech"
                    size="small"
                    round
                    effect="plain"
                  >
                    {{ tech }}
                  </el-tag>
                </div>
              </div>
              <div class="card-action">
                <el-button
                  type="primary"
                  size="large"
                  round
                  :loading="loading[pos.id]"
                  @click.stop="startInterview(pos.id)"
                  class="start-btn"
                >
                  开始面试
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <div class="interview-tips">
          <div class="tips-card">
            <div class="tips-header">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--primary-color)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
              <span class="tips-title">面试准备建议</span>
            </div>
            <ul class="tips-list">
              <li v-for="(tip, i) in tips" :key="i" class="tips-item">
                <span class="tip-bullet">{{ i + 1 }}</span>
                <span>{{ tip }}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useInterviewStore } from '@/stores/interview'

const router = useRouter()
const interviewStore = useInterviewStore()

const positionSectionRef = ref<HTMLElement>()

const selectedPosition = ref<string>('')
const loading = ref<Record<string, boolean>>({
  java_backend: false,
  web_frontend: false,
  fullstack_engineer: false,
  bigdata_engineer: false
})

const tips = [
  '提前准备好个人项目和技术亮点的介绍',
  '思考常见面试问题的回答思路与案例',
  '确保网络环境良好，麦克风工作正常',
  '每次面试后认真阅读评估报告，针对性改进',
]

const positions = [
  {
    id: 'java_backend',
    title: 'Java后端开发工程师',
    description: '掌握Java、Spring Boot、MySQL、Redis等后端技术栈，熟悉分布式系统设计与高并发处理',
    gradient: 'linear-gradient(135deg, #f97316, #ea580c)',
    techs: ['Java', 'Spring Boot', 'MySQL', 'Redis'],
    iconPath: 'M12 2A10 10 0 1 1 2 12 10 10 0 0 1 12 2M11 17H13V19H11V17M14.2 14.2L15.6 15.6C16.4 14.9 17 13.9 17 12.7C17 10.6 15.4 9 13.3 9H10V15H13.3C14.1 15 14.8 14.7 15.4 14.2M11 5H13V12H11V5Z'
  },
  {
    id: 'web_frontend',
    title: 'Web前端开发工程师',
    description: '精通Vue/React、TypeScript、前端工程化，熟悉性能优化与用户体验设计',
    gradient: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
    techs: ['Vue', 'React', 'TypeScript', 'Webpack'],
    iconPath: 'M12 2L2 7L12 12L22 7L12 2M2 17L12 22L22 17M2 12L12 17L22 12'
  },
  {
    id: 'fullstack_engineer',
    title: '全栈开发工程师',
    description: '精通前后端开发，掌握Vue/React、Spring Boot、MySQL等技术栈，具备全流程开发与架构设计能力',
    gradient: 'linear-gradient(135deg, #10b981, #059669)',
    techs: ['Vue', 'React', 'Spring Boot', 'MySQL'],
    iconPath: 'M12 2L2 7L12 12L22 7L12 2M2 17L12 22L22 17M2 12L12 17L22 12'
  },
  {
    id: 'bigdata_engineer',
    title: '大数据开发工程师',
    description: '掌握Hadoop、Spark、Flink等大数据技术栈，熟悉数据仓库、实时计算与数据治理',
    gradient: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
    techs: ['Hadoop', 'Spark', 'Flink', 'Kafka'],
    iconPath: 'M12 2A10 10 0 1 1 2 12 10 10 0 0 1 12 2M11 17H13V19H11V17M14.2 14.2L15.6 15.6C16.4 14.9 17 13.9 17 12.7C17 10.6 15.4 9 13.3 9H10V15H13.3C14.1 15 14.8 14.7 15.4 14.2M11 5H13V12H11V5Z'
  }
]

const scrollToPositions = () => {
  positionSectionRef.value?.scrollIntoView({ behavior: 'smooth' })
}

const selectPosition = (position: string) => {
  selectedPosition.value = position
}

const startInterview = async (position: string) => {
  try {
    const loadingKey = position as keyof typeof loading.value
    loading.value[loadingKey] = true
    await interviewStore.startInterview(position, true)
    router.push('/interview/video')
  } catch (error) {
    ElMessage.error('开始面试失败，请重试')
    console.error(error)
  } finally {
    const positionKey = position as keyof typeof loading.value
    loading.value[positionKey] = false
  }
}
</script>

<style scoped>
.home-view {
  min-height: 100vh;
  background: var(--background-color);
}

.hero-section {
  position: relative;
  padding: 7rem 0 2rem;
  background: linear-gradient(160deg, #0f172a 0%, #1e3a5f 30%, #1e4b7c 60%, #2563eb 100%);
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.hero-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.3;
  animation: float 8s ease-in-out infinite;
}

.orb-1 {
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.4), transparent);
  top: -200px;
  right: -100px;
  animation-delay: 0s;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.4), transparent);
  bottom: -100px;
  left: -50px;
  animation-delay: 2s;
}

.orb-3 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(16, 185, 129, 0.3), transparent);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: 4s;
}

.hero-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 60px 60px;
  mask-image: radial-gradient(circle at 50% 50%, black 30%, transparent 70%);
}

.hero-wave {
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  line-height: 0;
}

.hero-wave svg {
  width: 100%;
  height: 80px;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

.hero-content {
  position: relative;
  z-index: 1;
  max-width: 800px;
  margin: 0 auto;
  text-align: center;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 1rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 999px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.8rem;
  font-weight: 500;
  margin-bottom: 1.5rem;
  backdrop-filter: blur(8px);
}

.badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
}

.hero-title {
  font-size: 3.75rem;
  font-weight: 800;
  margin-bottom: 1.25rem;
  line-height: 1.15;
  letter-spacing: -0.02em;
}

.gradient-text {
  background: linear-gradient(135deg, #ffd700, #fbbf24, #f59e0b);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 2.5rem;
  line-height: 1.7;
}

.hero-stats {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0;
  margin-bottom: 2.5rem;
  padding: 1.25rem 2rem;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-xl);
  backdrop-filter: blur(12px);
  max-width: 560px;
  margin-left: auto;
  margin-right: auto;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.375rem;
  flex: 1;
  padding: 0.5rem;
}

.stat-icon-wrapper {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 0.25rem;
}

.stat-divider {
  width: 1px;
  height: 48px;
  background: rgba(255, 255, 255, 0.1);
  flex-shrink: 0;
}

.stat-number {
  font-size: 1.75rem;
  font-weight: 800;
  color: white;
  line-height: 1;
}

.stat-label {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.55);
  font-weight: 500;
}

.hero-cta {
  margin-bottom: 0;
}

.hero-button {
  padding: 0.875rem 2.5rem;
  font-size: 1rem;
  font-weight: 600;
  height: auto;
  transition: all var(--transition-base);
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4);
}

.hero-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(59, 130, 246, 0.5);
}

.btn-arrow {
  margin-left: 4px;
  transition: transform var(--transition-fast);
}

.hero-button:hover .btn-arrow {
  transform: translateX(3px);
}

.position-section {
  padding: 5rem 0 4rem;
}

.section-header {
  text-align: center;
  margin-bottom: 3rem;
}

.section-badge {
  display: inline-block;
  padding: 0.25rem 0.875rem;
  background: var(--primary-lighter);
  color: var(--primary-color);
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.section-header h2 {
  font-size: 2.25rem;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
  letter-spacing: -0.01em;
}

.section-header p {
  font-size: 1.05rem;
  color: var(--text-secondary);
  max-width: 480px;
  margin: 0 auto;
}

.position-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.position-card {
  position: relative;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  background: var(--surface-color);
  cursor: pointer;
  transition: all var(--transition-base);
  overflow: hidden;
}

.position-card:hover {
  border-color: transparent;
  box-shadow: var(--shadow-lg);
  transform: translateY(-4px);
}

.position-card.selected {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px var(--primary-lighter);
}

.card-accent {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  opacity: 0;
  transition: opacity var(--transition-base);
}

.position-card:hover .card-accent,
.position-card.selected .card-accent {
  opacity: 1;
}

.card-content {
  display: flex;
  align-items: flex-start;
  gap: 1.5rem;
  padding: 2rem;
}

.card-icon-wrapper {
  flex-shrink: 0;
}

.card-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.card-icon svg {
  width: 28px;
  height: 28px;
}

.card-body {
  flex: 1;
}

.card-body h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.card-description {
  color: var(--text-secondary);
  font-size: 0.9rem;
  line-height: 1.6;
  margin-bottom: 0.75rem;
}

.card-tech {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.card-action {
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

.start-btn {
  padding: 0.625rem 1.5rem;
  font-weight: 600;
  font-size: 0.9rem;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all var(--transition-base);
}

.start-btn:hover {
  gap: 8px;
}

.start-btn svg {
  transition: transform var(--transition-fast);
}

.start-btn:hover svg {
  transform: translateX(3px);
}

.interview-tips {
  max-width: 800px;
  margin: 0 auto;
}

.tips-card {
  background: var(--surface-color);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: 1.75rem 2rem;
  box-shadow: var(--shadow-sm);
}

.tips-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.tips-title {
  font-weight: 700;
  color: var(--text-primary);
  font-size: 1rem;
}

.tips-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.625rem;
}

.tips-item {
  display: flex;
  align-items: flex-start;
  gap: 0.625rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
  line-height: 1.5;
}

.tip-bullet {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--primary-lighter);
  color: var(--primary-color);
  font-size: 0.7rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 1px;
}

@media (max-width: 768px) {
  .hero-section {
    padding: 5rem 0 1.5rem;
  }

  .hero-title {
    font-size: 2.25rem;
  }

  .hero-subtitle {
    font-size: 1rem;
  }

  .hero-stats {
    flex-wrap: wrap;
    gap: 1rem;
    padding: 1rem;
  }

  .stat-divider {
    display: none;
  }

  .position-cards {
    grid-template-columns: 1fr;
  }

  .card-content {
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 1.5rem;
  }

  .card-tech {
    justify-content: center;
  }

  .card-action {
    width: 100%;
    justify-content: center;
  }

  .tips-list {
    grid-template-columns: 1fr;
  }

  .section-header h2 {
    font-size: 1.75rem;
  }
}
</style>
