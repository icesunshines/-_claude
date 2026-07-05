<script setup>
import { ref, onMounted } from 'vue'
import { getStatsOverview } from '../api/request'

const overview = ref(null)
const loading = ref(true)

onMounted(async () => {
  try {
    const data = await getStatsOverview()
    overview.value = data
    console.log('数据加载成功:', data)
  } catch (e) {
    console.error('加载失败:', e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="p-8">
    <h1 class="text-3xl font-bold mb-8">可视化大屏测试</h1>
    
    <div v-if="loading" class="text-lg">正在加载...</div>
    
    <div v-else class="grid grid-cols-4 gap-6">
      <div class="p-6 bg-white rounded-xl shadow-lg border border-slate-200">
        <h3 class="text-slate-500 mb-2">总样本量</h3>
        <p class="text-3xl font-bold text-teal-600">{{ overview.sample_count_initial }}</p>
      </div>
      <div class="p-6 bg-white rounded-xl shadow-lg border border-slate-200">
        <h3 class="text-slate-500 mb-2">特征维度</h3>
        <p class="text-3xl font-bold text-cyan-600">{{ overview.feature_count_blood_sugar }}</p>
      </div>
      <div class="p-6 bg-white rounded-xl shadow-lg border border-slate-200">
        <h3 class="text-slate-500 mb-2">预测准确率</h3>
        <p class="text-3xl font-bold text-green-600">{{ (overview.diabetes_metrics.accuracy * 100).toFixed(0) }}%</p>
      </div>
      <div class="p-6 bg-white rounded-xl shadow-lg border border-slate-200">
        <h3 class="text-slate-500 mb-2">模型 AUC</h3>
        <p class="text-3xl font-bold text-yellow-600">{{ overview.diabetes_metrics.auc.toFixed(2) }}</p>
      </div>
    </div>
    
    <div class="mt-8 p-6 bg-slate-50 rounded-xl">
      <h3 class="font-bold mb-4">完整数据:</h3>
      <pre class="text-sm">{{ JSON.stringify(overview, null, 2) }}</pre>
    </div>
  </div>
</template>
