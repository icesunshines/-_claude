# coding: utf-8
"""
FastAPI 主入口
提供 REST API 接口：认证、预测、统计、历史记录、实时推送
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import asyncio
from datetime import datetime, date
from typing import Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session
from sqlalchemy import func

from database import engine, get_db, Base
from models_orm import User, PredictionHistory
from auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_admin,
)
from predict import (
    predict_blood_sugar,
    predict_diabetes_from_request,
    get_blood_sugar_stats,
    get_diabetes_stats,
    get_feature_importance,
    get_stats_overview,
    get_blood_sugar_feature_means,
)
from preprocessing import load_metrics_meta
from schemas import (
    BloodSugarRequest,
    BloodSugarResponse,
    DiabetesRequest,
    DiabetesResponse,
    ChatRequest,
    ChatResponse,
    FeatureImportanceResponse,
    HealthResponse,
    UserCreate,
    UserResponse,
    TokenResponse,
    HistoryItem,
)

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title='医疗健康风险预测 API',
    description='基于 FastAPI 的医疗健康数据可视化与风险预测系统',
    version='2.0.0',
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


# ==================== 健康检查 ====================

@app.get('/', response_model=HealthResponse)
def health():
    """健康检查"""
    return HealthResponse(status='ok', message='医疗健康风险预测系统 API 运行中')


# ==================== 认证相关 ====================

@app.post('/api/auth/register', response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail='用户名已存在')
    new_user = User(
        username=user.username,
        hashed_password=get_password_hash(user.password),
        role='user',
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        role=new_user.role,
        created_at=new_user.created_at.strftime('%Y-%m-%d %H:%M'),
    )


@app.post('/api/auth/login', response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """用户登录，返回 JWT token"""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail='用户名或密码错误')
    access_token = create_access_token(data={'sub': user.username})
    return TokenResponse(access_token=access_token, token_type='bearer', role=user.role)


@app.get('/api/auth/me', response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        created_at=current_user.created_at.strftime('%Y-%m-%d %H:%M'),
    )


# ==================== 预测接口 ====================

@app.post('/api/predict/blood-sugar', response_model=BloodSugarResponse)
def api_predict_blood_sugar(request: BloodSugarRequest):
    """血糖预测接口"""
    data = request.dict()
    result = predict_blood_sugar(data)
    return BloodSugarResponse(**result)


@app.post('/api/predict/diabetes', response_model=DiabetesResponse)
def api_predict_diabetes(request: DiabetesRequest):
    """糖尿病风险预测接口"""
    data = request.model_dump(exclude_none=True)
    result = predict_diabetes_from_request(data)
    return DiabetesResponse(**result)


# ==================== 统计接口 ====================

@app.get('/api/stats/overview')
def api_stats_overview():
    """大屏 KPI 概览"""
    return get_stats_overview()


@app.get('/api/stats/blood-sugar/means')
def api_blood_sugar_means():
    """血糖预测表单默认值（训练集中位数）"""
    return get_blood_sugar_feature_means()


@app.get('/api/stats/blood-sugar')
def api_stats_blood_sugar():
    """血糖统计数据接口"""
    return get_blood_sugar_stats()


@app.get('/api/stats/diabetes')
def api_stats_diabetes():
    """糖尿病统计数据接口"""
    return get_diabetes_stats()


@app.get('/api/feature-importance', response_model=FeatureImportanceResponse)
def api_feature_importance(model_type: str = 'blood_sugar'):
    """特征重要性接口"""
    result = get_feature_importance(model_type)
    return FeatureImportanceResponse(**result)


# ==================== 预测历史 ====================

@app.post('/api/history')
def save_history(
    data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """保存预测历史"""
    history = PredictionHistory(
        user_id=current_user.id,
        type=data.get('type', 'unknown'),
        input_data=json.dumps(data.get('input', {}), ensure_ascii=False),
        result=json.dumps(data.get('result', {}), ensure_ascii=False),
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return {'status': 'ok', 'id': history.id}


@app.get('/api/history', response_model=list[HistoryItem])
def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户预测历史"""
    history = (
        db.query(PredictionHistory)
        .filter(PredictionHistory.user_id == current_user.id)
        .order_by(PredictionHistory.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        HistoryItem(
            type=h.type,
            input=json.loads(h.input_data),
            result=json.loads(h.result),
            created_at=h.created_at.strftime('%Y-%m-%d %H:%M'),
        )
        for h in history
    ]


@app.get('/api/admin/dashboard')
def admin_dashboard(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """管理员仪表盘数据"""
    total_users = db.query(User).count()
    total_predictions = db.query(PredictionHistory).count()
    today = date.today()
    today_active = (
        db.query(PredictionHistory)
        .filter(func.date(PredictionHistory.created_at) == today)
        .count()
    )

    metrics = load_metrics_meta()
    dm_acc = metrics.get('diabetes', {}).get('validation', {}).get('accuracy', 0)
    accuracy = f'{dm_acc * 100:.0f}%' if dm_acc else '0%'

    users = db.query(User).order_by(User.id).all()
    user_list = []
    for u in users:
        pred_count = (
            db.query(PredictionHistory)
            .filter(PredictionHistory.user_id == u.id)
            .count()
        )
        user_list.append({
            'id': u.id,
            'username': u.username,
            'role': u.role,
            'prediction_count': pred_count,
            'created_at': u.created_at.strftime('%Y-%m-%d %H:%M'),
        })

    history_rows = (
        db.query(PredictionHistory)
        .order_by(PredictionHistory.created_at.desc())
        .limit(100)
        .all()
    )
    user_map = {u.id: u.username for u in users}
    history = [
        {
            'id': h.id,
            'user_id': h.user_id,
            'username': user_map.get(h.user_id, '未知'),
            'type': h.type,
            'result': json.loads(h.result),
            'created_at': h.created_at.strftime('%Y-%m-%d %H:%M'),
        }
        for h in history_rows
    ]

    return {
        'stats': {
            'total_users': total_users,
            'total_predictions': total_predictions,
            'today_active': today_active,
            'accuracy': accuracy,
            'model_metrics': metrics,
        },
        'users': user_list,
        'history': history,
    }


@app.get('/api/admin/history')
def admin_get_history(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """管理员查看所有用户预测历史"""
    history = (
        db.query(PredictionHistory)
        .order_by(PredictionHistory.created_at.desc())
        .limit(100)
        .all()
    )
    user_ids = sorted({h.user_id for h in history})
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    user_map = {u.id: u.username for u in users}
    return [
        {
            'id': h.id,
            'user_id': h.user_id,
            'username': user_map.get(h.user_id, '未知'),
            'type': h.type,
            'result': json.loads(h.result),
            'created_at': h.created_at.strftime('%Y-%m-%d %H:%M'),
        }
        for h in history
    ]


# ==================== 实时推送 ====================

async def event_generator(db: Session):
    """SSE 实时统计数据流"""
    while True:
        total = db.query(PredictionHistory).count()
        users = db.query(User).count()
        payload = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'total_predictions': total,
            'total_users': users,
        }
        yield f'data: {json.dumps(payload, ensure_ascii=False)}\n\n'
        await asyncio.sleep(2)


@app.get('/api/realtime/stats')
async def realtime_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """SSE 实时统计推送"""
    return StreamingResponse(event_generator(db), media_type='text/event-stream')


# ==================== 智能问答 ====================

# 医疗健康知识库
HEALTH_KNOWLEDGE = {
    "糖尿病预防": {
        "keywords": ["糖尿病", "预防", "预防糖尿病", "预防糖尿"],
        "response": "糖尿病预防建议：\n1. 保持健康饮食：控制碳水化合物摄入，增加膳食纤维，避免高糖食物\n2. 定期运动：每周至少150分钟中等强度有氧运动\n3. 控制体重：保持BMI在18.5-23.9之间\n4. 定期检查：监测血糖、血压和血脂\n5. 戒烟限酒：避免不良生活习惯"
    },
    "血糖管理": {
        "keywords": ["血糖", "高血糖", "血糖高", "降血糖"],
        "response": "血糖管理建议：\n1. 监测血糖：定期检测血糖水平\n2. 饮食控制：少食多餐，选择低GI食物\n3. 适量运动：餐后散步有助于降低血糖\n4. 规律作息：保证充足睡眠\n5. 遵医嘱：按时服药或注射胰岛素\n6. 避免应激管理：保持心情舒畅"
    },
    "健康饮食": {
        "keywords": ["饮食", "吃什么", "健康饮食", "食谱", "膳食"],
        "response": "健康饮食建议：\n1. 增加蔬菜摄入：每天至少500克蔬菜\n2. 选择全谷物：糙米、燕麦等\n3. 优质蛋白：鱼、禽、豆类等\n4. 控制油脂：选择橄榄油、茶籽油\n5. 限盐限糖：每日食盐<6克\n6. 充足饮水：每天1500-2000ml"
    },
    "妊娠期糖尿病": {
        "keywords": ["妊娠", "孕妇", "妊娠期", "GDM"],
        "response": "妊娠期糖尿病（GDM）相关知识：\n1. 定义：妊娠期间首次发现的血糖异常\n2. 高危因素：高龄妊娠、肥胖、糖尿病家族史等\n3. 筛查时机：孕24-28周进行OGTT筛查\n4. 管理：饮食控制、适量运动、必要时胰岛素治疗\n5. 预后：多数产后恢复正常，但将来患糖尿病风险增加"
    },
    "运动建议": {
        "keywords": ["运动", "锻炼", "健身"],
        "response": "运动建议：\n1. 有氧运动：快走、慢跑、游泳、骑自行车等\n2. 运动频率：每周至少150分钟/周，分5天进行\n3. 运动强度：中等强度，心率控制在（220-年龄）×60-70%\n4. 注意事项：运动前热身，运动后拉伸，避免空腹运动\n5. 循序渐进：从低强度开始，逐渐增加"
    },
    "体检指标": {
        "keywords": ["体检", "检查", "指标"],
        "response": "建议定期检查的指标：\n1. 血糖：空腹血糖、餐后2小时血糖\n2. 血压：正常<140/90mmHg\n3. 血脂：总胆固醇、甘油三酯、LDL、HDL\n4. 体重：BMI、腰围\n5. 肝功能、肾功能等"
    },
    "BMI计算": {
        "keywords": ["BMI", "体重指数", "体重"],
        "response": "BMI（体重指数）计算：\nBMI = 体重(kg) / 身高(m)²\n正常范围：18.5-23.9\n偏瘦：<18.5\n超重：24-27.9\n肥胖：≥28\n注意：BMI仅供参考，需结合体脂率和腰围综合判断"
    }
}

@app.post('/api/chat', response_model=ChatResponse)
def api_chat(request: ChatRequest):
    """智能健康问答接口"""
    user_message = request.message.strip().lower()
    
    # 关键词匹配
    for category, info in HEALTH_KNOWLEDGE.items():
        for keyword in info["keywords"]:
            if keyword in user_message:
                return ChatResponse(reply=info["response"])
    
    # 默认回复
    general_reply = f"""您好！我是您的健康助手。

关于您的问题"{request.message}"，我建议您：

1. 可以尝试以下方向的问题：
   - 糖尿病预防
   - 血糖管理
   - 健康饮食建议
   - 妊娠期糖尿病知识
   - 运动建议
   - 体检指标解读
   - BMI计算

2. 如果需要准确的健康建议，请咨询专业医生。

3. 您也可以使用我们的【风险预测功能进行健康评估！"""
    
    return ChatResponse(reply=general_reply)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
