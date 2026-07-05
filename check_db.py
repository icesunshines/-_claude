#!/usr/bin/env python
# coding: utf-8
"""检查数据库用户"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from database import SessionLocal, engine
from models_orm import Base, User
from auth import get_password_hash, verify_password


def check_and_reset_users():
    """检查并重置用户"""
    db = SessionLocal()
    
    print("检查数据库用户:")
    
    users = db.query(User).all()
    print(f"\n当前用户数: {len(users)}")
    for user in users:
        print(f"  - ID: {user.id}, 用户名: {user.username}, 角色: {user.role}")
    
    # 删除现有用户并重新创建
    print("\n重置用户...")
    for user in users:
        db.delete(user)
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
    
    print("\n已创建用户:")
    print("  - admin / admin123 (管理员)")
    print("  - user / user123 (普通用户)")
    
    # 验证密码
    print("\n验证密码:")
    admin_test = db.query(User).filter(User.username == "admin").first()
    if admin_test:
        result = verify_password("admin123", admin_test.hashed_password)
        print(f"  admin 密码验证: {result}")
    
    user_test = db.query(User).filter(User.username == "user").first()
    if user_test:
        result = verify_password("user123", user_test.hashed_password)
        print(f"  user 密码验证: {result}")
    
    db.close()
    print("\n完成!")


if __name__ == "__main__":
    check_and_reset_users()
