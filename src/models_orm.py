# coding: utf-8
"""
SQLAlchemy ORM 模型
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    role = Column(String(20), default="user")  # user / admin
    created_at = Column(DateTime, server_default=func.now())


class PredictionHistory(Base):
    """预测历史表"""
    __tablename__ = "prediction_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    type = Column(String(20))  # blood_sugar / diabetes
    input_data = Column(Text)  # JSON
    result = Column(Text)  # JSON
    created_at = Column(DateTime, server_default=func.now())
