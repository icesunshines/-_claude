<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  predictBloodSugar,
  predictDiabetes,
  predictBloodSugarEnsemble,
  predictDiabetesEnsemble,
  getBloodSugarMeans,
  saveHistory,
  getStatsOverview,
  getDiabetesStats,
  getFeatureImportance,
  getEnsembleComparison
} from '../api/request'
import {
  Loading,
  CircleCheck,
  Warning,
  Refresh,
  MagicStick,
  DataLine,
  TrendCharts,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Promotion
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import FeatureBarChart from '../components/Charts/FeatureBarChart.vue'
import ROCCurveChart from '../components/Charts/ROCCurveChart.vue'
import ConfusionMatrix from '../components/Charts/ConfusionMatrix.vue'

// ==================== 向导状态 ====================
const wizardStep = ref(1)
const selectedTask = ref(null)

// ==================== 表单数据 ====================
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

// ==================== 分组配置 ====================
const bsGroups = [
  { title: '基本信息', fields: ['性别', '年龄'] },
  { title: '肝功能指标', fields: ['天门冬氨酸氨基转换酶', '丙氨酸氨基转换酶', '碱性磷酸酶', 'r_谷氨酰基转换酶', '总蛋白', '白蛋白', '球蛋白', '白球比例'] },
  { title: '血脂指标', fields: ['甘油三酯', '总胆固醇', '高密度脂蛋白胆固醇', '低密度脂蛋白胆固醇'] },
  { title: '肾功能指标', fields: ['尿素', '肌酐', '尿酸'] },
  { title: '血常规', fields: ['白细胞计数', '红细胞计数', '血红蛋白', '红细胞压积', '红细胞平均体积', '红细胞平均血红蛋白量', '红细胞平均血红蛋白浓度', '红细胞体积分布宽度', '血小板计数', '血小板平均体积', '血小板体积分布宽度', '血小板比积'] },
  { title: '白细胞分类', fields: ['中性粒细胞百分比', '淋巴细胞百分比', '单核细胞百分比', '嗜酸细胞百分比', '嗜碱细胞百分比'] }
]

const dmFields = [
  { key: '年龄', label: '年龄', integer: true },
  { key: '孕次', label: '孕次', integer: true },
  { key: '产次', label: '产次', integer: true },
  { key: '身高', label: '身高 (cm)', integer: true },
  { key: '孕前体重', label: '孕前体重 (kg)' },
  { key: '孕前BMI', label: '孕前 BMI' },
  { key: 'BMI分类', label: 'BMI 分类', integer: true },
  { key: '收缩压', label: '收缩压 (mmHg)', integer: true },
  { key: '舒张压', label: '舒张压 (mmHg)', integer: true },
  { key: '糖筛孕周', label: '糖筛孕周', integer: true },
  { key: 'wbc', label: '白细胞 WBC', integer: true },
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
  { key: 'DM家族史', label: '糖尿病家族史 (0/1)', integer: true }
]

// ==================== 预测结果 ====================
const bsResult = ref(null)
const dmResult = ref(null)
const loading = ref(false)
const activeResultTab = ref('result')

// ==================== 模型选择 ====================
const useEnsemble = ref(false)
const useEnsembleDiabetes = ref(false)

// ==================== 对比数据 ====================
const ensembleComparison = ref(null)
const ensembleLoading = ref(false)
const diabetesMetrics = ref(null)
const featureData = ref(null)

// ==================== 表单分组折叠 ====================
const expandedGroups = ref([true, true, true, false, false, false])
const BS_INTEGER_FIELDS = new Set(['年龄'])

// ==================== 医学解读文案 ====================
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

// ==================== 向导导航 ====================
function selectTask(task) {
  selectedTask.value = task
  wizardStep.value = 2
}

function nextStep() {
  if (wizardStep.value === 2) {
    if (!validateCurrentForm()) return
    wizardStep.value = 3
  } else if (wizardStep.value === 3) {
    wizardStep.value = 4
  }
}

function prevStep() {
  if (wizardStep.value === 2) {
    selectedTask.value = null
    wizardStep.value = 1
  } else if (wizardStep.value === 3) {
    wizardStep.value = 2
  } else if (wizardStep.value === 4) {
    wizardStep.value = 3
  }
}

function goToPredict() {
  wizardStep.value = 4
}

function resetWizard() {
  selectedTask.value = null
  wizardStep.value = 1
  bsResult.value = null
  dmResult.value = null
  activeResultTab.value = 'result'
  useEnsemble.value = false
  useEnsembleDiabetes.value = false
}

// ==================== 表单校验 ====================
function validateCurrentForm() {
  if (selectedTask.value === 'blood_sugar') {
    return validateBloodSugarForm()
  }
  return validateDiabetesForm()
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

// ==================== 预测逻辑 ====================
async function handleBloodSugarPredict() {
  if (!validateBloodSugarForm()) return
  coerceBloodSugarIntegers()
  loading.value = true
  bsResult.value = null
  try {
    const data = useEnsemble.value
      ? await predictBloodSugarEnsemble(bsForm.value)
      : await predictBloodSugar(bsForm.value)
    bsResult.value = data
    await saveHistory({
      type: 'blood_sugar',
      input: { ...bsForm.value },
      result: { ...data, model_type: useEnsemble.value ? 'ensemble' : 'single' }
    })
    ElMessage.success(useEnsemble.value ? '融合模型预测完成' : '预测完成')
    wizardStep.value = 5
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
    const data = useEnsembleDiabetes.value
      ? await predictDiabetesEnsemble(dmForm.value)
      : await predictDiabetes(dmForm.value)
    dmResult.value = data
    await saveHistory({
      type: 'diabetes',
      input: { ...dmForm.value },
      result: { ...data, model_type: useEnsembleDiabetes.value ? 'ensemble' : 'single' }
    })
    ElMessage.success(useEnsembleDiabetes.value ? '融合模型预测完成' : '预测完成')
    wizardStep.value = 5
  } catch (e) {
    ElMessage.error('预测失败，请检查输入数据')
  } finally {
    loading.value = false
  }
}

function coerceBloodSugarIntegers() {
  for (const field of BS_INTEGER_FIELDS) {
    if (bsForm.value[field] !== null && bsForm.value[field] !== '') {
      bsForm.value[field] = Math.round(Number(bsForm.value[field]))
    }
  }
}

// ==================== 模型信息加载 ====================
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

async function loadEnsembleComparison() {
  if (ensembleComparison.value) return
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

function getEnsembleMetrics() {
  const comparison = ensembleComparison.value
  if (!comparison) return null
  const bsMetrics = comparison?.blood_sugar || {}
  const dmMetrics = comparison?.diabetes || {}
  return {
    bsSingle: bsMetrics?.single || {},
    bsEnsemble: bsMetrics?.ensemble || {},
    dmSingle: dmMetrics?.single || {},
    dmEnsemble: dmMetrics?.ensemble || {},
  }
}

// ==================== 辅助功能 ====================
async function fillBloodSugarMeans() {
  try {
    const means = await getBloodSugarMeans()
    Object.assign(bsForm.value, means)
    ElMessage.success('已填充样本均值')
  } catch (e) {
    ElMessage.error('加载样本均值失败')
  }
}

function resetBloodSugarForm() {
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

// ==================== 摘要计算 ====================
const summaryFields = computed(() => {
  if (!selectedTask.value) return []
  if (selectedTask.value === 'blood_sugar') {
    return bsGroups.flatMap(g => g.fields).map(f => ({
      group: bsGroups.find(g => g.fields.includes(f))?.title || '',
      field: f,
      value: bsForm.value[f] ?? '--'
    }))
  }
  return dmFields.map(f => ({
    group: '临床指标',
    field: f.label,
    value: dmForm.value[f.key] ?? '--'
  }))
})

// ==================== 生命周期 ====================
onMounted(() => {
  loadModelInfo()
})
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

    <!-- 步骤条 -->
    <div class="card mb-6 p-6">
      <el-steps :active="wizardStep" finish-status="success" align-center>
        <el-step title="选择任务" description="血糖 / 糖尿病" />
        <el-step title="填写指标" description="临床数据输入" />
        <el-step title="确认数据" description="检查特征" />
        <el-step title="模型预测" description="选择模型" />
        <el-step title="查看结果" description="风险解读" />
      </el-steps>
    </div>

    <!-- ==================== Step 1：选择预测任务 ==================== -->
    <div v-if="wizardStep === 1" class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
      <div
        @click="selectTask('blood_sugar')"
        class="card p-8 cursor-pointer hover:-translate-y-1 transition-all duration-300 group"
      >
        <div class="flex flex-col items-center text-center gap-4">
          <div class="w-20 h-20 bg-gradient-to-br from-primary-100 to-medical-100 rounded-3xl flex items-center justify-center group-hover:shadow-glow transition-all duration-300">
            <el-icon :size="40" class="text-primary-600">
              <DataLine />
            </el-icon>
          </div>
          <div>
            <h2 class="text-2xl font-bold text-slate-800 mb-2">体检血糖预测</h2>
            <p class="text-slate-500">输入体检检验指标，预测空腹血糖值（mmol/L）</p>
          </div>
          <div class="flex items-center gap-2 text-primary-600 font-semibold">
            <span>开始预测</span>
            <el-icon :size="18"><ArrowRight /></el-icon>
          </div>
        </div>
      </div>

      <div
        @click="selectTask('diabetes')"
        class="card p-8 cursor-pointer hover:-translate-y-1 transition-all duration-300 group"
      >
        <div class="flex flex-col items-center text-center gap-4">
          <div class="w-20 h-20 bg-gradient-to-br from-medical-100 to-success-100 rounded-3xl flex items-center justify-center group-hover:shadow-glow transition-all duration-300">
            <el-icon :size="40" class="text-medical-600">
              <TrendCharts />
            </el-icon>
          </div>
          <div>
            <h2 class="text-2xl font-bold text-slate-800 mb-2">妊娠期糖尿病预测</h2>
            <p class="text-slate-500">输入妊娠期临床指标，预测 GDM 患病风险</p>
          </div>
          <div class="flex items-center gap-2 text-medical-600 font-semibold">
            <span>开始预测</span>
            <el-icon :size="18"><ArrowRight /></el-icon>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== Step 2：填写临床指标 ==================== -->
    <div v-if="wizardStep === 2" class="card p-6 mb-6">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-xl font-bold text-slate-800">
            {{ selectedTask === 'blood_sugar' ? '体检血糖预测' : '妊娠期糖尿病预测' }}
          </h2>
          <p class="text-slate-500 text-sm mt-1">请填写以下临床指标，带 * 为必填项</p>
        </div>
        <button @click="prevStep" class="btn-secondary flex items-center gap-2">
          <el-icon :size="16"><ArrowLeft /></el-icon>
          返回选择
        </button>
      </div>

      <!-- 血糖表单 -->
      <div v-if="selectedTask === 'blood_sugar'" class="space-y-6">
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
              <div v-for="field in group.fields" :key="field" class="space-y-2">
                <label class="text-sm font-semibold text-slate-600">
                  {{ field }}
                  <span v-if="field === '年龄' || field === '性别'" class="text-danger-500">*</span>
                </label>
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
                  :step="BS_INTEGER_FIELDS.has(field) ? 1 : 0.01"
                  v-model.number="bsForm[field]"
                  class="input-field"
                  :placeholder="`请输入 ${field}`"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 糖尿病表单 -->
      <div v-else class="space-y-4">
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          <div v-for="field in dmFields" :key="field.key" class="space-y-2">
            <label class="text-sm font-semibold text-slate-600">
              {{ field.label }}
              <span v-if="['年龄', '身高', '孕前体重'].includes(field.key)" class="text-danger-500">*</span>
            </label>
            <input
              type="number"
              :step="field.integer ? 1 : 0.01"
              v-model.number="dmForm[field.key]"
              class="input-field"
              :placeholder="`请输入 ${field.label}`"
            />
          </div>
        </div>
      </div>

      <!-- 底部操作栏 -->
      <div class="mt-8 pt-6 border-t-2 border-slate-100 flex items-center justify-between">
        <button @click="prevStep" class="btn-secondary flex items-center gap-2">
          <el-icon :size="18"><ArrowLeft /></el-icon>
          上一步
        </button>
        <div class="flex items-center gap-3">
          <button
            v-if="selectedTask === 'blood_sugar'"
            @click="fillBloodSugarMeans"
            class="btn-secondary flex items-center gap-2"
          >
            <el-icon :size="18"><MagicStick /></el-icon>
            填充样本均值
          </button>
          <button
            v-if="selectedTask === 'blood_sugar'"
            @click="resetBloodSugarForm"
            class="btn-secondary flex items-center gap-2"
          >
            <el-icon :size="18"><Refresh /></el-icon>
            重置
          </button>
          <button
            v-if="selectedTask === 'diabetes'"
            @click="resetDiabetesForm"
            class="btn-secondary flex items-center gap-2"
          >
            <el-icon :size="18"><Refresh /></el-icon>
            重置
          </button>
          <button @click="nextStep" class="btn-primary flex items-center gap-2">
            下一步
            <el-icon :size="18"><ArrowRight /></el-icon>
          </button>
        </div>
      </div>
    </div>

    <!-- ==================== Step 3：确认特征摘要 ==================== -->
    <div v-if="wizardStep === 3" class="card p-6 mb-6">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-xl font-bold text-slate-800">确认特征数据</h2>
          <p class="text-slate-500 text-sm mt-1">请检查以下数据是否正确，如有错误请返回修改</p>
        </div>
        <button @click="prevStep" class="btn-secondary flex items-center gap-2">
          <el-icon :size="16"><ArrowLeft /></el-icon>
          返回修改
        </button>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-slate-200">
              <th class="text-left py-3 px-4 text-slate-500 font-medium">分组</th>
              <th class="text-left py-3 px-4 text-slate-500 font-medium">指标</th>
              <th class="text-right py-3 px-4 text-slate-500 font-medium">数值</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in summaryFields" :key="item.field" class="border-b border-slate-50 hover:bg-slate-50">
              <td class="py-2.5 px-4 text-slate-500 text-xs">{{ item.group }}</td>
              <td class="py-2.5 px-4 text-slate-700 font-medium">{{ item.field }}</td>
              <td class="py-2.5 px-4 text-right font-mono text-slate-800">{{ item.value }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="mt-6 pt-6 border-t-2 border-slate-100 flex items-center justify-between">
        <button @click="prevStep" class="btn-secondary flex items-center gap-2">
          <el-icon :size="18"><ArrowLeft /></el-icon>
          上一步
        </button>
        <button @click="nextStep" class="btn-primary flex items-center gap-2">
          确认无误，下一步
          <el-icon :size="18"><ArrowRight /></el-icon>
        </button>
      </div>
    </div>

    <!-- ==================== Step 4：选择模型并预测 ==================== -->
    <div v-if="wizardStep === 4" class="card p-6 mb-6">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-xl font-bold text-slate-800">选择预测模型</h2>
          <p class="text-slate-500 text-sm mt-1">
            当前任务：{{ selectedTask === 'blood_sugar' ? '体检血糖预测' : '妊娠期糖尿病预测' }}
          </p>
        </div>
        <button @click="prevStep" class="btn-secondary flex items-center gap-2">
          <el-icon :size="16"><ArrowLeft /></el-icon>
          返回修改
        </button>
      </div>

      <div class="max-w-2xl mx-auto space-y-6">
        <div class="bg-slate-50 rounded-2xl p-6 border border-slate-100">
          <div class="flex items-center justify-between mb-4">
            <div class="text-sm text-slate-600 font-medium">模型选择</div>
            <el-radio-group v-if="selectedTask === 'blood_sugar'" v-model="useEnsemble" size="small">
              <el-radio-button :value="false">单模型 (LightGBM)</el-radio-button>
              <el-radio-button :value="true">融合模型 (LightGBM + XGBoost)</el-radio-button>
            </el-radio-group>
            <el-radio-group v-else v-model="useEnsembleDiabetes" size="small">
              <el-radio-button :value="false">单模型 (LightGBM)</el-radio-button>
              <el-radio-button :value="true">融合模型 (LightGBM + XGBoost)</el-radio-button>
            </el-radio-group>
          </div>

          <div class="bg-white rounded-xl p-4 border border-slate-100 mb-4">
            <p class="text-xs text-slate-500 leading-relaxed">
              <span v-if="selectedTask === 'blood_sugar'">
                <strong>单模型：</strong>使用 LightGBM 回归模型直接预测血糖值，RMSE ≈ 1.33 mmol/L。
                <br/>
                <strong>融合模型：</strong>采用 Stacking 集成策略，第一层由 LightGBM 和 XGBoost 组成，第二层使用 Ridge 回归融合，期望进一步提升预测精度。
              </span>
              <span v-else>
                <strong>单模型：</strong>使用 LightGBM 分类模型预测糖尿病风险，AUC ≈ 0.73。
                <br/>
                <strong>融合模型：</strong>采用 Stacking 集成策略，第一层由 LightGBM 和 XGBoost 组成，第二层使用 Logistic Regression 融合，期望提升分类性能。
              </span>
            </p>
          </div>

          <button
            @click="selectedTask === 'blood_sugar' ? handleBloodSugarPredict() : handleDiabetesPredict()"
            :disabled="loading"
            class="btn-primary w-full flex items-center justify-center gap-3 text-lg py-4"
          >
            <el-icon v-if="loading" class="animate-spin">
              <Loading />
            </el-icon>
            <Promotion v-else :size="22" />
            {{ loading ? '预测中...' : '开始预测' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ==================== Step 5：查看结果 ==================== -->
    <div v-if="wizardStep === 5" class="card p-6 mb-6">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-xl font-bold text-slate-800">预测结果</h2>
          <p class="text-slate-500 text-sm mt-1">
            {{ selectedTask === 'blood_sugar' ? '血糖预测结果及医学解读' : '糖尿病风险预测结果及医学解读' }}
          </p>
        </div>
        <div class="flex items-center gap-3">
          <button @click="goToPredict" class="btn-secondary flex items-center gap-2">
            <el-icon :size="16"><ArrowLeft /></el-icon>
            更换模型
          </button>
          <button @click="resetWizard" class="btn-secondary flex items-center gap-2">
            <el-icon :size="16"><Refresh /></el-icon>
            重新预测
          </button>
        </div>
      </div>

      <!-- 血糖结果 -->
      <div v-if="selectedTask === 'blood_sugar' && bsResult" class="space-y-6">
        <div class="flex items-center justify-between mb-4 gap-2">
          <div class="flex items-center gap-2">
            <h3 class="text-base font-bold text-slate-800">预测结果</h3>
            <span
              class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold"
              :class="useEnsemble ? 'bg-medical-50 text-medical-700 border border-medical-200' : 'bg-slate-50 text-slate-600 border border-slate-200'"
            >
              {{ useEnsemble ? '融合模型' : '单模型' }}
            </span>
          </div>
          <div class="inline-flex bg-slate-100 p-1 rounded-xl">
            <button
              @click="activeResultTab = 'result'"
              :class="[
                'px-3 py-1.5 rounded-lg text-xs font-semibold transition-all',
                activeResultTab === 'result' ? 'bg-white text-primary-600 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              ]"
            >预测结果</button>
            <button
              @click="activeResultTab = 'comparison'"
              :class="[
                'px-3 py-1.5 rounded-lg text-xs font-semibold transition-all',
                activeResultTab === 'comparison' ? 'bg-white text-primary-600 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              ]"
            >模型对比</button>
            <button
              @click="activeResultTab = 'features'"
              :class="[
                'px-3 py-1.5 rounded-lg text-xs font-semibold transition-all',
                activeResultTab === 'features' ? 'bg-white text-primary-600 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              ]"
            >特征解释</button>
          </div>
        </div>

        <!-- 预测结果 -->
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

        <!-- 模型对比 -->
        <div v-else-if="activeResultTab === 'comparison'" class="space-y-4">
          <div v-if="!ensembleComparison" class="text-center py-6">
            <p class="text-sm text-slate-500 mb-3">加载模型对比数据...</p>
            <button @click="loadEnsembleComparison" :disabled="ensembleLoading" class="btn-secondary text-sm">
              {{ ensembleLoading ? '加载中...' : '重新加载对比数据' }}
            </button>
          </div>
          <div v-else-if="getEnsembleMetrics()" class="space-y-4">
            <div class="bg-slate-50 rounded-xl p-4 border border-slate-100">
              <h4 class="text-sm font-bold text-slate-700 mb-3">血糖预测模型对比 (RMSE / R²)</h4>
              <div class="overflow-x-auto">
                <table class="w-full text-sm">
                  <thead>
                    <tr class="border-b border-slate-200">
                      <th class="text-left py-2 px-2 text-slate-500 font-medium">指标</th>
                      <th class="text-center py-2 px-2 text-slate-600 font-medium">单模型 (LightGBM)</th>
                      <th class="text-center py-2 px-2 text-medical-700 font-medium">融合模型 (Stacking)</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr class="border-b border-slate-100">
                      <td class="py-2 px-2 text-slate-600">RMSE</td>
                      <td class="py-2 px-2 text-center font-mono">{{ getEnsembleMetrics().bsSingle.rmse ?? '--' }}</td>
                      <td class="py-2 px-2 text-center font-mono text-medical-700 font-bold">{{ getEnsembleMetrics().bsEnsemble.rmse ?? '--' }}</td>
                    </tr>
                    <tr class="border-b border-slate-100">
                      <td class="py-2 px-2 text-slate-600">R²</td>
                      <td class="py-2 px-2 text-center font-mono">{{ getEnsembleMetrics().bsSingle.r2 ?? '--' }}</td>
                      <td class="py-2 px-2 text-center font-mono text-medical-700 font-bold">{{ getEnsembleMetrics().bsEnsemble.r2 ?? '--' }}</td>
                    </tr>
                    <tr>
                      <td class="py-2 px-2 text-slate-600">MAE</td>
                      <td class="py-2 px-2 text-center font-mono">{{ getEnsembleMetrics().bsSingle.mae ?? '--' }}</td>
                      <td class="py-2 px-2 text-center font-mono text-medical-700 font-bold">{{ getEnsembleMetrics().bsEnsemble.mae ?? '--' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p class="text-xs text-slate-400 mt-3">融合模型通过 Stacking 集成 LightGBM + XGBoost，期望在 RMSE 和 R² 上优于单模型</p>
            </div>
          </div>
          <div v-else class="text-center py-6">
            <p class="text-sm text-slate-500">暂无对比数据，请先训练融合模型</p>
          </div>
        </div>

        <!-- 特征解释 -->
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

      <!-- 糖尿病结果 -->
      <div v-if="selectedTask === 'diabetes' && dmResult" class="space-y-6">
        <div class="flex items-center justify-between mb-4 gap-2">
          <div class="flex items-center gap-2">
            <h3 class="text-base font-bold text-slate-800">预测结果</h3>
            <span
              class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold"
              :class="useEnsembleDiabetes ? 'bg-medical-50 text-medical-700 border border-medical-200' : 'bg-slate-50 text-slate-600 border border-slate-200'"
            >
              {{ useEnsembleDiabetes ? '融合模型' : '单模型' }}
            </span>
          </div>
          <div class="inline-flex bg-slate-100 p-1 rounded-xl">
            <button
              @click="activeResultTab = 'result'"
              :class="[
                'px-3 py-1.5 rounded-lg text-xs font-semibold transition-all',
                activeResultTab === 'result' ? 'bg-white text-primary-600 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              ]"
            >预测结果</button>
            <button
              @click="activeResultTab = 'comparison'"
              :class="[
                'px-3 py-1.5 rounded-lg text-xs font-semibold transition-all',
                activeResultTab === 'comparison' ? 'bg-white text-primary-600 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              ]"
            >模型对比</button>
            <button
              @click="activeResultTab = 'model'"
              :class="[
                'px-3 py-1.5 rounded-lg text-xs font-semibold transition-all',
                activeResultTab === 'model' ? 'bg-white text-primary-600 shadow-sm' : 'text-slate-600 hover:text-slate-900'
              ]"
            >模型评估</button>
          </div>
        </div>

        <!-- 预测结果 -->
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

        <!-- 模型对比 -->
        <div v-else-if="activeResultTab === 'comparison'" class="space-y-4">
          <div v-if="!ensembleComparison" class="text-center py-6">
            <p class="text-sm text-slate-500 mb-3">加载模型对比数据...</p>
            <button @click="loadEnsembleComparison" :disabled="ensembleLoading" class="btn-secondary text-sm">
              {{ ensembleLoading ? '加载中...' : '重新加载对比数据' }}
            </button>
          </div>
          <div v-else-if="getEnsembleMetrics()" class="space-y-4">
            <div class="bg-slate-50 rounded-xl p-4 border border-slate-100">
              <h4 class="text-sm font-bold text-slate-700 mb-3">糖尿病预测模型对比 (AUC / Accuracy / F1)</h4>
              <div class="overflow-x-auto">
                <table class="w-full text-sm">
                  <thead>
                    <tr class="border-b border-slate-200">
                      <th class="text-left py-2 px-2 text-slate-500 font-medium">指标</th>
                      <th class="text-center py-2 px-2 text-slate-600 font-medium">单模型 (LightGBM)</th>
                      <th class="text-center py-2 px-2 text-medical-700 font-medium">融合模型 (Stacking)</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr class="border-b border-slate-100">
                      <td class="py-2 px-2 text-slate-600">AUC</td>
                      <td class="py-2 px-2 text-center font-mono">{{ (getEnsembleMetrics().dmSingle.auc * 100)?.toFixed(1) ?? '--' }}%</td>
                      <td class="py-2 px-2 text-center font-mono text-medical-700 font-bold">{{ (getEnsembleMetrics().dmEnsemble.auc * 100)?.toFixed(1) ?? '--' }}%</td>
                    </tr>
                    <tr class="border-b border-slate-100">
                      <td class="py-2 px-2 text-slate-600">Accuracy</td>
                      <td class="py-2 px-2 text-center font-mono">{{ (getEnsembleMetrics().dmSingle.accuracy * 100)?.toFixed(1) ?? '--' }}%</td>
                      <td class="py-2 px-2 text-center font-mono text-medical-700 font-bold">{{ (getEnsembleMetrics().dmEnsemble.accuracy * 100)?.toFixed(1) ?? '--' }}%</td>
                    </tr>
                    <tr class="border-b border-slate-100">
                      <td class="py-2 px-2 text-slate-600">Precision</td>
                      <td class="py-2 px-2 text-center font-mono">{{ (getEnsembleMetrics().dmSingle.precision * 100)?.toFixed(1) ?? '--' }}%</td>
                      <td class="py-2 px-2 text-center font-mono text-medical-700 font-bold">{{ (getEnsembleMetrics().dmEnsemble.precision * 100)?.toFixed(1) ?? '--' }}%</td>
                    </tr>
                    <tr class="border-b border-slate-100">
                      <td class="py-2 px-2 text-slate-600">Recall</td>
                      <td class="py-2 px-2 text-center font-mono">{{ (getEnsembleMetrics().dmSingle.recall * 100)?.toFixed(1) ?? '--' }}%</td>
                      <td class="py-2 px-2 text-center font-mono text-medical-700 font-bold">{{ (getEnsembleMetrics().dmEnsemble.recall * 100)?.toFixed(1) ?? '--' }}%</td>
                    </tr>
                    <tr>
                      <td class="py-2 px-2 text-slate-600">F1</td>
                      <td class="py-2 px-2 text-center font-mono">{{ (getEnsembleMetrics().dmSingle.f1 * 100)?.toFixed(1) ?? '--' }}%</td>
                      <td class="py-2 px-2 text-center font-mono text-medical-700 font-bold">{{ (getEnsembleMetrics().dmEnsemble.f1 * 100)?.toFixed(1) ?? '--' }}%</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p class="text-xs text-slate-400 mt-3">融合模型通过 Stacking 集成 LightGBM + XGBoost，期望在 AUC 和 F1 上优于单模型</p>
            </div>
          </div>
          <div v-else class="text-center py-6">
            <p class="text-sm text-slate-500">暂无对比数据，请先训练融合模型</p>
          </div>
        </div>

        <!-- 模型评估 -->
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
    </div>
  </div>
</template>

<style scoped>
.predict-page {
  max-width: 1600px;
  margin: 0 auto;
}
</style>
