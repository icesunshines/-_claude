<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { getBloodSugarStats } from '../../api/request'

const chartRef = ref(null)
let chart = null

function initChart(stats) {
  chart = echarts.init(chartRef.value)
  
  const distribution = Object.entries(stats.distribution).map(([name, value]) => ({ name, value }))

  const option = {
    tooltip: {
      trigger: 'item'
    },
    legend: {
      top: '5%',
      left: 'center'
    },
    series: [
      {
        name: '血糖分布',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '60%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}\n{c}人'
        },
        data: distribution
      }
    ]
  }
  
  chart.setOption(option)
}

onMounted(async () => {
  try {
    const stats = await getBloodSugarStats()
    initChart(stats)
    
    const handleResize = () => chart?.resize()
    window.addEventListener('resize', handleResize)
    
    onBeforeUnmount(() => {
      window.removeEventListener('resize', handleResize)
      chart?.dispose()
    })
  } catch (error) {
    console.error('加载图表失败:', error)
  }
})
</script>

<template>
  <div ref="chartRef" style="width: 100%; height: 100%;"></div>
</template>
