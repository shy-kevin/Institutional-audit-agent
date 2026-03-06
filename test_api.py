"""
接口测试脚本
测试所有API接口
"""

import httpx
import json

base_url = 'http://localhost:8000'

def test_api():
    print('=== 1. 测试根路径 ===')
    response = httpx.get(f'{base_url}/')
    print(f'状态码: {response.status_code}')
    print(f'响应: {response.json()}')

    print('\n=== 2. 测试健康检查 ===')
    response = httpx.get(f'{base_url}/health')
    print(f'状态码: {response.status_code}')
    print(f'响应: {response.json()}')

    print('\n=== 3. 测试创建对话 ===')
    response = httpx.post(f'{base_url}/api/conversation/create', json={'title': '测试对话'})
    print(f'状态码: {response.status_code}')
    print(f'响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}')
    conversation_id = response.json()['id']

    print('\n=== 4. 测试获取对话列表 ===')
    response = httpx.get(f'{base_url}/api/conversation/list')
    print(f'状态码: {response.status_code}')
    print(f'响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}')

    print('\n=== 5. 测试获取知识库列表 ===')
    response = httpx.get(f'{base_url}/api/knowledge-base/list')
    print(f'状态码: {response.status_code}')
    print(f'响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}')

    print('\n=== 6. 测试获取对话详情 ===')
    response = httpx.get(f'{base_url}/api/conversation/{conversation_id}')
    print(f'状态码: {response.status_code}')
    print(f'响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}')

    print('\n=== 7. 测试更新对话 ===')
    response = httpx.put(f'{base_url}/api/conversation/{conversation_id}', json={'title': '更新后的对话'})
    print(f'状态码: {response.status_code}')
    print(f'响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}')

    print('\n=== 8. 测试同步问答接口 ===')
    response = httpx.post(
        f'{base_url}/api/chat/sync',
        json={
            'conversation_id': conversation_id,
            'message': '你好'
        },
        timeout=60.0
    )
    print(f'状态码: {response.status_code}')
    print(f'响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}')

    print('\n=== 9. 测试获取对话消息 ===')
    response = httpx.get(f'{base_url}/api/conversation/{conversation_id}/messages')
    print(f'状态码: {response.status_code}')
    print(f'响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}')

    print('\n=== 所有测试完成! ===')


if __name__ == '__main__':
    test_api()
