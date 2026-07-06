---
title: Chat 页面布局重新设计
date: 2026-07-06
scope: 仅修改 frontend/src/views/Chat.vue 的模板和样式，功能逻辑保持不变
---

## 背景

当前 Chat.vue 的布局存在几个问题：消息气泡紧凑、快捷问题卡片横向拥挤、顶部渐变标题栏风格不够统一。用户希望重新设计视觉和布局，功能（会话管理、流式响应、Markdown 渲染等）完全不变。

## 改动范围

仅修改 `frontend/src/views/Chat.vue` 的 `<template>` 和 `<style scoped>` 部分。

**不改动：**
- 所有 script 逻辑（会话 CRUD、SSE 流式接收、Markdown 渲染、快捷问题触发）
- 其他页面组件（Dashboard、Predict、Admin、Login、Profile）
- API 调用方式（仍使用原始 fetch，不引入 api/request.js 的 chat 函数）
- 全局样式（style.css、dashboard-theme.css、tailwind.config.js）

## 设计方案

### 整体布局
- 保留左侧会话列表 + 右侧聊天区的基本框架（侧栏可折叠 `showSidebar`）
- 去掉顶部青色渐变标题栏，改为简洁的纯白顶栏（保留折叠按钮和标题文字）
- 整体白色 + 浅灰背景

### 消息气泡
- 用户消息：靠右，primary-500 到 primary-600 渐变背景 + 白色文字，圆角去掉左侧三角
- AI 消息：靠左，白色卡片 + `border border-slate-200` + 柔和阴影，左侧小图标（ChatDotRound）
- 消息间距从 `space-y-2.5` 改为 `space-y-4`
- 消息气泡最大宽度 65%（`max-w-[65%]`）
- 时间戳用 `text-[10px] text-slate-400` 显示在气泡底部

### 快捷问题
- 位置：消息区底部、输入框上方
- 标签样式：白色背景 + primary-200 边框 + `hover:bg-primary-50`
- 空状态时展开显示全部 6 个，有对话后折叠为 3 个 + "更多"按钮
- 点击标签直接发送（保持现有 `quickQuestion` 逻辑不变）

### 输入区域
- 保持单行输入框 + 发送按钮布局
- 使用现有 `.input-field` 和 `.btn-primary` 组件类
- 发送按钮 hover 时上浮 1px（`hover:-translate-y-0.5` + `transition-transform`）

### 空状态页面
- 保持现有布局：图标 + 标题 + 引导文字
- 图标使用 primary 色系的柔和渐变背景
- 文字内容不变

### 加载状态
- 保持现有"正在思考..."动画样式

## 技术细节

- 使用现有 Tailwind 类名和全局 `.card`、`.input-field`、`.btn-primary` 组件类
- 不添加新的 CSS 变量或全局样式
- Markdown 渲染样式（`message-content :deep()`）保持现有规则
- 使用 `marked` 库继续渲染 AI 回复

## 验证方式

1. `npm run dev` 启动前端服务
2. 登录系统，进入"智能问答"页面
3. 验证：消息气泡样式变化、快捷问题标签可点击发送、会话列表正常折叠/展开
4. 发送消息确认 SSE 流式响应正常工作
5. 创建新对话、切换对话、删除会话
6. 暗色/亮色主题切换下正常显示
