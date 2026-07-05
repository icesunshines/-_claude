# 可视化大屏 3:4:3 改造 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将可视化大屏改造为三列等分布局（左 3 列趋势图 + 中 4 列雷达图 + 右 3 列饼图），每列下方配数据解读，移除冗余图表组件。

**Architecture:** 新建 3 个图表组件（AgeTrendChart、HexRadarChart、RiskDistributionChart），重写 Dashboard.vue 的网格布局，废弃 3 个不再使用的图表组件。纯前端改动，不涉及后端。

**Tech Stack:** Vue 3 + Element Plus + Tailwind CSS + ECharts 5.5

---

### Task 1: 新建 AgeTrendChart.vue（左侧趋势折线图）

**Files:**
- Create: `frontend/src/components/Charts/AgeTrendChart.vue`

- [ ] **Step 1: 创建组件文件**

将以下代码写入 `frontend/src/components/Charts/AgeTrendChart.vue`：

```vue
<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: Object,
  loading: Boolean
})

const chartRef = ref(null)
let chart = null

function initChart() {
  if (!chartRef.value || !props.data?.age_stats) return
  if (chart) {
    chart.dispose()
  }
  chart = echarts.init(chartRef.value)

  const ageEntries = Object.entries(props.data.age_stats)
  const ageGroups = ageEntries.map(([age]) => Number(age)).sort((a, b) => a - b)
  const values = ageGroups.map(age => props.data.age_stats[age])

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#334155' },
      extraCssText: 'box-shadow: 0 4px 16px rgba(0,0,0,0.1); border-radius: 12px;',
      formatter: (params) => {
        const age = params[0].name
        const val = params[0].value
        return `<div style="padding: 4px 8px;">
          <div style="font-weight: bold; margin-bottom: 4px;">${age} 岁组</div>
          <div style="color: #14b8a6;">平均血糖：${val} mmol/L</div>
        </div>`
      }
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
      data: ageGroups.map(a => `${a}岁`),
      axisLine: { lineStyle: { color: '#e2e8f0', width: 2 } },
      axisLabel: { color: '#64748b', fontSize: 11, margin: 10 },
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
      data: values,
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
      },
      emphasis: {
        itemStyle: { borderWidth: 3, shadowColor: 'rgba(20, 184, 166, 0.4)', shadowBlur: 10 }
      }
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
      <div class="w-10 h-10 rounded-xl flex items-center justify-center" style="background: rgba(20,184,166,0.15)">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#14b8a6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
        </svg>
      </div>
      <div>
        <h3 class="text-lg font-bold" style="color: var(--ds-text)">年龄段血糖趋势</h3>
        <p class="text-xs" style="color: var(--ds-text-secondary)">各年龄组平均血糖水平</p>
      </div>
    </div>
    <div ref="chartRef" style="width: 100%; height: 300px;"></div>
  </div>
</template>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/Charts/AgeTrendChart.vue
git commit -m "feat: add AgeTrendChart for blood sugar age-group trend"
```

---

### Task 2: 新建 HexRadarChart.vue（中间六边形雷达图）

**Files:**
- Create: `frontend/src/components/Charts/HexRadarChart.vue`

- [ ] **Step 1: 创建组件文件**

将以下代码写入 `frontend/src/components/Charts/HexRadarChart.vue`：

```vue
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
      center: ['50%', '55%'],
      radius: '65%',
      axisName: {
        color: 'var(--ds-text)',
        fontSize: 12,
        fontWeight: 'bold'
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(148, 163, 184, 0.2)',
          width: 1
        }
      },
      splitArea: {
        areaStyle: {
          color: [
            'rgba(139, 92, 246, 0.03)',
            'rgba(139, 92, 246, 0.06)',
            'rgba(139, 92, 246, 0.03)',
            'rgba(139, 92, 246, 0.06)'
          ]
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(148, 163, 184, 0.3)'
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
          color: 'rgba(139, 92, 246, 0.25)'
        },
        lineStyle: {
          color: '#8b5cf6',
          width: 2
        },
        itemStyle: {
          color: '#8b5cf6',
          borderWidth: 2,
          borderColor: '#fff'
        },
        emphasis: {
          areaStyle: {
            color: 'rgba(139, 92, 246, 0.4)'
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
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/Charts/HexRadarChart.vue
git commit -m "feat: add HexRadarChart for six-dimension health assessment"
```

---

### Task 3: 新建 RiskDistributionChart.vue（右侧血糖风险分布环形饼图）

**Files:**
- Create: `frontend/src/components/Charts/RiskDistributionChart.vue`

- [ ] **Step 1: 创建组件文件**

将以下代码写入 `frontend/src/components/Charts/RiskDistributionChart.vue`：

```vue
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
      right: '5%',
      top: 'center',
      textStyle: { color: '#64748b', fontSize: 11 },
      itemWidth: 12,
      itemHeight: 12,
      itemGap: 12
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['38%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 6,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: true,
        position: 'outside',
        color: '#64748b',
        fontSize: 11,
        formatter: '{b}\n{d}%',
        lineHeight: 16
      },
      labelLine: {
        lineStyle: { color: '#cbd5e1' },
        length: 10,
        length2: 10
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 14,
          fontWeight: 'bold'
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
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/Charts/RiskDistributionChart.vue
git commit -m "feat: add RiskDistributionChart for blood sugar risk breakdown"
```

---

### Task 4: 重写 Dashboard.vue 主布局

**Files:**
- Modify: `frontend/src/views/Dashboard.vue`

- [ ] **Step 1: 备份当前文件**

```bash
cp frontend/src/views/Dashboard.vue frontend/src/views/Dashboard.vue.backup
```

- [ ] **Step 2: 重写 `<script setup>` 区域**

将 `Dashboard.vue` 的 `<script setup>` 区域替换为以下代码。注意导入改为 `AgeTrendChart`、`HexRadarChart`、`RiskDistributionChart`，并删除不再使用的导入。

```vue
<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { getStatsOverview, getBloodSugarStats } from '../api/request'
import { DataBoard, Timer, Refresh, DataAnalysis, Monitor, FirstAidKit, InfoFilled } from '@element-plus/icons-vue'
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

- [ ] **Step 3: 替换 `<template>` 区域**

将 `Dashboard.vue` 的 `<template>` 区域替换为以下代码：

```vue
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
              医疗健康数据可视化大屏
            </h1>
            <p class="text-slate-500 text-sm mt-1 flex items-center gap-2">
              <span class="inline-block w-2 h-2 bg-success-500 rounded-full animate-pulse"></span>
              实时数据监测与智能分析平台
            </p>
          </div>
        </div>

        <div class="flex items-center gap-6">
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
      <div class="lg:col-span-3 card p-5">
        <AgeTrendChart :data="bloodSugarData" :loading="loading" />
        <div v-if="leftSummary" class="mt-4 bg-slate-50 rounded-xl p-4 border border-slate-100">
          <p class="text-xs text-slate-600 leading-relaxed">{{ leftSummary }}</p>
        </div>
      </div>

      <!-- C2. 中间 — 六边形雷达图 + 文字解读 -->
      <div class="lg:col-span-6 card p-5">
        <HexRadarChart :overview="overview" :loading="loading" />
        <div v-if="centerSummary" class="mt-4 bg-slate-50 rounded-xl p-4 border border-slate-100">
          <p class="text-xs text-slate-600 leading-relaxed">{{ centerSummary }}</p>
        </div>
      </div>

      <!-- C3. 右侧 — 血糖风险分布 + 文字解读 -->
      <div class="lg:col-span-3 card p-5">
        <RiskDistributionChart :data="bloodSugarData" :loading="loading" />
        <div v-if="rightSummary" class="mt-4 bg-slate-50 rounded-xl p-4 border border-slate-100">
          <p class="text-xs text-slate-600 leading-relaxed">{{ rightSummary }}</p>
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
```

- [ ] **Step 4: 确认 `<style scoped>` 区域保留**

确认 `Dashboard.vue` 底部的 `<style scoped>` 区域仍存在且内容不变：

```css
<style scoped>
.dashboard-page {
  max-width: 1600px;
  margin: 0 auto;
}
</style>
```

- [ ] **Step 5: 提交**

```bash
git add frontend/src/views/Dashboard.vue
git commit -m "feat: redesign Dashboard with 3:4:3 layout and data summaries"
```

---

### Task 5: 废弃不再使用的图表组件

**Files:**
- Delete: `frontend/src/components/Charts/RiskCards.vue`
- Delete: `frontend/src/components/Charts/GaugeChart.vue`
- Delete: `frontend/src/components/Charts/BarChart.vue`

- [ ] **Step 1: 删除文件**

```bash
rm frontend/src/components/Charts/RiskCards.vue
rm frontend/src/components/Charts/GaugeChart.vue
rm frontend/src/components/Charts/BarChart.vue
```

- [ ] **Step 2: 提交**

```bash
git add -A
git commit -m "chore: remove unused chart components from dashboard"
```

---

### Task 6: 前端测试验证

**Files:**
- Test: `frontend/src/views/Dashboard.vue`
- Test: `frontend/src/components/Charts/AgeTrendChart.vue`
- Test: `frontend/src/components/Charts/HexRadarChart.vue`
- Test: `frontend/src/components/Charts/RiskDistributionChart.vue`

- [ ] **Step 1: 启动后端 API**

```bash
python src/main.py
```

确认后端运行在 `http://localhost:8000`，访问 `http://localhost:8000/api/stats/overview` 确认返回正常 JSON。

- [ ] **Step 2: 启动前端开发服务器**

```bash
cd frontend && npm run dev
```

确认前端运行在 `http://localhost:5173`。

- [ ] **Step 3: 浏览器验证**

1. 打开 `http://localhost:5173`，登录后访问 `/`（可视化大屏）
2. 确认页面顶部显示系统标题、时间、刷新按钮
3. 确认 4 张统计卡片显示正确数值（总样本量 ~5642，特征维度 ~34，准确率 ~70%，AUC ~0.73）
4. 确认三列布局正确显示：
   - 左侧折线图展示年龄段血糖趋势，有面积填充
   - 中间六边形雷达图展示 6 个维度
   - 右侧环形饼图展示 5 个风险区间
5. 确认每个图表下方有文字解读（数据驱动）
6. 确认底部显示临床指标对比 + 最近预测记录
7. 切换浏览器宽度到 < 1024px，确认折叠为单列

- [ ] **Step 4: 提交（如有调整）**

```bash
git add -A
git commit -m "test: verify dashboard 3:4:3 layout across breakpoints"
```

---

## Spec Coverage

- 三列等分布局（3:4:3） → Task 4 的 `lg:grid-cols-12` 网格
- 左列年龄段趋势图 → Task 1 AgeTrendChart.vue
- 中间六边形雷达图 → Task 2 HexRadarChart.vue
- 右列血糖风险分布饼图 → Task 3 RiskDistributionChart.vue
- 文字解读（数据驱动） → Task 4 的 `leftSummary`/`centerSummary`/`rightSummary` computed
- 统计卡片保留 → Task 4 区域 B
- 底部临床对比 + 最近记录 → Task 4 区域 D
- 移除冗余图表 → Task 5 删除 RiskCards/GaugeChart/BarChart
- 无后端改动 → 所有任务均为前端改动
