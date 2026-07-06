<script setup>
import { ref, onMounted } from 'vue'
import { predictBloodSugar, predictDiabetes, getBloodSugarMeans, saveHistory, getStatsOverview, getDiabetesStats, getFeatureImportance } from '../api/request'
import { Loading, CircleCheck, Warning, Refresh, MagicStick, DataLine, TrendCharts, ArrowDown } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import FeatureBarChart from '../components/Charts/FeatureBarChart.vue'
import ROCCurveChart from '../components/Charts/ROCCurveChart.vue'
import ConfusionMatrix from '../components/Charts/ConfusionMatrix.vue'

const activeTab = ref('blood_sugar')
const loading = ref(false)
const bsResult = ref(null)
const dmResult = ref(null)

const bsForm = ref({
  性别: '男',
  年龄: 40,
  天门冬氨酸氨基转换酶: null,
  丙氨酸氨基转换酶: null,
  碱性磷酸酶: null,
  r_谷氨酰基转换酶: null,
  总蛋白: null,
  白蛋白: null,
  球蛋白: null,
  白球比例: null,
  甘油三酯: null,
  总胆固醇: null,
  高密度脂蛋白胆固醇: null,
  低密度脂蛋白胆固醇: null,
  尿素: null,
  肌酐: null,
  尿酸: null,
  白细胞计数: null,
  红细胞计数: null,
  血红蛋白: null,
  红细胞压积: null,
  红细胞平均体积: null,
  红细胞平均血红蛋白量: null,
  红细胞平均血红蛋白浓度: null,
  红细胞体积分布宽度: null,
  血小板计数: null,
  血小板平均体积: null,
  血小板体积分布宽度: null,
  血小板比积: null,
  中性粒细胞百分比: null,
  淋巴细胞百分比: null,
  单核细胞百分比: null,
  嗜酸细胞百分比: null,
  嗜碱细胞百分比: null
})

const dmForm = ref({
  年龄: 30,
  孕次: 2,
  产次: 1,
  身高: 160,
  孕前体重: 55,
  孕前BMI: 21.5,
  BMI分类: 0,
  收缩压: 120,
  舒张压: 80,
  糖筛孕周: 26,
  wbc: 8,
  ALT: 20,
  AST: 22,
  Cr: 50,
  BUN: 3,
  CHO: 5,
  TG: 1.5,
  HDLC: 1.5,
  LDLC: 3,
  ApoA1: 1.2,
  ApoB: 0.8,
  Lpa: 100,
  hsCRP: 2,
  DM家族史: 0
})

const bsGroups = [
  { title: '基本信息', fields: ['性别', '年龄'] },
  { title: '肝功能指标', fields: ['天门冬氨酸氨基转换酶', '丙氨酸氨基转换酶', '碱性磷酸酶', 'r_谷氨酰基转换酶', '总蛋白', '白蛋白', '球蛋白', '白球比例'] },
  { title: '血脂指标', fields: ['甘油三酯', '总胆固醇', '高密度脂蛋白胆固醇', '低密度脂蛋白胆固醇'] },
  { title: '肾功能指标', fields: ['尿素', '肌酐', '尿酸'] },
  { title: '血常规', fields: ['白细胞计数', '红细胞计数', '血红蛋白', '红细胞压积', '红细胞平均体积', '红细胞平均血红蛋白量', '红细胞平均血红蛋白浓度', '红细胞体积分布宽度', '血小板计数', '血小板平均体积', '血小板体积分布宽度', '血小板比积'] },
  { title: '白细胞分类', fields: ['中性粒细胞百分比', '淋巴细胞百分比', '单核细胞百分比', '嗜酸细胞百分比', '嗜碱细胞百分比'] }
]

const bsInterpretation = {
  '正常': '当前血糖水平处于正常范围。建议保持健康饮食和规律运动，每年定期体检监测血糖变化。',
  '偏高': '血糖略高于正常范围，提示糖耐量受损可能。建议减少高糖高脂饮食，增加运动量，3-6 个月后复查空腹血糖和糖化血红蛋白。',
  '高风险': '血糖显著升高，提示糖尿病可能。请尽快就医，进行空腹血糖、糖化血红蛋白及 OGTT 检查，明确诊断并在医生指导下治疗。'
}

const dmInterpretation = {
  '低风险': '当前妊娠期糖尿病风险较低。继续保持均衡饮食和适度运动，按医嘱完成孕期糖筛即可。',
  '中风险': '存在一定妊娠期糖尿病风险。建议控制碳水化合物摄入，增加餐后活动，并咨询产科医生是否需要提前干预。',
  '高风险': '妊娠期糖尿病风险较高。请尽快咨询产科医生，进行 OGTT 检查，必要时启动饮食控制或胰岛素治疗，保障母婴安全。'
}

function getBsInterpretation(riskLevel) {
  return bsInterpretation[riskLevel] || '建议结合临床指标综合评估，必要时咨询医生。'
}

function getDmInterpretation(probability) {
  if (probability < 0.3) return dmInterpretation['低风险']
  if (probability < 0.7) return dmInterpretation['中风险']
  return dmInterpretation['高风险']
}

const dmFields = [
  { key: '年龄', label: '年龄' },
  { key: '孕次', label: '孕次' },
  { key: '产次', label: '产次' },
  { key: '身高', label: '身高 (cm)' },
  { key: '孕前体重', label: '孕前体重 (kg)' },
  { key: '孕前BMI', label: '孕前 BMI' },
  { key: 'BMI分类', label: 'BMI 分类' },
  { key: '收缩压', label: '收缩压 (mmHg)' },
  { key: '舒张压', label: '舒张压 (mmHg)' },
  { key: '糖筛孕周', label: '糖筛孕周' },
  { key: 'wbc', label: '白细胞 WBC' },
  { key: 'ALT', label: 'ALT' },
  { key: 'AST', label: 'AST' },
  { key: 'Cr', label: '肌酐 Cr' },
  { key: 'BUN', label: '尿素氮 BUN' },
  { key: 'CHO', label: '总胆固醇 CHO' },
  { key: 'TG', label: '甘油三酯 TG' },
  { key: 'HDLC', label: 'HDL-C' },
  { key: 'LDLC', label: 'LDL-C' },
  { key: 'ApoA1', label: 'ApoA1' },
  { key: 'ApoB', label: 'ApoB' },
  { key: 'Lpa', label: 'Lp(a)' },
  { key: 'hsCRP', label: 'hsCRP' },
  { key: 'DM家族史', label: '糖尿病家族史 (0/1)' }
]

const diabetesMetrics = ref(null)
const featureData = ref(null)
const activeResultTab = ref('result')
const expandedGroups = ref([true, true, true, false, false, false])

async function loadModelInfo() {
  try {
    const [overviewData, dmStats, fiData] = await Promise.all([
      getStatsOverview(),
      getDiabetesStats(),
      getFeatureImportance('diabetes')
    ])
    diabetesMetrics.value = {
      accuracy: overviewData.diabetes_metrics?.accuracy || 0,
      auc: overviewData.diabetes_metrics?.auc || 0,
      precision: overviewData.diabetes_metrics?.precision || 0,
      recall: overviewData.diabetes_metrics?.recall || 0,
      f1: overviewData.diabetes_metrics?.f1 || 0,
      roc_curve: dmStats.roc_curve || null,
      confusion_matrix: dmStats.confusion_matrix || null,
    }
    featureData.value = fiData || { features: [], values: [] }
  } catch (e) {
    console.error('加载模型信息失败:', e)
    diabetesMetrics.value = null
    featureData.value = { features: [], values: [] }
  }
}

function validateBloodSugarForm() {
  const required = ['年龄', '性别']
  for (const field of required) {
    if (bsForm.value[field] === null || bsForm.value[field] === '') {
      ElMessage.warning(`请填写 ${field}`)
      return false
    }
  }
  return true
}

function validateDiabetesForm() {
  const required = ['年龄', '身高', '孕前体重']
  for (const field of required) {
    if (dmForm.value[field] === null || dmForm.value[field] === '') {
      ElMessage.warning(`请填写 ${field}`)
      return false
    }
  }
  return true
}

async function fillBloodSugarMeans() {
  try {
    const means = await getBloodSugarMeans()
    Object.assign(bsForm.value, means)
    ElMessage.success('已填充样本均值')
  } catch (e) {
    ElMessage.error('加载样本均值失败')
  }
}

async function handleBloodSugarPredict() {
  if (!validateBloodSugarForm()) return
  loading.value = true
  bsResult.value = null
  try {
    const data = await predictBloodSugar(bsForm.value)
    bsResult.value = data
    await saveHistory({
      type: 'blood_sugar',
      input: { ...bsForm.value },
      result: data
    })
    ElMessage.success('预测完成')
  } catch (e) {
    ElMessage.error('预测失败，请检查输入数据')
  } finally {
    loading.value = false
  }
}

async function handleDiabetesPredict() {
  if (!validateDiabetesForm()) return
  loading.value = true
  dmResult.value = null
  try {
    const data = await predictDiabetes(dmForm.value)
    dmResult.value = data
    await saveHistory({
      type: 'diabetes',
      input: { ...dmForm.value },
      result: data
    })
    ElMessage.success('预测完成')
  } catch (e) {
    ElMessage.error('预测失败，请检查输入数据')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadModelInfo()
})

function resetBloodSugarForm() {
  bsResult.value = null
  bsForm.value = {
    性别: '男',
    年龄: 40,
    天门冬氨酸氨基转换酶: null,
    丙氨酸氨基转换酶: null,
    碱性磷酸酶: null,
    r_谷氨酰基转换酶: null,
    总蛋白: null,
    白蛋白: null,
    球蛋白: null,
    白球比例: null,
    甘油三酯: null,
    总胆固醇: null,
    高密度脂蛋白胆固醇: null,
    低密度脂蛋白胆固醇: null,
    尿素: null,
    肌酐: null,
    尿酸: null,
    白细胞计数: null,
    红细胞计数: null,
    血红蛋白: null,
    红细胞压积: null,
    红细胞平均体积: null,
    红细胞平均血红蛋白量: null,
    红细胞平均血红蛋白浓度: null,
    红细胞体积分布宽度: null,
    血小板计数: null,
    血小板平均体积: null,
    血小板体积分布宽度: null,
    血小板比积: null,
    中性粒细胞百分比: null,
    淋巴细胞百分比: null,
    单核细胞百分比: null,
    嗜酸细胞百分比: null,
    嗜碱细胞百分比: null
  }
  ElMessage.info('表单已重置')
}

function resetDiabetesForm() {
  dmResult.value = null
  dmForm.value = {
    年龄: 30,
    孕次: 2,
    产次: 1,
    身高: 160,
    孕前体重: 55,
    孕前BMI: 21.5,
    BMI分类: 0,
    收缩压: 120,
    舒张压: 80,
    糖筛孕周: 26,
    wbc: 8,
    ALT: 20,
    AST: 22,
    Cr: 50,
    BUN: 3,
    CHO: 5,
    TG: 1.5,
    HDLC: 1.5,
    LDLC: 3,
    ApoA1: 1.2,
    ApoB: 0.8,
    Lpa: 100,
    hsCRP: 2,
    DM家族史: 0
  }
  ElMessage.info('表单已重置')
}
</script>

<template>
  <div class="predict-page">
    <!-- 页面头部 -->
    <div class="card mb-6 p-6">
      <div class="flex items-center gap-4">
        <div class="w-12 h-12 bg-gradient-to-br from-primary-500 to-medical-500 rounded-2xl flex items-center justify-center">
          <el-icon :size="24" color="white">
            <DataLine />
          </el-icon>
        </div>
        <div>
          <h1 class="text-3xl font-bold text-slate-800">智能风险预测</h1>
          <p class="text-slate-500 text-lg mt-1">基于机器学习模型的健康风险评估</p>
        </div>
      </div>
    </div>

    <!-- 标签页切换 -->
    <div class="mb-6">
      <div class="inline-flex bg-slate-100 p-2 rounded-2xl">
        <button
          @click="activeTab = 'blood_sugar'"
          :class="[
            'px-8 py-4 rounded-xl font-semibold text-lg transition-all duration-300 flex items-center gap-2',
            activeTab === 'blood_sugar' ? 'bg-white text-primary-600 shadow-soft' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
          ]"
        >
          <el-icon><DataLine /></el-icon>
          体检血糖预测
        </button>
        <button
          @click="activeTab = 'diabetes'"
          :class="[
            'px-8 py-4 rounded-xl font-semibold text-lg transition-all duration-300 flex items-center gap-2',
            activeTab === 'diabetes' ? 'bg-white text-primary-600 shadow-soft' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
          ]"
        >
          <el-icon><TrendCharts /></el-icon>
          妊娠期糖尿病预测
        </button>
      </div>
    </div>

    <!-- 血糖预测 -->
    <div v-if="activeTab === 'blood_sugar'" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 表单区域 -->
      <div class="lg:col-span-2 space-y-4">
        <div class="card p-6">
          <div class="flex items-center justify-between mb-6">
            <div>
              <h2 class="text-xl font-bold text-slate-800 mb-1">血糖预测</h2>
              <p class="text-slate-500 text-sm">输入体检数据进行血糖预测</p>
            </div>
            <div class="flex gap-3">
              <button
                @click="fillBloodSugarMeans"
                class="btn-secondary flex items-center gap-2"
              >
                <el-icon><MagicStick /></el-icon>
                填充样本均值
              </button>
              <button
                @click="resetBloodSugarForm"
                class="btn-secondary flex items-center gap-2"
              >
                <el-icon><Refresh /></el-icon>
                重置
              </button>
            </div>
          </div>

          <div class="space-y-6">
            <div
              v-for="(group, gIdx) in bsGroups"
              :key="group.title"
              class="border-t-2 border-slate-100 pt-6 first:border-t-0 first:pt-0"
            >
              <div
                @click="expandedGroups[gIdx] = !expandedGroups[gIdx]"
                class="flex items-center justify-between cursor-pointer mb-4 select-none"
              >
                <h3 class="text-lg font-bold text-slate-700 flex items-center gap-2">
                  <div class="w-1.5 h-6 bg-primary-500 rounded-full"></div>
                  {{ group.title }}
                </h3>
                <el-icon class="text-slate-400 transition-transform duration-300" :class="{ 'rotate-180': expandedGroups[gIdx] }">
                  <ArrowDown />
                </el-icon>
              </div>
              <div v-show="expandedGroups[gIdx]">
                <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  <div
                    v-for="field in group.fields"
                    :key="field"
                    class="space-y-2"
                  >
                    <label class="text-sm font-semibold text-slate-600">{{ field }}</label>
                    <select
                      v-if="field === '性别'"
                      v-model="bsForm[field]"
                      class="input-field"
                    >
                      <option value="男">男</option>
                      <option value="女">女</option>
                    </select>
                    <input
                      v-else
                      type="number"
                      step="0.01"
                      v-model.number="bsForm[field]"
                      class="input-field"
                      :placeholder="`请输入 ${field}`"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="mt-8 pt-6 border-t-2 border-slate-100">
            <button
              @click="handleBloodSugarPredict"
              :disabled="loading"
              class="btn-primary w-full flex items-center justify-center gap-3 text-lg py-4"
            >
              <el-icon v-if="loading" class="animate-spin">
                <Loading />
              </el-icon>
              {{ loading ? '预测中...' : '开始预测' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 结果展示 -->
      <div class="lg:col-span-1">
        <div v-if="bsResult" class="card p-5 animate-slide-up">
          <div class="flex items-center justify-between mb-4 gap-2">
            <h3 class="text-base font-bold text-slate-800 truncate">预测结果</h3>
            <div class="inline-flex bg-slate-100 p-1 rounded-xl flex-shrink-0">
              <button
                @click="activeResultTab = 'result'"
                :class="[
                  'px-3 py-1.5 rounded-lg text-xs font-semibold transition-all',
                  activeResultTab === 'result' ? 'bg-white text-primary-600 shadow-sm' : 'text-slate-600 hover:text-slate-900'
                ]"
              >预测结果</button>
              <button
                @click="activeResultTab = 'features'"
                :class="[
                  'px-3 py-1.5 rounded-lg text-xs font-semibold transition-all',
                  activeResultTab === 'features' ? 'bg-white text-primary-600 shadow-sm' : 'text-slate-600 hover:text-slate-900'
                ]"
              >特征解释</button>
            </div>
          </div>

          <!-- 预测结果 tab -->
          <div v-if="activeResultTab === 'result'" class="space-y-4">
            <div class="text-center mb-6">
              <div
                class="w-44 h-28 rounded-3xl mx-auto flex items-center justify-center mb-4 border-4"
                :class="[
                  bsResult.risk_level === '正常' ? 'bg-gradient-to-br from-success-100 to-success-200 border-success-300' :
                  bsResult.risk_level === '偏高' ? 'bg-gradient-to-br from-warning-100 to-warning-200 border-warning-300' :
                  'bg-gradient-to-br from-danger-100 to-danger-200 border-danger-300'
                ]"
              >
                <div
                  class="text-4xl font-bold"
                  :class="[
                    bsResult.risk_level === '正常' ? 'text-success-700' :
                    bsResult.risk_level === '偏高' ? 'text-warning-700' :
                    'text-danger-700'
                  ]"
                >
                  {{ bsResult.predicted_bgl }}
                </div>
              </div>
              <p class="text-slate-500 text-lg mb-2">mmol/L</p>
              <div
                class="inline-block py-3 px-6 rounded-2xl text-center"
                :class="[
                  bsResult.risk_level === '正常' ? 'bg-success-50 text-success-700 border-2 border-success-200' :
                  bsResult.risk_level === '偏高' ? 'bg-warning-50 text-warning-700 border-2 border-warning-200' :
                  'bg-danger-50 text-danger-700 border-2 border-danger-200'
                ]"
              >
                <span class="font-bold text-xl">{{ bsResult.risk_level }}</span>
              </div>
            </div>

            <div class="mb-6">
              <div class="flex justify-between text-base mb-2">
                <span class="text-slate-500 font-medium">风险评分</span>
                <span class="font-bold text-slate-800 text-lg">{{ bsResult.risk_score }}/100</span>
              </div>
              <div class="h-3 bg-slate-100 rounded-full overflow-hidden">
                <div
                  class="h-full transition-all duration-1000 ease-out"
                  :style="{
                    width: bsResult.risk_score + '%',
                    background: bsResult.risk_level === '正常' ? 'linear-gradient(90deg, #22c55e, #16a34a)' :
                                bsResult.risk_level === '偏高' ? 'linear-gradient(90deg, #f59e0b, #d97706)' :
                                'linear-gradient(90deg, #ef4444, #dc2626)'
                  }"
                ></div>
              </div>
            </div>

            <div v-if="bsResult.risk_level !== '正常'" class="bg-slate-50 rounded-xl p-4 border border-slate-200">
              <div class="flex items-start gap-3">
                <el-icon class="text-primary-600 mt-1" :size="20">
                  <DataLine />
                </el-icon>
                <p class="text-slate-600 leading-relaxed text-sm">
                  建议进一步检查血糖相关指标，并咨询医生。
                </p>
              </div>
            </div>

            <div class="bg-slate-50 rounded-xl p-4 border border-slate-100">
              <div class="flex items-start gap-3">
                <el-icon class="text-medical-600 mt-1" :size="20">
                  <CircleCheck />
                </el-icon>
                <p class="text-slate-600 leading-relaxed text-sm">
                  {{ getBsInterpretation(bsResult.risk_level) }}
                </p>
              </div>
            </div>
          </div>

          <!-- 特征解释 tab -->
          <div v-else class="space-y-4">
            <div class="bg-slate-50 rounded-xl p-4 border border-slate-100">
              <p class="text-sm text-slate-600 leading-relaxed">
                以下指标对本次血糖预测结果影响最大。条形越长，说明该特征在当前模型中对预测结果的贡献越大。
                该解释基于 LightGBM 模型的特征重要性，仅反映全局规律，不构成临床诊断依据。
              </p>
            </div>
            <FeatureBarChart :data="featureData" :loading="!featureData" />
          </div>
        </div>
        <div v-else class="card p-6 h-full flex items-center justify-center">
          <div class="text-center text-slate-400">
            <div class="w-20 h-20 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <el-icon :size="40">
                <DataLine />
              </el-icon>
            </div>
            <p class="text-lg font-medium mb-1">输入数据后点击预测</p>
            <p class="text-sm">查看血糖预测结果</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 糖尿病预测 -->
    <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 表单区域 -->
      <div class="lg:col-span-2">
        <div class="card p-6">
          <div class="flex items-center justify-between mb-6">
            <div>
              <h2 class="text-xl font-bold text-slate-800 mb-1">妊娠期糖尿病风险预测</h2>
              <p class="text-slate-500 text-sm">输入临床数据进行风险预测</p>
            </div>
            <button
              @click="resetDiabetesForm"
              class="btn-secondary flex items-center gap-2"
            >
              <el-icon><Refresh /></el-icon>
              重置
            </button>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            <div
              v-for="field in dmFields"
              :key="field.key"
              class="space-y-2"
            >
              <label class="text-sm font-semibold text-slate-600">{{ field.label }}</label>
              <input
                type="number"
                step="0.01"
                v-model.number="dmForm[field.key]"
                class="input-field"
                :placeholder="`请输入 ${field.label}`"
              />
            </div>
          </div>

          <div class="mt-8 pt-6 border-t-2 border-slate-100">
            <button
              @click="handleDiabetesPredict"
              :disabled="loading"
              class="btn-primary w-full flex items-center justify-center gap-3 text-lg py-4"
            >
              <el-icon v-if="loading" class="animate-spin">
                <Loading />
              </el-icon>
              {{ loading ? '预测中...' : '开始预测' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 结果展示 -->
      <div class="lg:col-span-1">
        <div v-if="dmResult" class="card p-5 animate-slide-up">
          <div class="flex items-center justify-between mb-4 gap-2">
            <h3 class="text-base font-bold text-slate-800 truncate">预测结果</h3>
            <div class="inline-flex bg-slate-100 p-1 rounded-xl flex-shrink-0">
              <button
                @click="activeResultTab = 'result'"
                :class="[
                  'px-3 py-1.5 rounded-lg text-xs font-semibold transition-all',
                  activeResultTab === 'result' ? 'bg-white text-primary-600 shadow-sm' : 'text-slate-600 hover:text-slate-900'
                ]"
              >预测结果</button>
              <button
                @click="activeResultTab = 'model'"
                :class="[
                  'px-3 py-1.5 rounded-lg text-xs font-semibold transition-all',
                  activeResultTab === 'model' ? 'bg-white text-primary-600 shadow-sm' : 'text-slate-600 hover:text-slate-900'
                ]"
              >模型评估</button>
            </div>
          </div>

          <!-- 预测结果 tab -->
          <div v-if="activeResultTab === 'result'" class="space-y-4">
            <div class="text-center mb-6">
              <div
                class="w-44 h-28 rounded-3xl mx-auto flex items-center justify-center mb-4 border-4"
                :class="[
                  dmResult.risk === 1 ? 'border-danger-500 bg-gradient-to-br from-danger-100 to-danger-200' : 'border-success-500 bg-gradient-to-br from-success-100 to-success-200'
                ]"
              >
                <span
                  class="text-4xl font-bold"
                  :class="[
                    dmResult.risk === 1 ? 'text-danger-700' : 'text-success-700'
                  ]"
                >
                  {{ (dmResult.probability * 100).toFixed(1) }}%
                </span>
              </div>
              <p class="text-slate-500 text-lg mb-2">患病概率</p>
              <div
                class="inline-block py-3 px-6 rounded-2xl text-center"
                :class="[
                  dmResult.risk === 1 ? 'bg-danger-50 text-danger-700 border-2 border-danger-200' : 'bg-success-50 text-success-700 border-2 border-success-200'
                ]"
              >
                <span class="font-bold text-xl">{{ dmResult.risk === 1 ? '高风险（建议进一步筛查）' : '低风险' }}</span>
              </div>
            </div>

            <div v-if="dmResult.risk === 1" class="bg-slate-50 rounded-xl p-4 border border-slate-200">
              <div class="flex items-start gap-3">
                <el-icon class="text-danger-600 mt-1" :size="20">
                  <Warning />
                </el-icon>
                <p class="text-slate-600 leading-relaxed text-sm">
                  建议咨询医生，进行进一步的检查和干预。
                </p>
              </div>
            </div>

            <div class="bg-slate-50 rounded-xl p-4 border border-slate-100">
              <div class="flex items-start gap-3">
                <el-icon class="text-medical-600 mt-1" :size="20">
                  <CircleCheck />
                </el-icon>
                <p class="text-slate-600 leading-relaxed text-sm">
                  {{ getDmInterpretation(dmResult.probability) }}
                </p>
              </div>
            </div>
          </div>

          <!-- 模型评估 tab -->
          <div v-else class="space-y-6">
            <div v-if="diabetesMetrics" class="grid grid-cols-2 gap-3">
              <div class="p-4 bg-slate-50 rounded-xl border border-slate-100 text-center">
                <p class="text-2xl font-bold text-slate-800">{{ ((diabetesMetrics.accuracy || 0) * 100).toFixed(1) }}%</p>
                <p class="text-xs text-slate-500 mt-1">准确率</p>
              </div>
              <div class="p-4 bg-slate-50 rounded-xl border border-slate-100 text-center">
                <p class="text-2xl font-bold text-slate-800">{{ ((diabetesMetrics.auc || 0) * 100).toFixed(1) }}%</p>
                <p class="text-xs text-slate-500 mt-1">AUC</p>
              </div>
              <div class="p-4 bg-slate-50 rounded-xl border border-slate-100 text-center">
                <p class="text-2xl font-bold text-slate-800">{{ ((diabetesMetrics.recall || 0) * 100).toFixed(1) }}%</p>
                <p class="text-xs text-slate-500 mt-1">召回率</p>
              </div>
              <div class="p-4 bg-slate-50 rounded-xl border border-slate-100 text-center">
                <p class="text-2xl font-bold text-slate-800">{{ ((diabetesMetrics.f1 || 0) * 100).toFixed(1) }}%</p>
                <p class="text-xs text-slate-500 mt-1">F1 分数</p>
              </div>
            </div>

            <ROCCurveChart v-if="diabetesMetrics?.roc_curve" :data="diabetesMetrics.roc_curve" :loading="!diabetesMetrics" />
            <ConfusionMatrix v-if="diabetesMetrics?.confusion_matrix" :data="diabetesMetrics.confusion_matrix" :loading="!diabetesMetrics" />
          </div>
        </div>
        <div v-else class="card p-6 h-full flex items-center justify-center">
          <div class="text-center text-slate-400">
            <div class="w-20 h-20 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <el-icon :size="40">
                <TrendCharts />
              </el-icon>
            </div>
            <p class="text-lg font-medium mb-1">输入数据后点击预测</p>
            <p class="text-sm">查看糖尿病风险预测结果</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.predict-page {
  max-width: 1600px;
  margin: 0 auto;
}
</style>
