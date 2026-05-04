<template>
  <div class="report-view">
    <div class="header">
      <el-page-header @back="goBack">
        <template #content>
          <div class="header-content">
            <span class="title">面试报告</span>
            <el-tag v-if="reportData" type="info">{{ formatDate(reportData.interviewDate) }}</el-tag>
          </div>
        </template>
        <template #extra>
          <el-button type="primary" @click="downloadReport" :loading="downloading">下载报告</el-button>
          <el-button @click="goHome">返回首页</el-button>
        </template>
      </el-page-header>
    </div>

    <div class="report-container" v-if="reportData">
      <!-- 报告摘要 -->
      <div class="report-summary">
        <el-card class="summary-card">
          <div class="summary-content">
            <div class="overall-score">
              <div class="score-circle">
                <span class="score-value">{{ Number(reportData.overallScore).toFixed(1) }}</span>
                <span class="score-label">综合得分</span>
              </div>
            </div>
            <div class="summary-details">
              <h3>{{ reportData.positionName }}</h3>
              <p class="summary-text">{{ reportData.summary }}</p>
              <div class="summary-stats">
                <div class="stat-item">
                  <span class="stat-label">面试时长</span>
                  <span class="stat-value">{{ reportData.duration }}分钟</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">问题数量</span>
                  <span class="stat-value">{{ reportData.questionCount }}个</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">平均得分</span>
                  <span class="stat-value">{{ Number(reportData.averageScore).toFixed(1) }}/10</span>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 能力雷达图 -->
      <div class="radar-section">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>能力评估雷达图</span>
            </div>
          </template>
          <div class="radar-chart">
            <ScoreRadar :data="reportData.radarData" />
          </div>
          <div class="radar-legend">
            <div v-for="item in reportData.radarData" :key="item.name" class="legend-item">
              <span class="legend-color" :style="{ backgroundColor: getColorForScore(item.value) }"></span>
              <span class="legend-name">{{ item.name }}</span>
              <span class="legend-score">{{ Number(item.value).toFixed(1) }}/10</span>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 详细评估 -->
      <div class="detailed-assessment">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-card class="strengths-card">
              <template #header>
                <div class="card-header">
                  <el-icon><SuccessFilled /></el-icon>
                  <span>亮点与优势</span>
                </div>
              </template>
              <ul class="assessment-list">
                <li v-for="(strength, index) in reportData.strengths" :key="index" class="assessment-item">
                  {{ strength }}
                </li>
              </ul>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="weaknesses-card">
              <template #header>
                <div class="card-header">
                  <el-icon><WarningFilled /></el-icon>
                  <span>待改进项</span>
                </div>
              </template>
              <ul class="assessment-list">
                <li v-for="(weakness, index) in reportData.weaknesses" :key="index" class="assessment-item">
                  {{ weakness }}
                </li>
              </ul>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 改进建议 -->
      <div class="suggestions-section">
        <el-card>
          <template #header>
            <div class="card-header">
              <el-icon><Star /></el-icon>
              <span>提升建议</span>
            </div>
          </template>
          <div class="suggestions-content">
            <div v-for="(suggestion, index) in reportData.suggestions" :key="index" class="suggestion-item">
              <div class="suggestion-header">
                <span class="suggestion-index">{{ Number(index) + 1 }}</span>
                <span class="suggestion-title">{{ suggestion.title }}</span>
              </div>
              <p class="suggestion-description">{{ suggestion.description }}</p>
              <div v-if="suggestion.resources" class="suggestion-resources">
                <span class="resources-label">推荐资源：</span>
                <span class="resources-list">{{ suggestion.resources }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 面试记录 -->
      <div class="interview-records" v-if="reportData.records">
        <el-card>
          <template #header>
            <div class="card-header">
              <el-icon><Document /></el-icon>
              <span>面试记录</span>
            </div>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="(record, index) in reportData.records"
              :key="index"
              :timestamp="`第${Number(index) + 1}轮`"
              placement="top"
            >
              <el-card>
                <h4>{{ record.question }}</h4>
                <p class="record-answer">{{ record.answer }}</p>
                <div class="record-scores">
                  <el-tag
                    v-for="score in record.scores"
                    :key="score.name"
                    :type="getScoreTagType(score.value)"
                    size="small"
                  >
                    {{ score.name }}: {{ Number(score.value).toFixed(1) }}/10
                  </el-tag>
                </div>
                <p class="record-feedback">{{ record.feedback }}</p>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </div>

      <!-- 行动按钮 -->
      <div class="action-buttons">
        <el-button type="primary" size="large" @click="restartInterview">重新面试</el-button>
        <el-button size="large" @click="goHome">返回首页</el-button>
      </div>
    </div>

    <div v-else-if="loading" class="loading-state">
      <el-result icon="info" title="报告加载中...">
        <template #extra>
          <el-button type="primary" @click="goHome">返回首页</el-button>
        </template>
      </el-result>
    </div>
    <div v-else class="loading-state">
      <el-result icon="error" title="报告加载失败">
        <template #sub-title>
          <span>无法获取面试报告数据，请检查后端服务状态</span>
        </template>
        <template #extra>
          <el-button type="primary" @click="loadReport">重新加载</el-button>
          <el-button @click="goHome">返回首页</el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { SuccessFilled, WarningFilled, Star, Document } from '@element-plus/icons-vue'
import ScoreRadar from '@/components/ScoreRadar.vue'
import { getReport, downloadReportPdf } from '@/api/interview'
import { formatDate, generateRadarData } from '@/utils/format'

const route = useRoute()
const router = useRouter()

const reportData = ref<any>(null)
const loading = ref(true)
const downloading = ref(false)

const loadReport = async () => {
  const interviewId = route.params.id as string
  if (!interviewId) {
    ElMessage.error('无效的报告ID')
    router.push('/')
    return
  }

  try {
    loading.value = true
    
    reportData.value = null
    
    const response = await getReport(parseInt(interviewId))
    
    let report
    if (typeof response === 'string') {
      try {
        report = JSON.parse(response)
      } catch {
        ElMessage.error('报告数据格式异常')
        reportData.value = null
        return
      }
    } else if (response && typeof response === 'object') {
      report = response
    } else {
      ElMessage.error('未能获取到报告数据')
      reportData.value = null
      return
    }
    
    if (!report || typeof report !== 'object') {
      ElMessage.error('报告数据无效')
      reportData.value = null
      return
    }
    
    const getRadarData = () => {
      if (report.radarData && Array.isArray(report.radarData) && report.radarData.length > 0) {
        return report.radarData.map((item: any) => ({
          name: item.name || '未知',
          value: Number(item.value) || 0,
          max: item.max ? Number(item.max) : 10
        }))
      }
      const defaultScore = Number(report.overallScore) || 0
      return [
        { name: '技术能力', value: defaultScore },
        { name: '知识深度', value: defaultScore },
        { name: '逻辑表达', value: defaultScore },
        { name: '岗位匹配', value: defaultScore }
      ]
    }
    
    reportData.value = {
      interviewId: parseInt(interviewId),
      positionName: report.positionName || report.position || '面试报告',
      overallScore: Number(report.overallScore) || 0,
      summary: report.summary || report.evaluation || '暂无报告摘要',
      duration: Number(report.duration) || 0,
      questionCount: Number(report.questionCount) || 0,
      averageScore: Number(report.averageScore) || 0,
      interviewDate: report.interviewDate || report.startTime || new Date().toISOString(),
      radarData: getRadarData(),
      strengths: report.strengths || [],
      weaknesses: report.weaknesses || [],
      suggestions: report.suggestions || report.detailedSuggestions || [],
      records: report.records || []
    }
    
  } catch (error) {
    console.error('加载报告失败:', error)
    ElMessage.error('加载报告失败，请检查后端服务是否正常运行')
    reportData.value = null
  } finally {
    loading.value = false
  }
}

const getColorForScore = (score: number): string => {
  if (score >= 9) return '#10b981'
  if (score >= 7) return '#3b82f6'
  if (score >= 5) return '#f59e0b'
  return '#ef4444'
}

const getScoreTagType = (score: number): string => {
  if (score >= 9) return 'success'
  if (score >= 7) return 'primary'
  if (score >= 5) return 'warning'
  return 'danger'
}

const goBack = () => {
  console.log('ReportView.goBack called, history length:', window.history.length)
  
  // 尝试返回上一页，如果失败则返回首页
  if (window.history.length > 1) {
    console.log('Navigating back with router.go(-1)')
    router.go(-1)
  } else {
    console.log('No history, navigating to home with router.push("/")')
    router.push('/')
  }
}

const goHome = () => {
  console.log('ReportView.goHome called, navigating to home')
  router.push('/')
}

const downloadReport = async () => {
  const interviewId = route.params.id as string
  if (!interviewId) {
    ElMessage.error('无效的报告ID')
    return
  }

  try {
    downloading.value = true
    ElMessage.info('正在准备下载报告，请稍候...')
    
    const response = await downloadReportPdf(parseInt(interviewId))
    
    let blob: Blob
    const responseData = response.data
    if (responseData instanceof Blob) {
      blob = responseData
    } else {
      blob = new Blob([responseData || response], { type: 'application/pdf' })
    }
    
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    const position = reportData.value?.positionName || '面试报告'
    const filename = `面试报告_${position}_${interviewId}.pdf`
    link.download = filename
    
    document.body.appendChild(link)
    link.click()
    
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('报告下载成功')
    
  } catch (error) {
    console.error('下载报告失败:', error)
    ElMessage.error('报告下载失败，请稍后重试')
  } finally {
    downloading.value = false
  }
}

const restartInterview = () => {
  if (reportData.value) {
    router.push(`/interview?position=${reportData.value.positionName.toLowerCase().replace(/ /g, '_')}`)
  } else {
    router.push('/')
  }
}

onMounted(() => {
  loadReport()
})

// 监听路由参数变化，当interviewId变化时重新加载报告
watch(() => route.params.id, (newId, oldId) => {
  if (newId && newId !== oldId) {
    loadReport()
  }
})
</script>

<style scoped>
.report-view {
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

.title {
  font-size: 1.25rem;
  font-weight: 600;
}

.report-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.report-summary {
  margin-bottom: 1.5rem;
}

.summary-card {
  border: none;
  box-shadow: var(--shadow-lg);
}

.summary-content {
  display: flex;
  align-items: center;
  gap: 2rem;
  padding: 1rem;
}

.overall-score {
  flex-shrink: 0;
}

.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: var(--shadow-lg);
}

.score-value {
  font-size: 2.5rem;
  font-weight: 700;
  line-height: 1;
}

.score-label {
  font-size: 0.875rem;
  opacity: 0.9;
}

.summary-details {
  flex: 1;
}

.summary-details h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
  color: var(--text-primary);
}

.summary-text {
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 1rem;
}

.summary-stats {
  display: flex;
  gap: 2rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--primary-color);
}

.radar-section {
  margin-bottom: 1.5rem;
}

.radar-chart {
  height: 400px;
}

.radar-legend {
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin-top: 1rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-name {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.legend-score {
  font-weight: 600;
  color: var(--text-primary);
}

.detailed-assessment {
  margin-bottom: 1.5rem;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
}

.assessment-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.assessment-item {
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border-color);
  line-height: 1.5;
}

.assessment-item:last-child {
  border-bottom: none;
}

.suggestions-section {
  margin-bottom: 1.5rem;
}

.suggestion-item {
  padding: 1rem 0;
  border-bottom: 1px solid var(--border-color);
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.suggestion-index {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: var(--primary-color);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
}

.suggestion-title {
  font-weight: 600;
  color: var(--text-primary);
}

.suggestion-description {
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 0.5rem;
  padding-left: 2.25rem;
}

.suggestion-resources {
  padding-left: 2.25rem;
  font-size: 0.875rem;
}

.resources-label {
  font-weight: 600;
  color: var(--text-primary);
}

.resources-list {
  color: var(--text-secondary);
}

.interview-records {
  margin-bottom: 1.5rem;
}

.record-answer {
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0.5rem 0;
}

.record-scores {
  display: flex;
  gap: 0.5rem;
  margin: 0.5rem 0;
}

.record-feedback {
  color: var(--text-primary);
  font-style: italic;
  border-left: 3px solid var(--primary-color);
  padding-left: 0.75rem;
  margin: 0.5rem 0;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 1rem;
  padding: 2rem 0;
}

.loading-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>