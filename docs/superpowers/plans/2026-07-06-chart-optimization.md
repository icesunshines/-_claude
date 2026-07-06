# 图表优化 Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 优化雷达图和临床指标对比图，适合答辩用的学术风格。

**Architecture:** 后端 `get_diabetes_stats()` 新增 `radar_comparison` 字段（6维度健康/患者均值）；前端 `HexRadarChart.vue` 改为双线对比、增大尺寸；`DiabetesCharts.vue` 去掉阴影、增加高度。

**Tech Stack:** Python/Pandas + ECharts + Vue 3

---

### 文件改动清单

| 文件 | 改动 |
|------|------|
| `src/predict.py` | 修改 `get_diabetes_stats()` 新增雷达图数据 |
| `frontend/src/components/Charts/HexRadarChart.vue` | 大幅改动：双线对比、尺寸、配色 |
| `frontend/src/components/Charts/DiabetesCharts.vue` | 视觉优化：去掉阴影、增加高度 |
| `frontend/src/views/Dashboard.vue` | 容器高度调整 |

---

### Task 1: 后端新增雷达图数据

**Files:**
- Modify: `src/predict.py:199-239`

- [ ] **Step 1: 修改 `get_diabetes_stats()` 添加 `radar_comparison`**

找到函数末尾的 return 语句，在 `clinical_comparison` 之后添加雷达图数据：

```python
    # 雷达图数据：6个临床指标的健康群体 vs 患者群体均值
    radar_labels = ['年龄', '孕前BMI', '收缩压', '舒张压', '糖筛孕周', '空腹血糖']
    radar_comparison = {}
    for col in radar_labels:
        if col in df.columns:
            radar_comparison[col] = {
                'healthy_mean': round(float(df[df['label'] == 0][col].mean()), 2),
                'patient_mean': round(float(df[df['label'] == 1][col].mean()), 2),
            }

    return {
        'clinical_comparison': comparison,
        'radar_comparison': radar_comparison,
        'model_metrics': metrics,
        'roc_curve': roc_data,
        'confusion_matrix': confusion,
    }
```

改动：在 `clinical_comparison` 计算之后、return 之前，添加 `radar_comparison` 字典。使用与 `clinical_comparison` 相同的逻辑，但维度固定为6个临床指标。

- [ ] **Step 2: 提交**

```bash
git add src/predict.py
git commit -m "feat: 后端新增 radar_comparison 数据用于雷达图对比"
```

---

### Task 2: HexRadarChart.vue 双线对比 + 尺寸增大

**Files:**
- Modify: `frontend/src/components/Charts/HexRadarChart.vue`

- [ ] **Step 1: 重写组件为双线对比**

将整个组件替换为以下代码：

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
```

**关键改动：**
- 容器高度：340px → 500px
- 数据源：从 `overview.mean_blood_sugar` 等 → `overview.radar_comparison`（6维度健康/患者均值）
- 双线对比：健康群体（绿色） vs 患者群体（红色）
- 雷达形状：hexagon → polygon（更适合6维度）
- 半径：72% → 65%（防止溢出）
- 标准化：每个维度按 `实际值 / 该维度最大值 * 100` 标准化到 0-100
- legend 放在底部
- tooltip 显示对应群体的值

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/Charts/HexRadarChart.vue
git commit -m "feat: 雷达图改为双线对比 + 增大尺寸 + 修正数据源"
```

---

### Task 3: DiabetesCharts.vue 学术风格优化

**Files:**
- Modify: `frontend/src/components/Charts/DiabetesCharts.vue`

- [ ] **Step 1: 优化柱状图样式**

找到 series 中的 itemStyle 配置，替换阴影和渐变：

```javascript
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
```

**改动：**
- 去掉 `shadowColor` 和 `shadowBlur`（发光阴影）
- 去掉渐变 `color: { type: 'linear', ... }`，改为纯色
- 圆角：10 → 6
- barWidth：35% → 40%（条形更宽）
- 添加 emphasis hover 时的颜色加深

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/Charts/DiabetesCharts.vue
git commit -m "feat: 临床指标柱状图改为学术风格，去掉发光阴影"
```

---

### Task 4: Dashboard.vue 容器高度调整

**Files:**
- Modify: `frontend/src/views/Dashboard.vue`

- [ ] **Step 1: 调整临床指标对比容器高度**

找到 h-72 的容器，改为 h-[420px]：

```html
<div class="h-[420px]">
  <DiabetesCharts />
</div>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/Dashboard.vue
git commit -m "feat: Dashboard 临床指标对比容器高度增加到 420px"
```

---

### Task 5: 最终验证

**Files:**
- 无新文件

- [ ] **Step 1: 构建验证**

```bash
cd frontend
npm run build 2>&1 | head -20
```

- [ ] **Step 2: 检查 git diff**

```bash
git diff --stat
```

确认只改了 4 个文件。

- [ ] **Step 3: 提交**

```bash
git add src/predict.py frontend/src/components/Charts/HexRadarChart.vue frontend/src/components/Charts/DiabetesCharts.vue frontend/src/views/Dashboard.vue
git commit -m "feat: 雷达图和临床指标对比图优化 — 学术风格"
```

---

## 注意事项

1. **雷达图标准化**：每个维度按 `实际值 / 该维度医学正常范围上限 * 100` 标准化，使6个维度可比较
2. **双线配色**：绿色 `#22c55e`（健康群体）、红色 `#ef4444`（患者群体），学术论文常用配色
3. **可回退**：后端新增 `radar_comparison` 字段，不影响现有 `clinical_comparison`
4. **fallback 数据**：如果 `radar_comparison` 为空，使用医学上合理的默认值
