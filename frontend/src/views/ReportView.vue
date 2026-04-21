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
          <el-button type="primary" @click="downloadReport">下载报告</el-button>
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
                <span class="score-value">{{ reportData.overallScore }}</span>
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
                  <span class="stat-value">{{ reportData.averageScore }}/10</span>
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
              <span class="legend-score">{{ item.value }}/10</span>
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
                    {{ score.name }}: {{ score.value }}/10
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

    <div v-else class="loading-state">
      <el-result icon="info" title="报告加载中...">
        <template #extra>
          <el-button type="primary" @click="goHome">返回首页</el-button>
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

const loadReport = async () => {
  const interviewId = route.params.id as string
  if (!interviewId) {
    ElMessage.error('无效的报告ID')
    router.push('/')
    return
  }

  try {
    loading.value = true
    
    // 清除之前的报告数据
    reportData.value = null
    
    // 尝试从API获取报告数据
    const response = await getReport(parseInt(interviewId))
    
    // 假设API返回JSON字符串或直接是对象
    // 如果是字符串，尝试解析
    let report
    if (typeof response === 'string') {
      try {
        report = JSON.parse(response)
      } catch {
        // 如果不是JSON，可能是文本报告
        report = {
          interviewId: parseInt(interviewId),
          positionName: '面试报告',
          overallScore: 0,
          summary: response || '暂无报告内容',
          duration: 0,
          questionCount: 0,
          averageScore: 0,
          interviewDate: new Date().toISOString(),
          radarData: [],
          strengths: [],
          weaknesses: [],
          suggestions: [],
          records: []
        }
      }
    } else {
      report = response
    }
    
    // 获取雷达数据，如果为空则使用默认数据
    const getRadarData = () => {
      if (report.radarData && Array.isArray(report.radarData) && report.radarData.length > 0) {
        // 确保每个雷达数据项的value是数字
        return report.radarData.map((item: any) => ({
          name: item.name || '未知',
          value: Number(item.value) || 0,
          max: item.max ? Number(item.max) : 10
        }))
      }
      // 使用默认雷达数据
      const defaultScore = Number(report.overallScore) || 0
      return [
        { name: '技术能力', value: defaultScore },
        { name: '知识深度', value: defaultScore },
        { name: '逻辑表达', value: defaultScore },
        { name: '岗位匹配', value: defaultScore }
      ]
    }
    
    // 确保报告数据有基本结构
    reportData.value = {
      interviewId: parseInt(interviewId),
      positionName: report.positionName || '面试报告',
      overallScore: Number(report.overallScore) || 0,
      summary: report.summary || '暂无报告摘要',
      duration: Number(report.duration) || 0,
      questionCount: Number(report.questionCount) || 0,
      averageScore: Number(report.averageScore) || 0,
      interviewDate: report.interviewDate || new Date().toISOString(),
      radarData: getRadarData(),
      strengths: report.strengths || [],
      weaknesses: report.weaknesses || [],
      suggestions: report.suggestions || [],
      records: report.records || []
    }
    
  } catch (error) {
    console.error('加载报告失败:', error)
    
    // API失败时使用模拟数据（仅用于演示）
    ElMessage.warning('报告API暂时不可用，显示示例报告')
    reportData.value = {
      interviewId: parseInt(interviewId),
      positionName: 'Java后端开发工程师',
      overallScore: 82,
      summary: '您在本次面试中展现了扎实的Java基础和良好的逻辑思维能力，但在分布式系统和高并发场景下的实践经验有待加强。',
      duration: 25,
      questionCount: 8,
      averageScore: 8.2,
      interviewDate: new Date().toISOString(),
      radarData: [
        { name: '技术能力', value: 8.5 },
        { name: '知识深度', value: 7.8 },
        { name: '逻辑表达', value: 8.2 },
        { name: '岗位匹配', value: 8.0 }
      ],
      strengths: [
        'Java基础扎实，对集合框架、多线程等核心概念理解透彻',
        '代码逻辑清晰，问题分析能力较强',
        '对Spring框架有一定了解，能够回答基本使用问题'
      ],
      weaknesses: [
        '分布式系统设计经验不足，对微服务架构理解不够深入',
        '高并发场景下的性能优化经验较少',
        '对JVM调优和内存管理了解不够全面'
      ],
      suggestions: [
        {
          title: '深入学习分布式系统',
          description: '建议学习分布式事务、服务治理、分布式缓存等核心概念，可以阅读《分布式系统概念与设计》等经典书籍。',
          resources: '《分布式系统概念与设计》、MIT 6.824课程'
        },
        {
          title: '掌握JVM性能调优',
          description: '深入理解JVM内存结构、垃圾回收机制，学习使用JVM监控工具进行性能分析和调优。',
          resources: '《深入理解Java虚拟机》、Arthas工具'
        },
        {
          title: '积累高并发实践经验',
          description: '通过实际项目或模拟场景练习高并发系统的设计和优化，学习限流、降级、熔断等保障策略。',
          resources: '《Java并发编程实战》、压测工具JMeter'
        }
      ],
      records: [
        {
          question: '请解释HashMap的工作原理',
          answer: 'HashMap是基于哈希表实现的Map接口，它使用数组和链表（或红黑树）的组合结构...',
          scores: [
            { name: '技术', value: 9 },
            { name: '深度', value: 8 },
            { name: '逻辑', value: 8 }
          ],
          feedback: '回答准确，但对红黑树转换条件和哈希冲突解决细节可以进一步深入。'
        },
        {
          question: 'Spring Bean的生命周期是怎样的？',
          answer: 'Spring Bean的生命周期包括实例化、属性赋值、初始化、使用和销毁等阶段...',
          scores: [
            { name: '技术', value: 8 },
            { name: '深度', value: 7 },
            { name: '逻辑', value: 8 }
          ],
          feedback: '基本流程正确，但对后置处理器和AOP代理的时机描述不够详细。'
        }
      ]
    }
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
    ElMessage.info('正在生成PDF报告，请稍候...')
    
    // 调用PDF下载API
    const response = await downloadReportPdf(parseInt(interviewId))
    
    // 创建Blob对象
    let blob: Blob
    const responseData = response.data
    if (responseData instanceof Blob) {
      // response.data已经是Blob对象
      blob = responseData
    } else {
      // 回退到原始方法
      blob = new Blob([responseData || response], { type: 'application/pdf' })
    }
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // 设置文件名
    const position = reportData.value?.positionName || '面试报告'
    const filename = `面试报告_${position}_${interviewId}.pdf`
    link.download = filename
    
    // 触发下载
    document.body.appendChild(link)
    link.click()
    
    // 清理
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('报告下载成功')
    
  } catch (error) {
    console.error('下载报告失败:', error)
    ElMessage.error('报告下载失败，请稍后重试')
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