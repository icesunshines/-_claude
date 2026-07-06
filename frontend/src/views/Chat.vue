<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { chat } from '../api/request'
import { ChatDotRound, Promotion, User, Refresh, MagicStick, Document, Menu, Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'

marked.setOptions({
  breaks: true,
  gfm: true,
})

const messages = ref([])
const input = ref('')
const loading = ref(false)
const messagesContainer = ref(null)
const currentSessionId = ref(null)
const sessions = ref([])
const showSidebar = ref(true)

const quickQuestions = [
  '如何预防糖尿病？',
  '血糖高应该注意什么？',
  '妊娠期糖尿病如何管理？',
  '体检血糖指标怎么解读？',
  '糖尿病患者饮食建议',
  '运动对血糖有什么影响？'
]

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

onMounted(async () => {
  scrollToBottom()
  await loadSessions()
})

async function loadSessions() {
  try {
    const res = await fetch('/api/chat/sessions', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    })
    if (res.ok) {
      sessions.value = await res.json()
      if (sessions.value.length > 0) {
        await loadSession(sessions.value[0].id)
      } else {
        await createNewSession()
      }
    }
  } catch (e) {
    console.error('加载会话列表失败:', e)
  }
}

async function loadSession(sessionId) {
  try {
    const res = await fetch(`/api/chat/sessions/${sessionId}/messages`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    })
    if (res.ok) {
      const msgs = await res.json()
      messages.value = msgs.map(m => ({
        id: Date.now() + Math.random(),
        role: m.role,
        content: m.content,
        html: m.role === 'user' ? m.content : marked.parse(m.content),
        timestamp: m.created_at
      }))
      currentSessionId.value = sessionId
      scrollToBottom()
    }
  } catch (e) {
    console.error('加载会话失败:', e)
  }
}

async function createNewSession() {
  try {
    const res = await fetch('/api/chat/sessions', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    })
    if (res.ok) {
      const session = await res.json()
      await loadSessions()
      await loadSession(session.id)
    }
  } catch (e) {
    console.error('创建会话失败:', e)
  }
}

async function sendMessage() {
  if (!input.value.trim() || loading.value) return

  const userMessageText = input.value.trim()
  input.value = ''

  const userMessage = {
    id: Date.now(),
    role: 'user',
    content: userMessageText,
    html: userMessageText,
    timestamp: new Date().toLocaleTimeString()
  }
  messages.value.push(userMessage)
  scrollToBottom()

  loading.value = true

  try {
    const token = localStorage.getItem('token')

    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        message: userMessageText,
        session_id: currentSessionId.value
      })
    })

    if (!response.ok) {
      throw new Error('请求失败')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let aiContent = ''

    const assistantMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      content: '',
      html: '',
      timestamp: new Date().toLocaleTimeString()
    }
    messages.value.push(assistantMessage)

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') continue

          try {
            const parsed = JSON.parse(data)
            aiContent += parsed.content
            assistantMessage.content = aiContent
            assistantMessage.html = marked.parse(aiContent)
            scrollToBottom()
          } catch (e) {
            console.error('解析流数据失败:', e)
          }
        }
      }
    }
  } catch (e) {
    console.error('发送消息失败:', e)
    ElMessage.error('发送消息失败，请稍后重试')
    const errorMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      content: '抱歉，发生了错误，请稍后再试。',
      html: '抱歉，发生了错误，请稍后再试。',
      timestamp: new Date().toLocaleTimeString()
    }
    messages.value.push(errorMessage)
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

function quickQuestion(question) {
  input.value = question
  sendMessage()
}

function clearChat() {
  messages.value = []
  createNewSession()
}

async function deleteSession(sessionId) {
  try {
    // TODO: 后端实现删除接口
    sessions.value = sessions.value.filter(s => s.id !== sessionId)
    if (currentSessionId.value === sessionId) {
      if (sessions.value.length > 0) {
        await loadSession(sessions.value[0].id)
      } else {
        await createNewSession()
      }
    }
  } catch (e) {
    console.error('删除会话失败:', e)
  }
}
</script>

<template>
  <div class="chat-page flex gap-0">
    <!-- 左侧会话列表 -->
    <div v-if="showSidebar" class="sidebar w-64 bg-slate-50 border-r border-slate-200 flex flex-col">
      <div class="p-4 border-b border-slate-200">
        <button @click="createNewSession" class="w-full btn-primary flex items-center justify-center gap-2">
          <el-icon><Document /></el-icon>
          <span>新对话</span>
        </button>
      </div>
      <div class="flex-1 overflow-y-auto p-2">
        <div
          v-for="session in sessions"
          :key="session.id"
          @click="loadSession(session.id)"
          class="session-item p-3 rounded-lg cursor-pointer mb-2 hover:bg-white transition-colors"
          :class="currentSessionId === session.id ? 'bg-white border border-primary-200' : 'border border-transparent'"
        >
          <div class="flex items-center justify-between">
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium text-slate-700 truncate">{{ session.title }}</div>
              <div class="text-xs text-slate-400 mt-1">{{ session.updated_at }}</div>
            </div>
            <button @click.stop="deleteSession(session.id)" class="text-slate-400 hover:text-red-500 ml-2">
              <el-icon :size="16"><Close /></el-icon>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧聊天区域 -->
    <div class="flex-1 flex flex-col">
      <div class="card p-0 overflow-hidden h-screen flex flex-col">
        <div class="bg-gradient-to-r from-primary-500 to-medical-500 p-4 text-white flex items-center justify-between">
          <div class="flex items-center gap-3">
            <button @click="showSidebar = !showSidebar" class="hover:bg-white/20 p-2 rounded-lg transition-colors">
              <el-icon :size="20"><Menu /></el-icon>
            </button>
            <div>
              <h2 class="text-xl font-bold">智能健康助手</h2>
              <p class="text-white/80 text-sm">为您提供健康咨询服务</p>
            </div>
          </div>
        </div>

        <div class="bg-slate-50 p-3 border-b border-slate-200">
          <div class="flex flex-wrap gap-2">
            <button
              v-for="q in quickQuestions"
              :key="q"
              @click="quickQuestion(q)"
              class="px-3 py-1.5 bg-white border border-primary-200 text-primary-700 rounded-lg hover:bg-primary-50 hover:border-primary-300 transition-all duration-300 text-sm"
            >
              {{ q }}
            </button>
          </div>
        </div>

        <div
          ref="messagesContainer"
          class="messages-container flex-1 overflow-y-auto p-4"
        >
          <div class="space-y-3">
            <div
              v-for="msg in messages"
              :key="msg.id"
              class="message-item flex"
              :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
            >
              <div
                class="message-bubble max-w-[70%]"
                :class="msg.role === 'user'
                  ? 'bg-gradient-to-r from-primary-500 to-medical-500 text-white rounded-xl rounded-tr-sm'
                  : 'bg-white border border-slate-200 text-slate-800 rounded-xl rounded-tl-sm'"
              >
                <div class="flex items-start gap-3">
                  <div
                    class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                    :class="msg.role === 'user' ? 'bg-primary-600' : 'bg-slate-100'"
                  >
                    <el-icon :size="16" :class="msg.role === 'user' ? 'text-white' : 'text-primary-600'">
                      <User v-if="msg.role === 'user'" />
                      <ChatDotRound v-else />
                    </el-icon>
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="message-content" v-html="msg.html"></div>
                    <div class="text-xs mt-1 opacity-70">
                      {{ msg.timestamp }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="loading" class="flex justify-start">
              <div class="bg-white border border-slate-200 text-slate-800 rounded-xl rounded-tl-sm p-3 flex items-center gap-2">
                <el-icon class="animate-spin text-primary-600" :size="18">
                  <Refresh />
                </el-icon>
                <span class="text-slate-500 text-sm">正在思考...</span>
              </div>
            </div>
          </div>
        </div>

        <div class="border-t border-slate-200 p-3 bg-slate-50">
          <div class="flex gap-3">
            <input
              v-model="input"
              @keyup.enter="sendMessage"
              type="text"
              :disabled="loading"
              placeholder="请输入您的问题..."
              class="input-field flex-1 text-base py-3 px-4"
            />
            <button
              @click="sendMessage"
              :disabled="loading"
              class="btn-primary px-6 flex items-center gap-2"
            >
              <el-icon :size="18"><Promotion /></el-icon>
              <span>发送</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-page {
  max-width: 1600px;
  margin: 0 auto;
  height: 100vh;
}

.sidebar {
  border-radius: 0;
}

.session-item:hover {
  background-color: #f8fafc;
}

.message-content :deep(p) {
  margin: 0.4em 0;
  line-height: 1.7;
}

.message-content :deep(p:first-child) {
  margin-top: 0;
}

.message-content :deep(p:last-child) {
  margin-bottom: 0;
}

.message-content :deep(strong) {
  font-weight: 600;
  color: #1a365d;
}

.message-content :deep(ul),
.message-content :deep(ol) {
  margin: 0.4em 0;
  padding-left: 1.5em;
}

.message-content :deep(li) {
  margin: 0.3em 0;
  line-height: 1.7;
}

.message-content :deep(code) {
  background: #f1f5f9;
  padding: 0.1em 0.3em;
  border-radius: 3px;
  font-size: 0.88em;
  font-family: 'Courier New', monospace;
}
</style>
