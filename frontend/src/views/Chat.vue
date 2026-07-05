<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { chat } from '../api/request'
import { ChatDotRound, Promotion, User, Refresh, MagicStick } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const messages = ref([
  {
    id: 1,
    role: 'assistant',
    content: '您好！我是您的健康助手。我可以帮助您解答关于健康、血糖管理、糖尿病预防等方面的问题。请随时提问！',
    timestamp: new Date().toLocaleTimeString()
  }
])
const input = ref('')
const loading = ref(false)
const messagesContainer = ref(null)

const quickQuestions = [
  '如何预防糖尿病？',
  '血糖高应该注意什么？',
  '健康饮食建议',
  '什么是妊娠期糖尿病？'
]

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

onMounted(() => {
  scrollToBottom()
})

async function sendMessage() {
  if (!input.value.trim() || loading.value) return

  const userMessage = {
    id: Date.now(),
    role: 'user',
    content: input.value.trim(),
    timestamp: new Date().toLocaleTimeString()
  }
  messages.value.push(userMessage)
  const userInput = input.value
  input.value = ''
  scrollToBottom()

  loading.value = true

  try {
    const data = await chat(userInput)
    const assistantMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      content: data.reply || '抱歉，我暂时无法回答您的问题。',
      timestamp: new Date().toLocaleTimeString()
    }
    messages.value.push(assistantMessage)
  } catch (e) {
    console.error('发送消息失败:', e)
    ElMessage.error('发送消息失败，请稍后重试')
    const errorMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      content: '抱歉，发生了错误，请稍后再试。',
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
  messages.value = [
    {
      id: 1,
      role: 'assistant',
      content: '您好！我是您的健康助手。我可以帮助您解答关于健康、血糖管理、糖尿病预防等方面的问题。请随时提问！',
      timestamp: new Date().toLocaleTimeString()
    }
  ]
  ElMessage.info('对话已清空')
}
</script>

<template>
  <div class="chat-page">
    <div class="card mb-6 p-6">
      <div class="flex items-center gap-4">
        <div class="w-12 h-12 bg-gradient-to-br from-primary-500 to-medical-500 rounded-2xl flex items-center justify-center">
          <el-icon :size="24" color="white">
            <ChatDotRound />
          </el-icon>
        </div>
        <div>
          <h1 class="text-3xl font-bold text-slate-800">智能健康助手</h1>
          <p class="text-slate-500 text-lg mt-1">专业的医疗健康咨询服务</p>
        </div>
      </div>
    </div>

    <div class="card p-0 overflow-hidden max-w-4xl mx-auto">
      <div class="bg-gradient-to-r from-primary-500 to-medical-500 p-6 text-white">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div class="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center">
              <el-icon :size="32">
                <ChatDotRound />
              </el-icon>
            </div>
            <div>
              <h2 class="text-2xl font-bold">智能健康助手</h2>
              <p class="text-white/80">为您提供健康咨询服务</p>
            </div>
          </div>
          <button
            @click="clearChat"
            class="bg-white/20 hover:bg-white/30 px-5 py-3 rounded-xl transition-all duration-300 flex items-center gap-2"
          >
            <el-icon><Refresh /></el-icon>
            <span>清空对话</span>
          </button>
        </div>
      </div>

      <div class="bg-slate-50 p-4 border-b border-slate-200">
        <div class="flex flex-wrap gap-3">
          <button
            v-for="q in quickQuestions"
            :key="q"
            @click="quickQuestion(q)"
            class="px-4 py-2 bg-white border border-primary-200 text-primary-700 rounded-xl hover:bg-primary-50 hover:border-primary-300 transition-all duration-300 flex items-center gap-2"
          >
            <el-icon :size="16"><MagicStick /></el-icon>
            {{ q }}
          </button>
        </div>
      </div>

      <div
        ref="messagesContainer"
        class="messages-container h-[50vh] overflow-y-auto p-6"
      >
        <div class="space-y-6">
          <div
            v-for="msg in messages"
            :key="msg.id"
            class="message-item flex"
            :class="[
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            ]"
          >
            <div
              class="message-bubble max-w-[70%]"
              :class="[
                msg.role === 'user'
                  ? 'bg-gradient-to-r from-primary-500 to-medical-500 text-white rounded-2xl rounded-tr-sm'
                  : 'bg-white border border-slate-200 text-slate-800 rounded-2xl rounded-tl-sm'
              ]"
            >
              <div class="flex items-start gap-4">
                <div
                  class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                  :class="[
                    msg.role === 'user' ? 'bg-primary-600' : 'bg-slate-100'
                  ]"
                >
                  <el-icon :size="20" :class="msg.role === 'user' ? 'text-white' : 'text-primary-600'">
                    <User v-if="msg.role === 'user'" />
                    <ChatDotRound v-else />
                  </el-icon>
                </div>
                <div class="flex-1">
                  <div class="message-content whitespace-pre-wrap leading-relaxed">
                    {{ msg.content }}
                  </div>
                  <div
                    class="text-xs mt-2 opacity-70"
                  >
                    {{ msg.timestamp }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="loading" class="flex justify-start">
            <div class="bg-white border border-slate-200 text-slate-800 rounded-2xl rounded-tl-sm p-4 flex items-center gap-3">
              <el-icon class="animate-spin text-primary-600" :size="20">
                <Refresh />
              </el-icon>
              <span class="text-slate-500">正在思考...</span>
            </div>
          </div>
        </div>
      </div>

      <div class="border-t border-slate-200 p-5 bg-slate-50">
        <div class="flex gap-4">
          <input
            v-model="input"
            @keyup.enter="sendMessage"
            type="text"
            :disabled="loading"
            placeholder="请输入您的问题..."
            class="input-field flex-1 text-lg py-4 px-5"
          />
          <button
            @click="sendMessage"
            :disabled="loading"
            class="btn-primary px-8 flex items-center gap-2"
          >
            <el-icon :size="20"><Promotion /></el-icon>
            发送
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-page {
  max-width: 1600px;
  margin: 0 auto;
}
</style>
