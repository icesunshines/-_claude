<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: Object,
  loading: Boolean
})

const chartRef = ref(null)
let chart = null

function initChart() {
  if (!chartRef.value || !props.data) return
  if (chart) chart.dispose()
  chart = echarts.init(chartRef.value)

  const cm = props.data
  const values = [
    cm.tn || 0, cm.fp || 0,
    cm.fn || 0, cm.tp || 0
  ]

  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#334155' },
      extraCssText: 'box-shadow: 0 4px 16px rgba(0,0,0,0.1); border-radius: 12px;',
      formatter: (params) => {
        const labels = ['真阴性', '假阳性', '假阴性', '真阳性']
        return `<div style="padding: 4px 8px;">
          <div style="font-weight: bold; margin-bottom: 4px;">${labels[params.dataIndex]}</div>
          <div style="color: #14b8a6;">数量：${params.value}</div>
        </div>`
      }
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: ['预测: 健康', '预测: 患病'],
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#475569', fontSize: 12, fontWeight: 'bold' },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'category',
      data: ['实际: 健康', '实际: 患病'],
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#475569', fontSize: 12, fontWeight: 'bold' },
      axisTick: { show: false }
    },
    visualMap: {
      show: false,
      min: 0,
      max: Math.max(values[0], values[1], values[2], values[3]) || 1,
      inRange: { color: ['#f1f5f9', '#0f766e'] }
    },
    series: [{
      type: 'heatmap',
      data: [],
      label: {
        show: true,
        fontSize: 16,
        fontWeight: 'bold',
        color: '#1e293b',
        formatter: (params) => {
          const total = values.reduce((a, b) => a + b, 0)
          const pct = total > 0 ? ((params.value[2] / total) * 100).toFixed(1) : 0
          return `${params.value[2]}\n(${pct}%)`
        }
      },
      itemStyle: {
        borderWidth: 4,
        borderColor: '#fff'
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.2)'
        }
      }
    }]
  }

  if (values.length === 4) {
    option.series[0].data = [
      { value: [0, 0, values[0]], itemStyle: { color: '#22c55e' } },
      { value: [1, 0, values[1]], itemStyle: { color: '#f59e0b' } },
      { value: [0, 1, values[2]], itemStyle: { color: '#f59e0b' } },
      { value: [1, 1, values[3]], itemStyle: { color: '#14b8a6' } }
    ]
  }

  chart.setOption(option)
}

watch(() => props.data, initChart)

onMounted(() => {
  if (!props.loading) initChart()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})

function handleResize() {
  chart?.resize()
}
</script>

<template>
  <div>
    <div class="flex items-center gap-3 mb-4">
      <div class="w-10 h-10 rounded-xl flex items-center justify-center" style="background: rgba(20,184,166,0.15)">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#14b8a6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <line x1="3" y1="9" x2="21" y2="9"></line>
          <line x1="9" y1="21" x2="9" y2="9"></line>
        </svg>
      </div>
      <div>
        <h3 class="text-lg font-bold" style="color: var(--ds-text)">混淆矩阵</h3>
        <p class="text-xs" style="color: var(--ds-text-secondary)">分类结果分布</p>
      </div>
    </div>
    <div ref="chartRef" style="width: 100%; height: 300px;"></div>
  </div>
</template>
