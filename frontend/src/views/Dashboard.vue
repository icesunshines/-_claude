<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { getStatsOverview, getBloodSugarStats } from '../api/request'
import { DataBoard, Timer, Refresh, DataAnalysis, Monitor } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import AgeTrendChart from '../components/Charts/AgeTrendChart.vue'
import HexRadarChart from '../components/Charts/HexRadarChart.vue'
import RiskDistributionChart from '../components/Charts/RiskDistributionChart.vue'
import DiabetesCharts from '../components/Charts/DiabetesCharts.vue'

const overview = ref(null)
const loading = ref(true)
const bloodSugarData = ref(null)

const realTimeStats = ref({
  time: new Date().toLocaleTimeString()
})

const stats = ref([
  { label: '总样本量', value: 0, icon: '📊', color: 'primary', animateValue: 0, trend: 'up', trendValue: 12 },
  { label: '特征维度', value: 0, icon: '📈', color: 'medical', animateValue: 0, trend: 'stable', trendValue: 0 },
  { label: '预测准确率', value: '0%', icon: '✅', color: 'success', animateValue: 0, trend: 'up', trendValue: 5 },
  { label: '模型 AUC', value: '0.0', icon: '🏆', color: 'warning', animateValue: 0, trend: 'up', trendValue: 3 }
])

const recentRecords = ref([
  { id: 1, type: '血糖预测', user: '张三', time: '2分钟前', result: '5.2 mmol/L' },
  { id: 2, type: '糖尿病预测', user: '李四', time: '15分钟前', result: '低风险' },
  { id: 3, type: '血糖预测', user: '王五', time: '30分钟前', result: '4.9 mmol/L' },
  { id: 4, type: '糖尿病预测', user: '赵六', time: '1小时前', result: '中风险' },
  { id: 5, type: '血糖预测', user: '钱七', time: '2小时前', result: '5.8 mmol/L' }
])

let realTimeInterval = null

function animateNumber(target, duration = 1500) {
  const start = 0
  const end = parseInt(target) || 0
  const startTime = Date.now()

  function update() {
    const elapsed = Date.now() - startTime
    const progress = Math.min(elapsed / duration, 1)
    const current = Math.floor(start + (end - start) * (1 - Math.pow(1 - progress, 3)))

    if (typeof target === 'string' && target.includes('%')) {
      stats.value.find(s => s.label.includes('准确率') || s.label.includes('AUC')).animateValue = current
    } else {
      const stat = stats.value.find(s => s.label.includes('总样本') || s.label.includes('特征') || s.label.includes('准确率'))
      if (stat) stat.animateValue = current
    }

    if (progress < 1) {
      requestAnimationFrame(update)
    }
  }

  update()
}

function updateRealTimeStats() {
  realTimeStats.value.time = new Date().toLocaleTimeString()
}

async function loadData() {
  try {
    const [overviewData, bsData] = await Promise.all([
      getStatsOverview(),
      getBloodSugarStats()
    ])

    overview.value = overviewData
    bloodSugarData.value = bsData

    stats.value[0].value = overviewData.sample_count_initial || 0
    stats.value[1].value = overviewData.feature_count_blood_sugar || 0
    stats.value[2].value = `${Math.round((overviewData.diabetes_metrics?.accuracy || 0) * 100)}%`
    stats.value[3].value = (overviewData.diabetes_metrics?.auc || 0).toFixed(2)

    animateNumber(overviewData.sample_count_initial || 0)
  } catch (e) {
    console.error('加载数据失败:', e)
  } finally {
    loading.value = false
  }
}

function manualRefresh() {
  ElMessage.info('正在刷新数据...')
  loadData()
}

onMounted(async () => {
  await loadData()
  realTimeInterval = setInterval(updateRealTimeStats, 3000)
})

onBeforeUnmount(() => {
  if (realTimeInterval) {
    clearInterval(realTimeInterval)
  }
  window.removeEventListener('resize', handleResize)
})

function handleResize() {
  window.dispatchEvent(new Event('resize'))
}

// ========== 数据解读 computed ==========

const leftSummary = computed(() => {
  if (!bloodSugarData.value?.age_stats) return ''
  const ages = Object.entries(bloodSugarData.value.age_stats)
  if (ages.length === 0) return ''
  const maxAge = ages.reduce((a, b) => a[1] > b[1] ? a : b)
  const minAge = ages.reduce((a, b) => a[1] < b[1] ? a : b)
  const diff = Math.abs(maxAge[1] - minAge[1]).toFixed(1)
  return `血糖随年龄增长呈上升趋势。${maxAge[0]} 岁组最高 (${maxAge[1]} mmol/L)，${minAge[0]} 岁组最低 (${minAge[1]} mmol/L)，差距 ${diff} mmol/L。`
})

const centerSummary = computed(() => {
  if (!overview.value) return ''
  const acc = overview.value.diabetes_metrics?.accuracy || 0
  const auc = overview.value.diabetes_metrics?.auc || 0
  const bgl = overview.value.mean_blood_sugar || 0
  return `综合健康评分基于多项指标计算。当前平均血糖 ${bgl.toFixed(2)} mmol/L，模型准确率 ${Math.round(acc * 100)}%，AUC ${auc.toFixed(2)}。建议结合临床指标综合评估。`
})

const rightSummary = computed(() => {
  if (!bloodSugarData.value?.distribution) return ''
  const dist = bloodSugarData.value.distribution
  const total = Object.values(dist).reduce((a, b) => a + b, 0)
  const normal = (dist['4-5.6'] || 0) + (dist['<4'] || 0)
  const elevated = dist['5.6-7'] || 0
  const normalPct = Math.round(normal / total * 100)
  const elevatedPct = Math.round(elevated / total * 100)
  return `本次共分析 ${total} 份体检数据。正常血糖占比 ${normalPct}%（${normal} 人），偏高占比 ${elevatedPct}%（${elevated} 人），建议关注偏高人群进一步筛查。`
})
</script>

<template>
  <div class="dashboard-page">
    <!-- A. 顶部区域 -->
    <div class="card mb-6 p-6">
      <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 bg-gradient-to-br from-primary-500 to-medical-500 rounded-2xl flex items-center justify-center shadow-glow">
            <el-icon :size="28" color="white">
              <DataBoard />
            </el-icon>
          </div>
          <div>
            <h1 class="text-2xl font-bold bg-gradient-to-r from-primary-600 to-medical-600 bg-clip-text text-transparent">
              健康数据智能分析平台
            </h1>
            <p class="text-slate-500 text-sm mt-1 flex items-center gap-2">
              <span class="inline-block w-2 h-2 bg-success-500 rounded-full animate-pulse"></span>
              血糖趋势 / 健康指标 / 风险分布
            </p>
          </div>
        </div>

        <div class="flex items-center gap-6">
          <div class="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full border border-emerald-200 bg-emerald-50 text-emerald-700 text-xs font-medium">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            系统运行正常
          </div>

          <div class="text-center">
            <p class="text-slate-500 text-xs mb-1 flex items-center gap-1 justify-center">
              <el-icon :size="14"><Timer /></el-icon>
              系统时间
            </p>
            <p class="text-xl font-bold text-slate-800 font-mono">{{ realTimeStats.time }}</p>
          </div>
          <button
            @click="manualRefresh"
            class="btn-secondary flex items-center gap-2 text-sm py-2 px-4"
          >
            <el-icon :size="16"><Refresh /></el-icon>
            刷新
          </button>
        </div>
      </div>
    </div>

    <!-- B. 统计卡片 -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div
        v-for="(stat, idx) in stats"
        :key="stat.label"
        class="stat-card card-hover animate-slide-up"
        :style="{ animationDelay: `${idx * 0.1}s` }"
      >
        <div class="flex items-center justify-between mb-3">
          <div
            class="w-12 h-12 rounded-xl flex items-center justify-center text-xl"
            :class="[
              stat.color === 'primary' ? 'bg-primary-100' :
              stat.color === 'medical' ? 'bg-medical-100' :
              stat.color === 'success' ? 'bg-success-100' :
              'bg-warning-100'
            ]"
          >
            {{ stat.icon }}
          </div>
        </div>
        <div>
          <p class="text-2xl font-bold text-slate-800 mb-1">{{ stat.value }}</p>
          <p class="text-slate-500 font-medium text-sm">{{ stat.label }}</p>
        </div>
      </div>
    </div>

    <!-- C. 三列主图表区域 (3:4:3) -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-6">
      <!-- C1. 左侧 — 年龄段血糖趋势 + 文字解读 -->
      <div class="lg:col-span-3 card p-6 flex flex-col">
        <div class="flex-1">
          <AgeTrendChart :data="bloodSugarData" :loading="loading" />
        </div>
        <div v-if="leftSummary" class="mt-5 pt-4 border-t border-slate-100">
          <p class="text-xs text-slate-500 leading-relaxed">{{ leftSummary }}</p>
        </div>
      </div>

      <!-- C2. 中间 — 六边形雷达图 + 文字解读 -->
      <div class="lg:col-span-6 card p-6 flex flex-col">
        <div class="flex-1">
          <HexRadarChart :overview="overview" :loading="loading" />
        </div>
        <div v-if="centerSummary" class="mt-5 pt-4 border-t border-slate-100">
          <p class="text-xs text-slate-500 leading-relaxed">{{ centerSummary }}</p>
        </div>
      </div>

      <!-- C3. 右侧 — 血糖风险分布 + 文字解读 -->
      <div class="lg:col-span-3 card p-6 flex flex-col">
        <div class="flex-1">
          <RiskDistributionChart :data="bloodSugarData" :loading="loading" />
        </div>
        <div v-if="rightSummary" class="mt-5 pt-4 border-t border-slate-100">
          <p class="text-xs text-slate-500 leading-relaxed">{{ rightSummary }}</p>
        </div>
      </div>
    </div>

    <!-- D. 底部区域：临床指标对比 + 最近预测记录 -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-6">
      <div class="lg:col-span-8 card p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 bg-medical-100 rounded-xl flex items-center justify-center">
            <DataAnalysis class="text-medical-600" />
          </div>
          <div>
            <h3 class="text-xl font-bold text-slate-800">临床指标对比</h3>
            <p class="text-slate-500 text-sm">健康人群 vs 患者群体</p>
          </div>
        </div>
        <div class="h-80">
          <DiabetesCharts />
        </div>
      </div>

      <div class="lg:col-span-4 card p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 bg-primary-100 rounded-xl flex items-center justify-center">
            <Monitor class="text-primary-600" />
          </div>
          <div>
            <h3 class="text-xl font-bold text-slate-800">最近预测</h3>
            <p class="text-slate-500 text-sm">实时预测数据</p>
          </div>
        </div>

        <div class="space-y-3 max-h-80 overflow-y-auto">
          <div
            v-for="(record, idx) in recentRecords"
            :key="record.id"
            class="p-4 bg-slate-50 rounded-xl border border-slate-100 hover:border-primary-200 transition-all duration-300"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-semibold text-slate-700">{{ record.type }}</span>
              <span class="text-xs text-slate-500">{{ record.time }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-slate-600">{{ record.user }}</span>
              <span class="text-sm font-bold" :class="
                record.result.includes('低') ? 'text-success-600' :
                record.result.includes('中') ? 'text-warning-600' :
                record.result.includes('高') ? 'text-danger-600' :
                'text-primary-600'
              ">{{ record.result }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-page {
  max-width: 1600px;
  margin: 0 auto;
}
</style>
