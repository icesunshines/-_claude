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
  if (!chartRef.value || !props.data?.age_stats) return
  if (chart) {
    chart.dispose()
  }
  chart = echarts.init(chartRef.value)

  const ageEntries = Object.entries(props.data.age_stats)
  const ageGroups = ageEntries.map(([age]) => Number(age)).sort((a, b) => a - b)
  const values = ageGroups.map(age => props.data.age_stats[age])

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#334155' },
      extraCssText: 'box-shadow: 0 4px 16px rgba(0,0,0,0.1); border-radius: 12px;',
      formatter: (params) => {
        const age = params[0].name
        const val = params[0].value
        return `<div style="padding: 4px 8px;">
          <div style="font-weight: bold; margin-bottom: 4px;">${age} 岁组</div>
          <div style="color: #14b8a6;">平均血糖：${val} mmol/L</div>
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
      type: 'category',
      data: ageGroups.map(a => `${a}岁`),
      axisLine: { lineStyle: { color: '#e2e8f0', width: 2 } },
      axisLabel: { color: '#64748b', fontSize: 11, margin: 10 },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      name: 'mmol/L',
      nameTextStyle: { color: '#64748b', fontSize: 11 },
      axisLine: { show: false },
      axisLabel: { color: '#64748b', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } }
    },
    series: [{
      type: 'line',
      data: values,
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: { color: '#14b8a6', width: 3 },
      itemStyle: { color: '#14b8a6', borderWidth: 2, borderColor: '#fff' },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(20, 184, 166, 0.25)' },
            { offset: 1, color: 'rgba(20, 184, 166, 0.02)' }
          ]
        }
      },
      emphasis: {
        itemStyle: { borderWidth: 3, shadowColor: 'rgba(20, 184, 166, 0.4)', shadowBlur: 10 }
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
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
        </svg>
      </div>
      <div>
        <h3 class="text-lg font-bold" style="color: var(--ds-text)">年龄段血糖趋势</h3>
        <p class="text-xs" style="color: var(--ds-text-secondary)">各年龄组平均血糖水平</p>
      </div>
    </div>
    <div ref="chartRef" style="width: 100%; height: 300px;"></div>
  </div>
</template>
