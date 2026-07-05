# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A medical health risk prediction system built with FastAPI + Vue 3, using LightGBM models for two independent prediction tasks: **blood sugar regression** (predict glucose in mmol/L) and **gestational diabetes (GDM) classification** (healthy vs diabetic). Data comes from Tianchi Precision Medicine Competition. Chinese-language UI throughout.

## Directory Structure

```
项目/                                    # or 第一次优化项目/ (copy)
├── src/                                 # Backend
│   ├── main.py                          # FastAPI entry, all routes
│   ├── database.py                      # SQLAlchemy engine (SQLite)
│   ├── models_orm.py                    # ORM models: User, PredictionHistory
│   ├── schemas.py                       # Pydantic request/response models
│   ├── auth.py                          # JWT auth, password hashing, deps
│   ├── preprocessing.py                 # InitialPipeline + FinalPipeline
│   ├── predict.py                       # Lazy-loaded model inference + stats
│   ├── train_models.py                  # Model training with CV
│   ├── evaluate_models.py               # Thesis figure generation
│   └── models/                          # Trained artifacts
│       ├── blood_sugar.lgb              # 34-feature regression model
│       ├── diabetes.lgb                 # 75-feature classification model
│       ├── blood_sugar_pipeline.joblib  # Preprocessing pipeline
│       ├── diabetes_pipeline.joblib
│       └── model_metrics.json
├── frontend/                            # Vue 3 SPA
│   ├── vite.config.js                   # Dev proxy /api -> localhost:8000
│   ├── tailwind.config.js               # Custom medical color scales
│   └── src/
│       ├── App.vue                      # Root layout (sidebar + header + router-view)
│       ├── main.js                      # Bootstrap: Pinia, Router, ElementPlus
│       ├── router/index.js              # 6 routes with auth guard
│       ├── api/request.js               # Axios client + typed API functions
│       ├── stores/auth.js               # Pinia auth store
│       ├── views/                       # Page components
│       │   ├── Login.vue                # Auth page
│       │   ├── Dashboard.vue            # Visualization dashboard
│       │   ├── Predict.vue              # Prediction forms (two-tab)
│       │   ├── Chat.vue                 # Chat Q&A interface
│       │   ├── Profile.vue              # User profile + prediction history
│       │   └── Admin.vue                # Admin panel (user list + records)
│       └── components/Charts/           # ECharts components
├── data/                                # CSV data (GBK encoding)
│   ├── initial/                         # Blood sugar: 5642 training samples
│   └── final/                           # GDM classification: 1000 samples
├── requirements.txt
└── .env.example                         # JWT_SECRET
```

## Key Commands

### Backend (Python)

```bash
# Install dependencies
pip install -r requirements.txt

# Train models (rebuilds all artifacts in src/models/)
python src/train_models.py

# Generate thesis figures (outputs to docs/thesis_figures/)
python src/evaluate_models.py

# Seed database (creates default admin/admin123, user/user123)
python src/seed.py

# Run API server (port 8000)
python src/main.py
```

### Frontend (Node.js)

```bash
cd frontend
npm install          # Install dependencies
npm run dev          # Dev server (port 5173, proxy /api to :8000)
npm run build        # Production build
npm run preview      # Preview production build locally
```

### Running Both

Open two terminals:
```bash
# Terminal 1: Backend
python src/main.py

# Terminal 2: Frontend
cd frontend && npm run dev
```

## Architecture

### Backend

- **App entry**: `src/main.py` — FastAPI app with CORS (wildcard), tables created via `Base.metadata.create_all(bind=engine)` at module level
- **Routes organized by prefix**: `/api/auth/*` (register/login/me), `/api/predict/*` (blood-sugar, diabetes), `/api/stats/*`, `/api/history`, `/api/admin/*`, `/api/realtime/stats` (SSE), `/api/chat`
- **Auth**: `auth.py` provides `get_current_user` / `get_current_admin` dependencies via JWT (HS256, 120min expiry). Passwords use SHA256 hashing (not bcrypt).
- **Database**: SQLite at `src/medical.db`. Two tables: `users` (id, username, hashed_password, role, created_at) and `prediction_history` (id, user_id, type, input_data as JSON, result as JSON, created_at).
- **ML inference**: `src/predict.py` — lazy-loading singleton pattern. Models and pipelines loaded once into module globals. Two independent pipelines: `InitialPipeline` (blood sugar regression, 34 features) and `FinalPipeline` (diabetes classification, 75 features).
- **Preprocessing**: `src/preprocessing.py` — `BLOOD_SUGAR_COL_MAPPING` translates frontend Chinese field names to internal column names. Missing values filled with training-set medians.
- **Stats endpoints**: Read raw CSVs from `data/`, compute distributions/correlations on the fly. Model metrics served from cached `model_metrics.json`.

### Frontend

- **Layout**: `App.vue` — `/login` renders login-only; other routes render collapsible sidebar + sticky header + `<router-view>`. Sidebar menu computed from auth state.
- **Auth**: Token stored in `localStorage`. Router guard redirects unauthenticated users to `/login`. Admin routes check `localStorage.role === 'admin'`.
- **API**: Single `src/api/request.js` file with Axios interceptors (request: Bearer token; response: 401 clears localStorage + redirects to `/login`). All API functions are flat exports.
- **Charts**: Mix of data-fetching patterns — `BloodSugarCharts` and `DiabetesCharts` fetch their own data from the API; `TrendChart`, `BarChart`, `RadarChart`, `GaugeChart`, `RiskCards` receive data via props from parent.
- **Styling**: Three layers — Tailwind CSS (utility classes with custom medical color scales), `src/style.css` (shared component classes like `.card`, `.btn-primary`), `src/styles/dashboard-theme.css` (dark/light CSS variables via `data-theme` attribute).

### ML Models

- **Blood sugar** (`blood_sugar.lgb`): LightGBM regression, 34 features, RMSE 1.33 on test set. Features log-transformed (甘油三酯, 尿酸).
- **Diabetes** (`diabetes.lgb`): LightGBM classification, 75 features, AUC 0.73 on test class imbalance handled via scale_pos_weight. Supports SNP features dict input.

## Conventions

- **No test framework** — the project has utility scripts (`test_login.py`, `check_all.py`, `check_db.py`, `reset_users.py`) but no pytest/unittest setup.
- **No CI/CD, no Docker, no Makefile**.
- **Chinese-language UI** throughout all code, comments, and user-facing strings.
- Data CSV files are **GBK encoded**.
- No composables, hooks, or typed API layer in frontend — all logic in `<script setup>` blocks and flat exports.
- The `项目/` subdirectory is a copy of the entire project; changes may need to be mirrored.
