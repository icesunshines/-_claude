#!/usr/bin/env python
# coding: utf-8
"""测试登录API"""

import requests
import json

BASE_URL = "http://localhost:8000/api"


def test_login():
    """测试登录功能"""
    print("测试登录API...")
    
    # 测试健康检查
    print("\n1. 测试健康检查:")
    try:
        response = requests.get("http://localhost:8000/")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text}")
    except Exception as e:
        print(f"   错误: {e}")
    
    # 测试登录
    print("\n2. 测试登录:")
    try:
        data = {
            "username": "admin",
            "password": "admin123"
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data=data,
            headers=headers
        )
        print(f"   状态码: {response.status_code}")
        print(f"   响应头: {dict(response.headers)}")
        print(f"   响应: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   成功! Token: {result.get('access_token')[:20]}...")
            return True
        else:
            return False
    except Exception as e:
        print(f"   错误: {e}")
        import traceback
        print(f"   堆栈: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    test_login()
