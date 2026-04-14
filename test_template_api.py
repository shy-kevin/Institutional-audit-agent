"""
模板管理接口测试脚本
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def register_and_login():
    """注册并登录用户"""
    register_data = {
        "username": "测试用户",
        "account": "test_user",
        "password": "123456",
        "phone": "13800138000",
        "department": "测试部门"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
        if response.status_code == 200:
            print("[OK] 用户注册成功")
        else:
            print(f"[!] 用户注册失败或已存在: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[!] 用户注册异常: {e}")
    
    login_data = {
        "account": "test_user",
        "password": "123456"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            result = response.json()
            print("[OK] 用户登录成功")
            return result["access_token"]
        else:
            print(f"[X] 用户登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"[X] 用户登录异常: {e}")
        return None


def test_create_template(token):
    """测试创建模板"""
    print("\n--- 测试创建模板 ---")
    
    template_data = {
        "name": "员工考勤管理制度模板",
        "category": "人事管理",
        "description": "规范员工考勤管理的标准模板，包含工作时间、请假流程、违纪处理等章节",
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
                "description": "本章规定制度的目的、适用范围和基本原则",
                "children": [
                    {
                        "id": "section_1_1",
                        "level": 2,
                        "title": "第一条 目的",
                        "description": "明确制度制定的目的和意义"
                    },
                    {
                        "id": "section_1_2",
                        "level": 2,
                        "title": "第二条 适用范围",
                        "description": "规定制度适用的部门和人员范围"
                    }
                ]
            },
            {
                "id": "section_2",
                "level": 1,
                "title": "第二章 工作时间",
                "description": "本章规定标准工作时间和弹性工作制",
                "children": []
            }
        ],
        "is_public": False,
        "tags": ["考勤", "人事", "管理制度"]
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/api/template/create", json=template_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"[OK] 模板创建成功 - ID: {result['template']['id']}")
        return result['template']['id']
    else:
        print(f"[X] 模板创建失败: {response.status_code} - {response.text}")
        return None


def test_get_template(template_id, token):
    """测试获取模板详情"""
    print("\n--- 测试获取模板详情 ---")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/template/{template_id}", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"[OK] 模板详情获取成功 - 名称: {result['template']['name']}")
        print(f"  章节数量: {len(result['template']['sections'])}")
        return result['template']
    else:
        print(f"[X] 模板详情获取失败: {response.status_code} - {response.text}")
        return None


def test_get_template_list(token):
    """测试获取模板列表"""
    print("\n--- 测试获取模板列表 ---")
    
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "keyword": "考勤",
        "category": "人事管理",
        "limit": 10
    }
    response = requests.get(f"{BASE_URL}/api/template/list", params=params, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"[OK] 模板列表获取成功 - 总数: {result['total']}, 返回: {len(result['items'])}")
        return result
    else:
        print(f"[X] 模板列表获取失败: {response.status_code} - {response.text}")
        return None


def test_update_template(template_id, token):
    """测试更新模板"""
    print("\n--- 测试更新模板 ---")
    
    update_data = {
        "name": "员工考勤管理制度模板（修订版）",
        "description": "更新后的模板描述"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.put(f"{BASE_URL}/api/template/{template_id}", json=update_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"[OK] 模板更新成功 - 新名称: {result['template']['name']}")
        return result['template']
    else:
        print(f"[X] 模板更新失败: {response.status_code} - {response.text}")
        return None


def test_get_categories(token):
    """测试获取模板分类"""
    print("\n--- 测试获取模板分类 ---")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/template/categories", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"[OK] 模板分类获取成功 - 数量: {len(result['categories'])}")
        for category in result['categories']:
            print(f"  - {category['name']}: {category['count']}个模板")
        return result['categories']
    else:
        print(f"[X] 模板分类获取失败: {response.status_code} - {response.text}")
        return None


def test_get_popular_tags(token):
    """测试获取热门标签"""
    print("\n--- 测试获取热门标签 ---")
    
    headers = {"Authorization": f"Bearer {token}"}
    params = {"limit": 10}
    response = requests.get(f"{BASE_URL}/api/template/popular-tags", params=params, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"[OK] 热门标签获取成功 - 数量: {len(result['tags'])}")
        for tag in result['tags']:
            print(f"  - {tag['name']}: {tag['count']}次")
        return result['tags']
    else:
        print(f"[X] 热门标签获取失败: {response.status_code} - {response.text}")
        return None


def test_export_markdown(template_id, token):
    """测试导出模板为Markdown"""
    print("\n--- 测试导出模板为Markdown ---")
    
    export_data = {
        "include_metadata": True,
        "include_format_section": True,
        "include_creator_info": True
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/api/template/{template_id}/export-markdown", json=export_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"[OK] 模板导出为Markdown成功")
        print(f"  文件名: {result['file_name']}")
        print(f"  文件大小: {result['file_size']}字节")
        print(f"  下载链接: {result['download_url']}")
        return result
    else:
        print(f"[X] 模板导出为Markdown失败: {response.status_code} - {response.text}")
        return None


def test_export_json(template_id, token):
    """测试导出模板为JSON"""
    print("\n--- 测试导出模板为JSON ---")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/api/template/{template_id}/export-json", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"[OK] 模板导出为JSON成功")
        print(f"  文件名: {result['file_name']}")
        print(f"  文件大小: {result['file_size']}字节")
        print(f"  下载链接: {result['download_url']}")
        return result
    else:
        print(f"[X] 模板导出为JSON失败: {response.status_code} - {response.text}")
        return None


def test_delete_template(template_id, token):
    """测试删除模板"""
    print("\n--- 测试删除模板 ---")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(f"{BASE_URL}/api/template/{template_id}", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"[OK] 模板删除成功 - ID: {result['deleted_template_id']}")
        return True
    else:
        print(f"[X] 模板删除失败: {response.status_code} - {response.text}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("模板管理接口测试")
    print("=" * 60)
    
    token = register_and_login()
    if not token:
        print("无法获取访问令牌，测试终止")
        exit(1)
    
    template_id = test_create_template(token)
    if not template_id:
        print("无法创建模板，测试终止")
        exit(1)
    
    test_get_template(template_id, token)
    test_get_template_list(token)
    test_update_template(template_id, token)
    test_get_categories(token)
    test_get_popular_tags(token)
    test_export_markdown(template_id, token)
    test_export_json(template_id, token)
    test_delete_template(template_id, token)
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
