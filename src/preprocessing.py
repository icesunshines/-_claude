# coding: utf-8
"""
数据预处理模块
处理初赛（血糖预测）和复赛（糖尿病分类）数据，支持 fit/transform 与 joblib 持久化
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from pandas.api.types import is_object_dtype
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'models')

# 前端字段名 -> 模型特征名
BLOOD_SUGAR_COL_MAPPING = {
    '天门冬氨酸氨基转换酶': '*天门冬氨酸氨基转换酶',
    '丙氨酸氨基转换酶': '*丙氨酸氨基转换酶',
    '碱性磷酸酶': '*碱性磷酸酶',
    'r_谷氨酰基转换酶': '*r-谷氨酰基转换酶',
    '总蛋白': '*总蛋白',
    '白蛋白': '白蛋白',
    '球蛋白': '*球蛋白',
    '白球比例': '白球比例',
    '甘油三酯': '甘油三酯',
    '总胆固醇': '总胆固醇',
    '高密度脂蛋白胆固醇': '高密度脂蛋白胆固醇',
    '低密度脂蛋白胆固醇': '低密度脂蛋白胆固醇',
    '尿素': '尿素',
    '肌酐': '肌酐',
    '尿酸': '尿酸',
    '白细胞计数': '白细胞计数',
    '红细胞计数': '红细胞计数',
    '血红蛋白': '血红蛋白',
    '红细胞压积': '红细胞压积',
    '红细胞平均体积': '红细胞平均体积',
    '红细胞平均血红蛋白量': '红细胞平均血红蛋白量',
    '红细胞平均血红蛋白浓度': '红细胞平均血红蛋白浓度',
    '红细胞体积分布宽度': '红细胞体积分布宽度',
    '血小板计数': '血小板计数',
    '血小板平均体积': '血小板平均体积',
    '血小板体积分布宽度': '血小板体积分布宽度',
    '血小板比积': '血小板比积',
    '中性粒细胞百分比': '中性粒细胞%',
    '淋巴细胞百分比': '淋巴细胞%',
    '单核细胞百分比': '单核细胞%',
    '嗜酸细胞百分比': '嗜酸细胞%',
    '嗜碱细胞百分比': '嗜碱细胞%',
}

HEPATITIS_COLS = ['乙肝表面抗原', '乙肝表面抗体', '乙肝e抗原', '乙肝e抗体', '乙肝核心抗体']
LOG_COLS_INITIAL = ['甘油三酯', '尿酸']


@dataclass
class InitialPipeline:
    """初赛血糖预测预处理 Pipeline"""

    feature_cols: List[str] = field(default_factory=list)
    label_col: str = '血糖'
    log_cols: List[str] = field(default_factory=lambda: LOG_COLS_INITIAL.copy())
    imputer: SimpleImputer = field(default_factory=lambda: SimpleImputer(strategy='median'))
    scaler: StandardScaler = field(default_factory=StandardScaler)
    feature_means: Dict[str, float] = field(default_factory=dict)

    def _clean_raw(self, df: pd.DataFrame, drop_outliers: bool = True) -> pd.DataFrame:
        df = df.copy()
        df = df.drop(columns=[c for c in HEPATITIS_COLS if c in df.columns], errors='ignore')
        if '性别' in df.columns and is_object_dtype(df['性别']):
            df['性别'] = df['性别'].map({'男': 0, '女': 1})
        df['性别'] = pd.to_numeric(df['性别'], errors='coerce')
        df = df.drop(columns=['id', '体检日期'], errors='ignore')
        if drop_outliers and self.label_col in df.columns:
            df = df[df[self.label_col] <= 30]
        for col in self.log_cols:
            if col in df.columns:
                df[col] = np.log1p(df[col].clip(lower=0))
        return df

    def fit(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        cleaned = self._clean_raw(df, drop_outliers=True)
        if self.label_col not in cleaned.columns:
            raise ValueError(f'标签列 {self.label_col} 不存在')

        y = cleaned[self.label_col].astype(float)
        X_raw = cleaned.drop(columns=[self.label_col])
        self.feature_cols = list(X_raw.columns)

        # 处理全为 NaN 的列：imputer 会跳过这类列，导致后续形状不匹配
        all_nan_cols = [col for col in self.feature_cols if X_raw[col].isna().all()]
        if all_nan_cols:
            X_raw = X_raw.drop(columns=all_nan_cols)
            self.feature_cols = [c for c in self.feature_cols if c not in all_nan_cols]

        X_imputed = pd.DataFrame(
            self.imputer.fit_transform(X_raw),
            columns=self.feature_cols,
            index=X_raw.index,
        )
        X_scaled = pd.DataFrame(
            self.scaler.fit_transform(X_imputed),
            columns=self.feature_cols,
            index=X_raw.index,
        )
        self.feature_means = X_raw.median(numeric_only=True).to_dict()
        return X_scaled, y

    def _request_to_row(self, request: Dict[str, Any]) -> Dict[str, Any]:
        gender_val = request.get('性别', '男')
        gender = 0 if gender_val == '男' else 1
        row: Dict[str, Any] = {'性别': gender, '年龄': request.get('年龄')}
        for front_key, model_key in BLOOD_SUGAR_COL_MAPPING.items():
            if front_key in request and request[front_key] is not None:
                row[model_key] = request[front_key]
            elif model_key in self.feature_means:
                row[model_key] = self.feature_means[model_key]
        return row

    def transform_request(self, request: Dict[str, Any]) -> pd.DataFrame:
        if not self.feature_cols:
            raise RuntimeError('Pipeline 尚未 fit，请先训练或加载 artifacts')

        row = self._request_to_row(request)
        df_row = pd.DataFrame([row])
        for col in self.feature_cols:
            if col not in df_row.columns:
                df_row[col] = self.feature_means.get(col, np.nan)
        df_row = df_row[self.feature_cols]
        for col in self.log_cols:
            if col in df_row.columns:
                df_row[col] = np.log1p(df_row[col].clip(lower=0).astype(float))

        imputed = self.imputer.transform(df_row)
        scaled = self.scaler.transform(imputed)
        return pd.DataFrame(scaled, columns=self.feature_cols)

    def transform_df(self, df: pd.DataFrame, has_label: bool = False) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
        cleaned = self._clean_raw(df, drop_outliers=False)
        y = None
        if has_label and self.label_col in cleaned.columns:
            y = cleaned[self.label_col].astype(float)
            cleaned = cleaned.drop(columns=[self.label_col])

        for col in self.feature_cols:
            if col not in cleaned.columns:
                cleaned[col] = np.nan
        cleaned = cleaned[self.feature_cols]
        for col in self.log_cols:
            if col in cleaned.columns:
                cleaned[col] = np.log1p(cleaned[col].clip(lower=0))

        imputed = self.imputer.transform(cleaned)
        scaled = self.scaler.transform(imputed)
        return pd.DataFrame(scaled, columns=self.feature_cols, index=cleaned.index), y


@dataclass
class FinalPipeline:
    """复赛糖尿病分类预处理 Pipeline"""

    feature_cols: List[str] = field(default_factory=list)
    label_col: str = 'label'
    dropped_cols: List[str] = field(default_factory=list)
    imputer: SimpleImputer = field(default_factory=lambda: SimpleImputer(strategy='median'))
    scaler: StandardScaler = field(default_factory=StandardScaler)
    feature_means: Dict[str, float] = field(default_factory=dict)

    def _clean_raw(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        null_ratio = df.isnull().sum() / len(df)
        high_missing = null_ratio[null_ratio > 0.8].index.tolist()
        self.dropped_cols = high_missing
        df = df.drop(columns=high_missing, errors='ignore')

        snp_cols = [c for c in df.columns if c.startswith('SNP') or c == 'ACEID']
        for col in snp_cols:
            if col in df.columns and df[col].isnull().sum() / len(df) > 0.5:
                df = df.drop(columns=[col], errors='ignore')

        df = df.drop(columns=['id'], errors='ignore')
        non_numeric = df.select_dtypes(include=['object']).columns.tolist()
        for col in non_numeric:
            if col == self.label_col:
                continue
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df

    def fit(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        cleaned = self._clean_raw(df)
        if self.label_col not in cleaned.columns:
            raise ValueError(f'标签列 {self.label_col} 不存在')

        y = cleaned[self.label_col].astype(int)
        X_raw = cleaned.drop(columns=[self.label_col])
        self.feature_cols = list(X_raw.columns)

        X_imputed = pd.DataFrame(
            self.imputer.fit_transform(X_raw),
            columns=self.feature_cols,
            index=X_raw.index,
        )
        X_scaled = pd.DataFrame(
            self.scaler.fit_transform(X_imputed),
            columns=self.feature_cols,
            index=X_raw.index,
        )
        self.feature_means = X_raw.median(numeric_only=True).to_dict()
        return X_scaled, y

    def transform_features(self, features: Dict[str, Any]) -> pd.DataFrame:
        if not self.feature_cols:
            raise RuntimeError('Pipeline 尚未 fit，请先训练或加载 artifacts')

        row = {}
        for col in self.feature_cols:
            if col in features and features[col] is not None:
                row[col] = features[col]
            else:
                row[col] = self.feature_means.get(col, np.nan)
        df_row = pd.DataFrame([row])[self.feature_cols]
        imputed = self.imputer.transform(df_row)
        scaled = self.scaler.transform(imputed)
        return pd.DataFrame(scaled, columns=self.feature_cols)

    def transform_df(self, df: pd.DataFrame, has_label: bool = False) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
        cleaned = self._clean_raw(df)
        y = None
        if has_label and self.label_col in cleaned.columns:
            y = cleaned[self.label_col].astype(int)
            cleaned = cleaned.drop(columns=[self.label_col])

        for col in self.feature_cols:
            if col not in cleaned.columns:
                cleaned[col] = np.nan
        cleaned = cleaned[self.feature_cols]
        imputed = self.imputer.transform(cleaned)
        scaled = self.scaler.transform(imputed)
        return pd.DataFrame(scaled, columns=self.feature_cols, index=cleaned.index), y


def save_pipeline(pipeline: Any, name: str) -> str:
    os.makedirs(MODEL_DIR, exist_ok=True)
    path = os.path.join(MODEL_DIR, f'{name}_pipeline.joblib')
    joblib.dump(pipeline, path)
    return path


def load_pipeline(name: str) -> Any:
    path = os.path.join(MODEL_DIR, f'{name}_pipeline.joblib')
    if not os.path.exists(path):
        raise FileNotFoundError(f'Pipeline 文件不存在: {path}')
    return joblib.load(path)


def save_metrics_meta(metrics: Dict[str, Any], name: str = 'model_metrics') -> str:
    os.makedirs(MODEL_DIR, exist_ok=True)
    path = os.path.join(MODEL_DIR, f'{name}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    return path


def load_metrics_meta(name: str = 'model_metrics') -> Dict[str, Any]:
    path = os.path.join(MODEL_DIR, f'{name}.json')
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ---- 兼容旧接口（统计图表仍使用原始尺度数据） ----

def preprocess_initial(df: pd.DataFrame) -> pd.DataFrame:
    """预处理初赛数据（用于统计展示，含血糖列，原始尺度）"""
    df = df.copy()
    df = df.drop(columns=[c for c in HEPATITIS_COLS if c in df.columns], errors='ignore')
    if '性别' in df.columns and is_object_dtype(df['性别']):
        df['性别'] = df['性别'].map({'男': 0, '女': 1})
    df['性别'] = pd.to_numeric(df['性别'], errors='coerce')
    df = df.drop(columns=['id', '体检日期'], errors='ignore')

    # 选出数值列，排除标签列
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    label_col = '血糖'
    if label_col in numeric_cols:
        numeric_cols.remove(label_col)

    # 排除全为 NaN 的列，避免 imputer 返回列数不匹配
    valid_cols = [col for col in numeric_cols if not df[col].isna().all()]
    if valid_cols != numeric_cols:
        df = df.drop(columns=[c for c in numeric_cols if c not in valid_cols])
        numeric_cols = valid_cols

    if numeric_cols:
        imputer = SimpleImputer(strategy='median')
        df[numeric_cols] = imputer.fit_transform(df[numeric_cols])
    if numeric_cols:
        scaler = StandardScaler()
        df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
    return df


def preprocess_final(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """预处理复赛数据（用于统计展示）"""
    pipeline = FinalPipeline()
    return pipeline.fit(df)


def get_preprocessing_artifacts() -> dict:
    """返回已保存的 pipeline 路径信息"""
    artifacts = {}
    for name in ('blood_sugar', 'diabetes'):
        path = os.path.join(MODEL_DIR, f'{name}_pipeline.joblib')
        if os.path.exists(path):
            artifacts[name] = path
    meta = load_metrics_meta()
    if meta:
        artifacts['metrics'] = meta
    return artifacts


def fit_initial_pipeline(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, InitialPipeline]:
    pipeline = InitialPipeline()
    X, y = pipeline.fit(df)
    return X, y, pipeline


def fit_final_pipeline(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, FinalPipeline]:
    pipeline = FinalPipeline()
    X, y = pipeline.fit(df)
    return X, y, pipeline
