# 可视化大屏改造设计

## 概述

将可视化大屏（Dashboard.vue）从当前多图表堆叠布局改造为**三列等分布局（3:4:3）**，左右各一个数据图表配文字解读，中间六边形雷达图配文字解读。去掉冗余图表（风险仪表盘、风险卡片、特征重要性柱状图），保留并优化临床指标对比和最近预测记录区域。

## 布局结构

```
┌──────────────────────────────────────────────────────────────┐
│ A. 顶部区域：系统标题 + 系统时间 + 刷新按钮                    │
├──────────────────────────────────────────────────────────────┤
│ B. 统计卡片：总样本量 | 特征维度 | 预测准确率 | 模型 AUC        │
├──────────┬────────────────────────┬──────────────────────────┤
│ C1. 左   │    C2. 中              │       C3. 右              │
│ (3 列)   │    (4 列)              │      (3 列)               │
│          │                        │                          │
│ 年龄段   │   六边形雷达图          │   血糖风险等级分布        │
│ 血糖趋势 │   六维度综合评估        │   环形饼图                │
│ 折线图   │   雷达图                │   环形饼图               │
│          │                        │                          │
│ ─────────│   ────────────────────  │   ─────────────────────  │
│ 数据解读 │   数据解读              │   数据解读               │
├──────────┴────────────────────────┴──────────────────────────┤
│ D. 底部区域：临床指标对比 + 最近预测记录（12 列网格）           │
└──────────────────────────────────────────────────────────────┘
```

< 1024px 时全部折叠为单列。

## 区域详细说明

### A. 顶部区域

保留系统标题、系统时间、刷新按钮。移除"在线用户""活跃预测""总预测次数"（这些数据是随机模拟的，不来自真实 API）。

### B. 统计卡片

保留现有 4 张卡片，绑定真实 API 数据：
- 总样本量 → `overview.sample_count_initial`
- 特征维度 → `overview.feature_count_blood_sugar`
- 预测准确率 → `overview.diabetes_metrics.accuracy * 100%`
- 模型 AUC → `overview.diabetes_metrics.auc`

### C. 三列主图表区域（3:4:3）

#### C1. 左侧 — 年龄段血糖趋势折线图

- **组件**：新建 `AgeTrendChart.vue`
- **数据**：`/api/stats/blood-sugar` → `age_stats`（年龄组 → 平均血糖值）
- **图表类型**：ECharts 折线图 + 面积填充渐变
- **X 轴**：年龄组（20-29, 30-39, 40-49...）
- **Y 轴**：平均血糖（mmol/L）
- **文字解读**：computed 自动计算 — 最高/最低年龄段及差值、趋势描述

#### C2. 中间 — 六边形雷达图

- **组件**：基于现有 `RadarChart.vue` 增强（改 `HexRadarChart.vue`）
- **数据**：`/api/stats/overview`
- **图表类型**：ECharts 六边形雷达
- **六个维度**：BMI、空腹血糖、血压、年龄风险、遗传风险、运动水平
- **文字解读**：computed 自动计算 — 各维度评分高低、综合健康评分

#### C3. 右侧 — 血糖风险等级分布环形饼图

- **组件**：新建 `RiskDistributionChart.vue`
- **数据**：`/api/stats/blood-sugar` → `distribution`（5 个区间的人数）
- **图表类型**：ECharts 环形饼图（内径 40%，外径 70%）
- **五个区间**：<4（危险低血糖）、4-5.6（正常）、5.6-7（偏高）、7-11.1（高血糖）、>11.1（危险高血糖）
- **文字解读**：computed 自动计算 — 正常人群占比、偏高/高风险人数及百分比

### D. 底部区域

保留 `DiabetesCharts.vue`（临床指标对比柱状图）+ 最近预测记录表格，改为左右 2:1 排列。移除健康指数 SVG、健康小贴士、底部 4 个统计行。

## 文字解读计算逻辑

文字解读由 `Dashboard.vue` 中的 `computed()` 基于 API 数据自动计算，不硬编码：

```js
// 左侧 — 年龄段趋势解读
const leftSummary = computed(() => {
  if (!bloodSugarData.value?.age_stats) return ''
  const ages = Object.entries(bloodSugarData.value.age_stats)
  const maxAge = ages.reduce((a, b) => a[1] > b[1] ? a : b)
  const minAge = ages.reduce((a, b) => a[1] < b[1] ? a : b)
  return `年龄段血糖呈随年龄增长而上升趋势。${maxAge[0]} 岁组最高 (${maxAge[1]} mmol/L)，${minAge[0]} 岁组最低 (${minAge[1]} mmol/L)，差距 ${Math.abs(maxAge[1] - minAge[1]).toFixed(1)} mmol/L。`
})

// 中间 — 雷达图解读
const centerSummary = computed(() => {
  // 从 overview 数据计算各维度评分
  // 展示最高/最低维度名称及分数
})

// 右侧 — 饼图解读
const rightSummary = computed(() => {
  if (!bloodSugarData.value?.distribution) return ''
  const total = Object.values(bloodSugarData.value.distribution).reduce((a, b) => a + b, 0)
  const normal = (bloodSugarData.value.distribution['4-5.6'] || 0) + (bloodSugarData.value.distribution['<4'] || 0)
  const pct = Math.round(normal / total * 100)
  return `本次共分析 ${total} 份体检数据。正常血糖人群占比 ${pct}%（${normal} 人），偏高人群占比 ${Math.round((bloodSugarData.value.distribution['5.6-7'] || 0) / total * 100)}%，需关注。`
})
```

## 组件修改清单

| 操作 | 路径 | 说明 |
|------|------|------|
| 新建 | `frontend/src/components/Charts/AgeTrendChart.vue` | 年龄段血糖趋势折线图 |
| 新建 | `frontend/src/components/Charts/HexRadarChart.vue` | 增强版六边形雷达图 |
| 新建 | `frontend/src/components/Charts/RiskDistributionChart.vue` | 血糖风险分布环形饼图 |
| 修改 | `frontend/src/views/Dashboard.vue` | 重写整体布局，绑定 computed 数据解读 |
| 修改 | `frontend/src/api/request.js` | 检查是否需要新增 API 调用 |
| 废弃 | `frontend/src/components/Charts/RiskCards.vue` | 不再导入 |
| 废弃 | `frontend/src/components/Charts/GaugeChart.vue` | 不再导入 |
| 废弃 | `frontend/src/components/Charts/BarChart.vue` | 不再导入 |

## 样式与美化要点

- 每张卡片统一使用 `.card` 共享样式 + `card-hover` 悬停效果
- 图表容器高度统一 `h-72`（约 288px），紧凑但不拥挤
- 文字解读区使用 `bg-slate-50 rounded-xl p-4 border border-slate-100` 背景块，与卡片主区域区分
- 文字解读中使用彩色标签（badge）突出关键数字
- 保持现有的暗色/亮色主题变量支持

## 无后端改动

所有数据均使用现有 API，不需要新增后端接口。
