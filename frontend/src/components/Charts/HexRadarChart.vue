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
  if (chart) {
    chart.dispose()
  }
  chart = echarts.init(chartRef.value)

  const data = props.overview ? [
    Math.min((props.overview.mean_blood_sugar || 5.5) / 15 * 100, 100),
    Math.min((props.overview.diabetes_metrics?.accuracy || 0.85) * 100, 100),
    Math.min((props.overview.diabetes_metrics?.auc || 0.85) * 100, 100),
    65,
    70,
    55
  ] : [60, 70, 80, 65, 70, 55]

  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#334155' },
      extraCssText: 'box-shadow: 0 4px 16px rgba(0,0,0,0.1); border-radius: 12px;',
      formatter: (params) => {
        return `<div style="padding: 4px 8px;">
          <div style="font-weight: bold; margin-bottom: 4px;">${params.name}</div>
          <div style="color: #8b5cf6;">得分：${params.value.toFixed(1)}</div>
        </div>`
      }
    },
    radar: {
      shape: 'hexagon',
      splitNumber: 4,
      center: ['50%', '52%'],
      radius: '72%',
      axisName: {
        color: '#1e293b',
        fontSize: 13,
        fontWeight: 'bold'
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(100, 116, 139, 0.35)',
          width: 1
        }
      },
      splitArea: {
        areaStyle: {
          color: [
            'rgba(139, 92, 246, 0.08)',
            'rgba(139, 92, 246, 0.14)',
            'rgba(139, 92, 246, 0.08)',
            'rgba(139, 92, 246, 0.14)'
          ]
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(100, 116, 139, 0.6)'
        }
      },
      indicator: indicators
    },
    series: [{
      type: 'radar',
      data: [{
        value: data,
        name: '健康指标',
        areaStyle: {
          color: 'rgba(124, 58, 237, 0.35)'
        },
        lineStyle: {
          color: '#8b5cf6',
          width: 3
        },
        itemStyle: {
          color: '#8b5cf6',
          borderWidth: 2,
          borderColor: '#fff'
        },
        emphasis: {
          areaStyle: {
            color: 'rgba(124, 58, 237, 0.5)'
          }
        }
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
      <div class="w-10 h-10 rounded-xl flex items-center justify-center" style="background: rgba(139,92,246,0.15)">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"></polygon>
          <line x1="12" y1="22" x2="12" y2="15.5"></line>
          <polyline points="22 8.5 12 15.5 2 8.5"></polyline>
        </svg>
      </div>
      <div>
        <h3 class="text-lg font-bold" style="color: var(--ds-text)">健康指标雷达图</h3>
        <p class="text-xs" style="color: var(--ds-text-secondary)">六维度综合健康评估</p>
      </div>
    </div>
    <div ref="chartRef" style="width: 100%; height: 340px;"></div>
  </div>
</template>
