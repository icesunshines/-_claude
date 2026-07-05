# coding: utf-8
"""
重置数据库用户
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from database import SessionLocal, engine
from models_orm import Base, User
from auth import get_password_hash


def reset_users():
    """重置用户"""
    db = SessionLocal()
    
    # 删除所有现有用户
    db.query(User).delete()
    db.commit()
    
    # 创建管理员
    admin = User(
        username="admin",
        hashed_password=get_password_hash("admin123"),
        role="admin",
    )
    db.add(admin)
    
    # 创建普通用户
    user = User(
        username="user",
        hashed_password=get_password_hash("user123"),
        role="user",
    )
    db.add(user)
    
    db.commit()
    
    print("用户重置成功！")
    print("  admin / admin123")
    print("  user / user123")
    
    db.close()


if __name__ == "__main__":
    reset_users()
