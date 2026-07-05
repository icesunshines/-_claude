# 基于FastAPI的医疗健康数据可视化与风险预测系统

## 项目简介

利用天池精准医疗大赛数据，构建 **体检血糖预测（回归）** 和 **妊娠期糖尿病风险预测（分类）** 双模型，通过 FastAPI 提供 REST API，Vue 3 + ECharts 构建可视化大屏与交互预测页面。

## 推荐论文题目

> 基于 FastAPI 与 LightGBM 的体检血糖预测及妊娠期糖尿病风险可视化系统

## 数据说明

| 数据集 | 样本量 | 任务 | 标签 |
|--------|--------|------|------|
| 初赛 initial | 5642 条 | 血糖回归 | 血糖 (mmol/L) |
| 复赛 final | 1000 条 | GDM 分类 | label (0/1) |

## 目录结构

```
项目/
├── data/                      # 原始 CSV 数据
├── docs/
│   ├── thesis_figures/        # 论文实验图表（运行 evaluate_models.py 生成）
│   └── *.md                   # 设计文档
├── src/
│   ├── main.py                # FastAPI 入口
│   ├── predict.py             # 预测与统计
│   ├── preprocessing.py       # 可持久化 Pipeline
│   ├── train_models.py        # 模型训练
│   ├── evaluate_models.py     # 论文图表生成
│   └── models/
│       ├── blood_sugar.lgb
│       ├── diabetes.lgb
│       ├── blood_sugar_pipeline.joblib
│       ├── diabetes_pipeline.joblib
│       └── model_metrics.json
├── frontend/                  # Vue 3 前端
├── requirements.txt
└── .env.example
```

## 快速开始

### 1. 环境准备

```bash
pip install -r requirements.txt
cd frontend && npm install
```

可选：复制 `.env.example` 为 `.env` 并设置 `JWT_SECRET`。

### 2. 训练模型

```bash
cd 项目
python src/train_models.py
```

训练完成后会保存 LightGBM 模型、预处理 Pipeline 和 `model_metrics.json`。

### 3. 生成论文图表

```bash
python src/evaluate_models.py
```

输出到 `docs/thesis_figures/`（6 张 PNG + metrics_summary.json）。

### 4. 启动服务

```bash
# 后端
python src/main.py

# 前端（新终端）
cd frontend && npm run dev
```

- 后端: http://localhost:8000
- 前端: http://localhost:5173
- 默认账号: admin/admin123, user/user123

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册（固定 role=user） |
| POST | `/api/auth/login` | 登录获取 JWT |
| POST | `/api/predict/blood-sugar` | 血糖预测 |
| POST | `/api/predict/diabetes` | 妊娠期糖尿病预测 |
| GET | `/api/stats/overview` | 大屏 KPI 概览 |
| GET | `/api/stats/blood-sugar` | 血糖统计数据 |
| GET | `/api/stats/blood-sugar/means` | 表单默认中位数值 |
| GET | `/api/stats/diabetes` | 糖尿病统计 + ROC/混淆矩阵 |
| GET | `/api/feature-importance` | 特征重要性 |
| POST/GET | `/api/history` | 预测历史（需登录） |
| GET | `/api/admin/dashboard` | 管理员仪表盘 |

## 模型性能（验证集 / 官方测试集）

### 血糖预测

| 指标 | 验证集 | 测试集 |
|------|--------|--------|
| RMSE | 1.2747 | 1.3330 |
| MAE | 0.7127 | 0.7395 |
| R² | 0.1543 | 0.1525 |

### 妊娠期糖尿病分类

| 指标 | 验证集 | 测试集 |
|------|--------|--------|
| AUC | 0.7825 | 0.7324 |
| Accuracy | 0.7000 | 0.6600 |
| F1 | 0.6471 | 0.6222 |

## 功能说明

- **可视化大屏**: 动态 KPI、血糖分布/年龄组/相关性、GDM 临床对比、ROC、混淆矩阵
- **预测页面**: 双 Tab（血糖 + GDM），完整字段，登录后自动保存历史
- **管理后台**: 用户列表、预测统计、历史记录
- **论文支撑**: 对比实验（LightGBM vs RF/LR）、实验图表一键导出

## 论文结构建议

1. 绪论 — 背景、意义、研究内容
2. 相关技术 — FastAPI、LightGBM、ECharts、JWT
3. 需求分析与系统设计 — 架构图、数据库设计
4. 数据处理与模型构建 — Pipeline、对比实验
5. 系统实现与可视化 — API、大屏、预测流程
6. 系统测试与结果分析 — 指标表、图表
7. 总结与展望

**知网检索关键词**: 妊娠期糖尿病+机器学习、LightGBM+医疗、血糖+预测模型、FastAPI+医疗信息系统

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + SQLAlchemy + JWT |
| 前端 | Vue 3 + Vite + ECharts 5 |
| ML | LightGBM + scikit-learn + joblib |
| 数据库 | SQLite |

## 注意事项

- LightGBM 模型使用相对路径加载（兼容中文项目路径）
- 训练与推理共用同一 Pipeline（joblib 持久化），确保预测一致性
- 数据文件 GBK 编码读取
