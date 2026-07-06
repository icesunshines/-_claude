# coding: utf-8
"""
模型训练脚本
训练血糖预测模型（回归）和糖尿病分类模型（二分类），保存 pipeline 与评估指标
"""

import os
import sys

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import StratifiedKFold, train_test_split

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from preprocessing import (
    fit_final_pipeline,
    fit_initial_pipeline,
    save_metrics_meta,
    save_pipeline,
)
from ensemble import (
    predict_stacked_blood_sugar,
    predict_stacked_diabetes,
    save_ensemble_models,
    train_stacked_blood_sugar,
    train_stacked_diabetes,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'models')
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'data'))


def _save_model(model: lgb.Booster, filename: str) -> str:
    os.makedirs(MODEL_DIR, exist_ok=True)
    rel_path = os.path.join('src', 'models', filename)
    model.save_model(rel_path)
    return rel_path


def _evaluate_regression(y_true, y_pred) -> dict:
    mse = mean_squared_error(y_true, y_pred)
    return {
        'mse': round(float(mse), 4),
        'rmse': round(float(np.sqrt(mse)), 4),
        'mae': round(float(mean_absolute_error(y_true, y_pred)), 4),
        'r2': round(float(r2_score(y_true, y_pred)), 4),
    }


def _evaluate_classification(y_true, y_prob, threshold: float = 0.5) -> dict:
    y_pred = (y_prob >= threshold).astype(int)
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    cm = confusion_matrix(y_true, y_pred)
    return {
        'auc': round(float(roc_auc_score(y_true, y_prob)), 4),
        'accuracy': round(float(accuracy_score(y_true, y_pred)), 4),
        'precision': round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        'recall': round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        'f1': round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        'patient_ratio': round(float(np.mean(y_true)), 4),
        'roc_curve': {
            'fpr': [round(float(x), 4) for x in fpr.tolist()],
            'tpr': [round(float(x), 4) for x in tpr.tolist()],
        },
        'confusion_matrix': {
            'tn': int(cm[0, 0]),
            'fp': int(cm[0, 1]),
            'fn': int(cm[1, 0]),
            'tp': int(cm[1, 1]),
        },
    }


def _load_blood_sugar_test() -> tuple[pd.DataFrame, pd.Series]:
    test_df = pd.read_csv(
        os.path.join(DATA_DIR, 'initial', 'd_test_A_20180102.csv'),
        encoding='gbk',
    )
    answers = pd.read_csv(
        os.path.join(DATA_DIR, 'initial', 'd_answer_a_20180128.csv'),
        encoding='gbk',
    )
    y = answers.iloc[:, 0].astype(float)
    return test_df, y


def _load_diabetes_test() -> tuple[pd.DataFrame, pd.Series]:
    test_df = pd.read_csv(
        os.path.join(DATA_DIR, 'final', 'f_test_a_20180204.csv'),
        encoding='gbk',
    )
    answers = pd.read_csv(
        os.path.join(DATA_DIR, 'final', 'f_answer_a_20180306.csv'),
        encoding='gbk',
        header=None,
        names=['label'],
    )
    y = answers['label'].astype(int)
    return test_df, y


def _tune_blood_sugar_params(X, y) -> dict:
    """5-Fold CV 选择 num_leaves 与 min_data_in_leaf"""
    candidates = [
        {'num_leaves': 31, 'min_data_in_leaf': 50},
        {'num_leaves': 63, 'min_data_in_leaf': 100},
        {'num_leaves': 127, 'min_data_in_leaf': 80},
    ]
    best_params = candidates[1]
    best_rmse = float('inf')
    kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    y_bins = pd.qcut(y, q=5, duplicates='drop', labels=False)

    for cand in candidates:
        scores = []
        for train_idx, val_idx in kf.split(X, y_bins):
            X_tr, X_va = X.iloc[train_idx], X.iloc[val_idx]
            y_tr, y_va = y.iloc[train_idx], y.iloc[val_idx]
            train_set = lgb.Dataset(X_tr, label=y_tr)
            val_set = lgb.Dataset(X_va, label=y_va, reference=train_set)
            params = {
                'objective': 'regression',
                'boosting': 'gbdt',
                'learning_rate': 0.01,
                'num_leaves': cand['num_leaves'],
                'min_data_in_leaf': cand['min_data_in_leaf'],
                'num_threads': 4,
                'lambda_l1': 0.01,
                'lambda_l2': 0.01,
                'metric': 'rmse',
                'feature_fraction': 0.7,
                'bagging_fraction': 0.7,
                'bagging_freq': 5,
                'verbose': -1,
            }
            model = lgb.train(
                params,
                train_set,
                num_boost_round=2000,
                valid_sets=[val_set],
                callbacks=[lgb.early_stopping(100, verbose=False)],
            )
            pred = model.predict(X_va)
            scores.append(np.sqrt(mean_squared_error(y_va, pred)))
        mean_rmse = float(np.mean(scores))
        print(f"  CV num_leaves={cand['num_leaves']}, min_data={cand['min_data_in_leaf']} -> RMSE={mean_rmse:.4f}")
        if mean_rmse < best_rmse:
            best_rmse = mean_rmse
            best_params = cand
    print(f"  最优参数: {best_params}, CV RMSE={best_rmse:.4f}")
    return best_params


def train_blood_sugar_model() -> lgb.Booster:
    print('加载初赛数据...')
    df = pd.read_csv(os.path.join(DATA_DIR, 'initial', 'd_train_20180102.csv'), encoding='gbk')
    print(f'原始数据: {df.shape}')

    X, y, pipeline = fit_initial_pipeline(df)
    print(f'预处理后: X={X.shape}, 特征数={len(pipeline.feature_cols)}')
    save_pipeline(pipeline, 'blood_sugar')

    tuned = _tune_blood_sugar_params(X, y)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    params = {
        'objective': 'regression',
        'boosting': 'gbdt',
        'learning_rate': 0.01,
        'num_leaves': tuned['num_leaves'],
        'min_data_in_leaf': tuned['min_data_in_leaf'],
        'num_threads': 4,
        'lambda_l1': 0.01,
        'lambda_l2': 0.01,
        'metric': 'rmse',
        'feature_fraction': 0.7,
        'bagging_fraction': 0.7,
        'bagging_freq': 5,
        'verbose': -1,
    }

    train_set = lgb.Dataset(X_train, label=y_train)
    val_set = lgb.Dataset(X_val, label=y_val, reference=train_set)
    print('开始训练血糖模型...')
    model = lgb.train(
        params,
        train_set,
        num_boost_round=3000,
        valid_sets=[val_set],
        callbacks=[lgb.early_stopping(100), lgb.log_evaluation(200)],
    )

    val_pred = model.predict(X_val)
    val_metrics = _evaluate_regression(y_val, val_pred)

    test_df, test_y = _load_blood_sugar_test()
    X_test, _ = pipeline.transform_df(test_df, has_label=False)
    test_pred = model.predict(X_test)
    test_metrics = _evaluate_regression(test_y, test_pred)

    print('=' * 60)
    print('血糖预测模型 - 验证集:')
    for k, v in val_metrics.items():
        print(f'  {k}: {v}')
    print('血糖预测模型 - 官方测试集:')
    for k, v in test_metrics.items():
        print(f'  {k}: {v}')
    print('=' * 60)

    _save_model(model, 'blood_sugar.lgb')
    return model, pipeline, val_metrics, test_metrics


def train_diabetes_model() -> lgb.Booster:
    print('加载复赛数据...')
    df = pd.read_csv(os.path.join(DATA_DIR, 'final', 'f_train_20180204.csv'), encoding='gbk')
    print(f'原始数据: {df.shape}')

    X, y, pipeline = fit_final_pipeline(df)
    print(f'预处理后: X={X.shape}, 特征数={len(pipeline.feature_cols)}')
    save_pipeline(pipeline, 'diabetes')

    pos_ratio = float(y.mean())
    scale_pos_weight = (1 - pos_ratio) / pos_ratio if pos_ratio > 0 else 1.0

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    params = {
        'objective': 'binary',
        'boosting': 'gbdt',
        'learning_rate': 0.05,
        'num_leaves': 31,
        'min_data_in_leaf': 20,
        'num_threads': 4,
        'lambda_l1': 0.1,
        'lambda_l2': 0.1,
        'metric': 'auc',
        'scale_pos_weight': scale_pos_weight,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1,
    }

    train_set = lgb.Dataset(X_train, label=y_train)
    val_set = lgb.Dataset(X_val, label=y_val, reference=train_set)
    print('开始训练糖尿病模型...')
    model = lgb.train(
        params,
        train_set,
        num_boost_round=2000,
        valid_sets=[val_set],
        callbacks=[lgb.early_stopping(100), lgb.log_evaluation(200)],
    )

    val_prob = model.predict(X_val)
    val_result = _evaluate_classification(y_val, val_prob)
    val_metrics = {k: v for k, v in val_result.items() if k not in ('roc_curve', 'confusion_matrix')}
    val_roc = val_result['roc_curve']
    val_cm = val_result['confusion_matrix']

    test_df, test_y = _load_diabetes_test()
    X_test, _ = pipeline.transform_df(test_df, has_label=False)
    test_prob = model.predict(X_test)
    test_result = _evaluate_classification(test_y, test_prob)
    test_metrics = {k: v for k, v in test_result.items() if k not in ('roc_curve', 'confusion_matrix')}
    test_roc = test_result['roc_curve']
    test_cm = test_result['confusion_matrix']

    print('=' * 60)
    print('糖尿病分类模型 - 验证集:')
    for k, v in val_metrics.items():
        print(f'  {k}: {v}')
    print('糖尿病分类模型 - 官方测试集:')
    for k, v in test_metrics.items():
        print(f'  {k}: {v}')
    print('=' * 60)

    _save_model(model, 'diabetes.lgb')
    return model, pipeline, val_metrics, test_metrics, val_roc, val_cm, test_roc, test_cm


if __name__ == '__main__':
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.chdir(os.path.join(BASE_DIR, '..'))

    print('#' * 60)
    print('# 血糖预测模型训练')
    print('#' * 60)
    _, bs_pipeline, bs_val, bs_test = train_blood_sugar_model()

    print()
    print('#' * 60)
    print('# 糖尿病分类模型训练')
    print('#' * 60)
    _, dm_pipeline, dm_val, dm_test, dm_val_roc, dm_val_cm, dm_test_roc, dm_test_cm = train_diabetes_model()

    # ========== 准备融合训练数据 ==========
    # 从预处理管道获取训练数据（用于融合模型训练）
    print()
    print('#' * 60)
    print('# 准备融合训练数据')
    print('#' * 60)

    # 血糖预处理
    print('加载初赛数据用于融合训练...')
    bs_train_df = pd.read_csv(
        os.path.join(DATA_DIR, 'initial', 'd_train_20180102.csv'),
        encoding='gbk',
    )
    bs_X, bs_y, _ = fit_initial_pipeline(bs_train_df)
    bs_train_full, bs_test_full = train_test_split(
        bs_train_df, test_size=0.2, random_state=42,
    )
    bs_X_full, _ = bs_pipeline.transform_df(bs_train_full, has_label=False)
    bs_y_full = bs_train_full['血糖'].astype(float)
    bs_X_test, _ = bs_pipeline.transform_df(bs_test_full, has_label=False)
    bs_y_test = bs_test_full['血糖'].astype(float)

    # 糖尿病预处理
    print('加载复赛数据用于融合训练...')
    dm_train_df = pd.read_csv(
        os.path.join(DATA_DIR, 'final', 'f_train_20180204.csv'),
        encoding='gbk',
    )
    dm_X, dm_y, _ = fit_final_pipeline(dm_train_df)
    dm_train_full, dm_test_full = train_test_split(
        dm_train_df, test_size=0.2, random_state=42, stratify=dm_train_df['label'],
    )
    dm_X_full, _ = dm_pipeline.transform_df(dm_train_full, has_label=False)
    dm_y_full = dm_train_full['label'].astype(int)
    dm_X_test, _ = dm_pipeline.transform_df(dm_test_full, has_label=False)
    dm_y_test = dm_test_full['label'].astype(int)

    # ========== Stacking 融合模型训练 ==========
    print()
    print('#' * 60)
    print('# Stacking 融合模型训练')
    print('#' * 60)

    # 血糖融合
    print()
    print('训练血糖融合模型...')
    bs_ensemble_models, bs_ensemble_metrics = train_stacked_blood_sugar(bs_X_full, bs_y_full)
    bs_ensemble_path = save_ensemble_models(
        bs_ensemble_models, bs_ensemble_metrics, 'blood_sugar'
    )
    print(f'  模型已保存: {bs_ensemble_path}')

    # 用官方测试集评估（融合模型已经在训练集上做了OOF评估）
    test_pred_stacked = predict_stacked_blood_sugar(bs_X_test, bs_ensemble_models)
    test_metrics_stacked = _evaluate_regression(bs_y_test, test_pred_stacked)

    print('  血糖融合模型 - OOF评估:')
    print(f'    RMSE: {bs_ensemble_metrics["oof_rmse"]}, R2: {bs_ensemble_metrics["oof_r2"]}')
    print('  血糖融合模型 - 官方测试集:')
    for k, v in test_metrics_stacked.items():
        print(f'    {k}: {v}')

    bs_ensemble_metrics['test'] = test_metrics_stacked

    # 糖尿病融合
    print()
    print('训练糖尿病融合模型...')
    dm_ensemble_models, dm_ensemble_metrics = train_stacked_diabetes(dm_X_full, dm_y_full)
    dm_ensemble_path = save_ensemble_models(
        dm_ensemble_models, dm_ensemble_metrics, 'diabetes'
    )
    print(f'  模型已保存: {dm_ensemble_path}')

    # 用官方测试集评估（融合模型已经在训练集上做了OOF评估）
    test_prob_stacked = predict_stacked_diabetes(dm_X_test, dm_ensemble_models)
    test_result_stacked = _evaluate_classification(dm_y_test, test_prob_stacked)
    test_metrics_dm_stacked = {k: v for k, v in test_result_stacked.items() if k not in ('roc_curve', 'confusion_matrix')}

    print('  糖尿病融合模型 - OOF评估:')
    print(f'    AUC: {dm_ensemble_metrics["oof_auc"]}, F1: {dm_ensemble_metrics["oof_f1"]}')
    print('  糖尿病融合模型 - 官方测试集:')
    for k, v in test_metrics_dm_stacked.items():
        print(f'    {k}: {v}')

    dm_ensemble_metrics['test'] = test_metrics_dm_stacked

    # 汇总所有指标
    # 关键点：blood_sugar_ensemble / diabetes_ensemble 单独存为顶层键，
    # 供前端和 Dashboard 的模型对比模块直接读取。
    all_metrics = {
        'blood_sugar': {
            'feature_count': len(bs_pipeline.feature_cols),
            'validation': bs_val,
            'test': bs_test,
        },
        'diabetes': {
            'feature_count': len(dm_pipeline.feature_cols),
            'validation': dm_val,
            'test': dm_test,
            'roc_curve': dm_test_roc,
            'confusion_matrix': dm_test_cm,
            'validation_roc_curve': dm_val_roc,
            'validation_confusion_matrix': dm_val_cm,
        },
        'blood_sugar_ensemble': bs_ensemble_metrics,
        'diabetes_ensemble': dm_ensemble_metrics,
    }
    save_metrics_meta(all_metrics)
    print()
    print('全部训练完成！指标已保存到 src/models/model_metrics.json')
