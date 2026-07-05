import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, register as registerApi } from '../api/request'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(username, password) {
    const data = await loginApi(username, password)
    token.value = data.access_token
    user.value = { username, role: data.role }
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify(user.value))
    if (data.role === 'admin') {
      localStorage.setItem('role', 'admin')
    }
    return data
  }

  async function register(username, password, role = 'user') {
    return await registerApi(username, password, role)
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('role')
  }

  return { token, user, isLoggedIn, isAdmin, login, register, logout }
})
