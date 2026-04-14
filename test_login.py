"""
测试登录接口
"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("测试登录接口...")
print("=" * 60)

login_data = {
    "account": "admin",
    "password": "123456"
}

try:
    print(f"\n请求URL: {BASE_URL}/api/auth/login")
    print(f"请求数据: {json.dumps(login_data, ensure_ascii=False)}")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json=login_data,
        timeout=10
    )
    
    print(f"\n状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        print(f"\n登录成功!")
        print(f"响应数据: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    else:
        print(f"\n登录失败!")
        
except Exception as e:
    print(f"\n异常: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
