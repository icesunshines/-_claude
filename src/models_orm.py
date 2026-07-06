# coding: utf-8
"""
SQLAlchemy ORM 模型
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
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
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")


class PredictionHistory(Base):
    """预测历史表"""
    __tablename__ = "prediction_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    type = Column(String(20))  # blood_sugar / diabetes
    input_data = Column(Text)  # JSON
    result = Column(Text)  # JSON
    created_at = Column(DateTime, server_default=func.now())


class ChatSession(Base):
    """聊天会话表"""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    title = Column(String(200), default="新对话")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    """聊天消息表"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), index=True, nullable=False)
    role = Column(String(20), nullable=False)  # user / assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    session = relationship("ChatSession", back_populates="messages")
