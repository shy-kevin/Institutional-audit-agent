"""
测试后端API是否可访问
"""

import requests

BASE_URL = "http://localhost:8000"

print("测试后端API...")
print("=" * 60)

try:
    print("\n1. 测试根路径 /")
    response = requests.get(f"{BASE_URL}/", timeout=5)
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")
except Exception as e:
    print(f"   错误: {e}")

try:
    print("\n2. 测试健康检查 /health")
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")
except Exception as e:
    print(f"   错误: {e}")

try:
    print("\n3. 测试API文档 /docs")
    response = requests.get(f"{BASE_URL}/docs", timeout=5)
    print(f"   状态码: {response.status_code}")
    print(f"   响应长度: {len(response.text)} 字符")
except Exception as e:
    print(f"   错误: {e}")

try:
    print("\n4. 测试模板分类接口 /api/template/categories")
    response = requests.get(f"{BASE_URL}/api/template/categories", timeout=5)
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")
except Exception as e:
    print(f"   错误: {e}")

print("\n" + "=" * 60)
print("测试完成")
