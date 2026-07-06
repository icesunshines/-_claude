# 全项目字体统一 Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立统一的 CSS 变量字体系统，全项目正文文本一致可读。

**Architecture:** 在 `style.css` 中添加 `:root` CSS 变量定义 `--text-xs` 到 `--text-5xl`，在 `@layer utilities` 中覆盖 Tailwind 默认的 `text-xs`（12px→13px）。同时修改 `body` 基准为 `text-sm`（14px）。Chat.vue 的自定义 `text-[13px]`/`text-[10px]` 替换为标准 class。

**Tech Stack:** CSS Variables + Tailwind CSS + Vue 3

---

### 文件改动清单

| 文件 | 操作 |
|------|------|
| `frontend/src/style.css` | 修改 — 添加 CSS 变量 + 覆盖 `text-xs` + body 基准 |
| `frontend/src/views/Chat.vue` | 修改 — 替换 2 处自定义像素值 |

---

### Task 1: style.css 添加 CSS 变量

**Files:**
- Modify: `frontend/src/style.css`

- [ ] **Step 1: 在 style.css 底部添加 `:root` CSS 变量**

在 `</style>` 标签之前（`style.css` 末尾）添加：

```css
/* ========== Font Size Scale ========== */
:root {
  --text-xs: 13px;
  --text-sm: 14px;
  --text-base: 16px;
  --text-lg: 18px;
  --text-xl: 20px;
  --text-2xl: 24px;
  --text-3xl: 30px;
  --text-4xl: 36px;
  --text-5xl: 48px;
}
```

- [ ] **Step 2: 覆盖 Tailwind 默认的 `text-xs`**

在 `@layer utilities` 中添加：

```css
  .text-xs { font-size: var(--text-xs); }
```

当前 `@layer utilities` 中没有任何内容。如果 `@layer utilities {}` 尚不存在（因为当前只有 `@layer base` 和 `@layer components`），需要在 Tailwind 指令之后、`@layer base` 之前添加：

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer utilities {
  .text-xs { font-size: var(--text-xs); }
}

@layer base {
  body {
    @apply bg-slate-50 text-sm leading-relaxed font-sans;
  }
}
```

同时修改 `@layer base` 中的 body：
- 添加 `text-sm leading-relaxed`（原来只有 `text-sm font-sans`）

**完整修改后的 style.css 内容应为：**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer utilities {
  .text-xs { font-size: var(--text-xs); }
}

@layer base {
  body {
    @apply bg-slate-50 text-sm leading-relaxed font-sans;
  }
}

@layer components {
  .card {
    @apply bg-white rounded-2xl border border-slate-100;
    box-shadow: 0 2px 8px -2px rgba(0, 0, 0, 0.08), 0 1px 3px -3px rgba(0, 0, 0, 0.05);
  }
  /* ... existing .card-hover, .btn-primary, etc. unchanged ... */
}

/* ========== Font Size Scale ========== */
:root {
  --text-xs: 13px;
  --text-sm: 14px;
  --text-base: 16px;
  --text-lg: 18px;
  --text-xl: 20px;
  --text-2xl: 24px;
  --text-3xl: 30px;
  --text-4xl: 36px;
  --text-5xl: 48px;
}
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/style.css
git commit -m "feat: 全项目字体统一 — CSS 变量 scale + text-xs 13px 基础"
```

---

### Task 2: Chat.vue 自定义值替换

**Files:**
- Modify: `frontend/src/views/Chat.vue`

- [ ] **Step 1: 替换消息内容字号**

找到 `text-[13px]`（消息内容），替换为 `text-sm`：

将：
```html
<div class="message-content text-[13px] leading-relaxed" v-html="msg.html"></div>
```

改为：
```html
<div class="message-content text-sm leading-relaxed" v-html="msg.html"></div>
```

- [ ] **Step 2: 替换时间戳字号**

找到 `text-[10px]`（时间戳），替换为 `text-[11px]`（元数据层级）：

将：
```html
<div class="text-[10px] mt-2 opacity-50">
```

改为：
```html
<div class="text-[11px] mt-2 opacity-50">
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/views/Chat.vue
git commit -m "fix: Chat 消息字号从自定义像素改为标准 class"
```

---

### Task 3: 最终验证

**Files:**
- 无新文件

- [ ] **Step 1: 构建验证**

```bash
cd frontend
npm run build 2>&1 | head -20
```

确认构建 0 错误。

- [ ] **Step 2: 检查 git diff 确认改动范围**

```bash
git diff --stat
```

确认只有 `style.css` 和 `Chat.vue` 被修改。

- [ ] **Step 3: 提交**

```bash
git add frontend/src/style.css frontend/src/views/Chat.vue
git commit -m "feat: 全项目字体统一 — 最终验证"
```

---

## 注意事项

1. **不改其他 Vue 组件** — 所有 `text-xs` class 自动通过 CSS 变量变为 13px，无需替换
2. **不改页面标题/数值** — `text-lg`/`text-xl`/`text-2xl` 等保持 Tailwind 默认值（与 CSS 变量一致）
3. **可回退** — 只需删除 `:root` 变量块和 `@layer utilities` 覆盖即可恢复原状
4. **Tailwind 的 `text-sm`（14px）与 body 基准一致** — 无需额外覆盖
5. **Chat 的 `text-[11px]` 保留像素值** — 11px 不属于标准 Tailwind scale，是特殊的元数据层级
