<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { Lock, User, FirstAidKit, Loading, ArrowRight, View, Hide } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()
const isRegister = ref(false)
const username = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

function clearCache() {
  localStorage.clear()
  authStore.logout()
  error.value = '缓存已清理，请重新登录'
}

async function handleSubmit() {
  if (!username.value || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }
  
  loading.value = true
  error.value = ''
  
  try {
    if (isRegister.value) {
      await authStore.register(username.value, password.value)
      isRegister.value = false
    } else {
      // 1. 调用登录API
      const data = await authStore.login(username.value, password.value)
      console.log('✅ 登录成功，返回数据:', data)
      
      // 2. 确保本地存储保存成功
      if (data.role === 'admin') {
        localStorage.setItem('role', 'admin')
      }
      
      console.log('💾 本地存储检查:', {
        token: localStorage.getItem('token'),
        user: localStorage.getItem('user'),
        role: localStorage.getItem('role')
      })
      
      // 3. 强制跳转到首页 - 使用 window.location 确保跳转成功
      console.log('🚀 准备跳转到首页...')
      window.location.href = '/'
      return
    }
  } catch (e) {
    console.error('❌ 登录错误:', e)
    if (e.response?.data?.detail) {
      error.value = e.response.data.detail
    } else if (e.message) {
      error.value = e.message
    } else {
      error.value = '操作失败，请稍后重试'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-primary-50 via-medical-50 to-success-50 flex items-center justify-center p-4 overflow-hidden relative">
    <!-- 装饰元素 -->
    <div class="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
      <div class="absolute -top-20 -left-20 w-80 h-80 bg-primary-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-pulse-soft"></div>
      <div class="absolute top-1/3 -right-20 w-72 h-72 bg-medical-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-pulse-soft" style="animation-delay: 1s"></div>
      <div class="absolute -bottom-20 left-1/3 w-80 h-80 bg-success-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-pulse-soft" style="animation-delay: 2s"></div>
    </div>

    <div class="w-full max-w-md relative z-10">
      <!-- Logo 区域 -->
      <div class="text-center mb-8 animate-fade-in">
        <div class="inline-flex items-center justify-center w-24 h-24 bg-gradient-to-br from-primary-500 to-medical-500 rounded-3xl shadow-glow mb-6">
          <el-icon :size="48" color="white">
            <FirstAidKit />
          </el-icon>
        </div>
        <h1 class="text-3xl font-bold bg-gradient-to-r from-primary-600 to-medical-600 bg-clip-text text-transparent mb-2">
          医疗健康风险预测
        </h1>
        <p class="text-slate-500 text-lg">AI驱动的健康智能分析平台</p>
      </div>

      <!-- 登录卡片 -->
      <div class="glass-card p-8 animate-slide-up">
        <div class="text-center mb-8">
          <h2 class="text-2xl font-bold text-slate-800 mb-2">
            {{ isRegister ? '创建账户' : '欢迎回来' }}
          </h2>
          <p class="text-slate-500">
            {{ isRegister ? '开始您的健康之旅' : '继续您的健康监测' }}
          </p>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-6">
          <!-- 用户名 -->
          <div class="space-y-2">
            <label class="text-sm font-semibold text-slate-700">用户名</label>
            <div class="relative">
              <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none">
                <el-icon :size="20" class="text-slate-400">
                  <User />
                </el-icon>
              </div>
              <input
                v-model="username"
                type="text"
                class="input-field pl-12"
                :placeholder="isRegister ? '设置您的用户名' : '输入您的用户名'"
              />
            </div>
          </div>

          <!-- 密码 -->
          <div class="space-y-2">
            <label class="text-sm font-semibold text-slate-700">密码</label>
            <div class="relative">
              <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none">
                <el-icon :size="20" class="text-slate-400">
                  <Lock />
                </el-icon>
              </div>
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                class="input-field pl-12 pr-12"
                :placeholder="isRegister ? '设置您的密码' : '输入您的密码'"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute inset-y-0 right-4 flex items-center text-slate-400 hover:text-slate-600 transition-colors"
              >
                <el-icon v-if="showPassword" :size="20">
                  <Hide />
                </el-icon>
                <el-icon v-else :size="20">
                  <View />
                </el-icon>
              </button>
            </div>
          </div>

          <!-- 错误信息 -->
          <transition name="fade">
            <div v-if="error" class="bg-danger-50 border-2 border-danger-200 text-danger-600 px-5 py-4 rounded-xl text-sm font-medium">
              {{ error }}
            </div>
          </transition>

          <!-- 登录按钮 -->
          <button
            type="submit"
            :disabled="loading"
            class="btn-primary w-full flex items-center justify-center gap-3 text-lg"
          >
            <el-icon v-if="loading" class="animate-spin">
              <Loading />
            </el-icon>
            <span>{{ loading ? '处理中...' : (isRegister ? '注册' : '登录') }}</span>
            <el-icon v-if="!loading">
              <ArrowRight />
            </el-icon>
          </button>
        </form>

        <!-- 切换登录/注册 -->
        <div class="mt-8 text-center">
          <span class="text-slate-500">
            {{ isRegister ? '已有账户？' : '还没有账户？' }}
          </span>
          <button
            @click="isRegister = !isRegister; error = ''"
            class="ml-2 text-primary-600 hover:text-primary-700 font-semibold transition-colors"
          >
            {{ isRegister ? '立即登录' : '立即注册' }}
          </button>
        </div>

        <!-- 演示账号 -->
        <div class="mt-8 pt-6 border-t border-slate-200">
          <p class="text-xs text-slate-400 text-center mb-4 font-medium uppercase tracking-wider">演示账号</p>
          <div class="grid grid-cols-2 gap-3">
            <div class="bg-slate-50 rounded-xl p-4 text-center">
              <p class="text-sm font-semibold text-slate-700 mb-1">管理员</p>
              <p class="text-xs text-slate-500 font-mono">admin / admin123</p>
            </div>
            <div class="bg-slate-50 rounded-xl p-4 text-center">
              <p class="text-sm font-semibold text-slate-700 mb-1">普通用户</p>
              <p class="text-xs text-slate-500 font-mono">user / user123</p>
            </div>
          </div>
          
          <!-- 清理缓存按钮 -->
          <div class="mt-6 text-center">
            <button 
              @click="clearCache"
              class="text-xs text-slate-400 hover:text-slate-600 transition-colors"
            >
              点击这里清理缓存后重试
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
