"""
简单的API测试
"""

import requests
import traceback

BASE_URL = "http://localhost:8000"

try:
    print("测试注册接口...")
    register_data = {
        "username": "testuser",
        "account": "testuser",
        "password": "123456"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    print(f"状态码: {response.status_code}")
    print(f"响应头: {response.headers}")
    print(f"响应内容: {response.text}")
    
except Exception as e:
    print(f"异常: {e}")
    traceback.print_exc()
