# coding: utf-8
"""Generate thesis experiment figures into docs/thesis_figures/."""

import json
import os
import sys

import lightgbm as lgb
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
    roc_curve,
)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from preprocessing import fit_final_pipeline, fit_initial_pipeline, load_metrics_meta, load_pipeline

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'docs', 'thesis_figures')

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

BGL_COL = '\u8840\u7cd6'  # Ѫ��


def _load_lgb_model(filename: str) -> lgb.Booster:
    rel_path = os.path.join('src', 'models', filename)
    cwd = os.getcwd()
    try:
        os.chdir(PROJECT_DIR)
        return lgb.Booster(model_file=rel_path)
    finally:
        os.chdir(cwd)


def _ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def _load_blood_sugar_test():
    test_df = pd.read_csv(os.path.join(DATA_DIR, 'initial', 'd_test_A_20180102.csv'), encoding='gbk')
    answers = pd.read_csv(os.path.join(DATA_DIR, 'initial', 'd_answer_a_20180128.csv'), encoding='gbk')
    return test_df, answers.iloc[:, 0].astype(float)


def _load_diabetes_test():
    test_df = pd.read_csv(os.path.join(DATA_DIR, 'final', 'f_test_a_20180204.csv'), encoding='gbk')
    answers = pd.read_csv(
        os.path.join(DATA_DIR, 'final', 'f_answer_a_20180306.csv'),
        encoding='gbk',
        header=None,
        names=['label'],
    )
    return test_df, answers['label'].astype(int)


def plot_blood_sugar_distribution():
    df = pd.read_csv(os.path.join(DATA_DIR, 'initial', 'd_train_20180102.csv'), encoding='gbk')
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(df[BGL_COL], bins=30, color='#2d7dd2', edgecolor='white', alpha=0.85)
    ax.axvline(5.6, color='#f1c40f', linestyle='--', label='Normal upper 5.6')
    ax.axvline(7.0, color='#e74c3c', linestyle='--', label='Diabetes threshold 7.0')
    ax.set_xlabel('Blood Glucose (mmol/L)')
    ax.set_ylabel('Count')
    ax.set_title('Training Set Blood Glucose Distribution')
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, 'blood_sugar_distribution.png'), dpi=150)
    plt.close(fig)


def plot_blood_sugar_scatter(pipeline, model):
    test_df, test_y = _load_blood_sugar_test()
    X_test, _ = pipeline.transform_df(test_df, has_label=False)
    pred = model.predict(X_test)
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(test_y, pred, alpha=0.5, color='#2d7dd2', s=20)
    lims = [min(test_y.min(), pred.min()), max(test_y.max(), pred.max())]
    ax.plot(lims, lims, 'r--', label='Ideal y=x')
    ax.set_xlabel('Actual BGL (mmol/L)')
    ax.set_ylabel('Predicted BGL (mmol/L)')
    ax.set_title('Blood Sugar Prediction Scatter (Test Set)')
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, 'blood_sugar_scatter.png'), dpi=150)
    plt.close(fig)


def plot_feature_importance(model, title, filename):
    importance = model.feature_importance(importance_type='gain')
    features = model.feature_name()
    idx = np.argsort(importance)[::-1][:15]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh([features[i] for i in idx[::-1]], [importance[i] for i in idx[::-1]], color='#45b7d1')
    ax.set_xlabel('Gain Importance')
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, filename), dpi=150)
    plt.close(fig)


def plot_diabetes_roc(y_true, y_prob):
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(fpr, tpr, color='#e056a0', lw=2, label=f'AUC = {roc_auc_score(y_true, y_prob):.3f}')
    ax.plot([0, 1], [0, 1], 'k--', alpha=0.5)
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.set_title('GDM Classification ROC Curve (Test Set)')
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, 'diabetes_roc.png'), dpi=150)
    plt.close(fig)


def plot_diabetes_confusion(y_true, y_prob):
    y_pred = (y_prob >= 0.5).astype(int)
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(5, 4))
    disp = ConfusionMatrixDisplay(cm, display_labels=['Healthy', 'GDM'])
    disp.plot(ax=ax, cmap='Blues', colorbar=False)
    ax.set_title('GDM Confusion Matrix (Test Set)')
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, 'diabetes_confusion.png'), dpi=150)
    plt.close(fig)


def run_baseline_comparison():
    summary = {'comparison': {}}

    df_bs = pd.read_csv(os.path.join(DATA_DIR, 'initial', 'd_train_20180102.csv'), encoding='gbk')
    X_bs, y_bs, bs_pipeline = fit_initial_pipeline(df_bs)
    test_df, test_y = _load_blood_sugar_test()
    X_test, _ = bs_pipeline.transform_df(test_df, has_label=False)

    lgb_model = _load_lgb_model('blood_sugar.lgb')
    lgb_pred = lgb_model.predict(X_test)
    summary['comparison']['blood_sugar'] = {
        'LightGBM': {
            'rmse': round(float(np.sqrt(mean_squared_error(test_y, lgb_pred))), 4),
            'mae': round(float(mean_absolute_error(test_y, lgb_pred)), 4),
            'r2': round(float(r2_score(test_y, lgb_pred)), 4),
        }
    }
    rf_reg = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf_reg.fit(X_bs, y_bs)
    rf_pred = rf_reg.predict(X_test)
    summary['comparison']['blood_sugar']['RandomForest'] = {
        'rmse': round(float(np.sqrt(mean_squared_error(test_y, rf_pred))), 4),
        'mae': round(float(mean_absolute_error(test_y, rf_pred)), 4),
        'r2': round(float(r2_score(test_y, rf_pred)), 4),
    }

    df_dm = pd.read_csv(os.path.join(DATA_DIR, 'final', 'f_train_20180204.csv'), encoding='gbk')
    X_dm, y_dm, dm_pipeline = fit_final_pipeline(df_dm)
    test_dm, test_y_dm = _load_diabetes_test()
    X_test_dm, _ = dm_pipeline.transform_df(test_dm, has_label=False)

    lgb_dm = _load_lgb_model('diabetes.lgb')
    lgb_prob = lgb_dm.predict(X_test_dm)
    lgb_pred = (lgb_prob >= 0.5).astype(int)
    summary['comparison']['diabetes'] = {
        'LightGBM': {
            'auc': round(float(roc_auc_score(test_y_dm, lgb_prob)), 4),
            'accuracy': round(float(accuracy_score(test_y_dm, lgb_pred)), 4),
            'f1': round(float(f1_score(test_y_dm, lgb_pred, zero_division=0)), 4),
        }
    }
    lr = LogisticRegression(max_iter=1000, random_state=42)
    lr.fit(X_dm, y_dm)
    lr_prob = lr.predict_proba(X_test_dm)[:, 1]
    lr_pred = (lr_prob >= 0.5).astype(int)
    summary['comparison']['diabetes']['LogisticRegression'] = {
        'auc': round(float(roc_auc_score(test_y_dm, lr_prob)), 4),
        'accuracy': round(float(accuracy_score(test_y_dm, lr_pred)), 4),
        'f1': round(float(f1_score(test_y_dm, lr_pred, zero_division=0)), 4),
    }
    rf_clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    rf_clf.fit(X_dm, y_dm)
    rf_prob = rf_clf.predict_proba(X_test_dm)[:, 1]
    rf_pred_dm = (rf_prob >= 0.5).astype(int)
    summary['comparison']['diabetes']['RandomForest'] = {
        'auc': round(float(roc_auc_score(test_y_dm, rf_prob)), 4),
        'accuracy': round(float(accuracy_score(test_y_dm, rf_pred_dm)), 4),
        'f1': round(float(f1_score(test_y_dm, rf_pred_dm, zero_division=0)), 4),
    }
    return summary


def main():
    _ensure_output_dir()
    metrics = load_metrics_meta()
    bs_pipeline = load_pipeline('blood_sugar')
    dm_pipeline = load_pipeline('diabetes')
    bs_model = _load_lgb_model('blood_sugar.lgb')
    dm_model = _load_lgb_model('diabetes.lgb')

    plot_blood_sugar_distribution()
    plot_blood_sugar_scatter(bs_pipeline, bs_model)
    plot_feature_importance(bs_model, 'Blood Sugar Feature Importance (LightGBM)', 'feature_importance_blood_sugar.png')
    plot_feature_importance(dm_model, 'GDM Feature Importance (LightGBM)', 'feature_importance_diabetes.png')

    test_dm, test_y_dm = _load_diabetes_test()
    X_test_dm, _ = dm_pipeline.transform_df(test_dm, has_label=False)
    dm_prob = dm_model.predict(X_test_dm)
    plot_diabetes_roc(test_y_dm, dm_prob)
    plot_diabetes_confusion(test_y_dm, dm_prob)

    comparison = run_baseline_comparison()
    summary = {'model_metrics': metrics, **comparison}
    out_path = os.path.join(OUTPUT_DIR, 'metrics_summary.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f'Figures saved to: {OUTPUT_DIR}')
    print(f'Metrics saved to: {out_path}')


if __name__ == '__main__':
    main()
