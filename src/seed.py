# coding: utf-8
"""
数据库初始化脚本
创建默认管理员和测试用户
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine
from models_orm import Base, User
from auth import get_password_hash


def init_db():
    """初始化数据库"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 创建默认管理员
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            role="admin",
        )
        db.add(admin)
        db.commit()
        print("[OK] 已创建默认管理员: admin / admin123")
    else:
        print("[INFO] 管理员已存在，跳过")

    # 创建测试用户
    user = db.query(User).filter(User.username == "user").first()
    if not user:
        user = User(
            username="user",
            hashed_password=get_password_hash("user123"),
            role="user",
        )
        db.add(user)
        db.commit()
        print("[OK] 已创建测试用户: user / user123")
    else:
        print("[INFO] 测试用户已存在，跳过")

    db.close()
    print("[OK] 数据库初始化完成")


if __name__ == "__main__":
    init_db()
