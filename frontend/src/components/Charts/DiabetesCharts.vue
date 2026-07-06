<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { getDiabetesStats } from '../../api/request'

const chartRef = ref(null)
let chart = null
let handleResize = null

function initChart(stats) {
  chart = echarts.init(chartRef.value)
  
  const features = Object.keys(stats.clinical_comparison)
  const healthy = features.map(f => stats.clinical_comparison[f].healthy_mean)
  const patient = features.map(f => stats.clinical_comparison[f].patient_mean)

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#334155' },
      extraCssText: 'box-shadow: 0 4px 16px rgba(0,0,0,0.1); border-radius: 12px;',
      axisPointer: {
        type: 'shadow',
        shadowStyle: {
          color: 'rgba(20, 184, 166, 0.08)'
        }
      }
    },
    legend: {
      top: '3%',
      left: 'center',
      textStyle: { color: '#64748b', fontSize: 13 },
      itemGap: 25,
      itemWidth: 14,
      itemHeight: 14
    },
    grid: {
      left: '5%',
      right: '5%',
      bottom: '5%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: features,
      axisLine: { lineStyle: { color: '#e2e8f0', width: 2 } },
      axisLabel: { 
        color: '#64748b', 
        fontSize: 12,
        rotate: 15,
        margin: 12
      },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { color: '#64748b', fontSize: 12 },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } }
    },
    series: [
      {
        name: '健康',
        type: 'bar',
        data: healthy,
        itemStyle: {
          color: '#22c55e',
          borderRadius: [6, 6, 0, 0]
        },
        barWidth: '40%',
        emphasis: {
          itemStyle: {
            color: '#16a34a'
          }
        }
      },
      {
        name: '患病',
        type: 'bar',
        data: patient,
        itemStyle: {
          color: '#ef4444',
          borderRadius: [6, 6, 0, 0]
        },
        barWidth: '40%',
        emphasis: {
          itemStyle: {
            color: '#dc2626'
          }
        }
      }
    ]
  })
}

onMounted(async () => {
  try {
    const stats = await getDiabetesStats()
    initChart(stats)
    
    handleResize = () => chart?.resize()
    window.addEventListener('resize', handleResize)
  } catch (error) {
    console.error('加载图表失败:', error)
  }
})

onBeforeUnmount(() => {
  if (handleResize) {
    window.removeEventListener('resize', handleResize)
  }
  chart?.dispose()
})
</script>

<template>
  <div ref="chartRef" style="width: 100%; height: 100%;"></div>
</template>
