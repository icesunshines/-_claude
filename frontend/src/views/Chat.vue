<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { chat } from '../api/request'
import { ChatDotRound, Promotion, User, Refresh, Document, Menu, Close } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
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
const creatingSession = ref(false)
const showAllQuickQuestions = ref(true)

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
  if (sessions.value.length === 0) {
    await ensureCurrentSession()
  } else if (!currentSessionId.value) {
    await loadSession(sessions.value[0].id)
  }
})

async function loadSessions() {
  try {
    const res = await fetch('/api/chat/sessions', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    })
    if (res.ok) {
      sessions.value = await res.json()
    }
  } catch (e) {
    console.error('加载会话列表失败:', e)
  }
}

async function ensureCurrentSession() {
  if (currentSessionId.value) {
    return currentSessionId.value
  }

  await loadSessions()
  const blankSession = sessions.value.find(s => s.title === '新对话')
  if (blankSession) {
    await loadSession(blankSession.id)
    return blankSession.id
  }

  const res = await fetch('/api/chat/sessions', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
  })
  if (res.ok) {
    const session = await res.json()
    await loadSessions()
    await loadSession(session.id)
    return session.id
  }

  return null
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
  if (creatingSession.value) return
  creatingSession.value = true
  try {
    await loadSessions()

    // 优先复用已有的空白"新对话"
    const blankSession = sessions.value.find(s => s.title === '新对话')
    if (blankSession) {
      // 如果当前已经是这个空白会话且无消息，直接返回
      if (currentSessionId.value === blankSession.id && messages.value.length === 0) {
        return
      }
      // 尝试加载这个空白会话，如果失败则创建新的
      await loadSession(blankSession.id)
      // loadSession 失败时 currentSessionId 不会变，需要创建新的
      if (!currentSessionId.value) {
        return await _doCreateSession()
      }
      return
    }

    // 没有空白会话时创建新的
    return await _doCreateSession()
  } finally {
    creatingSession.value = false
  }
}

async function _doCreateSession() {
  const res = await fetch('/api/chat/sessions', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
  })
  if (res.ok) {
    const session = await res.json()
    await loadSessions()
    await loadSession(session.id)
  }
}

async function sendMessage() {
  if (!input.value.trim() || loading.value) return

  // 确保有当前会话
  if (!currentSessionId.value) {
    await createNewSession()
    // 如果创建/加载仍然失败，不再发送
    if (!currentSessionId.value) {
      ElMessage.error('请先创建或选择一个对话')
      return
    }
  }

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
  // 快照当前会话ID，防止并发问题
  const activeSessionId = currentSessionId.value
  const token = localStorage.getItem('token')

  try {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        message: userMessageText,
        session_id: activeSessionId
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

    if (currentSessionId.value === activeSessionId) {
      const trimmed = userMessageText.slice(0, 20) + (userMessageText.length > 20 ? '...' : '')
      const session = sessions.value.find(s => s.id === currentSessionId.value)
      if (session && session.title === '新对话') {
        session.title = trimmed
      }
      await loadSessions()
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
    await ElMessageBox.confirm('确定删除该对话吗？删除后将无法恢复。', '删除对话', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const res = await fetch(`/api/chat/sessions/${sessionId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    })
    if (!res.ok) {
      const text = await res.text()
      throw new Error(text || '删除失败')
    }
    sessions.value = sessions.value.filter(s => s.id !== sessionId)
    if (currentSessionId.value === sessionId) {
      if (sessions.value.length > 0) {
        await loadSession(sessions.value[0].id)
      } else {
        await createNewSession()
      }
    }
    ElMessage.success('对话已删除')
  } catch (e) {
    if (e !== 'cancel') {
      console.error('删除会话失败:', e)
      ElMessage.error('删除失败')
    }
  }
}
</script>

<template>
  <div class="chat-page flex gap-0">
    <!-- 左侧会话列表 -->
    <div v-if="showSidebar" class="sidebar w-64 bg-slate-50 border-r border-slate-200 flex flex-col min-h-0">
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
    <div class="flex-1 flex flex-col min-h-0 overflow-hidden">
      <div class="flex flex-col min-h-0 flex-1 bg-white">
        <!-- 顶部标题栏 -->
        <div class="bg-white px-4 py-2.5 flex items-center justify-between border-b border-slate-100 flex-shrink-0">
          <div class="flex items-center gap-3">
            <button @click="showSidebar = !showSidebar" class="hover:bg-slate-100 p-2 rounded-lg transition-colors">
              <el-icon :size="18" class="text-slate-600"><Menu /></el-icon>
            </button>
            <div>
              <h2 class="text-base font-bold text-slate-800 leading-tight">智能健康助手</h2>
              <p class="text-xs text-slate-400 leading-tight">基于大模型医疗知识库</p>
            </div>
          </div>
        </div>

        <!-- 快捷问题标签 -->
        <div class="bg-white px-4 py-2 border-b border-slate-100 flex-shrink-0">
          <div class="flex flex-wrap gap-2" :class="messages.length === 0 ? '' : 'max-h-[40px] overflow-hidden transition-all duration-300'">
            <template v-if="showAllQuickQuestions || messages.length === 0">
              <button
                v-for="q in quickQuestions"
                :key="q"
                @click="quickQuestion(q)"
                class="px-3 py-1.5 bg-white border border-primary-200 text-primary-700 rounded-full hover:bg-primary-50 hover:border-primary-300 transition-all text-xs whitespace-nowrap"
              >
                {{ q }}
              </button>
            </template>
            <button
              v-if="messages.length > 0 && quickQuestions.length > 3"
              @click="showAllQuickQuestions = !showAllQuickQuestions"
              class="px-3 py-1.5 bg-white border border-slate-200 text-slate-500 rounded-full hover:bg-slate-50 hover:border-slate-300 transition-all text-xs whitespace-nowrap"
            >
              {{ showAllQuickQuestions ? '收起' : '更多' }}
            </button>
          </div>
        </div>

        <!-- 消息区 -->
        <div
          ref="messagesContainer"
          class="messages-container flex-1 overflow-y-auto px-3 py-3 bg-slate-50/50 min-h-0"
        >
          <!-- 空状态占位 -->
          <div v-if="!messages.length && !loading" class="h-full min-h-0 flex items-center justify-center">
            <div class="text-center text-slate-400">
              <div class="w-16 h-16 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-3">
                <el-icon :size="32" class="text-primary-400">
                  <ChatDotRound />
                </el-icon>
              </div>
              <p class="text-base font-medium text-slate-600 mb-1">开始对话</p>
              <p class="text-xs text-slate-400 max-w-xs leading-relaxed">
                请选择左侧会话或直接提问，<br/>我将基于医疗知识库为您解答健康问题。
              </p>
            </div>
          </div>

          <div v-if="messages.length" class="space-y-2.5">
            <div
              v-for="msg in messages"
              :key="msg.id"
              class="message-item flex"
              :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
            >
              <div
                class="message-bubble max-w-[75%]"
                :class="msg.role === 'user'
                  ? 'bg-gradient-to-r from-primary-500 to-medical-500 text-white rounded-xl rounded-tr-sm'
                  : 'bg-white border border-slate-200 text-slate-800 rounded-xl rounded-tl-sm'"
              >
                <div class="flex items-start gap-2">
                  <div
                    class="w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0"
                    :class="msg.role === 'user' ? 'bg-primary-600' : 'bg-slate-100'"
                  >
                    <el-icon :size="14" :class="msg.role === 'user' ? 'text-white' : 'text-primary-600'">
                      <User v-if="msg.role === 'user'" />
                      <ChatDotRound v-else />
                    </el-icon>
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="message-content text-[13px] leading-relaxed" v-html="msg.html"></div>
                    <div class="text-[11px] mt-1 opacity-60">
                      {{ msg.timestamp }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="loading" class="flex justify-start">
              <div class="bg-white border border-slate-200 text-slate-800 rounded-xl rounded-tl-sm px-3 py-2 flex items-center gap-2">
                <el-icon class="animate-spin text-primary-600" :size="16">
                  <Refresh />
                </el-icon>
                <span class="text-slate-500 text-xs">正在思考...</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区 -->
        <div class="border-t border-slate-200 px-3 py-2.5 bg-white flex-shrink-0">
          <div class="flex gap-2">
            <input
              v-model="input"
              @keyup.enter="sendMessage"
              type="text"
              :disabled="loading"
              placeholder="请输入健康问题..."
              class="input-field flex-1 text-sm py-2.5 px-3"
            />
            <button
              @click="sendMessage"
              :disabled="loading"
              class="btn-primary px-4 flex items-center gap-1.5 text-sm py-2.5"
            >
              <el-icon :size="16"><Promotion /></el-icon>
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
  display: flex;
  height: calc(100vh - 56px);
  width: 100%;
  overflow: hidden;
}

.sidebar {
  width: 260px;
  min-width: 260px;
  height: 100%;
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
