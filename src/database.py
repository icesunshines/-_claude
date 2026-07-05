# coding: utf-8
"""
数据库连接配置
使用 SQLite，可替换为 MySQL/PostgreSQL
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite 数据库文件路径
SQLALCHEMY_DATABASE_URL = "sqlite:///./medical.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """依赖注入用，获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
