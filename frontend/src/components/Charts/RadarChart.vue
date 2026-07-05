<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  overview: Object,
  loading: Boolean
})

const chartRef = ref(null)
let chart = null

const indicators = [
  { name: 'BMI', max: 40 },
  { name: '空腹血糖', max: 15 },
  { name: '血压', max: 200 },
  { name: '年龄风险', max: 100 },
  { name: '遗传风险', max: 100 },
  { name: '运动水平', max: 100 }
]

function initChart() {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)

  const data = props.overview ? [
    (props.overview.mean_blood_sugar || 5.5) / 15 * 100,
    Math.min((props.overview.diabetes_metrics?.accuracy || 0.85) * 100, 100),
    Math.min((props.overview.diabetes_metrics?.auc || 0.85) * 100, 100),
    65,
    70,
    55
  ] : [60, 70, 80, 65, 70, 55]

  const option = {
    tooltip: {},
    radar: {
      indicator: indicators,
      shape: 'hexagon',
      splitNumber: 4,
      axisName: { color: 'var(--ds-text)' },
      splitLine: { lineStyle: { color: 'var(--ds-border)' } },
      splitArea: { areaStyle: { color: ['rgba(20,184,166,0.05)', 'rgba(139,92,246,0.05)'] } },
      axisLine: { lineStyle: { color: 'var(--ds-border)' } }
    },
    series: [{
      type: 'radar',
      data: [{
        value: data,
        name: '健康指标',
        areaStyle: { color: 'rgba(20, 184, 166, 0.3)' },
        lineStyle: { color: '#14b8a6', width: 2 },
        itemStyle: { color: '#14b8a6' }
      }]
    }]
  }

  chart.setOption(option)
}

watch(() => props.overview, initChart)
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
      <div class="w-10 h-10 rounded-xl flex items-center justify-center" style="background: var(--ds-accent-1); opacity: 0.15"></div>
      <div>
        <h3 class="text-lg font-bold" style="color: var(--ds-text)">健康指标雷达图</h3>
        <p class="text-xs" style="color: var(--ds-text-secondary)">六维度综合评估</p>
      </div>
    </div>
    <div ref="chartRef" style="width: 100%; height: 400px;"></div>
  </div>
</template>
