<template>
  <div class="score-radar">
    <div ref="chartRef" class="radar-chart"></div>
    
    <div v-if="!hasData" class="empty-state">
      <el-empty description="暂无评估数据" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import type { ECharts, RadarSeriesOption } from 'echarts'

export interface RadarDataItem {
  name: string
  value: number
  max?: number
}

interface Props {
  data: RadarDataItem[]
  title?: string
  height?: number
  width?: number
}

const props = withDefaults(defineProps<Props>(), {
  data: () => [],
  title: '能力评估雷达图',
  height: 400,
  width: 600
})

const chartRef = ref<HTMLDivElement>()
const chartInstance = ref<ECharts | null>(null)
const hasData = ref(false)

// 计算雷达图指标
const radarIndicator = () => {
  return props.data.map(item => ({
    name: item.name,
    max: item.max || 10
  }))
}

// 计算雷达图数据
const radarData = () => {
  return {
    value: props.data.map(item => item.value),
    name: '能力评估'
  }
}

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return
  
  // 检查是否有数据
  if (props.data.length === 0) {
    console.log('ScoreRadar: 无数据，跳过图表初始化')
    return
  }
  
  // 销毁旧实例
  if (chartInstance.value) {
    chartInstance.value.dispose()
  }
  
  // 创建新实例
  chartInstance.value = echarts.init(chartRef.value)
  
  // 设置配置
  const option = {
    title: {
      text: props.title,
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: '600',
        color: '#1e293b'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: function(params: any) {
        if (!params || !params.data || !params.indicator) {
          return '-'
        }
        const indicatorName = params.indicator.name || params.name || ''
        const value = Number(params.value)
        const formattedValue = isNaN(value) ? '0.0' : value.toFixed(1)
        return `${indicatorName}: ${formattedValue}/${params.indicator.max}`
      }
    },
    legend: {
      show: false
    },
    radar: {
      indicator: radarIndicator(),
      shape: 'polygon',
      splitNumber: 5,
      radius: '65%',
      axisName: {
        color: '#64748b',
        fontSize: 12,
        padding: [3, 5]
      },
      splitLine: {
        lineStyle: {
          color: ['#e2e8f0', '#cbd5e1', '#94a3b8', '#64748b', '#475569'].reverse()
        }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['#f8fafc', '#f1f5f9', '#e2e8f0', '#cbd5e1', '#94a3b8'].reverse()
        }
      },
      axisLine: {
        lineStyle: {
          color: '#cbd5e1'
        }
      }
    },
    series: [
      {
        type: 'radar',
        data: [radarData()],
        symbolSize: 8,
        lineStyle: {
          width: 3,
          color: '#3b82f6'
        },
        areaStyle: {
          color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
            { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0.1)' }
          ])
        },
        itemStyle: {
          color: '#3b82f6'
        },
        label: {
          show: true,
          formatter: (params: any) => params.value.toFixed(1),
          color: '#1e293b',
          fontSize: 12,
          fontWeight: '600'
        }
      }
    ],
    color: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
  }
  
  chartInstance.value.setOption(option)
}

// 更新图表
const updateChart = () => {
  hasData.value = props.data.length > 0
  
  if (!hasData.value) {
    if (chartInstance.value) {
      chartInstance.value.clear()
    }
    return
  }
  
  if (chartInstance.value) {
    const option = {
      radar: {
        indicator: radarIndicator()
      },
      series: [
        {
          data: [radarData()]
        }
      ]
    }
    chartInstance.value.setOption(option)
  } else {
    initChart()
  }
}

// 窗口大小变化时重绘
const handleResize = () => {
  if (chartInstance.value) {
    chartInstance.value.resize()
  }
}

// 获取分数颜色
const getScoreColor = (score: number): string => {
  if (score >= 9) return '#10b981'
  if (score >= 7) return '#3b82f6'
  if (score >= 5) return '#f59e0b'
  return '#ef4444'
}

// 生命周期
onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (chartInstance.value) {
    chartInstance.value.dispose()
    chartInstance.value = null
  }
  window.removeEventListener('resize', handleResize)
})

// 监听数据变化
watch(() => props.data, () => {
  nextTick(() => {
    updateChart()
  })
}, { deep: true })

// 监听尺寸变化
watch(() => props.height, () => {
  if (chartRef.value) {
    chartRef.value.style.height = `${props.height}px`
  }
  handleResize()
})

watch(() => props.width, () => {
  if (chartRef.value) {
    chartRef.value.style.width = `${props.width}px`
  }
  handleResize()
})

// 暴露方法
defineExpose({
  getInstance: () => chartInstance.value,
  resize: handleResize
})
</script>

<style scoped>
.score-radar {
  width: 100%;
  height: 100%;
  position: relative;
}

.radar-chart {
  width: 100%;
  height: 100%;
  min-height: 300px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
  background: #f8fafc;
  border-radius: var(--radius-md);
  border: 1px dashed var(--border-color);
}
</style>