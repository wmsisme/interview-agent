<template>
  <div class="home-view">
    <div class="hero-section">
      <div class="container">
        <div class="hero-content">
          <h1 class="hero-title">
            <span class="gradient-text">AI模拟面试教练</span>
          </h1>
          <p class="hero-subtitle">
            专为计算机专业学生打造的智能面试练习平台<br>
            与AI面试官对话，获取专业评估，快速提升面试能力
          </p>
          <div class="hero-stats">
            <div class="stat-item">
              <span class="stat-number">100+</span>
              <span class="stat-label">面试题库</span>
            </div>
            <div class="stat-item">
              <span class="stat-number">5维</span>
              <span class="stat-label">能力评估</span>
            </div>
            <div class="stat-item">
              <span class="stat-number">实时</span>
              <span class="stat-label">语音反馈</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="position-section">
      <div class="container">
        <div class="section-header">
          <h2>选择目标岗位</h2>
          <p>选择您想要练习的岗位，开始模拟面试</p>
        </div>

        <div class="position-cards">
          <el-card
            class="position-card"
            :class="{ 'selected': selectedPosition === 'java_backend' }"
            shadow="hover"
            @click="selectPosition('java_backend')"
          >
            <div class="card-content">
              <div class="card-icon">
                <div class="icon-background java-bg">
                  <svg class="icon" viewBox="0 0 24 24">
                    <path d="M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22A10,10 0 0,1 2,12A10,10 0 0,1 12,2M11,17H13V19H11V17M14.2,14.2L15.6,15.6C16.4,14.9 17,13.9 17,12.7C17,10.6 15.4,9 13.3,9H10V15H13.3C14.1,15 14.8,14.7 15.4,14.2M11,5H13V12H11V5Z" />
                  </svg>
                </div>
              </div>
              <div class="card-details">
                <h3>Java后端开发工程师</h3>
                <p class="card-description">
                  掌握Java、Spring Boot、MySQL、Redis等后端技术栈，<br>
                  熟悉分布式系统设计与高并发处理
                </p>
                <div class="card-tech">
                  <el-tag size="small" type="info">Java</el-tag>
                  <el-tag size="small" type="info">Spring Boot</el-tag>
                  <el-tag size="small" type="info">MySQL</el-tag>
                  <el-tag size="small" type="info">Redis</el-tag>
                </div>
              </div>
              <div class="card-action">
                <el-button
                  type="primary"
                  size="large"
                  :loading="loading.java_backend"
                  @click.stop="startInterview('java_backend')"
                >
                  开始面试
                </el-button>
              </div>
            </div>
          </el-card>

          <el-card
            class="position-card"
            :class="{ 'selected': selectedPosition === 'web_frontend' }"
            shadow="hover"
            @click="selectPosition('web_frontend')"
          >
            <div class="card-content">
              <div class="card-icon">
                <div class="icon-background frontend-bg">
                  <svg class="icon" viewBox="0 0 24 24">
                    <path d="M12,18L16,6L8,6L12,18Z" />
                  </svg>
                </div>
              </div>
              <div class="card-details">
                <h3>Web前端开发工程师</h3>
                <p class="card-description">
                  精通Vue/React、TypeScript、前端工程化，<br>
                  熟悉性能优化与用户体验设计
                </p>
                <div class="card-tech">
                  <el-tag size="small" type="info">Vue</el-tag>
                  <el-tag size="small" type="info">React</el-tag>
                  <el-tag size="small" type="info">TypeScript</el-tag>
                  <el-tag size="small" type="info">Webpack</el-tag>
                </div>
              </div>
              <div class="card-action">
                <el-button
                  type="primary"
                  size="large"
                  :loading="loading.web_frontend"
                  @click.stop="startInterview('web_frontend')"
                >
                  开始面试
                </el-button>
              </div>
            </div>
          </el-card>

          <el-card
            class="position-card"
            :class="{ 'selected': selectedPosition === 'fullstack_engineer' }"
            shadow="hover"
            @click="selectPosition('fullstack_engineer')"
          >
            <div class="card-content">
              <div class="card-icon">
                <div class="icon-background fullstack-bg">
                  <svg class="icon" viewBox="0 0 24 24">
                    <path d="M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22A10,10 0 0,1 2,12A10,10 0 0,1 12,2M11,17H13V19H11V17M14.2,14.2L15.6,15.6C16.4,14.9 17,13.9 17,12.7C17,10.6 15.4,9 13.3,9H10V15H13.3C14.1,15 14.8,14.7 15.4,14.2M11,5H13V12H11V5Z" />
                  </svg>
                </div>
              </div>
              <div class="card-details">
                <h3>全栈开发工程师</h3>
                <p class="card-description">
                  精通前后端开发，掌握Vue/React、Spring Boot、MySQL等技术栈，<br>
                  具备全流程开发能力与系统架构设计经验
                </p>
                <div class="card-tech">
                  <el-tag size="small" type="info">Vue</el-tag>
                  <el-tag size="small" type="info">React</el-tag>
                  <el-tag size="small" type="info">Spring Boot</el-tag>
                  <el-tag size="small" type="info">MySQL</el-tag>
                </div>
              </div>
              <div class="card-action">
                <el-button
                  type="primary"
                  size="large"
                  :loading="loading.fullstack_engineer"
                  @click.stop="startInterview('fullstack_engineer')"
                >
                  开始面试
                </el-button>
              </div>
            </div>
          </el-card>

          <el-card
            class="position-card"
            :class="{ 'selected': selectedPosition === 'bigdata_engineer' }"
            shadow="hover"
            @click="selectPosition('bigdata_engineer')"
          >
            <div class="card-content">
              <div class="card-icon">
                <div class="icon-background bigdata-bg">
                  <svg class="icon" viewBox="0 0 24 24">
                    <path d="M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22A10,10 0 0,1 2,12A10,10 0 0,1 12,2M11,17H13V19H11V17M14.2,14.2L15.6,15.6C16.4,14.9 17,13.9 17,12.7C17,10.6 15.4,9 13.3,9H10V15H13.3C14.1,15 14.8,14.7 15.4,14.2M11,5H13V12H11V5Z" />
                  </svg>
                </div>
              </div>
              <div class="card-details">
                <h3>大数据开发工程师</h3>
                <p class="card-description">
                  掌握Hadoop、Spark、Flink等大数据技术栈，<br>
                  熟悉数据仓库、实时计算与数据治理
                </p>
                <div class="card-tech">
                  <el-tag size="small" type="info">Hadoop</el-tag>
                  <el-tag size="small" type="info">Spark</el-tag>
                  <el-tag size="small" type="info">Flink</el-tag>
                  <el-tag size="small" type="info">Kafka</el-tag>
                </div>
              </div>
              <div class="card-action">
                <el-button
                  type="primary"
                  size="large"
                  :loading="loading.bigdata_engineer"
                  @click.stop="startInterview('bigdata_engineer')"
                >
                  开始面试
                </el-button>
              </div>
            </div>
          </el-card>
        </div>

        <div class="interview-tips">
          <el-alert
            title="面试准备建议"
            type="info"
            :closable="false"
            show-icon
          >
            <ul class="tips-list">
              <li>提前准备好个人项目和技术亮点的介绍</li>
              <li>思考常见面试问题的回答思路</li>
              <li>确保网络环境良好，麦克风工作正常</li>
              <li>每次面试后认真阅读评估报告，针对性改进</li>
            </ul>
          </el-alert>
        </div>
      </div>
    </div>

    <div class="history-section" v-if="false"> <!-- 暂时隐藏历史记录 -->
      <div class="container">
        <div class="section-header">
          <h2>历史面试记录</h2>
          <el-button link>查看全部</el-button>
        </div>
        <div class="history-empty">
          <el-empty description="暂无历史面试记录" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useInterviewStore } from '@/stores/interview'

const router = useRouter()
const interviewStore = useInterviewStore()

const selectedPosition = ref<string>('')
const loading = ref({
  java_backend: false,
  web_frontend: false,
  fullstack_engineer: false,
  bigdata_engineer: false
})

const selectPosition = (position: string) => {
  selectedPosition.value = position
}

const startInterview = async (position: string) => {
  try {
    // 直接开始视频面试，不显示选择弹窗
    (loading.value as Record<string, boolean>)[position] = true
    
    // 使用视频面试
    await interviewStore.startInterview(position, true)
    router.push('/interview/video')
  } catch (error) {
    ElMessage.error('开始面试失败，请重试')
    console.error(error)
  } finally {
    const positionKey = position as keyof typeof loading.value
    if (positionKey in loading.value) {
      loading.value[positionKey] = false
    }
  }
}
</script>

<style scoped>
.home-view {
  min-height: 100vh;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
}

.hero-section {
  padding: 4rem 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-align: center;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

.hero-content {
  max-width: 800px;
  margin: 0 auto;
}

.hero-title {
  font-size: 3.5rem;
  font-weight: 800;
  margin-bottom: 1rem;
  line-height: 1.2;
}

.gradient-text {
  background: linear-gradient(90deg, #ffd700, #fbbf24);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 1.25rem;
  opacity: 0.9;
  margin-bottom: 2rem;
  line-height: 1.6;
}

.hero-stats {
  display: flex;
  justify-content: center;
  gap: 3rem;
  margin-top: 3rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-number {
  font-size: 2.5rem;
  font-weight: 700;
  line-height: 1;
}

.stat-label {
  font-size: 1rem;
  opacity: 0.8;
  margin-top: 0.5rem;
}

.position-section {
  padding: 4rem 0;
}

.section-header {
  text-align: center;
  margin-bottom: 3rem;
}

.section-header h2 {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.section-header p {
  font-size: 1.125rem;
  color: var(--text-secondary);
}

.position-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 2rem;
  margin-bottom: 3rem;
}

.position-card {
  border: 2px solid transparent;
  transition: all 0.3s ease;
  cursor: pointer;
}

.position-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg) !important;
}

.position-card.selected {
  border-color: var(--primary-color);
  background-color: rgba(59, 130, 246, 0.05);
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1.5rem;
}

.card-icon {
  display: flex;
  justify-content: center;
}

.icon-background {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.java-bg {
  background: linear-gradient(135deg, #f97316, #ea580c);
}

.frontend-bg {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
}

.fullstack-bg {
  background: linear-gradient(135deg, #10b981, #059669);
}

.bigdata-bg {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
}

.icon {
  width: 40px;
  height: 40px;
  fill: white;
}

.card-details h3 {
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.75rem;
}

.card-description {
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 1rem;
}

.card-tech {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.card-action {
  display: flex;
  justify-content: center;
}

.interview-tips {
  max-width: 800px;
  margin: 0 auto;
}

.tips-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.tips-list li {
  padding: 0.25rem 0;
  color: var(--text-secondary);
}

.history-section {
  padding: 3rem 0;
  border-top: 1px solid var(--border-color);
}

.history-empty {
  max-width: 400px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 2.5rem;
  }
  
  .position-cards {
    grid-template-columns: 1fr;
  }
  
  .hero-stats {
    gap: 1.5rem;
  }
  
  .stat-number {
    font-size: 2rem;
  }
}
</style>
