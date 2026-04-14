"""
测试模板列表接口
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_template_list():
    print("测试模板列表接口...")
    print("=" * 60)
    
    # 1. 先登录获取token
    print("\n1. 登录获取Token")
    login_data = {
        "account": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            result = response.json()
            token = result["access_token"]
            print(f"   [OK] 登录成功")
        else:
            print(f"   [X] 登录失败: {response.text}")
            return
    except Exception as e:
        print(f"   [X] 登录异常: {e}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. 获取模板列表
    print("\n2. 获取模板列表")
    try:
        response = requests.get(f"{BASE_URL}/api/template/list", headers=headers)
        print(f"   状态码: {response.status_code}")
        result = response.json()
        print(f"   总数: {result.get('total', 0)}")
        print(f"   模板列表: {json.dumps(result.get('items', []), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"   [X] 获取模板列表异常: {e}")
    
    # 3. 测试获取分类
    print("\n3. 获取模板分类")
    try:
        response = requests.get(f"{BASE_URL}/api/template/categories", headers=headers)
        print(f"   状态码: {response.status_code}")
        result = response.json()
        print(f"   分类列表: {json.dumps(result.get('categories', []), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"   [X] 获取分类异常: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_template_list()
