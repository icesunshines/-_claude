# Chat 页面布局重新设计 Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重新设计 Chat.vue 页面的视觉布局和样式，功能逻辑完全不变。

**Architecture:** 单文件组件改造——仅修改 `frontend/src/views/Chat.vue` 的 `<template>` 和 `<style scoped>` 部分，所有 `<script setup>` 逻辑保持不变。

**Tech Stack:** Vue 3 + Tailwind CSS + Element Plus 图标

---

### 文件改动清单

| 文件 | 操作 |
|------|------|
| `frontend/src/views/Chat.vue` | 修改 — 仅改 `<template>` 和 `<style scoped>` 两个块 |

**保持不变：**
- 所有 script 逻辑（会话管理、SSE 流式、Markdown 渲染、快捷问题等）
- 其他所有页面组件
- 全局样式文件
- API 调用方式

---

### Task 1: 顶部标题栏改造

**Files:**
- Modify: `frontend/src/views/Chat.vue:338-350`

- [ ] **Step 1: 替换渐变标题栏为简洁纯白顶栏**

将原来的 `bg-gradient-to-r from-primary-500 to-medical-500` 区域替换为：
```html
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
```

改动要点：
- 背景从青色渐变改为 `bg-white`
- 文字从 `text-white` 改为 `text-slate-800` / `text-slate-400`
- 折叠按钮从 `hover:bg-white/20` 改为 `hover:bg-slate-100`
- 图标颜色从默认白色改为 `text-slate-600`

- [ ] **Step 2: 验证编译通过**

运行：
```bash
cd frontend && npx vue-tsc --noEmit --skipLibCheck 2>&1 | head -20
```
或至少在浏览器中确认无报错。

- [ ] **Step 3: 提交**

```bash
git add frontend/src/views/Chat.vue
git commit -m "feat: chat 顶部标题栏改为简洁纯白风格"
```

---

### Task 2: 快捷问题标签改造

**Files:**
- Modify: `frontend/src/views/Chat.vue:352-364`

- [ ] **Step 1: 替换快捷问题展示为可收起标签列表**

将原来的 6 个按钮横向排列区域替换为：
```html
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
```

改动要点：
- 从 `bg-slate-50/80` 背景改为 `bg-white`
- 按钮从 `rounded-md` 改为 `rounded-full`（胶囊标签风格）
- 添加"更多/收起"按钮，默认只显示前 3 个
- 空状态时全部展示

- [ ] **Step 2: 添加 `showAllQuickQuestions` 响应式变量**

在 `<script setup>` 的 ref 声明区（第 20 行附近）添加：
```js
const showAllQuickQuestions = ref(true)
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/views/Chat.vue
git commit -m "feat: 快捷问题改为可收起的胶囊标签列表"
```

---

### Task 3: 消息气泡重新设计

**Files:**
- Modify: `frontend/src/views/Chat.vue:386-427`

- [ ] **Step 1: 重新设计消息气泡布局**

将消息列表循环和加载状态替换为：
```html
<div v-if="messages.length" class="space-y-4">
  <div
    v-for="msg in messages"
    :key="msg.id"
    class="flex"
    :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
  >
    <div
      class="max-w-[65%]"
      :class="msg.role === 'user' ? '' : 'flex items-start gap-2'"
    >
      <!-- AI 头像（仅 AI 消息显示） -->
      <div
        v-if="msg.role !== 'user'"
        class="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center flex-shrink-0 mt-1"
      >
        <el-icon :size="14" class="text-white"><ChatDotRound /></el-icon>
      </div>

      <div
        class="message-bubble rounded-2xl px-4 py-3"
        :class="msg.role === 'user'
          ? 'bg-gradient-to-r from-primary-500 to-primary-600 text-white rounded-br-sm'
          : 'bg-white border border-slate-100 text-slate-800 rounded-bl-sm shadow-soft'"
      >
        <div class="message-content text-[13px] leading-relaxed" v-html="msg.html"></div>
        <div class="text-[10px] mt-2 opacity-50">
          {{ msg.timestamp }}
        </div>
      </div>
    </div>
  </div>

  <div v-if="loading" class="flex justify-start">
    <div class="flex items-center gap-2 bg-white border border-slate-100 rounded-2xl rounded-bl-sm px-4 py-3 shadow-soft">
      <el-icon class="animate-spin text-primary-500" :size="16"><Refresh /></el-icon>
      <span class="text-slate-500 text-xs">正在思考...</span>
    </div>
  </div>
</div>
```

改动要点：
- 间距从 `space-y-2.5` 改为 `space-y-4`
- 最大宽度从 `max-w-[75%]` 改为 `max-w-[65%]`
- 用户消息：去掉左侧三角尖角（`rounded-br-sm`），保留渐变背景
- AI 消息：白色卡片 + `shadow-soft`（使用全局组件类），左侧加圆形 AI 头像
- 头像使用 `rounded-full` + primary 渐变背景 + 白色图标
- 时间戳缩小到 `text-[10px]`

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/Chat.vue
git commit -m "feat: 消息气泡重新设计，增大间距和改窄宽度"
```

---

### Task 4: 空状态页面优化

**Files:**
- Modify: `frontend/src/views/Chat.vue:372-384`

- [ ] **Step 1: 优化空状态页面视觉**

将空状态区域替换为：
```html
<div v-if="!messages.length && !loading" class="h-full min-h-0 flex items-center justify-center">
  <div class="text-center">
    <div class="w-20 h-20 bg-gradient-to-br from-primary-50 to-medical-50 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-soft">
      <el-icon :size="36" class="text-primary-500">
        <ChatDotRound />
      </el-icon>
    </div>
    <p class="text-base font-semibold text-slate-700 mb-1">开始对话</p>
    <p class="text-sm text-slate-400 max-w-xs leading-relaxed">
      请选择左侧会话或直接提问，<br/>我将基于医疗知识库为您解答健康问题。
    </p>
  </div>
</div>
```

改动要点：
- 图标容器从 `bg-slate-100` 改为 `bg-gradient-to-br from-primary-50 to-medical-50`
- 容器尺寸从 64px 放大到 80px（`w-20 h-20`）
- 图标从 32px 放大到 36px
- 标题从 `text-slate-600` 改为 `text-slate-700` 且更粗
- 说明文字从 `text-xs` 改为 `text-sm`
- 容器增加 `shadow-soft`

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/Chat.vue
git commit -m "feat: 优化空状态页面视觉，渐变图标容器"
```

---

### Task 5: 输入区域微调

**Files:**
- Modify: `frontend/src/views/Chat.vue:430-451`

- [ ] **Step 1: 输入框和发送按钮微调**

将输入区域替换为：
```html
<!-- 输入区 -->
<div class="border-t border-slate-100 px-4 py-3 bg-white flex-shrink-0">
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
      class="btn-primary px-4 flex items-center gap-1.5 text-sm py-2.5 hover:-translate-y-0.5 active:translate-y-0 transition-transform"
    >
      <el-icon :size="16"><Promotion /></el-icon>
      <span>发送</span>
    </button>
  </div>
</div>
```

改动要点：
- 边距从 `px-3 py-2.5` 改为 `px-4 py-3`
- 边框颜色从 `border-slate-200` 改为 `border-slate-100`
- 发送按钮添加 hover 上浮和 active 回弹的微动画

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/Chat.vue
git commit -m "feat: 输入区域微调，发送按钮添加 hover 动画"
```

---

### Task 6: 侧边栏样式微调

**Files:**
- Modify: `frontend/src/views/Chat.vue:308-334`

- [ ] **Step 1: 侧边栏样式与整体风格统一**

将侧边栏区域的 Tailwind 类名微调：
- 背景从 `bg-slate-50` 改为 `bg-white`
- 边框从 `border-slate-200` 改为 `border-slate-100`
- 会话项 hover 背景从 `bg-white` 改为 `bg-slate-50`（选中时反转）
- 新对话按钮保持 `btn-primary` 不变

在 `<style scoped>` 中更新 `.session-item:hover`：
```css
.session-item:hover {
  background-color: #f8fafc;
}

.session-item.active {
  background-color: #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/Chat.vue
git commit -m "feat: 侧边栏样式统一为白色清爽风格"
```

---

### Task 7: 最终验证

**Files:**
- 无新文件

- [ ] **Step 1: 启动前端并手动验证所有功能**

```bash
cd frontend
npm run dev
```

在浏览器中访问 http://localhost:5173，验证：
1. 登录系统
2. 进入"智能问答"页面，确认视觉更新
3. 发送一条消息，确认 SSE 流式响应正常
4. 确认 Markdown 渲染正常（标题、加粗、列表）
5. 点击快捷问题标签发送
6. 点击"更多/收起"切换快捷问题列表
7. 创建新对话、切换对话、删除对话
8. 折叠/展开侧边栏
9. 切换暗色/亮色主题

- [ ] **Step 2: 检查 Git 状态确认只改了 Chat.vue**

```bash
git diff --stat
```
确认只有 `frontend/src/views/Chat.vue` 被修改。

- [ ] **Step 3: 最终提交**

```bash
git add frontend/src/views/Chat.vue
git commit -m "feat: Chat 页面整体视觉重新设计 — 现代清爽风格"
```

---

## 注意事项

1. **不修改任何 script 逻辑** — 所有 ref、函数、生命周期钩子保持原样
2. **不引入新依赖** — 所有样式使用现有的 Tailwind 类名和全局组件类（`.card`, `.btn-primary`, `.input-field`, `shadow-soft`）
3. **保留 `message-content :deep()` 样式规则** — Markdown 渲染样式不变
4. **快捷问题数量从 6 减到默认显示 3 个** — 使用 `v-if="showAllQuickQuestions || messages.length === 0"` 控制，不影响 `quickQuestions` 数组
