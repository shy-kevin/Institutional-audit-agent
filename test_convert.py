"""
测试 Office 转 PDF 接口
"""

import httpx
import json

base_url = "http://localhost:8000"

# 测试转换接口
response = httpx.post(
    f"{base_url}/api/file/convert-to-pdf",
    json={"file_path": "test.docx"},
    timeout=30.0
)

print(f"状态码: {response.status_code}")
print(f"响应: {response.text}")
