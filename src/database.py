# coding: utf-8
"""
数据库连接配置
默认使用 MySQL（pymysql），可通过环境变量切换回 SQLite
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

USE_MYSQL = os.getenv("USE_MYSQL", "true").lower() in ("true", "1", "yes")

if USE_MYSQL:
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    MYSQL_DB = os.getenv("MYSQL_DB", "medical_db")
    SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
    DB_PATH = os.path.join(PROJECT_DIR, 'medical.db')
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} if not USE_MYSQL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """依赖注入用，获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
