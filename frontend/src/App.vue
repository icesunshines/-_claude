<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import {
  FirstAidKit,
  Sunny,
  Moon,
  User,
  SwitchButton,
  TrendCharts,
  DataLine,
  ChatLineRound,
  Setting
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const theme = ref(localStorage.getItem('theme') || 'dark')

// 顶栏导航标签
const navItems = computed(() => {
  const items = [
    { path: '/', label: '可视化大屏', icon: TrendCharts },
    { path: '/predict', label: '风险预测', icon: DataLine },
    { path: '/chat', label: '智能问答', icon: ChatLineRound },
  ]
  if (authStore.isAdmin) {
    items.push({ path: '/admin', label: '管理后台', icon: Setting })
  }
  return items
})

function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  document.documentElement.setAttribute('data-theme', theme.value)
  localStorage.setItem('theme', theme.value)
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

onMounted(() => {
  document.documentElement.setAttribute('data-theme', theme.value)
})
</script>

<template>
  <!-- 登录页：无顶栏 -->
  <div v-if="route.path === '/login'">
    <router-view />
  </div>

  <!-- 其他页面：顶栏 + 内容区 -->
  <div v-else class="min-h-screen bg-slate-50">
    <!-- 顶部导航栏 -->
    <header class="fixed top-0 left-0 right-0 h-14 bg-white/90 backdrop-blur-xl border-b border-slate-200 z-50">
      <div class="h-full flex items-center justify-between px-4 lg:px-6">
        <!-- 左侧：Logo + 导航标签 -->
        <div class="flex items-center gap-4 lg:gap-6">
          <!-- Logo -->
          <div class="flex items-center gap-2 cursor-pointer" @click="router.push('/')">
            <div class="w-9 h-9 bg-gradient-to-br from-primary-500 to-medical-500 rounded-xl flex items-center justify-center shadow-soft">
              <el-icon :size="20" color="white">
                <FirstAidKit />
              </el-icon>
            </div>
            <span class="hidden sm:block font-bold text-lg bg-gradient-to-r from-primary-600 to-medical-600 bg-clip-text text-transparent">
              医疗健康
            </span>
          </div>

          <!-- 导航标签 -->
          <nav class="hidden md:flex items-center gap-1">
            <router-link
              v-for="item in navItems"
              :key="item.path"
              :to="item.path"
              :class="[
                'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                route.path === item.path
                  ? 'bg-gradient-to-r from-primary-50 to-medical-50 text-primary-700 shadow-soft'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
              ]"
            >
              <el-icon :size="16" :class="route.path === item.path ? 'text-primary-600' : 'text-slate-400'">
                <component :is="item.icon" />
              </el-icon>
              {{ item.label }}
            </router-link>
          </nav>
        </div>

        <!-- 右侧：主题 + 用户信息 -->
        <div class="flex items-center gap-2 lg:gap-3">
          <button
            @click="toggleTheme"
            class="p-2 rounded-lg hover:bg-slate-100 transition-colors"
            title="切换主题"
          >
            <el-icon :size="18" class="text-slate-600">
              <Sunny v-if="theme === 'dark'" />
              <Moon v-else />
            </el-icon>
          </button>

          <div class="h-6 w-px bg-slate-200 hidden sm:block"></div>

          <!-- 用户头像 + 信息 -->
          <div class="flex items-center gap-2 cursor-pointer hover:bg-slate-50 rounded-lg px-2 py-1 transition-colors" @click="router.push('/profile')">
            <div class="w-8 h-8 bg-gradient-to-br from-primary-500 to-medical-500 rounded-lg flex items-center justify-center shadow-soft">
              <span class="text-white font-bold text-sm">
                {{ authStore.user?.username?.[0]?.toUpperCase() }}
              </span>
            </div>
            <div class="hidden lg:block">
              <p class="text-sm font-semibold text-slate-800 leading-tight">
                {{ authStore.user?.username }}
              </p>
              <p class="text-xs text-slate-500 leading-tight">
                {{ authStore.user?.role === 'admin' ? '系统管理员' : '普通用户' }}
              </p>
            </div>
          </div>

          <button
            @click="handleLogout"
            class="p-2 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-500 transition-colors"
            title="退出登录"
          >
            <el-icon :size="18">
              <SwitchButton />
            </el-icon>
          </button>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="pt-14">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
@keyframes pulse-slow {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
}

.animate-pulse-slow {
  animation: pulse-slow 3s ease-in-out infinite;
}
</style>
