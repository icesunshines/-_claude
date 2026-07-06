---
title: 全项目字体统一设计
date: 2026-07-06
scope: 仅修改 frontend/src/style.css，功能逻辑完全不变
---

## 背景

全项目目前使用了 11 种字号（text-xs=12px 到 text-5xl=48px），加上 Chat.vue 中自定义的 10px 和 13px。body 基础字体为浏览器默认 16px，无显式声明。各页面字号不统一，部分文本过小（10px、12px）影响可读性。

## 目标

建立一套统一的字体系统，所有字号通过 CSS 变量集中管理，调整时只需修改一处。

## 改动范围

仅修改 `frontend/src/style.css` 一个文件。不改任何 Vue 组件逻辑。

## 设计方案

### 1. CSS 变量定义（font-size scale）

在 `style.css` 底部添加 `:root` CSS 变量：

```css
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

### 2. Body 基准字体

`body` 添加 `@apply text-sm leading-relaxed`（14px 基准，行高舒适）。

### 3. Chat.vue 自定义值替换

- `text-[13px]`（消息内容）→ `text-sm`（14px）
- `text-[10px]`（时间戳）→ `text-[11px]`（11px，元数据层级）

### 4. Tailwind text-xs 覆盖

在 `@layer utilities` 中添加规则，将 Tailwind 默认的 `text-xs`（12px）覆盖为 `var(--text-xs)`（13px）：

```css
@layer utilities {
  .text-xs { font-size: var(--text-xs); }
}
```

这样所有 `text-xs` class 自动变为 13px，其他 `text-sm` 等保持 Tailwind 默认值（因为它们与 CSS 变量一致）。

## 不改动

- 所有 Vue 组件的 script 逻辑
- 页面标题字号（text-2xl/3xl/4xl/5xl）
- 统计数值字号
- 图标大小
- 布局结构

## 验证

1. `npm run dev` 启动前端
2. 遍历所有页面（Dashboard、Predict、Chat、Profile、Admin、Login）
3. 确认正文文字清晰可读
4. 确认标题和数值保持原有大小
5. 确认 Chat 消息内容和时间戳正确
6. 运行 `npm run build` 确认无错误
