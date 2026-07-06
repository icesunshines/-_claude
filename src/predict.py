# coding: utf-8
"""
预测逻辑模块
封装血糖预测、糖尿病分类、统计接口等业务逻辑
"""

import json
import os
import sys
from typing import Any, Dict, Optional

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from preprocessing import (
    load_metrics_meta,
    load_pipeline,
    preprocess_initial,
    preprocess_final,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'models')
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'data'))

_blood_sugar_model: Optional[lgb.Booster] = None
_diabetes_model: Optional[lgb.Booster] = None
_blood_sugar_pipeline = None
_diabetes_pipeline = None
_metrics_cache: Optional[Dict[str, Any]] = None
_stacked_bs_model: Optional[Dict[str, Any]] = None
_stacked_dm_model: Optional[Dict[str, Any]] = None


def _load_metrics() -> Dict[str, Any]:
    global _metrics_cache
    if _metrics_cache is None:
        _metrics_cache = load_metrics_meta()
    return _metrics_cache


PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))


def _load_lgb_model(filename: str) -> lgb.Booster:
    """LightGBM 无法读取中文绝对路径，使用相对路径加载"""
    rel_path = os.path.join('src', 'models', filename)
    cwd = os.getcwd()
    try:
        os.chdir(PROJECT_DIR)
        return lgb.Booster(model_file=rel_path)
    finally:
        os.chdir(cwd)


def get_blood_sugar_model() -> lgb.Booster:
    global _blood_sugar_model
    if _blood_sugar_model is None:
        _blood_sugar_model = _load_lgb_model('blood_sugar.lgb')
    return _blood_sugar_model


def get_diabetes_model() -> lgb.Booster:
    global _diabetes_model
    if _diabetes_model is None:
        _diabetes_model = _load_lgb_model('diabetes.lgb')
    return _diabetes_model


def get_blood_sugar_pipeline():
    global _blood_sugar_pipeline
    if _blood_sugar_pipeline is None:
        _blood_sugar_pipeline = load_pipeline('blood_sugar')
    return _blood_sugar_pipeline


def get_diabetes_pipeline():
    global _diabetes_pipeline
    if _diabetes_pipeline is None:
        _diabetes_pipeline = load_pipeline('diabetes')
    return _diabetes_pipeline


def predict_blood_sugar(request: Dict[str, Any]) -> Dict[str, Any]:
    """血糖预测"""
    model = get_blood_sugar_model()
    pipeline = get_blood_sugar_pipeline()
    df_row = pipeline.transform_request(request)
    pred = float(model.predict(df_row)[0])

    if pred < 5.6:
        risk_level = '正常'
        risk_score = max(0, 100 - (pred - 3.0) / 2.6 * 30)
    elif pred < 7.0:
        risk_level = '偏高'
        risk_score = 50 + (pred - 5.6) / 1.4 * 30
    else:
        risk_level = '高风险'
        risk_score = min(100, 80 + (pred - 7.0) / 31.43 * 20)

    return {
        'predicted_bgl': round(pred, 2),
        'risk_level': risk_level,
        'risk_score': round(risk_score, 1),
    }


def predict_diabetes(features: Dict[str, Any]) -> Dict[str, Any]:
    """糖尿病风险预测（二分类）"""
    model = get_diabetes_model()
    pipeline = get_diabetes_pipeline()
    df_row = pipeline.transform_features(features)
    prob = float(model.predict(df_row)[0])
    risk = 1 if prob >= 0.5 else 0
    return {'risk': risk, 'probability': round(prob, 4)}


def predict_diabetes_from_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """从结构化请求或 features 字典进行糖尿病预测"""
    if request_data.get('features'):
        features = request_data['features']
    else:
        features = {}
        skip_keys = {'features', 'snp_features'}
        for key, val in request_data.items():
            if key not in skip_keys and val is not None:
                features[key] = val
        if request_data.get('snp_features'):
            features.update(request_data['snp_features'])
    return predict_diabetes(features)


def get_blood_sugar_stats() -> Dict[str, Any]:
    """返回血糖统计数据（用于大屏展示，原始尺度）"""
    df = pd.read_csv(
        os.path.join(DATA_DIR, 'initial', 'd_train_20180102.csv'),
        encoding='gbk',
    )
    raw_df = df.copy()
    raw_df = raw_df.drop(
        columns=['乙肝表面抗原', '乙肝表面抗体', '乙肝e抗原', '乙肝e抗体', '乙肝核心抗体'],
        errors='ignore',
    )
    if raw_df['性别'].dtype == object:
        # 原始数据可能已为中文或需要映射
        raw_df['性别'] = pd.Categorical(raw_df['性别'], categories=['男', '女'], ordered=True).codes  # 0=男, 1=女

    df_processed = preprocess_initial(df)

    bins = [0, 4, 5.6, 7, 11.1, 50]
    labels = ['<4', '4-5.6', '5.6-7', '7-11.1', '>11.1']
    raw_df['bgl_bin'] = pd.cut(raw_df['血糖'], bins=bins, labels=labels)
    dist = raw_df['bgl_bin'].value_counts().sort_index()
    distribution = {str(k): int(v) for k, v in dist.items()}

    gender_group = raw_df.groupby('性别')['血糖'].agg(['mean', 'std', 'count']).round(2)
    gender_stats = {}
    for idx, row in gender_group.iterrows():
        mean_val = row['mean'] if np.isfinite(row['mean']) else 0.0
        std_val = row['std'] if np.isfinite(row['std']) else 0.0
        gender_stats[str(idx)] = {
            'mean': float(mean_val),
            'std': float(std_val),
            'count': int(row['count']),
        }

    raw_df['age_group'] = (raw_df['年龄'] // 10) * 10
    age_means = raw_df.groupby('age_group')['血糖'].mean().round(2)
    age_stats = {}
    for k, v in age_means.items():
        age_stats[str(k)] = float(v) if np.isfinite(v) else 0.0

    numeric_df = df_processed.select_dtypes(include=[np.number])
    corr = numeric_df.corr()['血糖'].drop('血糖', errors='ignore')
    corr = corr.abs().sort_values(ascending=False).head(10)
    top_corr = {}
    for col, val in corr.items():
        fval = float(val)
        if np.isfinite(fval):
            top_corr[str(col)] = round(fval, 3)

    return {
        'distribution': distribution,
        'gender_stats': gender_stats,
        'age_stats': age_stats,
        'top_correlation': top_corr,
    }


def get_diabetes_stats() -> Dict[str, Any]:
    """返回糖尿病分类统计数据（指标来自保存的 model_metrics）"""
    df = pd.read_csv(
        os.path.join(DATA_DIR, 'final', 'f_train_20180204.csv'),
        encoding='gbk',
    )

    clinical_cols = ['年龄', '孕前BMI', '收缩压', '舒张压', '糖筛孕周']
    available_cols = [c for c in clinical_cols if c in df.columns]
    comparison = {}
    for col in available_cols:
        comparison[col] = {
            'healthy_mean': round(float(df[df['label'] == 0][col].mean()), 2),
            'patient_mean': round(float(df[df['label'] == 1][col].mean()), 2),
        }

    # 雷达图数据：6个临床指标的健康群体 vs 患者群体均值
    radar_labels = ['年龄', '孕前BMI', '收缩压', '舒张压', '糖筛孕周', '空腹血糖']
    radar_comparison = {}
    for col in radar_labels:
        if col in df.columns:
            radar_comparison[col] = {
                'healthy_mean': round(float(df[df['label'] == 0][col].mean()), 2),
                'patient_mean': round(float(df[df['label'] == 1][col].mean()), 2),
            }

    metrics = _load_metrics().get('diabetes', {}).get('validation', {})
    if not metrics:
        model = get_diabetes_model()
        pipeline = get_diabetes_pipeline()
        X_scaled, y_true = pipeline.transform_df(df, has_label=True)
        probs = model.predict(X_scaled)
        preds = (probs >= 0.5).astype(int)
        metrics = {
            'auc': round(float(roc_auc_score(y_true, probs)), 4),
            'accuracy': round(float(accuracy_score(y_true, preds)), 4),
            'precision': round(float(precision_score(y_true, preds, zero_division=0)), 4),
            'recall': round(float(recall_score(y_true, preds, zero_division=0)), 4),
            'f1': round(float(f1_score(y_true, preds, zero_division=0)), 4),
            'patient_ratio': round(float(y_true.mean()), 4),
        }

    roc_data = _load_metrics().get('diabetes', {}).get('roc_curve', {})
    confusion = _load_metrics().get('diabetes', {}).get('confusion_matrix', {})

    return {
        'clinical_comparison': comparison,
        'radar_comparison': radar_comparison,
        'model_metrics': metrics,
        'roc_curve': roc_data,
        'confusion_matrix': confusion,
    }


def get_stats_overview() -> Dict[str, Any]:
    """大屏 KPI 概览"""
    metrics = _load_metrics()
    bs_train = pd.read_csv(
        os.path.join(DATA_DIR, 'initial', 'd_train_20180102.csv'),
        encoding='gbk',
    )
    dm_train = pd.read_csv(
        os.path.join(DATA_DIR, 'final', 'f_train_20180204.csv'),
        encoding='gbk',
    )

    bs_metrics = metrics.get('blood_sugar', {})
    dm_metrics = metrics.get('diabetes', {})

    return {
        'sample_count_initial': len(bs_train),
        'sample_count_final': len(dm_train),
        'feature_count_blood_sugar': bs_metrics.get('feature_count', 35),
        'feature_count_diabetes': dm_metrics.get('feature_count', 0),
        'mean_blood_sugar': round(float(bs_train['血糖'].mean()), 2),
        'blood_sugar_metrics': bs_metrics.get('validation', {}),
        'diabetes_metrics': dm_metrics.get('validation', {}),
        'blood_sugar_test_metrics': bs_metrics.get('test', {}),
        'diabetes_test_metrics': dm_metrics.get('test', {}),
    }


def get_feature_importance(model_type: str = 'blood_sugar', top_n: int = 20) -> Dict[str, Any]:
    """返回特征重要性数据"""
    if model_type == 'blood_sugar':
        model = get_blood_sugar_model()
    else:
        model = get_diabetes_model()

    importance = model.feature_importance(importance_type='gain')
    features = model.feature_name()
    sorted_idx = np.argsort(importance)[::-1][:top_n]
    return {
        'features': [features[i] for i in sorted_idx],
        'values': [float(importance[i]) for i in sorted_idx],
    }


def get_blood_sugar_feature_means() -> Dict[str, Any]:
    """返回训练集特征中位数，供前端「填入样本均值」"""
    from preprocessing import BLOOD_SUGAR_COL_MAPPING

    pipeline = get_blood_sugar_pipeline()
    means = pipeline.feature_means.copy()
    reverse = {v: k for k, v in BLOOD_SUGAR_COL_MAPPING.items()}
    result: Dict[str, Any] = {}
    for model_col, val in means.items():
        if model_col == '性别':
            result['性别'] = '男' if val == 0 else '女'
        elif model_col == '年龄':
            result['年龄'] = int(round(float(val)))
        elif model_col in reverse:
            result[reverse[model_col]] = round(float(val), 2)
        elif model_col == '白蛋白':
            result['白蛋白'] = round(float(val), 2)
    if '性别' not in result:
        result['性别'] = '男'
    if '年龄' not in result:
        result['年龄'] = 40
    return result


# ========== Stacking 融合预测接口 ==========
# 对应论文中的集成学习优化章节。
# 前端通过单模型/融合模型切换，可直观对比 LightGBM 单模型与
# LightGBM + XGBoost Stacking 融合模型的预测效果。

def get_stacked_blood_sugar_model() -> Dict[str, Any]:
    """懒加载融合血糖模型

    使用模块级缓存，避免每次预测都重新加载 joblib 文件。
    模型文件由训练脚本写入 src/models/blood_sugar_ensemble.joblib。
    """
    global _stacked_bs_model
    if _stacked_bs_model is None:
        from ensemble import load_ensemble_models
        _stacked_bs_model, _ = load_ensemble_models('blood_sugar')
    return _stacked_bs_model


def get_stacked_diabetes_model() -> Dict[str, Any]:
    """懒加载融合糖尿病模型"""
    global _stacked_dm_model
    if _stacked_dm_model is None:
        from ensemble import load_ensemble_models
        _stacked_dm_model, _ = load_ensemble_models('diabetes')
    return _stacked_dm_model


def predict_blood_sugar_ensemble(request: Dict[str, Any]) -> Dict[str, Any]:
    """血糖融合预测

    流程：
    1. 复用单模型相同的预处理 pipeline，保证特征空间一致
    2. 使用 Stacking 融合模型进行预测（Ridge 元学习器融合 LightGBM/XGBoost）
    3. 返回结构与单模型一致，方便前端直接替换
    """
    model = get_stacked_blood_sugar_model()
    pipeline = get_blood_sugar_pipeline()
    df_row = pipeline.transform_request(request)
    pred = float(predict_stacked_blood_sugar(df_row, model)[0])

    if pred < 5.6:
        risk_level = '正常'
        risk_score = max(0, 100 - (pred - 3.0) / 2.6 * 30)
    elif pred < 7.0:
        risk_level = '偏高'
        risk_score = 50 + (pred - 5.6) / 1.4 * 30
    else:
        risk_level = '高风险'
        risk_score = min(100, 80 + (pred - 7.0) / 31.43 * 20)

    return {
        'predicted_bgl': round(pred, 2),
        'risk_level': risk_level,
        'risk_score': round(risk_score, 1),
    }


def predict_diabetes_ensemble(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """糖尿病融合预测

    兼容两种请求格式：
    - 完整结构化请求：直接提取数值字段
    - features 字典：从 features 字段读取
    """
    model = get_stacked_diabetes_model()
    pipeline = get_diabetes_pipeline()

    if request_data.get('features'):
        features = request_data['features']
    else:
        features = {}
        skip_keys = {'features', 'snp_features'}
        for key, val in request_data.items():
            if key not in skip_keys and val is not None:
                features[key] = val
        if request_data.get('snp_features'):
            features.update(request_data['snp_features'])

    df_row = pipeline.transform_features(features)
    prob = float(predict_stacked_diabetes(df_row, model)[0])
    risk = 1 if prob >= 0.5 else 0
    return {'risk': risk, 'probability': round(prob, 4)}


def predict_diabetes_ensemble_from_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """从结构化请求进行糖尿病融合预测

    保持与主路由兼容的入口命名，内部委托给 predict_diabetes_ensemble。
    """
    return predict_diabetes_ensemble(request_data)


def get_ensemble_comparison() -> Dict[str, Any]:
    """返回单一模型与融合模型的效果对比

    注意：ensemble 指标在 model_metrics.json 中的存储方式与单模型不同。
    - 单模型指标：metrics['blood_sugar']['validation'] / metrics['diabetes']['validation']
    - 融合模型指标：metrics['blood_sugar_ensemble']['oof_*'] / metrics['diabetes_ensemble']['oof_*']

    因此这里需要做一次结构适配，让前端统一使用 single/ensemble 两列展示。
    """
    metrics = _load_metrics()
    bs_single = metrics.get('blood_sugar', {}).get('validation', {})
    bs_ensemble_raw = metrics.get('blood_sugar_ensemble', {})
    dm_single = metrics.get('diabetes', {}).get('validation', {})
    dm_ensemble_raw = metrics.get('diabetes_ensemble', {})

    # ensemble 指标可能直接存顶层，也可能有 validation 子键
    if 'validation' not in bs_ensemble_raw and 'oof_rmse' in bs_ensemble_raw:
        bs_ensemble_metrics = {
            'rmse': bs_ensemble_raw.get('oof_rmse'),
            'r2': bs_ensemble_raw.get('oof_r2'),
            'mae': bs_ensemble_raw.get('oof_mae'),
        }
    else:
        bs_ensemble_metrics = bs_ensemble_raw.get('validation', {})

    if 'validation' not in dm_ensemble_raw and 'oof_auc' in dm_ensemble_raw:
        dm_ensemble_metrics = {
            'auc': dm_ensemble_raw.get('oof_auc'),
            'accuracy': dm_ensemble_raw.get('oof_accuracy'),
            'precision': dm_ensemble_raw.get('oof_precision'),
            'recall': dm_ensemble_raw.get('oof_recall'),
            'f1': dm_ensemble_raw.get('oof_f1'),
        }
    else:
        dm_ensemble_metrics = dm_ensemble_raw.get('validation', {})

    return {
        'blood_sugar': {'single': bs_single, 'ensemble': bs_ensemble_metrics},
        'diabetes': {'single': dm_single, 'ensemble': dm_ensemble_metrics},
    }


def predict_stacked_blood_sugar(
    X: pd.DataFrame, models: Dict[str, Any],
) -> np.ndarray:
    """使用 Stacking 融合模型预测血糖

    models 结构：
    - models['lgb']：全量数据训练的 LightGBM 基学习器
    - models['xgb']：全量数据训练的 XGBoost 基学习器
    - models['meta_learner']：第二层 Ridge 元学习器
    """
    from ensemble import predict_stacked_blood_sugar as _pred
    return _pred(X, models)


def predict_stacked_diabetes(
    X: pd.DataFrame, models: Dict[str, Any],
) -> np.ndarray:
    """使用 Stacking 融合模型预测糖尿病概率

    与回归任务的区别：基学习器输出概率，元学习器输入为 [lgb_proba, xgb_proba]。
    """
    from ensemble import predict_stacked_diabetes as _pred
    return _pred(X, models)
