<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import { useAuthStore } from '../stores/auth'
import { getHistory } from '../api/request'
import { User, Document, DataLine, Calendar, FirstAidKit, TrendCharts, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const authStore = useAuthStore()
const history = ref([])
const loading = ref(true)
const chartRef = ref(null)
let chart = null
const filterType = ref('all')

const filteredHistory = computed(() => {
  if (filterType.value === 'all') return history.value
  return history.value.filter(h => h.type === filterType.value)
})

const trendData = computed(() => {
  const items = filteredHistory.value
    .filter(h => h.type === 'blood_sugar' && h.result?.predicted_bgl)
    .slice()
    .reverse()
  return {
    dates: items.map(h => h.created_at),
    values: items.map(h => h.result.predicted_bgl)
  }
})

function initTrendChart() {
  if (!chartRef.value || trendData.value.dates.length === 0) return
  if (chart) chart.dispose()
  chart = echarts.init(chartRef.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#334155' },
      extraCssText: 'box-shadow: 0 4px 16px rgba(0,0,0,0.1); border-radius: 12px;'
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
      data: trendData.value.dates,
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#64748b', fontSize: 11, rotate: 30 },
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
      data: trendData.value.values,
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
      }
    }]
  }

  chart.setOption(option)
}

watch(() => filteredHistory.value, initTrendChart)

onMounted(async () => {
  try {
    history.value = await getHistory()
  } catch (e) {
    console.error('加载历史失败:', e)
    ElMessage.error('加载历史记录失败')
  } finally {
    loading.value = false
  }
})

function formatDate(dateStr) {
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateStr
  }
}

function deleteHistory(index) {
  ElMessageBox.confirm('确定要删除这条记录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    history.value.splice(index, 1)
    ElMessage.success('删除成功')
  }).catch(() => {
    // 用户取消
  })
}
</script>

<template>
  <div class="profile-page max-w-4xl mx-auto">
    <div class="card mb-6 p-6">
      <div class="flex items-center gap-4 mb-6">
        <div class="w-12 h-12 bg-gradient-to-br from-primary-500 to-medical-500 rounded-2xl flex items-center justify-center">
          <el-icon :size="24" color="white">
            <User />
          </el-icon>
        </div>
        <div>
          <h1 class="text-3xl font-bold text-slate-800">个人中心</h1>
          <p class="text-slate-500 text-lg mt-1">管理您的账户和预测记录</p>
        </div>
      </div>
    </div>

    <div class="card mb-6 p-6 bg-gradient-to-br from-primary-50 to-medical-50 border-none">
      <div class="flex flex-col md:flex-row items-start md:items-center gap-6">
        <div class="w-24 h-24 bg-gradient-to-br from-primary-500 to-medical-500 rounded-3xl flex items-center justify-center flex-shrink-0 shadow-glow">
          <span class="text-white text-5xl font-bold">
            {{ authStore.user?.username?.[0]?.toUpperCase() }}
          </span>
        </div>
        <div class="flex-1">
          <h2 class="text-3xl font-bold text-slate-800 mb-1">{{ authStore.user?.username }}</h2>
          <p class="text-slate-500 text-lg">
            {{ authStore.user?.role === 'admin' ? '系统管理员' : '普通用户' }}
          </p>
        </div>
        <span
          class="badge text-base px-6 py-3"
          :class="[
            authStore.user?.role === 'admin'
              ? 'bg-primary-100 text-primary-700'
              : 'bg-success-100 text-success-700'
          ]"
        >
          {{ authStore.user?.role === 'admin' ? '管理员' : '用户' }}
        </span>
      </div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
      <div class="stat-card card-hover p-6">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 bg-primary-100 rounded-2xl flex items-center justify-center border-2 border-primary-200">
            <el-icon :size="28" class="text-primary-600">
              <Document />
            </el-icon>
          </div>
          <div>
            <p class="text-3xl font-bold text-slate-800 mb-1">{{ history.length }}</p>
            <p class="text-slate-500 font-medium text-lg">总预测次数</p>
          </div>
        </div>
      </div>
      <div class="stat-card card-hover p-6">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 bg-success-100 rounded-2xl flex items-center justify-center border-2 border-success-200">
            <el-icon :size="28" class="text-success-600">
              <DataLine />
            </el-icon>
          </div>
          <div>
            <p class="text-3xl font-bold text-slate-800 mb-1">{{ history.filter(h => h.type === 'blood_sugar').length }}</p>
            <p class="text-slate-500 font-medium text-lg">血糖预测</p>
          </div>
        </div>
      </div>
      <div class="stat-card card-hover p-6">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 bg-medical-100 rounded-2xl flex items-center justify-center border-2 border-medical-200">
            <el-icon :size="28" class="text-medical-600">
              <TrendCharts />
            </el-icon>
          </div>
          <div>
            <p class="text-3xl font-bold text-slate-800 mb-1">{{ history.filter(h => h.type === 'diabetes').length }}</p>
            <p class="text-slate-500 font-medium text-lg">糖尿病预测</p>
          </div>
        </div>
      </div>
    </div>

    <div class="card mb-6 p-6">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-primary-100 rounded-xl flex items-center justify-center">
            <TrendCharts class="text-primary-600" />
          </div>
          <div>
            <h3 class="text-xl font-bold text-slate-800">血糖趋势</h3>
            <p class="text-slate-500 text-sm">历史预测血糖变化</p>
          </div>
        </div>
        <div class="inline-flex bg-slate-100 p-1 rounded-xl">
          <button
            @click="filterType = 'all'"
            :class="[
              'px-3 py-1.5 rounded-lg text-xs font-semibold transition-all',
              filterType === 'all' ? 'bg-white text-primary-600 shadow-sm' : 'text-slate-600'
            ]"
          >全部</button>
          <button
            @click="filterType = 'blood_sugar'"
            :class="[
              'px-3 py-1.5 rounded-lg text-xs font-semibold transition-all',
              filterType === 'blood_sugar' ? 'bg-white text-primary-600 shadow-sm' : 'text-slate-600'
            ]"
          >血糖</button>
          <button
            @click="filterType = 'diabetes'"
            :class="[
              'px-3 py-1.5 rounded-lg text-xs font-semibold transition-all',
              filterType === 'diabetes' ? 'bg-white text-primary-600 shadow-sm' : 'text-slate-600'
            ]"
          >糖尿病</button>
        </div>
      </div>
      <div ref="chartRef" style="width: 100%; height: 300px;"></div>
    </div>

    <div class="card p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-gradient-to-br from-primary-500 to-medical-500 rounded-2xl flex items-center justify-center shadow-soft">
            <el-icon :size="24" class="text-white">
              <Calendar />
            </el-icon>
          </div>
          <div>
            <h3 class="text-xl font-bold text-slate-800">预测历史</h3>
            <p class="text-slate-500 text-sm mt-1">查看您的所有预测记录</p>
          </div>
        </div>
        <div class="text-base text-slate-500 font-medium">
          共 {{ history.length }} 条记录
        </div>
      </div>

      <div v-if="loading" class="py-16 text-center text-slate-400">
        <el-icon class="animate-spin" :size="40">
          <TrendCharts />
        </el-icon>
        <p class="mt-4 text-lg">加载中...</p>
      </div>

      <div v-else-if="history.length === 0" class="py-16 text-center">
        <div class="w-24 h-24 bg-slate-100 rounded-3xl flex items-center justify-center mx-auto mb-4">
          <el-icon :size="48" class="text-slate-400">
            <Document />
          </el-icon>
        </div>
        <h4 class="text-slate-800 font-bold text-xl mb-2">暂无预测记录</h4>
        <p class="text-slate-500 text-base">开始进行预测，记录将显示在这里</p>
      </div>

      <div v-else class="space-y-4">
        <div
          v-for="(item, index) in history.slice().reverse()"
          :key="item.created_at + item.type"
          class="p-5 bg-slate-50 rounded-2xl hover:bg-slate-100 transition-all duration-300"
        >
          <div class="flex items-start justify-between gap-6">
            <div class="flex items-start gap-4 flex-1">
              <div
                class="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                :class="[
                  item.type === 'blood_sugar'
                    ? 'bg-primary-100 border-2 border-primary-200'
                    : 'bg-medical-100 border-2 border-medical-200'
                ]"
              >
                <el-icon
                  :size="24"
                  :class="[
                    item.type === 'blood_sugar'
                      ? 'text-primary-600'
                      : 'text-medical-600'
                  ]"
                >
                  <DataLine v-if="item.type === 'blood_sugar'" />
                  <TrendCharts v-else />
                </el-icon>
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-3 mb-3 flex-wrap">
                  <span
                    class="badge text-sm px-4 py-2"
                    :class="[
                      item.type === 'blood_sugar'
                        ? 'bg-primary-100 text-primary-700'
                        : 'bg-medical-100 text-medical-700'
                    ]"
                  >
                    {{ item.type === 'blood_sugar' ? '血糖预测' : '糖尿病预测' }}
                  </span>
                  <span class="text-sm text-slate-500 flex items-center gap-2">
                    <el-icon :size="16">
                      <Calendar />
                    </el-icon>
                    {{ formatDate(item.created_at) }}
                  </span>
                </div>
                <div class="text-slate-600 text-lg">
                  <span v-if="item.result.predicted_bgl !== undefined">
                    预测血糖: <span class="font-bold text-slate-800 text-xl">{{ item.result.predicted_bgl }} mmol/L</span>
                    <span class="ml-3">
                      ({{ item.result.risk_level }})
                    </span>
                  </span>
                  <span v-else>
                    患病概率: <span class="font-bold text-slate-800 text-xl">{{ (item.result.probability * 100).toFixed(1) }}%</span>
                    <span class="ml-3">
                      ({{ item.result.risk === 1 ? '高风险' : '低风险' }})
                    </span>
                  </span>
                </div>
              </div>
            </div>
            <button
              @click="deleteHistory(history.length - 1 - index)"
              class="text-slate-400 hover:text-danger-500 transition-colors p-2"
            >
              <el-icon :size="20">
                <Delete />
              </el-icon>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-page {
  max-width: 1600px;
  margin: 0 auto;
}
</style>
