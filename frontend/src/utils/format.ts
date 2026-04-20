export const formatScore = (score: number): string => {
  return score.toFixed(1)
}

export const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

export const formatDate = (date: Date | string): string => {
  const d = new Date(date)
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

export const getPositionName = (position: string): string => {
  const positions: Record<string, string> = {
    'java_backend': 'Java后端开发工程师',
    'web_frontend': 'Web前端开发工程师',
    'fullstack_engineer': '全栈开发工程师',
    'bigdata_engineer': '大数据开发工程师',
    'java': 'Java后端开发工程师',
    'frontend': 'Web前端开发工程师',
    'fullstack': '全栈开发工程师',
    'bigdata': '大数据开发工程师'
  }
  return positions[position] || position
}

export const getPositionDescription = (position: string): string => {
  const descriptions: Record<string, string> = {
    'java_backend': '掌握Java、Spring Boot、MySQL等技术栈',
    'web_frontend': '熟悉Vue/React、TypeScript、前端工程化',
    'fullstack_engineer': '精通前后端开发，掌握Vue/React、Spring Boot、MySQL等技术栈',
    'bigdata_engineer': '掌握Hadoop、Spark、Flink等大数据技术栈',
    'java': '深入理解JVM、多线程、分布式系统设计',
    'frontend': '精通现代前端框架、性能优化、用户体验设计',
    'fullstack': '精通前后端开发，掌握Vue/React、Spring Boot、MySQL等技术栈',
    'bigdata': '掌握Hadoop、Spark、Flink等大数据技术栈'
  }
  return descriptions[position] || '计算机相关技术岗位'
}

export const calculateAverageScore = (scores: number[]): number => {
  if (scores.length === 0) return 0
  const sum = scores.reduce((a, b) => a + b, 0)
  return Number((sum / scores.length).toFixed(1))
}

export const generateRadarData = (evaluation: {
  techScore: number
  depthScore: number
  logicScore: number
  matchScore: number
}) => {
  return [
    { name: '技术能力', value: evaluation.techScore },
    { name: '知识深度', value: evaluation.depthScore },
    { name: '逻辑表达', value: evaluation.logicScore },
    { name: '岗位匹配', value: evaluation.matchScore }
  ]
}