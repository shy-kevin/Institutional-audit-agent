"""
测试模板创建接口
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_template_api():
    print("测试模板管理接口...")
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
            print(f"   Token: {token[:20]}...")
        else:
            print(f"   [X] 登录失败: {response.text}")
            return
    except Exception as e:
        print(f"   [X] 登录异常: {e}")
        return
    
    # 2. 创建模板
    print("\n2. 创建模板")
    template_data = {
        "name": "测试模板",
        "category": "人事管理",
        "description": "这是一个测试模板",
        "format": {
            "fontSize": "14px",
            "fontFamily": "仿宋_GB2312",
            "lineHeight": "1.75",
            "margin": "2.54cm"
        },
        "sections": [
            {
                "id": "section_1",
                "level": 1,
                "title": "第一章 总则",
                "description": "本章规定制度的目的和适用范围",
                "children": []
            }
        ],
        "is_public": False,
        "tags": ["测试", "模板"]
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/template/create",
            json=template_data,
            headers=headers
        )
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"   [X] 创建模板异常: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_template_api()
