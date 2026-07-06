# coding: utf-8
"""
模型融合模块 (Stacking Ensemble)
基于 Stacking 集成学习，融合 LightGBM 与 XGBoost 预测结果
采用两层架构：
  第1层（基学习器）：LightGBM + XGBoost，通过 K-Fold CV 生成 out-of-fold (OOF) 预测
  第2层（元学习器）：Ridge 回归（回归任务）/ Logistic Regression（分类任务）

适用任务：
- 血糖回归预测：输入临床体检指标，预测空腹血糖值（mmol/L）
- 糖尿病分类预测：输入妊娠期临床指标，预测 GDM 患病概率

训练流程：
1. 对训练集做 K-Fold 划分，每折用其余折训练基学习器
2. 基学习器对验证折做 OOF 预测，拼接为元特征
3. 元学习器在元特征上训练
4. 全量数据重新训练基学习器，用于最终预测
"""

import os
from typing import Any, Callable, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import KFold, StratifiedKFold
from xgboost import XGBRegressor, XGBClassifier

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'models')


def _generate_oof_predictions(
    X: pd.DataFrame,
    y: pd.Series,
    base_estimator,
    is_regression: bool = True,
    random_state: int = 42,
) -> np.ndarray:
    """
    通过 K-Fold 交叉验证生成 out-of-fold (OOF) 预测。

    每个 fold 的验证集使用训练集的其他 fold 的模型来预测，
    确保 OOF 预测不会过拟合。

    返回: OOF 预测值，形状 (n_samples,)
    """
    n = X.shape[0]
    oof_preds = np.zeros(n)

    if is_regression:
        kf = KFold(n_splits=5, shuffle=True, random_state=random_state)
    else:
        kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)

    for train_idx, val_idx in kf.split(X, y):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train = y.iloc[train_idx]

        model = base_estimator.__class__(**base_estimator.get_params())
        model.fit(X_train, y_train)
        oof_preds[val_idx] = model.predict(X_val)

    return oof_preds


def train_stacked_blood_sugar(
    X: pd.DataFrame,
    y: pd.Series,
    random_state: int = 42,
) -> Tuple[Dict[str, Any], Dict[str, float]]:
    """
    训练 Stacking 血糖回归模型。

    基学习器: LightGBM + XGBoost
    元学习器: Ridge 回归

    返回:
        models: 包含训练好的基学习器、元学习器、以及全量训练的融合模型的字典
        metrics: 评估指标字典
    """
    print('  [Stacking] 训练血糖融合模型...')

    # 基学习器参数
    lgb_params = {
        'objective': 'regression',
        'boosting': 'gbdt',
        'learning_rate': 0.01,
        'num_leaves': 63,
        'min_data_in_leaf': 100,
        'lambda_l1': 0.01,
        'lambda_l2': 0.01,
        'feature_fraction': 0.7,
        'bagging_fraction': 0.7,
        'bagging_freq': 5,
        'verbose': -1,
        'nthreads': 4,
    }
    xgb_params = {
        'objective': 'reg:squarederror',
        'learning_rate': 0.05,
        'max_depth': 6,
        'min_child_weight': 3,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'lambda': 1.0,
        'alpha': 1.0,
        'eval_metric': 'rmse',
        'nthread': 4,
        'seed': random_state,
        'verbosity': 0,
    }

    # 第1层：生成 OOF 预测
    print('    生成 OOF 预测...')
    lgb_model_oof = lgb_params.copy()
    xgb_model_oof = xgb_params.copy()

    # 用 sklearn API 包装 XGBoost，便于统一调用
    xgb_sklearn = XGBRegressor(**xgb_params)

    # 生成 LightGBM 的 OOF 预测
    oof_lgb = _generate_oof_predictions(
        X, y, xgb_sklearn, is_regression=True, random_state=random_state,
    )

    # 生成 XGBoost 的 OOF 预测
    import lightgbm as lgb
    kf = KFold(n_splits=5, shuffle=True, random_state=random_state)
    n = X.shape[0]
    oof_xgb = np.zeros(n)

    for train_idx, val_idx in kf.split(X):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train = y.iloc[train_idx]
        y_val = y.iloc[val_idx]

        train_set = lgb.Dataset(X_train, label=y_train)
        val_set = lgb.Dataset(X_val, label=y_val, reference=train_set)
        model = lgb.train(
            lgb_params,
            train_set,
            num_boost_round=2000,
            valid_sets=[val_set],
            callbacks=[lgb.early_stopping(100, verbose=False)],
        )
        oof_xgb[val_idx] = model.predict(X_val)

    # 拼接两个基学习器的 OOF 预测作为元特征
    meta_X = pd.DataFrame({
        'lgb_oof': oof_lgb,
        'xgb_oof': oof_xgb,
    })

    # 第2层：训练元学习器
    print('    训练元学习器 (Ridge)...')
    meta_learner = Ridge(alpha=1.0)
    meta_learner.fit(meta_X, y)

    # 评估 OOF 结果
    oof_preds = meta_learner.predict(meta_X)
    oof_rmse = float(np.sqrt(mean_squared_error(y, oof_preds)))
    oof_r2 = float(r2_score(y, oof_preds))
    print(f'    OOF RMSE: {oof_rmse:.4f}, OOF R2: {oof_r2:.4f}')

    # 全量数据训练基学习器（用于最终预测）
    print('    全量训练基学习器...')
    train_set_full = lgb.Dataset(X, label=y)
    full_lgb = lgb.train(
        lgb_params,
        train_set_full,
        num_boost_round=3000,
        callbacks=[lgb.log_evaluation(0)],
    )
    full_xgb = xgb_sklearn.__class__(**xgb_params)
    full_xgb.fit(X, y)

    models = {
        'lgb': full_lgb,
        'xgb': full_xgb,
        'meta_learner': meta_learner,
        'oof_rmse': oof_rmse,
        'oof_r2': oof_r2,
        'feature_names': ['lgb_oof', 'xgb_oof'],
    }

    metrics = {
        'oof_rmse': round(oof_rmse, 4),
        'oof_r2': round(oof_r2, 4),
    }

    print(f'    训练完成! OOF RMSE={oof_rmse:.4f}, R2={oof_r2:.4f}')
    return models, metrics


def train_stacked_diabetes(
    X: pd.DataFrame,
    y: pd.Series,
    random_state: int = 42,
) -> Tuple[Dict[str, Any], Dict[str, float]]:
    """
    训练 Stacking 糖尿病分类模型。

    基学习器: LightGBM + XGBoost
    元学习器: Logistic Regression

    返回:
        models: 包含训练好的基学习器、元学习器、以及全量训练的融合模型的字典
        metrics: 评估指标字典
    """
    print('  [Stacking] 训练糖尿病融合模型...')

    # 计算类别权重
    pos_ratio = float(y.mean())
    scale_pos_weight = (1 - pos_ratio) / pos_ratio if pos_ratio > 0 else 1.0

    lgb_params = {
        'objective': 'binary',
        'boosting': 'gbdt',
        'learning_rate': 0.05,
        'num_leaves': 31,
        'min_data_in_leaf': 20,
        'lambda_l1': 0.1,
        'lambda_l2': 0.1,
        'metric': 'auc',
        'scale_pos_weight': scale_pos_weight,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1,
        'nthreads': 4,
    }
    xgb_params = {
        'objective': 'binary:logistic',
        'learning_rate': 0.05,
        'max_depth': 6,
        'min_child_weight': 3,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'lambda': 1.0,
        'alpha': 1.0,
        'eval_metric': 'auc',
        'nthread': 4,
        'seed': random_state,
        'verbosity': 0,
    }

    # 第1层：生成 OOF 预测
    print('    生成 OOF 预测...')
    import lightgbm as lgb

    kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
    n = X.shape[0]
    oof_lgb = np.zeros(n)
    oof_xgb = np.zeros(n)

    xgb_sklearn = XGBClassifier(**xgb_params)

    for train_idx, val_idx in kf.split(X, y):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train = y.iloc[train_idx]
        y_val = y.iloc[val_idx]

        # LightGBM
        train_set = lgb.Dataset(X_train, label=y_train)
        val_set = lgb.Dataset(X_val, label=y_val, reference=train_set)
        model = lgb.train(
            lgb_params,
            train_set,
            num_boost_round=2000,
            valid_sets=[val_set],
            callbacks=[lgb.early_stopping(100, verbose=False)],
        )
        oof_lgb[val_idx] = model.predict(X_val)

        # XGBoost
        model_xgb = xgb_sklearn.__class__(**xgb_params)
        model_xgb.fit(X_train, y_train)
        oof_xgb[val_idx] = model_xgb.predict_proba(X_val)[:, 1]

    # 拼接 OOF 预测作为元特征（回归用预测值，分类用概率）
    meta_X = pd.DataFrame({
        'lgb_proba': oof_lgb,
        'xgb_proba': oof_xgb,
    })

    # 第2层：训练元学习器
    print('    训练元学习器 (Logistic Regression)...')
    meta_learner = LogisticRegression(C=1.0, max_iter=1000, random_state=random_state)
    meta_learner.fit(meta_X, y)

    # 评估 OOF 结果
    oof_preds = meta_learner.predict_proba(meta_X)[:, 1]
    from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
    y_pred = (oof_preds >= 0.5).astype(int)

    oof_auc = float(roc_auc_score(y, oof_preds))
    oof_acc = float(accuracy_score(y, y_pred))
    oof_f1 = float(f1_score(y, y_pred, zero_division=0))

    print(f'    OOF AUC: {oof_auc:.4f}, Accuracy: {oof_acc:.4f}, F1: {oof_f1:.4f}')

    # 全量数据训练基学习器
    print('    全量训练基学习器...')
    train_set_full = lgb.Dataset(X, label=y)
    full_lgb = lgb.train(
        lgb_params,
        train_set_full,
        num_boost_round=2000,
        callbacks=[lgb.log_evaluation(0)],
    )
    full_xgb = xgb_sklearn.__class__(**xgb_params)
    full_xgb.fit(X, y)

    models = {
        'lgb': full_lgb,
        'xgb': full_xgb,
        'meta_learner': meta_learner,
        'oof_auc': oof_auc,
        'oof_accuracy': oof_acc,
        'oof_f1': oof_f1,
        'feature_names': ['lgb_proba', 'xgb_proba'],
    }

    metrics = {
        'oof_auc': round(oof_auc, 4),
        'oof_accuracy': round(oof_acc, 4),
        'oof_f1': round(oof_f1, 4),
    }

    print(f'    训练完成! OOF AUC={oof_auc:.4f}, F1={oof_f1:.4f}')
    return models, metrics


def predict_stacked_blood_sugar(
    X: pd.DataFrame,
    models: Dict[str, Any],
) -> np.ndarray:
    """使用 Stacking 融合模型预测血糖"""
    lgb_pred = models['lgb'].predict(X)
    xgb_pred = models['xgb'].predict(X)
    meta_X = pd.DataFrame({
        'lgb_oof': lgb_pred,
        'xgb_oof': xgb_pred,
    })
    return models['meta_learner'].predict(meta_X)


def predict_stacked_diabetes(
    X: pd.DataFrame,
    models: Dict[str, Any],
) -> np.ndarray:
    """使用 Stacking 融合模型预测糖尿病概率"""
    lgb_proba = models['lgb'].predict(X)
    xgb_proba = models['xgb'].predict_proba(X)[:, 1]
    meta_X = pd.DataFrame({
        'lgb_proba': lgb_proba,
        'xgb_proba': xgb_proba,
    })
    return models['meta_learner'].predict_proba(meta_X)[:, 1]


def save_ensemble_models(models: Dict[str, Any], metrics: Dict[str, float], name: str) -> str:
    """保存融合模型到文件"""
    os.makedirs(MODEL_DIR, exist_ok=True)
    path = os.path.join(MODEL_DIR, f'{name}_ensemble.joblib')
    joblib.dump(models, path)

    # 同时保存指标
    metrics_path = os.path.join(MODEL_DIR, f'{name}_ensemble_metrics.json')
    import json
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    return path


def load_ensemble_models(name: str) -> Tuple[Dict[str, Any], Dict[str, float]]:
    """加载融合模型和指标"""
    model_path = os.path.join(MODEL_DIR, f'{name}_ensemble.joblib')
    metrics_path = os.path.join(MODEL_DIR, f'{name}_ensemble_metrics.json')

    if not os.path.exists(model_path):
        raise FileNotFoundError(f'融合模型文件不存在: {model_path}')

    models = joblib.load(model_path)
    metrics = {}
    if os.path.exists(metrics_path):
        import json
        with open(metrics_path, 'r', encoding='utf-8') as f:
            metrics = json.load(f)

    return models, metrics
