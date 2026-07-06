import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API 错误:', error)
    console.error('错误响应:', error.response)
    
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export async function login(username, password) {
  const params = new URLSearchParams()
  params.append('username', username)
  params.append('password', password)
  const res = await api.post('/auth/login', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })
  return res.data
}

export async function register(username, password) {
  const res = await api.post('/auth/register', { username, password, role: 'user' })
  return res.data
}

export async function getCurrentUser() {
  const res = await api.get('/auth/me')
  return res.data
}

export async function getStatsOverview() {
  const res = await api.get('/stats/overview')
  return res.data
}

export async function getBloodSugarStats() {
  const res = await api.get('/stats/blood-sugar')
  return res.data
}

export async function getBloodSugarMeans() {
  const res = await api.get('/stats/blood-sugar/means')
  return res.data
}

export async function getDiabetesStats() {
  const res = await api.get('/stats/diabetes')
  return res.data
}

export async function getFeatureImportance(modelType = 'blood_sugar') {
  const res = await api.get('/feature-importance', { params: { model_type: modelType } })
  return res.data
}

export async function predictBloodSugar(data) {
  const res = await api.post('/predict/blood-sugar', data)
  return res.data
}

export async function predictDiabetes(data) {
  const res = await api.post('/predict/diabetes', data)
  return res.data
}

export async function saveHistory(data) {
  const res = await api.post('/history', data)
  return res.data
}

export async function getHistory() {
  const res = await api.get('/history')
  return res.data
}

export async function getAdminStats() {
  const res = await api.get('/admin/dashboard')
  return res.data
}

export async function chat(message) {
  const res = await api.post('/chat', { message })
  return res.data
}

let realtimeAbortController = null

export function connectRealtimeStats(onMessage, onError) {
  disconnectRealtimeStats()
  realtimeAbortController = new AbortController()

  async function connect() {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/realtime/stats', {
        headers: { 'Authorization': `Bearer ${token}` },
        signal: realtimeAbortController.signal
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim()
            if (data && data !== '[DONE]') {
              try {
                const parsed = JSON.parse(data)
                if (onMessage) onMessage(parsed)
              } catch (e) {
                console.error('解析 SSE 数据失败:', e)
              }
            }
          }
        }
      }
    } catch (e) {
      if (e.name !== 'AbortError') {
        console.error('SSE 连接失败:', e)
        if (onError) onError(e)
        // 3秒后自动重连
        setTimeout(connect, 3000)
      }
    }
  }

  connect()
}

export function disconnectRealtimeStats() {
  if (realtimeAbortController) {
    realtimeAbortController.abort()
    realtimeAbortController = null
  }
}

export default api
