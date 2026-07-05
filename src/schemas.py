# coding: utf-8
"""
Pydantic 数据模型定义
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any


class BloodSugarRequest(BaseModel):
    """血糖预测请求模型"""
    性别: str = Field(..., description="性别: 男/女")
    年龄: int = Field(..., ge=0, le=120, description="年龄")

    # 肝功指标
    天门冬氨酸氨基转换酶: Optional[float] = Field(None, description="AST")
    丙氨酸氨基转换酶: Optional[float] = Field(None, description="ALT")
    碱性磷酸酶: Optional[float] = Field(None, description="ALP")
    r_谷氨酰基转换酶: Optional[float] = Field(None, description="GGT")
    总蛋白: Optional[float] = Field(None, description="TP")
    白蛋白: Optional[float] = Field(None, description="ALB")
    球蛋白: Optional[float] = Field(None, description="GLB")
    白球比例: Optional[float] = Field(None, description="A/G ratio")

    # 血脂指标
    甘油三酯: Optional[float] = Field(None, description="TG")
    总胆固醇: Optional[float] = Field(None, description="TC")
    高密度脂蛋白胆固醇: Optional[float] = Field(None, description="HDL-C")
    低密度脂蛋白胆固醇: Optional[float] = Field(None, description="LDL-C")

    # 肾功指标
    尿素: Optional[float] = Field(None, description="BUN")
    肌酐: Optional[float] = Field(None, description="Cr")
    尿酸: Optional[float] = Field(None, description="UA")

    # 血常规指标
    白细胞计数: Optional[float] = Field(None, description="WBC")
    红细胞计数: Optional[float] = Field(None, description="RBC")
    血红蛋白: Optional[float] = Field(None, description="HGB")
    红细胞压积: Optional[float] = Field(None, description="HCT")
    红细胞平均体积: Optional[float] = Field(None, description="MCV")
    红细胞平均血红蛋白量: Optional[float] = Field(None, description="MCH")
    红细胞平均血红蛋白浓度: Optional[float] = Field(None, description="MCHC")
    红细胞体积分布宽度: Optional[float] = Field(None, description="RDW")
    血小板计数: Optional[float] = Field(None, description="PLT")
    血小板平均体积: Optional[float] = Field(None, description="MPV")
    血小板体积分布宽度: Optional[float] = Field(None, description="PDW")
    血小板比积: Optional[float] = Field(None, description="PCT")

    # 白细胞分类
    中性粒细胞百分比: Optional[float] = Field(None, description="NEUT%")
    淋巴细胞百分比: Optional[float] = Field(None, description="LYMPH%")
    单核细胞百分比: Optional[float] = Field(None, description="MONO%")
    嗜酸细胞百分比: Optional[float] = Field(None, description="EOS%")
    嗜碱细胞百分比: Optional[float] = Field(None, description="BASO%")


class BloodSugarResponse(BaseModel):
    """血糖预测响应模型"""
    predicted_bgl: float = Field(..., description="预测血糖值 (mmol/L)")
    risk_level: str = Field(..., description="风险等级: 正常/偏高/高风险")
    risk_score: float = Field(..., ge=0, le=100, description="风险评分 0-100")


class DiabetesRequest(BaseModel):
    """糖尿病预测请求模型（临床指标 + 可选 SNP）"""
    年龄: Optional[float] = Field(None, description="年龄")
    孕次: Optional[float] = Field(None, description="孕次")
    产次: Optional[float] = Field(None, description="产次")
    身高: Optional[float] = Field(None, description="身高 cm")
    孕前体重: Optional[float] = Field(None, description="孕前体重 kg")
    孕前BMI: Optional[float] = Field(None, description="孕前 BMI")
    BMI分类: Optional[float] = Field(None, description="BMI 分类")
    收缩压: Optional[float] = Field(None, description="收缩压 mmHg")
    舒张压: Optional[float] = Field(None, description="舒张压 mmHg")
    糖筛孕周: Optional[float] = Field(None, description="糖筛孕周")
    wbc: Optional[float] = Field(None, description="白细胞")
    ALT: Optional[float] = Field(None, description="ALT")
    AST: Optional[float] = Field(None, description="AST")
    Cr: Optional[float] = Field(None, description="肌酐")
    BUN: Optional[float] = Field(None, description="尿素氮")
    CHO: Optional[float] = Field(None, description="总胆固醇")
    TG: Optional[float] = Field(None, description="甘油三酯")
    HDLC: Optional[float] = Field(None, description="高密度脂蛋白")
    LDLC: Optional[float] = Field(None, description="低密度脂蛋白")
    ApoA1: Optional[float] = Field(None, description="载脂蛋白 A1")
    ApoB: Optional[float] = Field(None, description="载脂蛋白 B")
    Lpa: Optional[float] = Field(None, description="脂蛋白 a")
    hsCRP: Optional[float] = Field(None, description="超敏 CRP")
    DM家族史: Optional[float] = Field(None, description="糖尿病家族史")
    snp_features: Optional[Dict[str, float]] = Field(None, description="SNP 基因位点（高级）")
    features: Optional[Dict[str, float]] = Field(None, description="完整特征字典（兼容旧接口）")


class DiabetesResponse(BaseModel):
    """糖尿病预测响应模型"""
    risk: int = Field(..., description="预测结果: 0=健康, 1=患病")
    probability: float = Field(..., ge=0, le=1, description="患病概率")


class ChatRequest(BaseModel):
    """智能问答请求模型"""
    message: str = Field(..., description="用户提问")


class ChatResponse(BaseModel):
    """智能问答响应模型"""
    reply: str = Field(..., description="回复内容")


class FeatureImportanceResponse(BaseModel):
    """特征重要性响应模型"""
    features: List[str] = Field(..., description="特征名称列表")
    values: List[float] = Field(..., description="重要性值列表")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    message: str


class UserCreate(BaseModel):
    """用户注册请求"""
    username: str
    password: str
    role: str = "user"


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    role: str
    created_at: str


class TokenResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str
    role: str


class HistoryItem(BaseModel):
    """预测历史项"""
    type: str
    input: dict
    result: dict
    created_at: str
