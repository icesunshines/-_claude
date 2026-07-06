<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  overview: Object,
  loading: Boolean
})

const chartRef = ref(null)
let chart = null

const radarLabels = ['年龄', '孕前BMI', '收缩压', '舒张压', '糖筛孕周', '空腹血糖']
const radarMax = {
  '年龄': 100,
  '孕前BMI': 50,
  '收缩压': 200,
  '舒张压': 120,
  '糖筛孕周': 30,
  '空腹血糖': 15
}

function initChart() {
  if (!chartRef.value) return
  if (chart) {
    chart.dispose()
  }
  chart = echarts.init(chartRef.value)

  let healthyValues = []
  let patientValues = []
  let useFallback = false

  if (props.overview && props.overview.radar_comparison) {
    const radar = props.overview.radar_comparison
    healthyValues = radarLabels.map(label => {
      const val = radar[label]?.healthy_mean || 0
      const maxVal = radarMax[label] || 100
      return Math.min((val / maxVal) * 100, 100)
    })
    patientValues = radarLabels.map(label => {
      const val = radar[label]?.patient_mean || 0
      const maxVal = radarMax[label] || 100
      return Math.min((val / maxVal) * 100, 100)
    })
  } else {
    useFallback = true
    healthyValues = [35, 24, 115, 75, 18, 5.0].map((v, i) => {
      const label = radarLabels[i]
      const maxVal = radarMax[label] || 100
      return Math.min((v / maxVal) * 100, 100)
    })
    patientValues = [38, 28, 125, 82, 16, 6.5].map((v, i) => {
      const label = radarLabels[i]
      const maxVal = radarMax[label] || 100
      return Math.min((v / maxVal) * 100, 100)
    })
  }

  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#334155' },
      extraCssText: 'box-shadow: 0 4px 16px rgba(0,0,0,0.1); border-radius: 12px;',
      formatter: (params) => {
        const idx = params.dataIndex
        const label = radarLabels[idx]
        const healthyVal = healthyValues[idx]
        const patientVal = patientValues[idx]
        if (params.seriesName === '健康群体') {
          return `<div style="padding: 4px 8px;">
            <div style="font-weight: bold; margin-bottom: 4px;">${label}</div>
            <div style="color: #22c55e;">健康群体：${healthyVal.toFixed(1)}</div>
          </div>`
        } else {
          return `<div style="padding: 4px 8px;">
            <div style="font-weight: bold; margin-bottom: 4px;">${label}</div>
            <div style="color: #ef4444;">患者群体：${patientVal.toFixed(1)}</div>
          </div>`
        }
      }
    },
    legend: {
      data: ['健康群体', '患者群体'],
      bottom: '2%',
      textStyle: { color: '#64748b', fontSize: 12 },
      itemGap: 20
    },
    radar: {
      shape: 'polygon',
      splitNumber: 4,
      center: ['50%', '48%'],
      radius: '65%',
      axisName: {
        color: '#1e293b',
        fontSize: 13,
        fontWeight: 'bold'
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(100, 116, 139, 0.25)',
          width: 1
        }
      },
      splitArea: {
        areaStyle: {
          color: [
            'rgba(148, 163, 184, 0.06)',
            'rgba(148, 163, 184, 0.12)',
            'rgba(148, 163, 184, 0.06)',
            'rgba(148, 163, 184, 0.12)'
          ]
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(100, 116, 139, 0.4)'
        }
      },
      indicator: radarLabels.map(label => ({
        name: label,
        max: radarMax[label] || 100
      }))
    },
    series: [{
      type: 'radar',
      data: [
        {
          value: healthyValues,
          name: '健康群体',
          lineStyle: { color: '#22c55e', width: 2.5 },
          itemStyle: { color: '#22c55e', borderWidth: 2, borderColor: '#fff' },
          areaStyle: { color: 'rgba(34, 197, 94, 0.2)' },
          emphasis: { areaStyle: { color: 'rgba(34, 197, 94, 0.35)' } }
        },
        {
          value: patientValues,
          name: '患者群体',
          lineStyle: { color: '#ef4444', width: 2.5 },
          itemStyle: { color: '#ef4444', borderWidth: 2, borderColor: '#fff' },
          areaStyle: { color: 'rgba(239, 68, 68, 0.2)' },
          emphasis: { areaStyle: { color: 'rgba(239, 68, 68, 0.35)' } }
        }
      ]
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
    <div ref="chartRef" style="width: 100%; height: 500px;"></div>
  </div>
</template>
