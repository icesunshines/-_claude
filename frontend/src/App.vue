<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import {
  DataLine,
  DataAnalysis,
  User,
  Setting,
  Menu,
  Close,
  HomeFilled,
  SwitchButton,
  FirstAidKit,
  ChatLineRound,
  TrendCharts,
  Sunny,
  Moon
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const sidebarOpen = ref(true)
const mobileMenuOpen = ref(false)
const theme = ref(localStorage.getItem('theme') || 'dark')

function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  document.documentElement.setAttribute('data-theme', theme.value)
  localStorage.setItem('theme', theme.value)
}

const menuItems = computed(() => {
  const items = [
    { path: '/', icon: TrendCharts, label: '可视化大屏' },
    { path: '/predict', icon: DataLine, label: '风险预测' },
    { path: '/chat', icon: ChatLineRound, label: '智能问答' },
    { path: '/profile', icon: User, label: '个人中心' },
  ]
  if (authStore.isAdmin) {
    items.push({ path: '/admin', icon: Setting, label: '管理面板' })
  }
  return items
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function toggleSidebar() {
  if (window.innerWidth < 768) {
    mobileMenuOpen.value = !mobileMenuOpen.value
  } else {
    sidebarOpen.value = !sidebarOpen.value
  }
}

function handleResize() {
  if (window.innerWidth >= 768) {
    mobileMenuOpen.value = false
  }
}

onMounted(() => {
  document.documentElement.setAttribute('data-theme', theme.value)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div v-if="route.path === '/login'">
    <router-view />
  </div>

  <div v-else class="min-h-screen bg-slate-50">
    <div 
      v-if="mobileMenuOpen" 
      class="fixed inset-0 bg-black/40 z-40 md:hidden backdrop-blur-sm"
      @click="mobileMenuOpen = false"
    ></div>

    <aside 
      :class="[
        'fixed top-0 left-0 h-full bg-white border-r border-slate-200 z-50 transition-all duration-300 shadow-soft overflow-hidden',
        sidebarOpen ? 'w-72' : 'w-20',
        mobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
      ]"
    >
      <div class="h-20 flex items-center px-6 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-gradient-to-br from-primary-500 to-medical-500 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-glow animate-pulse-slow">
            <el-icon :size="28" color="white">
              <FirstAidKit />
            </el-icon>
          </div>
          <span v-show="sidebarOpen" class="font-bold text-xl bg-gradient-to-r from-primary-600 to-medical-600 bg-clip-text text-transparent">
            医疗健康
          </span>
        </div>
      </div>

      <nav class="p-4 space-y-2 overflow-y-auto max-h-[calc(100vh-160px)]">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          @click="mobileMenuOpen = false"
          :class="[
            'flex items-center gap-4 px-5 py-4 rounded-2xl transition-all duration-300 group relative',
            route.path === item.path 
              ? 'bg-gradient-to-r from-primary-50 to-medical-50 text-primary-700 shadow-soft border border-primary-100' 
              : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
          ]"
        >
          <div v-if="route.path === item.path" class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-gradient-to-b from-primary-500 to-medical-500 rounded-r-full"></div>
          <el-icon 
            :size="22" 
            :class="route.path === item.path ? 'text-primary-600' : 'text-slate-400 group-hover:text-primary-500 transition-colors'"
          >
            <component :is="item.icon" />
          </el-icon>
          <span v-show="sidebarOpen" class="font-semibold text-base">
            {{ item.label }}
          </span>
        </router-link>
      </nav>

      <div class="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-100 bg-slate-50">
        <button
          @click="handleLogout"
          class="w-full flex items-center gap-4 px-5 py-4 text-danger-600 hover:bg-danger-50 rounded-2xl transition-all duration-300 group"
        >
          <el-icon :size="22" class="text-danger-500">
            <SwitchButton />
          </el-icon>
          <span v-show="sidebarOpen" class="font-semibold">
            退出登录
          </span>
        </button>
      </div>
    </aside>

    <main 
      :class="[
        'transition-all duration-300 min-h-screen',
        sidebarOpen ? 'md:ml-72' : 'md:ml-20'
      ]"
    >
      <header class="sticky top-0 z-30 bg-white/80 backdrop-blur-xl border-b border-slate-200 shadow-soft">
        <div class="h-20 flex items-center justify-between px-6 md:px-8">
          <div class="flex items-center gap-5">
            <button 
              @click="toggleSidebar"
              class="p-3 hover:bg-slate-100 rounded-xl transition-all duration-300 text-slate-600 hover:text-primary-600 hover:shadow-soft"
            >
              <el-icon :size="24">
                <Menu v-if="!mobileMenuOpen" />
                <Close v-else />
              </el-icon>
            </button>
            <div>
              <h1 class="text-xl font-bold text-slate-800">
                {{ route.meta.title || '医疗健康系统' }}
              </h1>
              <p class="text-sm text-slate-500">
                为您的健康保驾护航
              </p>
            </div>
          </div>

          <div class="flex items-center gap-4">
            <button
              @click="toggleTheme"
              class="p-2 rounded-lg hover:bg-slate-100 transition-colors"
              title="切换主题"
            >
              <el-icon :size="20">
                <Sunny v-if="theme === 'dark'" />
                <Moon v-else />
              </el-icon>
            </button>

            <div class="flex items-center gap-4">
              <div class="w-12 h-12 bg-gradient-to-br from-primary-500 to-medical-500 rounded-2xl flex items-center justify-center shadow-soft hover:shadow-glow transition-shadow">
                <span class="text-white font-bold text-lg">
                  {{ authStore.user?.username?.[0]?.toUpperCase() }}
                </span>
              </div>
              <div class="hidden md:block">
                <p class="font-semibold text-slate-800">
                  {{ authStore.user?.username }}
                </p>
                <p class="text-sm text-slate-500">
                  {{ authStore.user?.role === 'admin' ? '系统管理员' : '普通用户' }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div class="p-6 md:p-8">
        <router-view />
      </div>
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
