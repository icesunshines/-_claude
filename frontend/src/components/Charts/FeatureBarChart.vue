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
  if (!chartRef.value || !props.data?.features) return
  if (chart) chart.dispose()
  chart = echarts.init(chartRef.value)

  const features = props.data.features.slice(0, 10)
  const values = props.data.values.slice(0, 10)

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#334155' },
      extraCssText: 'box-shadow: 0 4px 16px rgba(0,0,0,0.1); border-radius: 12px;',
      formatter: (params) => {
        const item = params[0]
        return `<div style="padding: 4px 8px;">
          <div style="font-weight: bold; margin-bottom: 4px;">${item.name}</div>
          <div style="color: #14b8a6;">重要性：${item.value}</div>
        </div>`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { color: '#64748b', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } }
    },
    yAxis: {
      type: 'category',
      data: features.reverse(),
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#475569', fontSize: 11, fontWeight: 'bold' },
      axisTick: { show: false }
    },
    series: [{
      type: 'bar',
      data: values.reverse(),
      barWidth: '60%',
      itemStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 1, y2: 0,
          colorStops: [
            { offset: 0, color: '#14b8a6' },
            { offset: 1, color: '#0d9488' }
          ]
        },
        borderRadius: [0, 6, 6, 0]
      },
      emphasis: {
        itemStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 1, y2: 0,
            colorStops: [
              { offset: 0, color: '#0d9488' },
              { offset: 1, color: '#14b8a6' }
            ]
          }
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
      <div class="w-10 h-10 rounded-xl flex items-center justify-center" style="background: rgba(20,184,166,0.15)">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#14b8a6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="20" x2="18" y2="10"></line>
          <line x1="12" y1="20" x2="12" y2="4"></line>
          <line x1="6" y1="20" x2="6" y2="14"></line>
        </svg>
      </div>
      <div>
        <h3 class="text-lg font-bold" style="color: var(--ds-text)">特征重要性</h3>
        <p class="text-xs" style="color: var(--ds-text-secondary)">Top 10 影响因素</p>
      </div>
    </div>
    <p class="text-xs text-slate-500 mb-4">数值越高，表示该指标对血糖预测的影响越大</p>
    <div ref="chartRef" style="width: 100%; height: 320px;"></div>
  </div>
</template>
