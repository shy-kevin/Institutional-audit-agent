import httpx
import json

response = httpx.post(
    "http://localhost:8000/api/file/convert-to-pdf",
    json={"file_path": "test.docx"}
)

print(f"状态码: {response.status_code}")
print(f"响应: {response.text}")
