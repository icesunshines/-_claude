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
  chart = echarts.init(chartRef.value)

  const ageGroups = Object.keys(props.data.age_stats || {}).map(Number).sort((a, b) => a - b)
  const values = ageGroups.map(age => props.data.age_stats[age])

  const option = {
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: ageGroups.map(a => `${a}岁`),
      axisLine: { lineStyle: { color: 'var(--ds-border)' } },
      axisLabel: { color: 'var(--ds-text-secondary)' }
    },
    yAxis: {
      type: 'value',
      name: '血糖 (mmol/L)',
      splitLine: { lineStyle: { color: 'var(--ds-border)' } },
      axisLabel: { color: 'var(--ds-text-secondary)' }
    },
    series: [{
      type: 'line',
      data: values,
      smooth: true,
      lineStyle: { color: '#14b8a6', width: 3 },
      itemStyle: { color: '#14b8a6' },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(20, 184, 166, 0.3)' },
            { offset: 1, color: 'rgba(20, 184, 166, 0.05)' }
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
      <div class="w-10 h-10 rounded-xl flex items-center justify-center" style="background: #14b8a6; opacity: 0.15"></div>
      <div>
        <h3 class="text-lg font-bold" style="color: var(--ds-text)">血糖趋势分析</h3>
        <p class="text-xs" style="color: var(--ds-text-secondary)">各年龄段平均血糖</p>
      </div>
    </div>
    <div ref="chartRef" style="width: 100%; height: 300px;"></div>
  </div>
</template>
