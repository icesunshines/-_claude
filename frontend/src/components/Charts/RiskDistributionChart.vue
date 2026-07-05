<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: Object,
  loading: Boolean
})

const chartRef = ref(null)
let chart = null

const rangeLabels = {
  '<4': '危险低血糖',
  '4-5.6': '正常',
  '5.6-7': '偏高',
  '7-11.1': '高血糖',
  '>11.1': '危险高血糖'
}

const rangeColors = {
  '<4': '#ef4444',
  '4-5.6': '#22c55e',
  '5.6-7': '#f59e0b',
  '7-11.1': '#f97316',
  '>11.1': '#dc2626'
}

function initChart() {
  if (!chartRef.value || !props.data?.distribution) return
  if (chart) {
    chart.dispose()
  }
  chart = echarts.init(chartRef.value)

  const distribution = props.data.distribution
  const pieData = Object.entries(distribution).map(([range, count]) => ({
    name: rangeLabels[range] || range,
    value: count,
    itemStyle: { color: rangeColors[range] || '#94a3b8' }
  }))

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
          <div style="color: #14b8a6;">人数：${params.value} 人</div>
          <div style="color: #64748b; font-size: 12px;">占比：${params.percent}%</div>
        </div>`
      }
    },
    legend: {
      orient: 'vertical',
      right: '0%',
      top: 'center',
      textStyle: { color: '#475569', fontSize: 11 },
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 10
    },
    series: [{
      type: 'pie',
      radius: ['42%', '68%'],
      center: ['36%', '50%'],
      avoidLabelOverlap: true,
      itemStyle: {
        borderRadius: 6,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: true,
        position: 'outside',
        color: '#475569',
        fontSize: 11,
        formatter: '{b}\n{d}%',
        lineHeight: 16
      },
      labelLine: {
        lineStyle: { color: '#cbd5e1' },
        length: 12,
        length2: 8
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 13,
          fontWeight: 'bold',
          color: '#1e293b'
        },
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.2)'
        }
      },
      data: pieData
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
      <div class="w-10 h-10 rounded-xl flex items-center justify-center" style="background: rgba(245,158,11,0.15)">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
          <line x1="12" y1="9" x2="12" y2="13"></line>
          <line x1="12" y1="17" x2="12.01" y2="17"></line>
        </svg>
      </div>
      <div>
        <h3 class="text-lg font-bold" style="color: var(--ds-text)">血糖风险分布</h3>
        <p class="text-xs" style="color: var(--ds-text-secondary)">血糖区间人数占比</p>
      </div>
    </div>
    <div ref="chartRef" style="width: 100%; height: 300px;"></div>
  </div>
</template>
