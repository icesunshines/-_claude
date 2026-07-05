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
  if (!chartRef.value || !props.data?.fpr) return
  if (chart) chart.dispose()
  chart = echarts.init(chartRef.value)

  const fpr = props.data.fpr
  const tpr = props.data.tpr

  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#334155' },
      extraCssText: 'box-shadow: 0 4px 16px rgba(0,0,0,0.1); border-radius: 12px;',
      formatter: (params) => {
        const point = params.value
        return `<div style="padding: 4px 8px;">
          <div style="font-weight: bold; margin-bottom: 4px;">ROC 曲线</div>
          <div style="color: #8b5cf6;">FPR: ${point[0].toFixed(3)}</div>
          <div style="color: #14b8a6;">TPR: ${point[1].toFixed(3)}</div>
        </div>`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: 'False Positive Rate',
      nameTextStyle: { color: '#64748b', fontSize: 11 },
      min: 0,
      max: 1,
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#64748b', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } }
    },
    yAxis: {
      type: 'value',
      name: 'True Positive Rate',
      nameTextStyle: { color: '#64748b', fontSize: 11 },
      min: 0,
      max: 1,
      axisLine: { show: false },
      axisLabel: { color: '#64748b', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } }
    },
    series: [{
      type: 'line',
      data: fpr.map((x, i) => [x, tpr[i]]),
      smooth: true,
      symbol: 'none',
      lineStyle: { color: '#8b5cf6', width: 3 },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(139, 92, 246, 0.25)' },
            { offset: 1, color: 'rgba(139, 92, 246, 0.02)' }
          ]
        }
      }
    }]
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
      <div class="w-10 h-10 rounded-xl flex items-center justify-center" style="background: rgba(139,92,246,0.15)">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <polyline points="12 6 12 12 16 14"></polyline>
        </svg>
      </div>
      <div>
        <h3 class="text-lg font-bold" style="color: var(--ds-text)">ROC 曲线</h3>
        <p class="text-xs" style="color: var(--ds-text-secondary)">模型 discriminative 能力</p>
      </div>
    </div>
    <div ref="chartRef" style="width: 100%; height: 300px;"></div>
  </div>
</template>
