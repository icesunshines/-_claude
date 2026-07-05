<script setup>
import { ref, onMounted } from 'vue'
import { getAdminStats } from '../api/request'
import { User, Document, DataLine, CircleCheck, Calendar, FirstAidKit, Setting, TrendCharts, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const stats = ref(null)
const history = ref([])
const loading = ref(true)

async function loadData() {
  try {
    const data = await getAdminStats()
    stats.value = data.stats
    history.value = data.history || []
  } catch (e) {
    console.error('加载管理员数据失败:', e)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
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
</script>

<template>
  <div class="admin-page max-w-6xl mx-auto">
    <div class="card mb-6 p-6">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-gradient-to-br from-primary-500 to-medical-500 rounded-2xl flex items-center justify-center">
            <el-icon :size="24" color="white">
              <Setting />
            </el-icon>
          </div>
          <div>
            <h1 class="text-3xl font-bold text-slate-800">管理员面板</h1>
            <p class="text-slate-500 text-lg mt-1">系统运营数据与用户管理</p>
          </div>
        </div>
        <button
          @click="loadData"
          class="btn-secondary flex items-center gap-2"
        >
          <el-icon><Refresh /></el-icon>
          刷新数据
        </button>
      </div>
    </div>

    <div v-if="loading" class="py-24 text-center text-slate-400">
      <el-icon class="animate-spin" :size="48">
        <TrendCharts />
      </el-icon>
      <p class="mt-4 text-xl">加载中...</p>
    </div>

    <template v-else>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="stat-card card-hover p-6">
          <div class="flex items-center gap-4">
            <div class="w-14 h-14 bg-primary-100 rounded-2xl flex items-center justify-center border-2 border-primary-200">
              <el-icon :size="28" class="text-primary-600">
                <User />
              </el-icon>
            </div>
            <div>
              <p class="text-3xl font-bold text-slate-800 mb-1">{{ stats?.total_users || 0 }}</p>
              <p class="text-slate-500 font-medium text-lg">总用户数</p>
            </div>
          </div>
        </div>
        <div class="stat-card card-hover p-6">
          <div class="flex items-center gap-4">
            <div class="w-14 h-14 bg-success-100 rounded-2xl flex items-center justify-center border-2 border-success-200">
              <el-icon :size="28" class="text-success-600">
                <Document />
              </el-icon>
            </div>
            <div>
              <p class="text-3xl font-bold text-slate-800 mb-1">{{ stats?.total_predictions || 0 }}</p>
              <p class="text-slate-500 font-medium text-lg">总预测次数</p>
            </div>
          </div>
        </div>
        <div class="stat-card card-hover p-6">
          <div class="flex items-center gap-4">
            <div class="w-14 h-14 bg-warning-100 rounded-2xl flex items-center justify-center border-2 border-warning-200">
              <el-icon :size="28" class="text-warning-600">
                <CircleCheck />
              </el-icon>
            </div>
            <div>
              <p class="text-3xl font-bold text-slate-800 mb-1">{{ stats?.today_active || 0 }}</p>
              <p class="text-slate-500 font-medium text-lg">今日活跃</p>
            </div>
          </div>
        </div>
        <div class="stat-card card-hover p-6">
          <div class="flex items-center gap-4">
            <div class="w-14 h-14 bg-danger-100 rounded-2xl flex items-center justify-center border-2 border-danger-200">
              <el-icon :size="28" class="text-danger-600">
                <TrendCharts />
              </el-icon>
            </div>
            <div>
              <p class="text-3xl font-bold text-slate-800 mb-1">{{ stats?.accuracy || '0%' }}</p>
              <p class="text-slate-500 font-medium text-lg">模型准确率</p>
            </div>
          </div>
        </div>
      </div>

      <div class="card mb-6 p-6">
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 bg-primary-100 rounded-2xl flex items-center justify-center border-2 border-primary-200">
              <el-icon :size="24" class="text-primary-600">
                <User />
              </el-icon>
            </div>
            <div>
              <h3 class="text-xl font-bold text-slate-800">用户列表</h3>
              <p class="text-slate-500 text-sm mt-1">系统所有注册用户</p>
            </div>
          </div>
          <span class="text-base text-slate-500 font-medium">共 {{ stats?.users?.length || 0 }} 位用户</span>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b-2 border-slate-200">
                <th class="text-left py-4 px-4 text-sm font-bold text-slate-600 uppercase tracking-wider bg-slate-50 rounded-tl-xl">ID</th>
                <th class="text-left py-4 px-4 text-sm font-bold text-slate-600 uppercase tracking-wider bg-slate-50">用户名</th>
                <th class="text-left py-4 px-4 text-sm font-bold text-slate-600 uppercase tracking-wider bg-slate-50">角色</th>
                <th class="text-left py-4 px-4 text-sm font-bold text-slate-600 uppercase tracking-wider bg-slate-50">预测次数</th>
                <th class="text-left py-4 px-4 text-sm font-bold text-slate-600 uppercase tracking-wider bg-slate-50 rounded-tr-xl">注册时间</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="user in stats?.users || []" :key="user.id" class="hover:bg-slate-50 transition-colors">
                <td class="py-5 px-4 text-sm text-slate-800 font-medium">#{{ user.id }}</td>
                <td class="py-5 px-4">
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-gradient-to-br from-primary-500 to-medical-500 rounded-xl flex items-center justify-center flex-shrink-0">
                      <span class="text-white font-bold text-base">
                        {{ user.username?.[0]?.toUpperCase() }}
                      </span>
                    </div>
                    <span class="text-sm font-semibold text-slate-800">{{ user.username }}</span>
                  </div>
                </td>
                <td class="py-5 px-4">
                  <span
                    class="badge"
                    :class="[
                      user.role === 'admin'
                        ? 'bg-primary-100 text-primary-700'
                        : 'bg-success-100 text-success-700'
                    ]"
                  >
                    {{ user.role === 'admin' ? '管理员' : '用户' }}
                  </span>
                </td>
                <td class="py-5 px-4 text-sm text-slate-800 font-semibold">{{ user.prediction_count }}</td>
                <td class="py-5 px-4 text-sm text-slate-500">{{ formatDate(user.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card p-6">
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 bg-medical-100 rounded-2xl flex items-center justify-center border-2 border-medical-200">
              <el-icon :size="24" class="text-medical-600">
                <DataLine />
              </el-icon>
            </div>
            <div>
              <h3 class="text-xl font-bold text-slate-800">最近预测记录</h3>
              <p class="text-slate-500 text-sm mt-1">所有用户的最新预测活动</p>
            </div>
          </div>
          <span class="text-base text-slate-500 font-medium">最近 {{ Math.min(20, history.length) }} 条记录</span>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b-2 border-slate-200">
                <th class="text-left py-4 px-4 text-sm font-bold text-slate-600 uppercase tracking-wider bg-slate-50 rounded-tl-xl">ID</th>
                <th class="text-left py-4 px-4 text-sm font-bold text-slate-600 uppercase tracking-wider bg-slate-50">用户</th>
                <th class="text-left py-4 px-4 text-sm font-bold text-slate-600 uppercase tracking-wider bg-slate-50">类型</th>
                <th class="text-left py-4 px-4 text-sm font-bold text-slate-600 uppercase tracking-wider bg-slate-50">结果</th>
                <th class="text-left py-4 px-4 text-sm font-bold text-slate-600 uppercase tracking-wider bg-slate-50 rounded-tr-xl">时间</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="record in history.slice(0, 20)" :key="record.id" class="hover:bg-slate-50 transition-colors">
                <td class="py-5 px-4 text-sm text-slate-800 font-medium">#{{ record.id }}</td>
                <td class="py-5 px-4">
                  <div class="flex items-center gap-3">
                    <div class="w-8 h-8 bg-gradient-to-br from-primary-400 to-medical-400 rounded-lg flex items-center justify-center flex-shrink-0">
                      <span class="text-white font-bold text-xs">
                        {{ record.username?.[0]?.toUpperCase() }}
                      </span>
                    </div>
                    <span class="text-sm font-semibold text-slate-800">{{ record.username }}</span>
                  </div>
                </td>
                <td class="py-5 px-4">
                  <span
                    class="badge"
                    :class="[
                      record.type === 'blood_sugar'
                        ? 'bg-primary-100 text-primary-700'
                        : 'bg-medical-100 text-medical-700'
                    ]"
                  >
                    {{ record.type === 'blood_sugar' ? '血糖预测' : '糖尿病预测' }}
                  </span>
                </td>
                <td class="py-5 px-4 text-sm text-slate-800">
                  <span v-if="typeof record.result === 'string'">
                    {{ record.result }}
                  </span>
                  <span v-else-if="record.result.predicted_bgl !== undefined">
                    <span class="font-bold text-primary-700">{{ record.result.predicted_bgl }} mmol/L</span>
                    <span class="ml-2 text-slate-500">({{ record.result.risk_level }})</span>
                  </span>
                  <span v-else>
                    <span class="font-bold text-medical-700">{{ (record.result.probability * 100).toFixed(1) }}%</span>
                    <span class="ml-2 text-slate-500">({{ record.result.risk === 1 ? '高风险' : '低风险' }})</span>
                  </span>
                </td>
                <td class="py-5 px-4 text-sm text-slate-500">{{ formatDate(record.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.admin-page {
  max-width: 1600px;
  margin: 0 auto;
}
</style>
