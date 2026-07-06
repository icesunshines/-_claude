<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { getStatsOverview, getBloodSugarStats, getHistory, connectRealtimeStats, disconnectRealtimeStats, getEnsembleComparison } from '../api/request'
import { DataBoard, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import AgeTrendChart from '../components/Charts/AgeTrendChart.vue'
import HexRadarChart from '../components/Charts/HexRadarChart.vue'
import RiskDistributionChart from '../components/Charts/RiskDistributionChart.vue'
import DiabetesCharts from '../components/Charts/DiabetesCharts.vue'

const overview = ref(null)
const loading = ref(true)
const bloodSugarData = ref(null)
const recentRecords = ref([])

// 实时统计数据
const realtimeStats = ref({
  total_predictions: 0,
  total_users: 0,
  connected: false
})

// 4个统计卡片
const stats = ref([
  { label: '总样本量', value: '--', icon: '📊', color: 'primary' },
  { label: '特征维度', value: '--', icon: '📈', color: 'medical' },
  { label: '总预测数', value: '--', icon: '🎯', color: 'success', isRealtime: true },
  { label: '模型 AUC', value: '--', icon: '🏆', color: 'warning' }
])

// 自动刷新
const refreshCountdown = ref(30)
let countdownTimer = null
let autoRefreshTimer = null

function startAutoRefresh() {
  refreshCountdown.value = 30
  countdownTimer = setInterval(() => {
    refreshCountdown.value--
    if (refreshCountdown.value <= 0) {
      refreshCountdown.value = 30
    }
  }, 1000)

  autoRefreshTimer = setInterval(() => {
    loadData()
    refreshCountdown.value = 30
  }, 30000)
}

function stopAutoRefresh() {
  if (countdownTimer) clearInterval(countdownTimer)
  if (autoRefreshTimer) clearInterval(autoRefreshTimer)
  countdownTimer = null
  autoRefreshTimer = null
}

async function loadData() {
  try {
    const [overviewData, bsData, historyData] = await Promise.all([
      getStatsOverview(),
      getBloodSugarStats(),
      getHistory()
    ])

    overview.value = overviewData
    bloodSugarData.value = bsData

    // 更新统计卡片
    stats.value[0].value = (overviewData.sample_count_initial || 0).toLocaleString()
    stats.value[1].value = (overviewData.feature_count_blood_sugar || 0).toLocaleString()
    stats.value[2].value = (realtimeStats.value.total_predictions || 0).toLocaleString()
    stats.value[3].value = (overviewData.diabetes_metrics?.auc || 0).toFixed(2)

    // 加载最近预测记录
    recentRecords.value = (historyData || []).slice(0, 5).map(item => ({
      id: item.id || item.created_at,
      type: item.type === 'blood_sugar' ? '血糖预测' : '糖尿病预测',
      time: formatTime(item.created_at),
      result: formatResult(item.type, item.result),
      riskLevel: item.type === 'blood_sugar'
        ? (item.result?.risk_level || '低风险')
        : (item.result?.risk === 1 ? '高风险' : (item.result?.probability > 0.7 ? '高风险' : (item.result?.probability > 0.3 ? '中风险' : '低风险')))
    }))
  } catch (e) {
    console.error('加载数据失败:', e)
    ElMessage.error('数据加载失败')
  } finally {
    loading.value = false
  }
}

function manualRefresh() {
  ElMessage.success('数据已刷新')
  loadData()
  refreshCountdown.value = 30
}

// 实时数据回调
function handleRealtimeMessage(data) {
  realtimeStats.value.total_predictions = data.total_predictions || 0
  realtimeStats.value.total_users = data.total_users || 0
  realtimeStats.value.connected = true

  // 更新统计卡片中的实时数据
  stats.value[2].value = (data.total_predictions || 0).toLocaleString()
}

function handleRealtimeError() {
  realtimeStats.value.connected = false
}

async function loadEnsembleComparison() {
  ensembleLoading.value = true
  try {
    ensembleComparison.value = await getEnsembleComparison()
  } catch (e) {
    console.error('加载模型对比数据失败:', e)
    ensembleComparison.value = null
  } finally {
    ensembleLoading.value = false
  }
}

// 健康预警区
const alerts = computed(() => {
  if (!bloodSugarData.value?.distribution || !overview.value) {
    return []
  }

  const alerts = []
  const dist = bloodSugarData.value.distribution
  const total = Object.values(dist).reduce((a, b) => a + b, 0)

  // 红色预警：高血糖比例 > 20%
  if (total > 0) {
    const elevated = (dist['5.6-7'] || 0) + (dist['7-11.1'] || 0) + (dist['>11.1'] || 0)
    const elevatedPct = elevated / total
    if (elevatedPct > 0.2) {
      alerts.push({
        level: 'high',
        color: 'red',
        title: '高血糖风险预警',
        message: `检测到 ${(elevatedPct * 100).toFixed(1)}% 的样本血糖偏高，建议加强血糖监测和管理。`,
        icon: '⚠️'
      })
    }
  }

  // 黄色预警：模型 AUC 偏低
  const auc = overview.value.diabetes_metrics?.auc || 0
  if (auc < 0.7 && auc > 0) {
    alerts.push({
      level: 'medium',
      color: 'yellow',
      title: '模型性能提醒',
      message: `当前糖尿病预测模型 AUC 为 ${auc.toFixed(2)}，建议关注模型性能。`,
      icon: '📊'
    })
  }

  // 蓝色提示：高风险年龄段
  if (bloodSugarData.value?.age_stats) {
    const ages = Object.entries(bloodSugarData.value.age_stats)
    const highRiskAges = ages.filter(([_, value]) => value > 7)
    if (highRiskAges.length > 0) {
      const ageRanges = highRiskAges.map(([range]) => range).join('、')
      alerts.push({
        level: 'low',
        color: 'blue',
        title: '高风险年龄段提示',
        message: `${ageRanges} 岁年龄段平均血糖较高，建议重点关注该人群健康管理。`,
        icon: '💡'
      })
    }
  }

  return alerts
})

const ensembleComparison = ref(null)
const ensembleLoading = ref(false)

const alertLevelColor = {
  high: { border: 'border-red-500', bg: 'bg-red-50', text: 'text-red-700', badge: 'bg-red-500' },
  medium: { border: 'border-yellow-500', bg: 'bg-yellow-50', text: 'text-yellow-700', badge: 'bg-yellow-500' },
  low: { border: 'border-blue-500', bg: 'bg-blue-50', text: 'text-blue-700', badge: 'bg-blue-500' }
}

function formatTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = (now - date) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function formatResult(type, result) {
  if (!result) return '--'
  if (type === 'blood_sugar') {
    return result.predicted_bgl !== undefined ? `${result.predicted_bgl} mmol/L` : '--'
  }
  if (type === 'diabetes') {
    if (result.risk === 1) return '高风险'
    if (result.risk === 0) return '低风险'
    if (result.probability !== undefined) return `${(result.probability * 100).toFixed(1)}%`
    return '--'
  }
  return '--'
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

onMounted(async () => {
  await loadData()
  startAutoRefresh()
  connectRealtimeStats(handleRealtimeMessage, handleRealtimeError)
  loadEnsembleComparison()
})

onBeforeUnmount(() => {
  stopAutoRefresh()
  disconnectRealtimeStats()
})
</script>

<template>
  <div class="dashboard-page h-full overflow-y-auto">
    <!-- 统计卡片 -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
      <div
        v-for="(stat, idx) in stats"
        :key="stat.label"
        class="stat-card p-4"
      >
        <div class="flex items-center justify-between mb-2">
          <div
            class="w-10 h-10 rounded-lg flex items-center justify-center text-lg"
            :class="{
              'bg-primary-100': stat.color === 'primary',
              'bg-medical-100': stat.color === 'medical',
              'bg-success-100': stat.color === 'success',
              'bg-warning-100': stat.color === 'warning'
            }"
          >
            {{ stat.icon }}
          </div>
          <div v-if="stat.isRealtime" class="flex items-center gap-1">
            <span class="w-1.5 h-1.5 rounded-full animate-pulse" :class="realtimeStats.connected ? 'bg-success-500' : 'bg-slate-300'"></span>
            <span class="text-xs text-slate-500">实时</span>
          </div>
        </div>
        <div>
          <p class="text-xl font-bold text-slate-800">{{ stat.value }}</p>
          <p class="text-xs text-slate-500">{{ stat.label }}</p>
        </div>
      </div>
    </div>

    <!-- 中轴对称图表布局 -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-4 mb-4">
      <!-- 左侧：年龄趋势 -->
      <div class="lg:col-span-3 card p-4">
        <AgeTrendChart :data="bloodSugarData" :loading="loading" />
        <div v-if="leftSummary" class="mt-3 pt-3 border-t border-slate-100">
          <p class="text-xs text-slate-500 leading-relaxed">{{ leftSummary }}</p>
        </div>
      </div>

      <!-- 中间：六维雷达图（视觉重心） -->
      <div class="lg:col-span-6 card p-4">
        <HexRadarChart :overview="overview" :loading="loading" />
        <div v-if="centerSummary" class="mt-3 pt-3 border-t border-slate-100">
          <p class="text-xs text-slate-500 leading-relaxed">{{ centerSummary }}</p>
        </div>
      </div>

      <!-- 右侧：血糖风险分布 -->
      <div class="lg:col-span-3 card p-4">
        <RiskDistributionChart :data="bloodSugarData" :loading="loading" />
        <div v-if="rightSummary" class="mt-3 pt-3 border-t border-slate-100">
          <p class="text-xs text-slate-500 leading-relaxed">{{ rightSummary }}</p>
        </div>
      </div>
    </div>

    <!-- 底部：临床指标对比 + 最近预测 -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-4 mb-4">
      <div class="lg:col-span-8 card p-4">
        <div class="flex items-center gap-3 mb-3">
          <div class="w-8 h-8 bg-medical-100 rounded-lg flex items-center justify-center">
            <DataBoard class="text-medical-600" />
          </div>
          <div>
            <h3 class="text-lg font-bold text-slate-800">临床指标对比</h3>
            <p class="text-xs text-slate-500">健康人群 vs 患者群体</p>
          </div>
        </div>
        <div class="h-[420px]">
          <DiabetesCharts />
        </div>
      </div>

      <div class="lg:col-span-4 card p-4">
        <div class="flex items-center gap-3 mb-3">
          <div class="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center">
            <span class="text-primary-600 text-sm">📋</span>
          </div>
          <div>
            <h3 class="text-lg font-bold text-slate-800">最近预测</h3>
            <p class="text-xs text-slate-500">实时预测记录</p>
          </div>
        </div>

        <div class="space-y-2 max-h-72 overflow-y-auto">
          <div
            v-for="record in recentRecords"
            :key="record.id"
            class="p-3 bg-slate-50 rounded-lg border border-slate-100 hover:border-primary-200 transition-all duration-300"
          >
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs font-semibold text-slate-700">{{ record.type }}</span>
              <span class="text-xs text-slate-500">{{ record.time }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-slate-600">预测结果</span>
              <span class="text-xs font-bold" :class="{
                'text-success-600': record.riskLevel === '低风险',
                'text-warning-600': record.riskLevel === '中风险',
                'text-danger-600': record.riskLevel === '高风险'
              }">{{ record.result }}</span>
            </div>
          </div>
          <div v-if="!recentRecords.length && !loading" class="text-center text-slate-400 py-6 text-xs">
            暂无预测记录
          </div>
        </div>
      </div>
    </div>

    <!-- 模型性能对比 -->
    <div v-if="ensembleComparison" class="grid grid-cols-1 lg:grid-cols-12 gap-4 mb-4">
      <div class="lg:col-span-12 card p-5">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-8 h-8 bg-medical-100 rounded-lg flex items-center justify-center">
            <span class="text-medical-600 text-sm">🏆</span>
          </div>
          <div>
            <h3 class="text-lg font-bold text-slate-800">模型性能对比</h3>
            <p class="text-xs text-slate-500">单一 LightGBM 模型 vs Stacking 融合模型 (LightGBM + XGBoost)</p>
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- 血糖预测对比 -->
          <div>
            <h4 class="text-sm font-bold text-slate-700 mb-3 pb-2 border-b border-slate-100">血糖预测 (回归)</h4>
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-slate-200">
                    <th class="text-left py-2 px-2 text-slate-500 font-medium">指标</th>
                    <th class="text-center py-2 px-2 text-slate-600 font-medium">单模型</th>
                    <th class="text-center py-2 px-2 text-medical-700 font-medium">融合模型</th>
                  </tr>
                </thead>
                <tbody>
                  <tr class="border-b border-slate-100">
                    <td class="py-2 px-2 text-slate-600">RMSE</td>
                    <td class="py-2 px-2 text-center font-mono">{{ ensembleComparison?.blood_sugar?.single?.rmse ?? '--' }}</td>
                    <td class="py-2 px-2 text-center font-mono text-medical-700 font-bold">{{ ensembleComparison?.blood_sugar?.ensemble?.rmse ?? '--' }}</td>
                  </tr>
                  <tr class="border-b border-slate-100">
                    <td class="py-2 px-2 text-slate-600">R²</td>
                    <td class="py-2 px-2 text-center font-mono">{{ ensembleComparison?.blood_sugar?.single?.r2 ?? '--' }}</td>
                    <td class="py-2 px-2 text-center font-mono text-medical-700 font-bold">{{ ensembleComparison?.blood_sugar?.ensemble?.r2 ?? '--' }}</td>
                  </tr>
                  <tr>
                    <td class="py-2 px-2 text-slate-600">MAE</td>
                    <td class="py-2 px-2 text-center font-mono">{{ ensembleComparison?.blood_sugar?.single?.mae ?? '--' }}</td>
                    <td class="py-2 px-2 text-center font-mono text-medical-700 font-bold">{{ ensembleComparison?.blood_sugar?.ensemble?.mae ?? '--' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- 糖尿病预测对比 -->
          <div>
            <h4 class="text-sm font-bold text-slate-700 mb-3 pb-2 border-b border-slate-100">糖尿病预测 (分类)</h4>
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-slate-200">
                    <th class="text-left py-2 px-2 text-slate-500 font-medium">指标</th>
                    <th class="text-center py-2 px-2 text-slate-600 font-medium">单模型</th>
                    <th class="text-center py-2 px-2 text-medical-700 font-medium">融合模型</th>
                  </tr>
                </thead>
                <tbody>
                  <tr class="border-b border-slate-100">
                    <td class="py-2 px-2 text-slate-600">AUC</td>
                    <td class="py-2 px-2 text-center font-mono">{{ ((ensembleComparison?.diabetes?.single?.auc || 0) * 100).toFixed(1) }}%</td>
                    <td class="py-2 px-2 text-center font-mono text-medical-700 font-bold">{{ ((ensembleComparison?.diabetes?.ensemble?.auc || 0) * 100).toFixed(1) }}%</td>
                  </tr>
                  <tr class="border-b border-slate-100">
                    <td class="py-2 px-2 text-slate-600">Accuracy</td>
                    <td class="py-2 px-2 text-center font-mono">{{ ((ensembleComparison?.diabetes?.single?.accuracy || 0) * 100).toFixed(1) }}%</td>
                    <td class="py-2 px-2 text-center font-mono text-medical-700 font-bold">{{ ((ensembleComparison?.diabetes?.ensemble?.accuracy || 0) * 100).toFixed(1) }}%</td>
                  </tr>
                  <tr class="border-b border-slate-100">
                    <td class="py-2 px-2 text-slate-600">Precision</td>
                    <td class="py-2 px-2 text-center font-mono">{{ ((ensembleComparison?.diabetes?.single?.precision || 0) * 100).toFixed(1) }}%</td>
                    <td class="py-2 px-2 text-center font-mono text-medical-700 font-bold">{{ ((ensembleComparison?.diabetes?.ensemble?.precision || 0) * 100).toFixed(1) }}%</td>
                  </tr>
                  <tr class="border-b border-slate-100">
                    <td class="py-2 px-2 text-slate-600">Recall</td>
                    <td class="py-2 px-2 text-center font-mono">{{ ((ensembleComparison?.diabetes?.single?.recall || 0) * 100).toFixed(1) }}%</td>
                    <td class="py-2 px-2 text-center font-mono text-medical-700 font-bold">{{ ((ensembleComparison?.diabetes?.ensemble?.recall || 0) * 100).toFixed(1) }}%</td>
                  </tr>
                  <tr>
                    <td class="py-2 px-2 text-slate-600">F1</td>
                    <td class="py-2 px-2 text-center font-mono">{{ ((ensembleComparison?.diabetes?.single?.f1 || 0) * 100).toFixed(1) }}%</td>
                    <td class="py-2 px-2 text-center font-mono text-medical-700 font-bold">{{ ((ensembleComparison?.diabetes?.ensemble?.f1 || 0) * 100).toFixed(1) }}%</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        <div class="mt-4 pt-3 border-t border-slate-100">
          <p class="text-xs text-slate-400">融合模型采用 Stacking 集成策略，第一层由 LightGBM 和 XGBoost 组成，第二层使用元学习器融合基学习器输出。绿色高亮数值为融合模型结果。</p>
        </div>
      </div>
    </div>
    <div v-else class="mb-4">
      <div class="card p-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 bg-medical-100 rounded-lg flex items-center justify-center">
            <span class="text-medical-600 text-sm">🏆</span>
          </div>
          <div>
            <h3 class="text-lg font-bold text-slate-800">模型性能对比</h3>
            <p class="text-xs text-slate-500">单一 LightGBM 模型 vs Stacking 融合模型</p>
          </div>
        </div>
        <button @click="loadEnsembleComparison" :disabled="ensembleLoading" class="btn-secondary text-sm">
          {{ ensembleLoading ? '加载中...' : '加载对比数据' }}
        </button>
      </div>
    </div>

    <!-- 预警区 -->
    <div v-if="alerts.length > 0" class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
      <div
        v-for="alert in alerts"
        :key="alert.level"
        class="border-l-4 p-4 rounded-r-lg"
        :class="{
          'border-red-500 bg-red-50': alert.level === 'high',
          'border-yellow-500 bg-yellow-50': alert.level === 'medium',
          'border-blue-500 bg-blue-50': alert.level === 'low'
        }"
      >
        <div class="flex items-start gap-3">
          <span class="text-xl">{{ alert.icon }}</span>
          <div class="flex-1">
            <h4 class="text-sm font-bold mb-1" :class="{
              'text-red-700': alert.level === 'high',
              'text-yellow-700': alert.level === 'medium',
              'text-blue-700': alert.level === 'low'
            }">{{ alert.title }}</h4>
            <p class="text-xs leading-relaxed" :class="{
              'text-red-600': alert.level === 'high',
              'text-yellow-600': alert.level === 'medium',
              'text-blue-600': alert.level === 'low'
            }">{{ alert.message }}</p>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="mb-4 p-4 bg-success-50 border border-success-200 rounded-lg">
      <div class="flex items-center gap-2">
        <span class="text-success-600 text-lg">✓</span>
        <p class="text-sm text-success-700 font-medium">当前无预警信息，系统运行正常</p>
      </div>
    </div>

    <!-- 右下角浮动刷新按钮 -->
    <button
      @click="manualRefresh"
      class="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-r from-primary-500 to-medical-500 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-300 flex items-center justify-center group z-40"
      :title="`下次自动刷新: ${refreshCountdown}秒`"
    >
      <div class="relative">
        <el-icon :size="24" class="group-hover:rotate-180 transition-transform duration-500">
          <Refresh />
        </el-icon>
        <span class="absolute -top-1 -right-1 w-5 h-5 bg-white text-primary-600 text-xs font-bold rounded-full flex items-center justify-center">
          {{ refreshCountdown }}
        </span>
      </div>
    </button>
  </div>
</template>

<style scoped>
.dashboard-page {
  max-width: 1600px;
  margin: 0 auto;
  padding: 1rem;
  min-height: calc(100vh - 56px);
}
</style>
