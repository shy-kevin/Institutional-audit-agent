# 智能编制助手模块 API 接口文档

## 📋 目录

- [1. 主页面相关接口](#1-主页面相关接口)
- [2. 选择模板页面接口](#2-选择模板页面接口)
- [3. 关联上下位制度页面接口](#3-关联上下位制度页面接口)
- [4. 上传资料页面接口](#4-上传资料页面接口)
- [5. 生成大纲页面接口](#5-生成大纲页面接口)
- [6. 编辑完善页面接口](#6-编辑完善页面接口)
- [7. 通用文件上传接口](#7-通用文件上传接口)

---

## 基础信息

**Base URL**: `http://localhost:8000`

**认证方式**: Bearer Token (JWT)

**请求头格式**:
```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer <access_token>"
}
```

**文件上传请求头格式**:
```json
{
  "Authorization": "Bearer <access_token>"
}
```

---

## 1. 主页面相关接口

### 1.1 获取文档统计数据

**接口描述**: 获取智能编制助手主页面的统计卡片数据，包括总数、起草中、已完成、待审查等统计信息。

**请求方式**: `GET`

**请求路径**: `/api/document/statistics`

**请求参数**: 无

**请求示例**:
```bash
curl -X GET http://localhost:8000/api/document/statistics \
  -H "Authorization: Bearer <token>"
```

**响应结果**:
```json
{
  "total": 65,
  "drafting_count": 12,
  "drafting_week_new": 3,
  "completed_count": 48,
  "completed_month_count": 6,
  "archived_count": 0,
  "pending_review_count": 5
}
```

**字段说明**:
| 字段名 | 类型 | 说明 |
|--------|------|------|
| total | integer | 制度总数 |
| drafting_count | integer | 起草中制度数量 |
| drafting_week_new | integer | 本周新增起草数量 |
| completed_count | integer | 已完成制度数量 |
| completed_month_count | integer | 本月完成数量 |
| archived_count | integer | 已归档数量 |
| pending_review_count | integer | 待审查数量 |

---

### 1.2 获取制度文档列表

**接口描述**: 分页获取用户的制度文档列表，支持关键词搜索。

**请求方式**: `GET`

**请求路径**: `/api/document/list`

**Query参数**:
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| keyword | string | 否 | "" | 制度名称搜索关键词 |
| status | string | 否 | 全部 | 状态筛选：`drafting`(起草中)、`pending_review`(待审核)、`published`(已发布)、`needs_revision`(待修改) |
| type | string | 否 | 全部 | 类型筛选：`人事管理`、`财务管理`、`业务流程`、`安全管理`等 |
| skip | integer | 否 | 0 | 分页偏移量 |
| limit | integer | 否 | 20 | 每页数量 |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/document/list?keyword=考勤&status=drafting&skip=0&limit=10" \
  -H "Authorization: Bearer <token>"
```

**响应结果**:
```json
{
  "total": 12,
  "items": [
    {
      "id": 1,
      "name": "员工考勤管理制度",
      "type": "人事管理",
      "status": "drafting",
      "author": "张明",
      "updated_at": "2026-04-02 16:30",
      "created_at": "2026-03-15 09:00"
    },
    {
      "id": 2,
      "name": "招聘管理制度",
      "type": "人事管理",
      "status": "drafting",
      "author": "李华",
      "updated_at": "2026-04-01 10:20",
      "created_at": "2026-03-20 14:30"
    }
  ]
}
```

**字段说明**:
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 文档唯一标识 |
| name | string | 制度名称 |
| type | string | 制度类型 |
| status | string | 状态：`drafting`/`pending_review`/`published`/`needs_revision` |
| author | string | 起草人姓名 |
| updated_at | string | 更新时间 (YYYY-MM-DD HH:mm) |
| created_at | string | 创建时间 (YYYY-MM-DD HH:mm) |

---

### 1.3 获取可授权用户列表

**接口描述**: 获取可用于文档授权的用户列表。

**请求方式**: `GET`

**请求路径**: `/api/document/{doc_id}/available-users`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| doc_id | integer | 是 | 文档ID |

**Query参数**:
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| keyword | string | 否 | "" | 用户名/部门搜索关键词 |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/document/1/available-users?keyword=lumi" \
  -H "Authorization: Bearer <token>"
```

**响应结果**:
```json
{
  "total": 25,
  "items": [
    {
      "id": 1,
      "username": "lumi",
      "department": "IT部",
      "role": "user",
      "can_view": true,
      "can_edit": false
    },
    {
      "id": 2,
      "username": "javis",
      "department": "IT部",
      "role": "user",
      "can_view": false,
      "can_edit": true
    }
  ]
}
```

**字段说明**:
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 用户ID |
| username | string | 用户名 |
| department | string | 部门名称 |
| role | string | 角色：`admin`/`user` |
| can_view | boolean | 是否有查看权限 |
| can_edit | boolean | 是否有编辑权限 |

---

### 1.4 设置文档用户权限

**接口描述**: 批量设置指定文档的用户访问权限（查看/编辑）。

**请求方式**: `POST`

**请求路径**: `/api/document/{doc_id}/permissions`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| doc_id | integer | 是 | 文档ID |

**请求体参数**:
```json
{
  "user_permissions": [
    {
      "user_id": 1,
      "can_view": true,
      "can_edit": false
    },
    {
      "user_id": 2,
      "can_view": true,
      "can_edit": true
    }
  ]
}
```

**字段说明**:
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| user_permissions | array | 是 | 权限设置数组 |
| user_permissions[].user_id | integer | 是 | 用户ID |
| user_permissions[].can_view | boolean | 是 | 是否允许查看 |
| user_permissions[].can_edit | boolean | 是 | 是否允许编辑 |

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/document/1/permissions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_permissions": [
      { "user_id": 1, "can_view": true, "can_edit": false },
      { "user_id": 2, "can_view": true, "can_edit": true }
    ]
  }'
```

**响应结果**:
```json
{
  "success": true,
  "message": "权限设置成功",
  "affected_users": 2
}
```

---

## 2. 选择模板页面接口

### 2.1 获取模板列表

**接口描述**: 获取系统预定义的制度模板列表，支持按类型筛选和关键词搜索。

**请求方式**: `GET`

**请求路径**: `/api/template/list`

**Query参数**:
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| type | string | 否 | 全部 | 模板类型：`行政制度`、`人事制度`、`财务制度`等 |
| keyword | string | 否 | "" | 模板名称或描述的搜索关键词 |
| skip | integer | 否 | 0 | 分页偏移量 |
| limit | integer | 否 | 50 | 每页数量 |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/template/list?type=人事制度&keyword=考勤" \
  -H "Authorization: Bearer <token>"
```

**响应结果**:
```json
{
  "total": 6,
  "items": [
    {
      "id": 1,
      "name": "员工考勤管理制度",
      "type": "人事管理",
      "category": "行政制度",
      "description": "规范员工考勤管理，明确考勤时间、请假流程、迟到早退处理等规定，适用于各类企业。",
      "icon": "👥",
      "version": "1.0",
      "usage_count": 156,
      "preview_url": "/templates/attendance-preview.md",
      "created_at": "2026-01-15T08:00:00Z"
    },
    {
      "id": 2,
      "name": "招聘管理制度",
      "type": "人事管理",
      "category": "人事制度",
      "description": "规范招聘流程，明确岗位需求、面试流程、录用标准，适用于人力资源部门使用。",
      "icon": "📋",
      "version": "1.2",
      "usage_count": 89,
      "preview_url": "/templates/recruit-preview.md",
      "created_at": "2026-02-20T10:30:00Z"
    }
  ]
}
```

**字段说明**:
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 模板唯一标识 |
| name | string | 模板名称 |
| type | string | 模板所属领域分类 |
| category | string | 模板类别（用于筛选） |
| description | string | 模板详细描述 |
| icon | string | 模板图标（emoji或图标URL） |
| version | string | 模板版本号 |
| usage_count | integer | 使用次数 |
| preview_url | string | 预览内容URL |
| created_at | datetime | 创建时间 (ISO 8601) |

---

### 2.2 获取模板详情（预览）

**接口描述**: 获取指定模板的详细内容和结构信息，用于模板预览。

**请求方式**: `GET`

**请求路径**: `/api/template/{template_id}`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| template_id | integer | 是 | 模板ID |

**请求示例**:
```bash
curl -X GET http://localhost:8000/api/template/1 \
  -H "Authorization: Bearer <token>"
```

**响应结果**:
```json
{
  "id": 1,
  "name": "员工考勤管理制度",
  "type": "人事管理",
  "category": "行政制度",
  "description": "规范员工考勤管理...",
  "icon": "👥",
  "version": "1.0",
  "content_structure": [
    {
      "chapter": "第一章 总则",
      "sections": ["第一条 目的", "第二条 适用范围", "第三条 基本原则"]
    },
    {
      "chapter": "第二章 工作时间",
      "sections": ["第四条 标准工作时间", "第五条 弹性工作制"]
    },
    {
      "chapter": "第三章 请假管理",
      "sections": ["第六条 请假事由与类别", "第七条 各类假期规定"]
    },
    {
      "chapter": "第四章 违纪处理",
      "sections": ["第八条 迟到/早退/旷工", "第九条 处罚措施"]
    },
    {
      "chapter": "第五章 附则",
      "sections": ["第十条 生效时间", "第十一条 解释权"]
    }
  ],
  "sample_content": "# 员工考勤管理制度\n\n## 第一章 总则\n\n### 第一条 目的...",
  "related_templates": [3, 5],
  "tags": ["考勤", "人事", "员工管理"],
  "created_at": "2026-01-15T08:00:00Z",
  "updated_at": "2026-03-20T14:00:00Z"
}
```

**字段说明**:
| 字段名 | 类型 | 说明 |
|--------|------|------|
| content_structure | array | 内容章节结构数组 |
| content_structure[].chapter | string | 章节标题 |
| content_structure[].sections | array | 该章节下的条款列表 |
| sample_content | string | 示例内容（Markdown格式） |
| related_templates | array | 相关模板ID列表 |
| tags | array | 标签列表 |

---

### 2.3 上传自定义模板文件

**接口描述**: 用户上传自己的Word/PDF文档作为自定义模板使用。

**请求方式**: `POST`

**请求路径**: `/api/template/upload-custom`

**Content-Type**: `multipart/form-data`

**请求参数** (FormData):
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | File | 是 | 模板文件（支持 .docx, .doc, .pdf 格式） |
| name | string | 是 | 自定义模板名称 |
| category | string | 否 | 模板类别（默认为"自定义"） |
| description | string | 否 | 模板描述说明 |

**请求示例** (FormData):
```
file: [二进制文件]
name: "公司内部培训管理制度"
category: "行政制度"
description: "基于XX集团培训管理办法制定"
```

**响应结果**:
```json
{
  "success": true,
  "template_id": 101,
  "message": "模板上传成功",
  "file_path": "/uploads/templates/custom_101.docx",
  "parsed_outline": {
    "chapters": [...],
    "word_count": 3580
  }
}
```

---

## 3. 关联上下位制度页面接口

### 3.1 搜索上位制度/法律依据

**接口描述**: 根据关键词搜索可作为当前制度上位法或法律依据的相关制度文档。

**请求方式**: `GET`

**请求路径**: `/api/document/search-upper`

**Query参数**:
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| keyword | string | 是 | - | 搜索关键词（制度名称或法律条文） |
| document_type | string | 否 | 全部 | 限制文档类型 |
| limit | integer | 否 | 20 | 返回结果上限 |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/document/search-upper?keyword=劳动法&limit=10" \
  -H "Authorization: Bearer <token>"
```

**响应结果**:
```json
{
  "total": 15,
  "items": [
    {
      "id": "law_001",
      "name": "《中华人民共和国劳动法》（2024修订）",
      "type": "法律法规",
      "publish_date": "2024-11-01",
      "effective_date": "2025-01-01",
      "authority": "全国人民代表大会常务委员会",
      "summary": "调整劳动关系的基本法律...",
      "relevance_score": 0.95,
      "related_articles": ["第三十六条", "第四十四条", "第五十条"]
    },
    {
      "id": "doc_002",
      "name": "《企业职工带薪年休假实施办法》",
      "type": "部门规章",
      "publish_date": "2008-09-18",
      "effective_date": "2008-09-18",
      "authority": "人力资源社会保障部",
      "summary": "具体规定企业职工年休假制度...",
      "relevance_score": 0.87,
      "related_articles": null
    }
  ]
}
```

**字段说明**:
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | string | 文档唯一标识 |
| name | string | 法律法规/制度全称 |
| type | string | 类型：`法律法规`/`部门规章`/`地方性法规`/`企业制度` |
| publish_date | date | 发布日期 |
| effective_date | date | 生效日期 |
| authority | string | 发布机构/制定机关 |
| summary | string | 内容摘要 |
| relevance_score | float | 与查询词的相关度评分 (0-1) |
| related_articles | array/null | 相关条款编号列表 |

---

### 3.2 搜索下位制度/执行手册

**接口描述**: 搜索可以作为当前制度下位执行细则的相关文档。

**请求方式**: `GET`

**请求路径**: `/api/document/search-lower`

**Query参数**:
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| keyword | string | 是 | - | 搜索关键词 |
| parent_doc_type | string | 否 | - | 上位制度类型（用于关联推荐） |
| limit | integer | 否 | 20 | 返回结果上限 |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/document/search-lower?keyword=考勤实施细则" \
  -H "Authorization: Bearer <token>"
```

**响应结果**:
```json
{
  "total": 8,
  "items": [
    {
      "id": "manual_001",
      "name": "《员工考勤管理实施细则》",
      "type": "执行手册",
      "parent_document": "员工考勤管理制度",
      "department": "人力资源部",
      "version": "2.1",
      "status": "published",
      "summary": "详细规定考勤打卡、请假审批流程等操作细节..."
    }
  ]
}
```

**字段说明**:
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | string | 文档唯一标识 |
| name | string | 下位制度/手册名称 |
| type | string | 类型：`执行手册`/`操作指南`/`实施细则` |
| parent_document | string | 关联的上位制度名称 |
| department | string | 制定部门 |
| version | string | 版本号 |
| status | string | 状态 |
| summary | string | 内容摘要 |

---

### 3.3 保存制度关联关系

**接口描述**: 保存当前正在创建的制度与其他制度的上下位关系及备注说明。

**请求方式**: `POST`

**请求路径**: `/api/document/{doc_id}/relations`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| doc_id | integer/string | 是 | 当前创建的文档ID（可为临时ID） |

**请求体参数**:
```json
{
  "upper_documents": [
    {
      "document_id": "law_001",
      "document_name": "《中华人民共和国劳动法》（2024修订）",
      "relation_type": "legal_basis",
      "notes": "本制度主要依据该法关于工作时间和休息休假的条款制定"
    }
  ],
  "lower_documents": [],
  "workflow_notes": "本制度是《公司人力资源管理制度》体系的组成部分，需与其保持一致。"
}
```

**字段说明**:
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| upper_documents | array | 是 | 上位制度/法律依据列表 |
| upper_documents[].document_id | string | 是 | 关联文档ID |
| upper_documents[].document_name | string | 是 | 关联文档名称 |
| upper_documents[].relation_type | string | 是 | 关系类型：`legal_basis`(法律依据)/`superior_regulation`(上级规章) |
| upper_documents[].notes | string | 否 | 关系备注说明 |
| lower_documents | array | 是 | 下位制度列表（结构与upper相同） |
| workflow_notes | string | 否 | 整体工作流/关系说明 |

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/document/temp_001/relations \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "upper_documents": [{
      "document_id": "law_001",
      "document_name": "《中华人民共和国劳动法》（2024修订）",
      "relation_type": "legal_basis",
      "notes": ""
    }],
    "lower_documents": [],
    "workflow_notes": "本制度需与薪酬管理制度协调一致。"
  }'
```

**响应结果**:
```json
{
  "success": true,
  "message": "关联关系保存成功",
  "saved_relations": {
    "upper_count": 1,
    "lower_count": 0
  }
}
```

---

## 4. 上传资料页面接口

### 4.1 上传参考材料文件

**接口描述**: 批量上传制度编制所需的参考文档、旧版本文件、法规资料等。

**请求方式**: `POST`

**请求路径**: `/api/draft/{draft_id}/upload-materials`

**Content-Type**: `multipart/form-data`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| draft_id | string | 是 | 当前草稿会话ID |

**请求参数** (FormData):
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| files | File[] | 是 | 参考文件数组（支持多文件） |
| material_type | string | 否 | 材料类型：`reference`(参考资料)、`old_version`(旧版本)、`regulation`(法规)、`other`(其他) |

**支持的文件格式**:
- Word: `.doc`, `.docx`
- Excel: `.xls`, `.xlsx`
- PDF: `.pdf`
- 文本: `.txt`, `.md`
- 最大单文件大小: **10MB**

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/draft/session_abc123/upload-materials \
  -H "Authorization: Bearer <token>" \
  -F "files=@old_attendance_policy.docx" \
  -F "files=@labor_law_2024.pdf" \
  -F "material_type=reference"
```

**响应结果**:
```json
{
  "success": true,
  "uploaded_files": [
    {
      "file_id": "file_001",
      "file_name": "old_attendance_policy.docx",
      "file_size": 245760,
      "file_type": "docx",
      "file_path": "/uploads/materials/file_001.docx",
      "uploaded_at": "2026-04-10T03:30:00Z"
    },
    {
      "file_id": "file_002",
      "file_name": "labor_law_2024.pdf",
      "file_size": 512000,
      "file_type": "pdf",
      "file_path": "/uploads/materials/file_002.pdf",
      "uploaded_at": "2026-04-10T03:30:00Z"
    }
  ],
  "total_files": 2
}
```

---

### 4.2 删除已上传的参考材料

**接口描述**: 删除指定的参考材料文件。

**请求方式**: `DELETE`

**请求路径**: `/api/draft/{draft_id}/material/{file_id}`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| draft_id | string | 是 | 草稿会话ID |
| file_id | string | 是 | 要删除的文件ID |

**请求示例**:
```bash
curl -X DELETE http://localhost:8000/api/draft/session_abc123/material/file_001 \
  -H "Authorization: Bearer <token>"
```

**响应结果**:
```json
{
  "success": true,
  "message": "文件删除成功",
  "deleted_file_id": "file_001"
}
```

---

### 4.3 保存需求和补充信息

**接口描述**: 保存用户对制度的具体要求、特殊规定说明以及补充备注信息。

**请求方式**: `POST`

**请求路径**: `/api/draft/{draft_id}/requirements`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| draft_id | string | 是 | 草稿会话ID |

**请求体参数**:
```json
{
  "requirements": "适用范围为公司全体正式员工（含试用期），不包括外包人员和实习生。需要特别强调弹性工作制的申请条件和审批流程。合规方面需符合最新劳动法关于加班费计算的规定。",
  "additional_notes": "参考了同行业三家标杆企业的考勤管理制度，重点借鉴了XX公司的弹性工作制方案。",
  "special_constraints": [
    "必须包含远程办公相关规定",
    "加班调休规则需明确",
    "节假日排班机制要细化"
  ]
}
```

**字段说明**:
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| requirements | string | 是 | 需求/参考说明（详细描述期望包含的内容和要求） |
| additional_notes | string | 否 | 补充工作备注 |
| special_constraints | array | 否 | 特殊约束条件列表 |

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/draft/session_abc123/requirements \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": "适用于全体正式员工...",
    "additional_notes": "参考了XX公司的方案...",
    "special_constraints": ["必须包含远程办公规定"]
  }'
```

**响应结果**:
```json
{
  "success": true,
  "message": "需求信息保存成功",
  "saved_at": "2026-04-10T03:35:00Z"
}
```

---

## 5. 生成大纲页面接口

### 5.1 创建草稿会话（开始新制度创建）

**接口描述**: 初始化一个新的制度草稿会话，返回会话ID用于后续步骤的数据关联。

**请求方式**: `POST`

**请求路径**: `/api/draft/create-session`

**请求体参数**:
```json
{
  "template_id": 1,
  "template_name": "员工考勤管理制度",
  "document_type": "人事管理",
  "custom_name": "",
  "creator_id": 1
}
```

**字段说明**:
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| template_id | integer | 是 | 选择的模板ID（0表示完全自定义） |
| template_name | string | 是 | 模板名称或自定义名称 |
| document_type | string | 是 | 制度类型分类 |
| custom_name | string | 否 | 自定义制度名称（如果未使用预设模板） |
| creator_id | integer | 是 | 创建者用户ID |

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/draft/create-session \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": 1,
    "template_name": "员工考勤管理制度",
    "document_type": "人事管理",
    "custom_name": "",
    "creator_id": 1
  }'
```

**响应结果**:
```json
{
  "success": true,
  "draft_session": {
    "session_id": "draft_20260410_abc123",
    "template_id": 1,
    "template_name": "员工考勤管理制度",
    "document_type": "人事管理",
    "status": "initialized",
    "created_at": "2026-04-10T03:20:00Z",
    "expires_at": "2026-04-17T03:20:00Z"
  }
}
```

---

### 5.2 AI生成制度大纲（SSE流式接口）

**接口描述**: 基于前面步骤收集的所有信息（模板、关联文档、参考材料、需求说明），调用AI生成制度草案大纲。采用Server-Sent Events (SSE) 流式返回生成进度和内容。

**请求方式**: `POST`

**请求路径**: `/api/draft/{session_id}/generate-outline`

**Content-Type**: `application/json`

**Accept**: `text/event-stream`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| session_id | string | 是 | 草稿会话ID |

**请求体参数**:
```json
{
  "document_title": "员工考勤管理制度",
  "generation_options": {
    "include_examples": true,
    "detail_level": "standard",
    "style": "formal"
  }
}
```

**字段说明**:
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| document_title | string | 是 | 制度文档标题 |
| generation_options | object | 否 | 生成选项配置 |
| generation_options.include_examples | boolean | 否 | 是否包含示例说明（默认true） |
| generation_options.detail_level | string | 否 | 详细程度：`brief`(简略)/`standard`(标准)/`detailed`(详细) |
| generation_options.style | string | 否 | 文风风格：`formal`(正式)/`plain`(通俗) |

**请求示例**:
```bash
curl -N -X POST http://localhost:8000/api/draft/draft_20260410_abc123/generate-outline \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "document_title": "员工考勤管理制度",
    "generation_options": {
      "include_examples": true,
      "detail_level": "standard",
      "style": "formal"
    }
  }'
```

**SSE流式响应格式**:

事件流将按顺序返回以下类型的消息：

#### 阶段1: 开始生成
```
data: {"event": "generation_started", "message": "开始生成大纲...", "timestamp": "2026-04-10T03:40:00Z"}
```

#### 阶段2: 进度更新
```
data: {"event": "progress_update", "progress": 25, "current_chapter": "正在生成第一章 总则...", "estimated_time_remaining": 45, "is_end": false}
data: {"event": "progress_update", "progress": 50, "current_chapter": "正在生成第二章 工作时间...", "estimated_time_remaining": 30, "is_end": false}
data: {"event": "progress_update", "progress": 75, "current_chapter": "正在生成第三章 请假管理...", "estimated_time_remaining": 15, "is_end": false}
```

#### 阶段3: 大纲内容块（增量）
```
data: {"event": "outline_chunk", "content": "# 员工考勤管理制度（草案大纲）\n\n## 第一章 总则\n\n### 第一条 目的\n为规范公司员工考勤管理，确保正常工作秩序，提高工作效率，依据《中华人民共和国劳动法》及相关法律法规，特制定本制度。\n\n### 第二条 适用范围\n本制度适用于公司全体员工（含试用期员工）、临时工、以及因工作需要及临时聘用人员。\n\n### 第三条 基本原则\n考勤管理应遵循公平、公正、公开的原则；", "is_end": false}

data: {"event": "outline_chunk", "content": "\n## 第二章 工作时间\n\n### 第四条 标准工作时间\n公司实行标准工时制，工作时间：周一至周五，上午9:00-12:00，下午13:30-18:00。\n\n### 第五条 弹性工作制\n部分岗位经申请批准后可实行弹性工作制，具体要求详见《弹性工作管理办法》。", "is_end": false}
```

#### 阶段4: 生成完成
```
data: {"event": "generation_completed", "message": "大纲生成成功！", "total_tokens": 2850, "generation_time_ms": 1850, "outline_id": "outline_xyz789", "is_end": true}
```

**完整响应事件汇总**:

| 事件类型 (event) | 触发时机 | 主要字段 |
|-------------------|----------|----------|
| `generation_started` | 开始时 | message, timestamp |
| `progress_update` | 生成过程中多次 | progress(0-100), current_chapter, estimated_time_remaining |
| `outline_chunk` | 内容增量输出 | content(Markdown文本片段), is_end(false) |
| `generation_error` | 出错时 | error_code, error_message, suggestion |
| `generation_completed` | 完成时 | total_tokens, generation_time_ms, outline_id, is_end(true) |

---

### 5.3 重新生成大纲

**接口描述**: 重新触发AI生成大纲（例如修改了某些输入后希望获得新的结果）。

**请求方式**: `POST`

**请求路径**: `/api/draft/{session_id}/regenerate-outline`

**路径参数**: 同5.2

**请求体参数**: 同5.2

**响应格式**: SSE流式（同5.2）

**额外说明**: 调用此接口会清除之前生成的大纲内容，从头开始重新生成。

---

### 5.4 获取已生成的大纲内容

**接口描述**: 获取之前生成的完整大纲内容（非流式，用于回显或导出）。

**请求方式**: `GET`

**请求路径**: `/api/draft/{session_id}/outline`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| session_id | string | 是 | 草稿会话ID |

**Query参数**:
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| format | string | 否 | markdown | 返回格式：`markdown`/`html`/`json`(结构化) |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/draft/draft_20260410_abc123/outline?format=markdown" \
  -H "Authorization: Bearer <token>"
```

**响应结果 (format=json 时)**:
```json
{
  "session_id": "draft_20260410_abc123",
  "outline_id": "outline_xyz789",
  "document_title": "员工考勤管理制度",
  "generated_at": "2026-04-10T03:43:20Z",
  "chapters": [
    {
      "chapter_number": "第一章",
      "chapter_title": "总则",
      "order": 1,
      "articles": [
        {
          "article_number": "第一条",
          "article_title": "目的",
          "content": "为规范公司员工考勤管理，确保正常工作秩序，提高工作效率，依据《中华人民共和国劳动法》及相关法律法规，特制定本制度。",
          "order": 1
        },
        {
          "article_number": "第二条",
          "article_title": "适用范围",
          "content": "本制度适用于公司全体员工（含试用期员工）、临时工、以及因工作需要及临时聘用人员。",
          "order": 2
        },
        {
          "article_number": "第三条",
          "article_title": "基本原则",
          "content": "考勤管理应遵循公平、公正、公开的原则；",
          "order": 3
        }
      ]
    },
    {
      "chapter_number": "第二章",
      "chapter_title": "工作时间",
      "order": 2,
      "articles": [...]
    }
  ],
  "statistics": {
    "total_chapters": 5,
    "total_articles": 11,
    "word_count": 2850,
    "estimated_reading_minutes": 9
  }
}
```

---

### 5.5 导出大纲为Word文档

**接口描述**: 将当前生成的制度大纲导出为Word (.docx) 格式文件。

**请求方式**: `POST`

**请求路径**: `/api/draft/{session_id}/export-outline-word`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| session_id | string | 是 | 草稿会话ID |

**请求体参数**:
```json
{
  "include_toc": true,
  "include_header_footer": true,
  "header_text": "{document_title} - 草案大纲",
  "footer_text": "第 {page} 页 / 共 {pages} 页"
}
```

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/draft/draft_20260410_abc123/export-outline-word \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "include_toc": true,
    "include_header_footer": true,
    "header_text": "员工考勤管理制度 - 草案大纲",
    "footer_text": "第 {page} 页 / 共 {pages} 页"
  }'
```

**响应结果**:
```json
{
  "success": true,
  "download_url": "/api/files/download/outline_20260410_abc123.docx",
  "file_name": "员工考勤管理制度_草案大纲.docx",
  "file_size": 45680,
  "expires_at": "2026-04-11T03:43:20Z"
}
```

---

## 6. 编辑完善页面接口

### 6.1 保存制度草稿

**接口描述**: 保存当前编辑中的制度内容（自动保存或手动保存）。

**请求方式**: `PUT`

**请求路径**: `/api/draft/{session_id}/save-draft`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| session_id | string | 是 | 草稿会话ID |

**请求体参数**:
```json
{
  "content": "# 员工考勤管理制度\n\n## 第一章 总则\n\n### 第一条 目的\n为规范公司员工考勤管理...\n\n[完整Markdown内容]",
  "content_format": "markdown",
  "last_edited_chapter": "第一章 总则",
  "auto_save": false
}
```

**字段说明**:
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| content | string | 是 | 完整的制度文档内容（Markdown格式） |
| content_format | string | 是 | 内容格式（固定为`markdown`） |
| last_edited_chapter | string | 否 | 最后编辑的章节（用于恢复定位） |
| auto_save | boolean | 否 | 是否为自动保存（默认false） |

**请求示例**:
```bash
curl -X PUT http://localhost:8000/api/draft/draft_20260410_abc123/save-draft \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "# 员工考勤管理制度\n\n## 第一章 总则\n\n### 第一条 目的\n...",
    "content_format": "markdown",
    "last_edited_chapter": "第一章 总则",
    "auto_save": false
  }'
```

**响应结果**:
```json
{
  "success": true,
  "message": "草稿保存成功",
  "saved_at": "2026-04-10T04:00:00Z",
  "version": 5,
  "word_count": 3200
}
```

---

### 6.2 导出最终版本文档

**接口描述**: 将编辑完成的制度导出为最终格式的Word文档（排版优化后的正式版本）。

**请求方式**: `POST`

**请求路径**: `/api/draft/{session_id}/export-final`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| session_id | string | 是 | 草稿会话ID |

**请求体参数**:
```json
{
  "format": "docx",
  "options": {
    "include_cover_page": true,
    "cover_info": {
      "title": "员工考勤管理制度",
      "document_number": "HR-POL-001",
      "version": "V1.0（草案）",
      "department": "人力资源部",
      "date": "2026年4月"
    },
    "include_toc": true,
    "include_approval_section": true,
    "font_family": "仿宋_GB2312",
    "title_font_size": 22,
    "body_font_size": 14,
    "line_spacing": 1.75,
    "margins": {
      "top": 2.54,
      "bottom": 2.54,
      "left": 3.17,
      "right": 3.17
    }
  }
}
```

**字段说明**:
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| format | string | 是 | 导出格式：`docx`/`pdf` |
| options | object | 否 | 导出配置选项 |
| options.include_cover_page | boolean | 否 | 是否包含封面页（默认true） |
| options.cover_info | object | 否 | 封面页信息 |
| options.include_toc | boolean | 否 | 是否包含目录（默认true） |
| options.include_approval_section | boolean | 否 | 是否包含签批栏（默认true） |
| options.font_family | string | 否 | 正文字体（默认"仿宋_GB2312"） |
| options.title_font_size | integer | 否 | 标题字号（默认22磅） |
| options.body_font_size | integer | 否 | 正文字号（默认14磅，即小四） |
| options.line_spacing | float | 否 | 行距（默认1.75倍） |
| options.margins | object | 否 | 页边距（单位cm） |

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/draft/draft_20260410_abc123/export-final \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "docx",
    "options": {
      "include_cover_page": true,
      "cover_info": {
        "title": "员工考勤管理制度",
        "document_number": "HR-POL-001",
        "version": "V1.0（草案）",
        "department": "人力资源部",
        "date": "2026年4月"
      },
      "include_toc": true,
      "include_approval_section": true
    }
  }'
```

**响应结果**:
```json
{
  "success": true,
  "download_url": "/api/files/download/final_20260410_abc123.docx",
  "file_name": "员工考勤管理制度_V1.0草案.docx",
  "file_size": 128500,
  "page_count": 8,
  "expires_at": "2026-04-11T04:05:00Z"
}
```

---

### 6.3 提交制度审核

**接口描述**: 将编辑完成的制度提交进入审核流程。

**请求方式**: `POST`

**请求路径**: `/api/draft/{session_id}/submit-review`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| session_id | string | 是 | 草稿会话ID |

**请求体参数**:
```json
{
  "document_name": "员工考勤管理制度",
  "document_type": "人事管理",
  "reviewers": [2, 3],
  "review_deadline": "2026-04-24T23:59:59Z",
  "priority": "normal",
  "attachments": ["file_001", "file_002"],
  "submission_note": "请重点审核弹性工作制相关条款的合规性。"
}
```

**字段说明**:
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| document_name | string | 是 | 制度最终名称 |
| document_type | string | 是 | 制度类型分类 |
| reviewers | integer[] | 是 | 指定的审核人用户ID列表 |
| review_deadline | datetime | 否 | 审核截止时间 (ISO 8601) |
| priority | string | 否 | 优先级：`low`/`normal`/`high`/`urgent`（默认`normal`） |
| attachments | string[] | 否 | 附件文件ID列表 |
| submission_note | string | 否 | 提交说明/备注 |

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/draft/draft_20260410_abc123/submit-review \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "document_name": "员工考勤管理制度",
    "document_type": "人事管理",
    "reviewers": [2, 3],
    "review_deadline": "2026-04-24T23:59:59Z",
    "priority": "normal",
    "submission_note": "请重点审核弹性工作制相关条款的合规性。"
  }'
```

**响应结果**:
```json
{
  "success": true,
  "message": "制度提交审核成功",
  "document_id": 102,
  "review_task_id": "review_task_456",
  "status": "pending_review",
  "submitted_at": "2026-04-10T04:10:00Z",
  "review_deadline": "2026-04-24T23:59:59Z",
  "assigned_reviewers": [
    {"user_id": 2, "username": "javis", "status": "pending"},
    {"user_id": 3, "username": "yvan", "status": "pending"}
  ]
}
```

---

### 6.4 AI助手对话（SSE流式接口）

**接口描述**: 在编辑页面右侧AI助手中进行对话，向AI提问或提出修改建议。采用SSE流式返回AI回复。

**请求方式**: `POST**

**请求路径**: `/api/draft/{session_id}/ai-chat`

**Content-Type**: `application/json`

**Accept**: `text/event-stream`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| session_id | string | 是 | 草稿会话ID |

**请求体参数**:
```json
{
  "message": "请帮我把第三条关于基本原则的内容扩充一下，增加关于公平性的具体表述。",
  "context": {
    "current_chapter": "第一章 总则",
    "selected_text": "考勤管理应遵循公平、公正、公开的原则；",
    "conversation_history": [
      {"role": "assistant", "content": "您好！我是您的AI助手..."},
      {"role": "user", "content": "这个大纲看起来不错"}
    ]
  },
  "mode": "qna"
}
```

**字段说明**:
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| message | string | is | 用户提问或指令内容 |
| context | object | 否 | 对话上下文 |
| context.current_chapter | string | 否 | 当前所在章节 |
| context.selected_text | string | 否 | 用户选中的文本片段 |
| context.conversation_history | array | 否 | 历史对话记录（最近N轮） |
| mode | string | 否 | 对话模式：`qna`(问答)/`modify`(修改建议)/`expand`(智能扩充) |

**请求示例**:
```bash
curl -N -X POST http://localhost:8000/api/draft/draft_20260410_abc123/ai-chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "message": "请帮我把第三条关于基本原则的内容扩充一下",
    "context": {
      "current_chapter": "第一章 总则",
      "selected_text": "考勤管理应遵循公平、公正、公开的原则；"
    },
    "mode": "expand"
  }'
```

**SSE流式响应格式**:

```
data: {"event": "thinking", "content": "", "is_end": false}

data: {"event": "content_chunk", "content": "好的，我来帮您扩充第三条的基本原则内容。以下是我建议的修改版本：\n\n", "is_end": false}

data: {"event": "content_chunk", "content": "**第三条 基本原则**\n\n考勤管理应当遵循以下原则：\n\n1. ", "is_end": false}

data: {"event": "content_chunk", "content": "**公平原则**：对所有员工一视同仁，不因性别、年龄、职位等因素区别对待考勤标准和处罚措施。考勤数据的采集、统计和处理过程应当透明、可追溯。\n\n2. **公正原则**：", "is_end": false}

...

data: {"event": "completed", "message": "回答完成", "tokens_used": 450, "is_end": true}
```

**响应事件类型**:

| 事件类型 (event) | 说明 | 主要字段 |
|-------------------|------|----------|
| `thinking` | AI思考中 | - |
| `content_chunk` | 回复内容增量 | content, is_end(false) |
| `suggested_modification` | 修改建议（mode=modify时） | original_text, suggested_text, explanation |
| `error` | 出错 | error_code, error_message |
| `completed` | 完成 | tokens_used, is_end(true) |

---

### 6.5 合规检查

**接口描述**: 对当前制度内容进行自动化合规检查，检测潜在的法律风险、格式问题、逻辑矛盾等。

**请求方式**: `POST`

**请求路径**: `/api/draft/{session_id}/compliance-check`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| session_id | string | 是 | 草稿会话ID |

**请求体参数**:
```json
{
  "check_scope": ["legal_compliance", "format_standard", "internal_consistency", "terminology"],
  "reference_documents": ["law_001", "file_002"]
}
```

**字段说明**:
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| check_scope | string[] | 是 | 检查范围 |
| reference_documents | string[] | 否 | 参考文档ID列表（用于对比检查） |

**check_scope 可选值**:
| 值 | 说明 |
|----|------|
| `legal_compliance` | 法律合规性检查（与上位法冲突检测） |
| `format_standard` | 格式规范性检查（公文格式、条款编号等） |
| `internal_consistency` | 内部一致性检查（前后矛盾、重复定义等） |
| `terminology` | 术语规范性检查（专业术语使用是否准确） |

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/draft/draft_20260410_abc123/compliance-check \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "check_scope": ["legal_compliance", "format_standard", "internal_consistency"],
    "reference_documents": ["law_001"]
  }'
```

**响应结果**:
```json
{
  "success": true,
  "check_id": "check_789",
  "overall_status": "warning",
  "checked_at": "2026-04-10T04:15:00Z",
  "summary": {
    "total_issues": 5,
    "critical": 1,
    "warning": 3,
    "info": 1
  },
  "issues": [
    {
      "issue_id": "issue_001",
      "severity": "critical",
      "category": "legal_compliance",
      "location": "第三章 第七条 各类假期规定",
      "description": "年假天数规定（'入职满一年享受带薪年假'）不够具体，可能与《职工带薪年休假条例》规定的最低标准不一致。",
      "suggestion": "建议明确写明：'职工累计工作已满1年不满10年的，年休假5天；已满10年不满20年的，年休假10天；已满20年的，年休假15天。'",
      "reference_article": "《职工带薪年休假条例》第三条",
      "auto_fixable": false
    },
    {
      "issue_id": "issue_002",
      "severity": "warning",
      "category": "format_standard",
      "location": "全文",
      "description": "部分条款缺少明确的生效日期说明。",
      "suggestion": "建议在附则章节增加专门的生效日期条款。",
      "auto_fixable": true
    },
    {
      "issue_id": "issue_003",
      "severity": "warning",
      "category": "internal_consistency",
      "location": "第二章 第五条 vs 第四章 第八条",
      "description": "'弹性工作制'在第五条提到但未定义具体申请条件，而第八条的迟到判定可能与之冲突。",
      "suggestion": "建议补充弹性工作制的申请流程和审批标准，或在迟到判定条款中排除弹性工作制人员。",
      "auto_fixable": false
    }
  ],
  "passed_checks": [
    {"check_type": "terminology", "message": "术语使用规范，无明显不当之处。"}
  ]
}
```

**severity 严重级别说明**:
| 级别 | 含义 | 建议 |
|------|------|------|
| `critical` | 严重问题 | 必须修改后才能提交 |
| `warning` | 警告问题 | 强烈建议修改 |
| `info` | 信息提示 | 可选修改，仅供参考 |

---

### 6.6 引用查看

**接口描述**: 获取制度内容中引用的外部文档、法律条文等的详细信息。

**请求方式**: `GET`

**请求路径**: `/api/draft/{session_id}/references`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| session_id | string | 是 | 草稿会话ID |

**Query参数**:
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| reference_id | string | 否 | 全部 | 查看特定引用的详情 |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/draft/draft_20260410_abc123/references" \
  -H "Authorization: Bearer <token>"
```

**响应结果**:
```json
{
  "total_references": 4,
  "references": [
    {
      "ref_id": "ref_001",
      "source_type": "law",
      "source_id": "law_001",
      "source_name": "《中华人民共和国劳动法》（2024修订）",
      "cited_in": ["第一条", "第三条", "第七条"],
      "cited_articles": ["第三十六条", "第四十四条", "第四十五条", "第五十条"],
      "excerpt": "第三十六条 国家实行劳动者每日工作时间不超过八小时、平均每周工作时间不超过四十四小时的工时制度...",
      "validity": "current",
      "link": "/api/references/law_001/detail"
    },
    {
      "ref_id": "ref_002",
      "source_type": "document",
      "source_id": "file_002",
      "source_name": "公司2025年度考勤管理规定（旧版）",
      "cited_in": ["第八条 处罚措施"],
      "cited_articles": null,
      "excerpt": "...月累计迟到3次以上者，扣除当月绩效奖金的20%...",
      "validity": "superseded",
      "note": "此文件已被当前新制度替代"
    }
  ]
}
```

---

## 7. 通用文件上传接口

### 7.1 编辑器附件上传

**接口描述**: 在编辑页面通过工具栏"上传附件"功能上传的文件（如图片、表格等嵌入到文档中）。

**请求方式**: `POST`

**请求路径**: `/api/draft/{session_id}/upload-attachment`

**Content-Type**: `multipart/form-data`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| session_id | string | 是 | 草稿会话ID |

**请求参数** (FormData):
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | File | 是 | 附件文件 |
| attachment_type | string | 否 | 附件类型：`image`/`table`/`other`（默认自动识别） |

**支持的文件格式**:
- 图片: `.jpg`, `.jpeg`, `.png`, `.gif`, `.svg` (最大 5MB)
- 表格: `.xls`, `.xlsx`, `.csv` (最大 2MB)
- 其他: `.pdf` (最大 10MB)

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/draft/draft_20260410_abc123/upload-attachment \
  -H "Authorization: Bearer <token>" \
  -F "file=@schedule_table.xlsx" \
  -F "attachment_type=table"
```

**响应结果**:
```json
{
  "success": true,
  "attachment": {
    "attachment_id": "att_001",
    "file_name": "schedule_table.xlsx",
    "file_size": 25600,
    "file_type": "xlsx",
    "file_url": "/uploads/attachments/att_001.xlsx",
    "markdown_reference": "![排班表](/api/files/att_001)",
    "uploaded_at": "2026-04-10T04:20:00Z"
  }
}
```

---

## 附录A: 错误码说明

| HTTP状态码 | 错误码 (error_code) | 说明 | 解决方案 |
|------------|---------------------|------|----------|
| 400 | `INVALID_REQUEST` | 请求参数错误 | 检查必填参数和参数格式 |
| 401 | `UNAUTHORIZED` | 未登录或Token过期 | 重新登录获取新Token |
| 403 | `FORBIDDEN` | 无权限执行该操作 | 联系管理员分配相应权限 |
| 404 | `NOT_FOUND` | 资源不存在 | 检查ID是否正确 |
| 409 | `CONFLICT` | 资源冲突（如重复提交） | 检查操作状态，避免重复操作 |
| 413 | `FILE_TOO_LARGE` | 上传文件超出大小限制 | 压缩文件或分批上传 |
| 422 | `UNPROCESSABLE_ENTITY` | 文件格式不支持 | 使用支持的文件格式 |
| 429 | `RATE_LIMITED` | 请求频率超限 | 降低请求频率，稍后重试 |
| 500 | `INTERNAL_ERROR` | 服务器内部错误 | 联系技术支持 |
| 503 | `SERVICE_UNAVAILABLE` | AI服务不可用 | 稍后重试或联系管理员 |
| 504 | `GENERATION_TIMEOUT` | AI生成超时 | 减少生成内容量或重试 |

---

## 附录B: 数据状态流转图

```
                    ┌─────────────────┐
                    │   initialized   │ ← create-session
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  collecting_data │ ← 步骤1-3 收集数据
                    │ (收集模板/关联/资料)│
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   generating    │ ← generate-outline
                    │   (AI生成大纲中)  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼──────┐ ┌─────▼───────┐ ┌───▼──────────┐
     │  outline_ready │ │  generation │ │   error       │
     │ (大纲生成完成)  │ │ _failed     │ │  (生成失败)    │
     └────────┬───────┘ └─────┬───────┘ └───┬──────────┘
              │               │              │
              │         regenerate-outline  │
              │              │              │
     ┌────────▼──────────────┘              │
     │ editing                               │
     │ (编辑完善中)                           │
     │  ├─ save-draft (随时保存草稿)         │
     │  ├─ ai-chat (AI辅助)                  │
     │  ├─ compliance-check (合规检查)       │
     │  └─ export-final (导出)               │
     └────────┬──────────────────────────────┘
              │
     ┌────────▼────────┐
     │ submitted       │ ← submit-review
     │ (已提交审核)     │
     └────────┬────────┘
              │
     ┌────────▼────────┐     ┌──────────────┐
     │ under_review     │────▶│ approved     │
     │ (审核中)         │     │ (审核通过)    │
     └────────┬────────┘     └──────────────┘
              │
     ┌────────▼────────┐     ┌──────────────┐
     │ needs_revision  │◀────│ rejected     │
     │ (需修改)         │     │ (审核驳回)    │
     └─────────────────┘     └──────────────┘
                                    │
                              返回 editing
```

---

## 附录C: 接口调用时序图（完整流程）

```
前端                          后端 API
 │                              │
 ├── 1. GET /api/template/list  │
 │◄─────────────────────────── │ 模板列表
 │                              │
 ├── 2. POST /api/draft/       │
 │   create-session            │
 │◄─────────────────────────── │ session_id
 │                              │
 ├── 3. POST /api/document/    │
 │   {session}/relations       │
 │◄─────────────────────────── │ OK
 │                              │
 ├── 4. POST /api/draft/       │
 │   {session}/upload-materials│
 │◄─────────────────────────── │ file_ids
 │                              │
 ├── 5. POST /api/draft/       │
 │   {session}/requirements    │
 │◄─────────────────────────── │ OK
 │                              │
 ├── 6. POST /api/draft/       │
 │   {session}/generate-outline│
 │◄═══ SSE stream ════════════ │ 大纲内容(流式)
 │                              │
 ├── 7. PUT /api/draft/        │
 │   {session}/save-draft      │ (多次)
 │◄─────────────────────────── │ OK
 │                              │
 ├── 8. POST /api/draft/       │
 │   {session}/ai-chat         │ (多次)
 │◄═══ SSE stream ════════════ │ AI回复(流式)
 │                              │
 ├── 9. POST /api/draft/       │
 │   {session}/compliance-check│
 │◄─────────────────────────── │ 检查报告
 │                              │
 ├── 10. POST /api/draft/      │
 │   {session}/export-final    │
 │◄─────────────────────────── │ download_url
 │                              │
 ├── 11. POST /api/draft/      │
 │   {session}/submit-review   │
 │◄─────────────────────────── │ document_id, review_task_id
 │                              │
```

---

**文档版本**: v1.0  
**最后更新**: 2026-04-10  
**维护者**: 前端开发团队
