# 模板管理模块 API 接口文档

## 📋 目录

- [1. 模板CRUD接口](#1-模板crud接口)
- [2. 模板搜索与筛选](#2-模板搜索与筛选)
- [3. 模板导出接口](#3-模板导出接口)

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

---

## 数据模型

### Template 模板数据结构

```typescript
interface Template {
  id: string;                    // 模板唯一标识
  name: string;                  // 模板名称
  category: string;              // 模板分类（人事管理/财务管理/行政管理/业务流程/安全管理/自定义）
  description: string;           // 模板描述
  
  // 格式设置
  format: {
    fontSize: string;            // 字号（12px/14px/16px/18px）
    fontFamily: string;          // 字体（仿宋_GB2312/宋体/黑体/楷体）
    lineHeight: string;          // 行距（1.5/1.75/2）
    margin: string;              // 页边距（2.54cm/2cm/3cm）
  };
  
  // 章节结构
  sections: TemplateSection[];
  
  // 元数据
  creator_id: number;            // 创建者用户ID
  creator_name: string;          // 创建者姓名
  created_at: string;            // 创建时间 (ISO 8601)
  updated_at: string;            // 更新时间 (ISO 8601)
  is_public: boolean;            // 是否公开模板
  usage_count: number;           // 使用次数
  tags: string[];                // 标签列表
}

interface TemplateSection {
  id: string;                    // 章节唯一标识
  level: number;                 // 层级（1=一级标题/章，2=二级标题/条）
  title: string;                 // 章节标题
  description?: string;          // 章节描述
  children?: TemplateSection[];  // 子章节列表
}
```

---

## 1. 模板CRUD接口

### 1.1 创建新模板

**接口描述**: 创建一个新的制度模板，保存模板的基本信息、格式设置和章节结构。

**请求方式**: `POST`

**请求路径**: `/api/template/create`

**请求体参数**:
```json
{
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
  "is_public": false,
  "tags": ["考勤", "人事", "管理制度"]
}
```

**字段说明**:
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | string | 是 | 模板名称，最大长度100字符 |
| category | string | 是 | 模板分类，可选值见附录 |
| description | string | 否 | 模板描述，最大长度500字符 |
| format | object | 是 | 格式设置对象 |
| format.fontSize | string | 是 | 字号：`12px`/`14px`/`16px`/`18px` |
| format.fontFamily | string | 是 | 字体：`仿宋_GB2312`/`宋体`/`黑体`/`楷体` |
| format.lineHeight | string | 是 | 行距：`1.5`/`1.75`/`2` |
| format.margin | string | 是 | 页边距：`2.54cm`/`2cm`/`3cm` |
| sections | array | 是 | 章节结构数组，至少包含1个章节 |
| sections[].id | string | 是 | 章节唯一标识，建议格式：`section_1`、`section_1_1` |
| sections[].level | number | 是 | 层级：1=章，2=条 |
| sections[].title | string | 是 | 章节标题 |
| sections[].description | string | 否 | 章节描述 |
| sections[].children | array | 否 | 子章节数组，结构同父章节 |
| is_public | boolean | 否 | 是否公开，默认false |
| tags | string[] | 否 | 标签列表，最多10个标签 |

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/template/create \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "员工考勤管理制度模板",
    "category": "人事管理",
    "description": "规范员工考勤管理的标准模板",
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
        "children": [
          {
            "id": "section_1_1",
            "level": 2,
            "title": "第一条 目的",
            "description": "明确制度制定的目的"
          }
        ]
      }
    ],
    "is_public": false,
    "tags": ["考勤", "人事"]
  }'
```

**响应结果**:
```json
{
  "success": true,
  "message": "模板创建成功",
  "template": {
    "id": "template_20260410_abc123",
    "name": "员工考勤管理制度模板",
    "category": "人事管理",
    "description": "规范员工考勤管理的标准模板",
    "format": {
      "fontSize": "14px",
      "fontFamily": "仿宋_GB2312",
      "lineHeight": "1.75",
      "margin": "2.54cm"
    },
    "sections": [...],
    "creator_id": 1,
    "creator_name": "张明",
    "created_at": "2026-04-10T10:30:00Z",
    "updated_at": "2026-04-10T10:30:00Z",
    "is_public": false,
    "usage_count": 0,
    "tags": ["考勤", "人事"]
  }
}
```

---

### 1.2 获取模板详情

**接口描述**: 根据模板ID获取模板的完整信息，包括基本信息、格式设置和章节结构。

**请求方式**: `GET`

**请求路径**: `/api/template/{template_id}`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| template_id | string | 是 | 模板唯一标识 |

**请求示例**:
```bash
curl -X GET http://localhost:8000/api/template/template_20260410_abc123 \
  -H "Authorization: Bearer <token>"
```

**响应结果**:
```json
{
  "success": true,
  "template": {
    "id": "template_20260410_abc123",
    "name": "员工考勤管理制度模板",
    "category": "人事管理",
    "description": "规范员工考勤管理的标准模板",
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
        "children": [
          {
            "id": "section_1_1",
            "level": 2,
            "title": "第一条 目的",
            "description": "明确制度制定的目的"
          }
        ]
      }
    ],
    "creator_id": 1,
    "creator_name": "张明",
    "created_at": "2026-04-10T10:30:00Z",
    "updated_at": "2026-04-10T10:30:00Z",
    "is_public": false,
    "usage_count": 5,
    "tags": ["考勤", "人事"]
  }
}
```

---

### 1.3 更新模板

**接口描述**: 更新已存在的模板信息，包括基本信息、格式设置和章节结构。

**请求方式**: `PUT`

**请求路径**: `/api/template/{template_id}`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| template_id | string | 是 | 模板唯一标识 |

**请求体参数**: 同创建接口，所有字段均为可选，只更新提供的字段

**请求示例**:
```bash
curl -X PUT http://localhost:8000/api/template/template_20260410_abc123 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "员工考勤管理制度模板（修订版）",
    "description": "更新后的模板描述",
    "sections": [
      {
        "id": "section_1",
        "level": 1,
        "title": "第一章 总则",
        "description": "更新后的章节描述",
        "children": []
      }
    ]
  }'
```

**响应结果**:
```json
{
  "success": true,
  "message": "模板更新成功",
  "template": {
    "id": "template_20260410_abc123",
    "name": "员工考勤管理制度模板（修订版）",
    "updated_at": "2026-04-10T15:30:00Z",
    ...
  }
}
```

---

### 1.4 删除模板

**接口描述**: 删除指定的模板（软删除或硬删除，根据业务需求决定）。

**请求方式**: `DELETE`

**请求路径**: `/api/template/{template_id}`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| template_id | string | 是 | 模板唯一标识 |

**请求示例**:
```bash
curl -X DELETE http://localhost:8000/api/template/template_20260410_abc123 \
  -H "Authorization: Bearer <token>"
```

**响应结果**:
```json
{
  "success": true,
  "message": "模板删除成功",
  "deleted_template_id": "template_20260410_abc123"
}
```

---

### 1.5 获取模板列表

**接口描述**: 分页获取模板列表，支持按分类筛选、关键词搜索和排序。

**请求方式**: `GET`

**请求路径**: `/api/template/list`

**Query参数**:
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| keyword | string | 否 | "" | 搜索关键词（匹配名称、描述） |
| category | string | 否 | 全部 | 分类筛选 |
| creator_id | number | 否 | - | 创建者ID筛选 |
| is_public | boolean | 否 | - | 是否公开筛选 |
| tags | string | 否 | - | 标签筛选（多个标签用逗号分隔） |
| sort_by | string | 否 | updated_at | 排序字段：`created_at`/`updated_at`/`usage_count`/`name` |
| sort_order | string | 否 | desc | 排序方向：`asc`/`desc` |
| skip | number | 否 | 0 | 分页偏移量 |
| limit | number | 否 | 20 | 每页数量（最大100） |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/template/list?keyword=考勤&category=人事管理&sort_by=updated_at&sort_order=desc&limit=10" \
  -H "Authorization: Bearer <token>"
```

**响应结果**:
```json
{
  "success": true,
  "total": 15,
  "items": [
    {
      "id": "template_20260410_abc123",
      "name": "员工考勤管理制度模板",
      "category": "人事管理",
      "description": "规范员工考勤管理的标准模板",
      "creator_id": 1,
      "creator_name": "张明",
      "created_at": "2026-04-10T10:30:00Z",
      "updated_at": "2026-04-10T15:30:00Z",
      "is_public": false,
      "usage_count": 5,
      "tags": ["考勤", "人事"]
    },
    {
      "id": "template_20260409_def456",
      "name": "考勤打卡流程模板",
      "category": "人事管理",
      "description": "规范员工打卡流程",
      "creator_id": 2,
      "creator_name": "李华",
      "created_at": "2026-04-09T08:00:00Z",
      "updated_at": "2026-04-09T08:00:00Z",
      "is_public": true,
      "usage_count": 12,
      "tags": ["打卡", "流程"]
    }
  ],
  "page": 1,
  "page_size": 10,
  "total_pages": 2
}
```

---

## 2. 模板搜索与筛选

### 2.1 获取模板分类列表

**接口描述**: 获取所有可用的模板分类。

**请求方式**: `GET`

**请求路径**: `/api/template/categories`

**请求示例**:
```bash
curl -X GET http://localhost:8000/api/template/categories \
  -H "Authorization: Bearer <token>"
```

**响应结果**:
```json
{
  "success": true,
  "categories": [
    {
      "name": "人事管理",
      "count": 25,
      "description": "包含招聘、考勤、薪酬等人事相关制度模板"
    },
    {
      "name": "财务管理",
      "count": 18,
      "description": "包含预算、报销、采购等财务相关制度模板"
    },
    {
      "name": "行政管理",
      "count": 32,
      "description": "包含办公、会议、档案等行政相关制度模板"
    },
    {
      "name": "业务流程",
      "count": 15,
      "description": "包含审批、执行、监督等业务流程模板"
    },
    {
      "name": "安全管理",
      "count": 12,
      "description": "包含信息安全、生产安全等安全管理模板"
    },
    {
      "name": "自定义",
      "count": 8,
      "description": "用户自定义模板"
    }
  ]
}
```

---

### 2.2 获取热门标签

**接口描述**: 获取使用频率最高的标签列表。

**请求方式**: `GET`

**请求路径**: `/api/template/popular-tags`

**Query参数**:
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| limit | number | 否 | 20 | 返回标签数量 |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/template/popular-tags?limit=10" \
  -H "Authorization: Bearer <token>"
```

**响应结果**:
```json
{
  "success": true,
  "tags": [
    { "name": "考勤", "count": 45 },
    { "name": "人事", "count": 38 },
    { "name": "财务", "count": 32 },
    { "name": "报销", "count": 28 },
    { "name": "审批", "count": 25 },
    { "name": "安全", "count": 22 },
    { "name": "流程", "count": 20 },
    { "name": "管理", "count": 18 },
    { "name": "制度", "count": 15 },
    { "name": "规范", "count": 12 }
  ]
}
```

---

## 3. 模板导出接口

### 3.1 导出模板为Markdown文件

**接口描述**: 将模板导出为Markdown格式的文件，包含完整的章节结构和格式说明。

**请求方式**: `POST`

**请求路径**: `/api/template/{template_id}/export-markdown`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| template_id | string | 是 | 模板唯一标识 |

**请求体参数**:
```json
{
  "include_metadata": true,
  "include_format_section": true,
  "include_creator_info": true
}
```

**字段说明**:
| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| include_metadata | boolean | 否 | true | 是否包含元数据（创建者、时间等） |
| include_format_section | boolean | 否 | true | 是否包含格式设置说明 |
| include_creator_info | boolean | 否 | true | 是否包含创建者信息 |

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/template/template_20260410_abc123/export-markdown \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "include_metadata": true,
    "include_format_section": true,
    "include_creator_info": true
  }'
```

**响应结果**:
```json
{
  "success": true,
  "download_url": "/api/files/download/template_20260410_abc123.md",
  "file_name": "员工考勤管理制度模板.md",
  "file_size": 3580,
  "expires_at": "2026-04-11T10:30:00Z"
}
```

**导出的Markdown文件示例**:
```markdown
# 员工考勤管理制度模板

## 模板信息

- **模板ID**: template_20260410_abc123
- **分类**: 人事管理
- **创建者**: 张明
- **创建时间**: 2026-04-10 10:30:00
- **最后更新**: 2026-04-10 15:30:00
- **使用次数**: 5次
- **标签**: 考勤, 人事

## 格式设置

- **字号**: 14px (小四)
- **字体**: 仿宋_GB2312
- **行距**: 1.75倍
- **页边距**: 2.54cm (标准)

---

## 第一章 总则

> 本章规定制度的目的和适用范围

### 第一条 目的

明确制度制定的目的和意义。

### 第二条 适用范围

规定制度适用的部门和人员范围。

---

## 第二章 工作时间

> 本章规定标准工作时间和弹性工作制

### 第四条 标准工作时间

规定公司的标准工作时间安排。

### 第五条 弹性工作制

说明弹性工作制的申请条件和执行方式。

---

## 模板使用说明

1. 本模板为制度编制提供标准结构参考
2. 请根据实际情况调整章节内容和描述
3. 建议在使用前咨询相关部门意见
4. 模板内容仅供参考，具体条款需符合法律法规要求
```

---

### 3.2 导出模板为JSON文件

**接口描述**: 将模板导出为JSON格式的文件，保留完整的数据结构。

**请求方式**: `POST`

**请求路径**: `/api/template/{template_id}/export-json`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| template_id | string | 是 | 模板唯一标识 |

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/template/template_20260410_abc123/export-json \
  -H "Authorization: Bearer <token>"
```

**响应结果**:
```json
{
  "success": true,
  "download_url": "/api/files/download/template_20260410_abc123.json",
  "file_name": "员工考勤管理制度模板.json",
  "file_size": 2450,
  "expires_at": "2026-04-11T10:30:00Z"
}
```

---

### 3.3 导入模板（从JSON文件）

**接口描述**: 从JSON文件导入模板数据，创建新模板。

**请求方式**: `POST`

**请求路径**: `/api/template/import-json`

**Content-Type**: `multipart/form-data`

**请求参数** (FormData):
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | File | 是 | JSON格式的模板文件 |
| overwrite | boolean | 否 | false | 如果模板ID已存在，是否覆盖 |

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/template/import-json \
  -H "Authorization: Bearer <token>" \
  -F "file=@template.json" \
  -F "overwrite=false"
```

**响应结果**:
```json
{
  "success": true,
  "message": "模板导入成功",
  "template": {
    "id": "template_20260410_xyz789",
    "name": "导入的模板名称",
    ...
  }
}
```

---

## 附录A: 错误码说明

| HTTP状态码 | 错误码 | 说明 | 解决方案 |
|------------|--------|------|----------|
| 400 | `INVALID_REQUEST` | 请求参数错误 | 检查必填参数和参数格式 |
| 401 | `UNAUTHORIZED` | 未登录或Token过期 | 重新登录获取新Token |
| 403 | `FORBIDDEN` | 无权限操作此模板 | 只有创建者和管理员可以修改/删除模板 |
| 404 | `TEMPLATE_NOT_FOUND` | 模板不存在 | 检查模板ID是否正确 |
| 409 | `DUPLICATE_NAME` | 模板名称已存在 | 修改模板名称后重试 |
| 413 | `FILE_TOO_LARGE` | 导入文件超出大小限制 | 文件大小限制为5MB |
| 422 | `INVALID_FILE_FORMAT` | 文件格式不支持 | 仅支持JSON格式的模板文件 |
| 500 | `INTERNAL_ERROR` | 服务器内部错误 | 联系技术支持 |

---

## 附录B: 模板分类枚举值

| 分类名称 | 说明 |
|---------|------|
| `人事管理` | 招聘、考勤、薪酬、培训等人事相关制度 |
| `财务管理` | 预算、报销、采购、资产管理等财务相关制度 |
| `行政管理` | 办公、会议、档案、印章等行政相关制度 |
| `业务流程` | 审批、执行、监督、评估等业务流程规范 |
| `安全管理` | 信息安全、生产安全、消防安全等安全管理制度 |
| `自定义` | 用户自定义的其他类型制度模板 |

---

## 附录C: 数据库存储建议

### 模板主表 (templates)

```sql
CREATE TABLE templates (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  category VARCHAR(50) NOT NULL,
  description TEXT,
  
  -- 格式设置（JSON格式存储）
  format JSON NOT NULL,
  
  -- 元数据
  creator_id INT NOT NULL,
  creator_name VARCHAR(100) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_public BOOLEAN DEFAULT FALSE,
  usage_count INT DEFAULT 0,
  tags JSON,
  
  -- 软删除标记
  is_deleted BOOLEAN DEFAULT FALSE,
  deleted_at TIMESTAMP NULL,
  
  INDEX idx_category (category),
  INDEX idx_creator_id (creator_id),
  INDEX idx_created_at (created_at),
  INDEX idx_updated_at (updated_at),
  INDEX idx_is_public (is_public),
  FULLTEXT idx_name_desc (name, description)
);
```

### 章节表 (template_sections)

```sql
CREATE TABLE template_sections (
  id VARCHAR(50) PRIMARY KEY,
  template_id VARCHAR(50) NOT NULL,
  parent_id VARCHAR(50) NULL,
  level INT NOT NULL,
  title VARCHAR(200) NOT NULL,
  description TEXT,
  sort_order INT NOT NULL,
  
  FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE,
  FOREIGN KEY (parent_id) REFERENCES template_sections(id) ON DELETE CASCADE,
  
  INDEX idx_template_id (template_id),
  INDEX idx_parent_id (parent_id),
  INDEX idx_level (level)
);
```

### 文件存储建议

Markdown文件存储路径：
```
/uploads/templates/
  ├── template_20260410_abc123.md
  ├── template_20260410_abc123.json
  └── ...
```

---

## 附录D: 前端集成示例

### 创建模板

```typescript
// 在 api.ts 中添加
async createTemplate(templateData: any): Promise<{ success: boolean; template: Template }> {
  const response = await fetch(`${API_BASE_URL}/api/template/create`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(templateData),
  });
  return response.json();
}

// 在 TemplateManagement.tsx 中调用
const handleSave = async () => {
  if (!selectedTemplate) return;

  try {
    const result = await api.createTemplate(editForm);
    if (result.success) {
      alert('模板保存成功！');
      // 更新本地状态
      setTemplates([...templates, result.template]);
      setIsEditing(false);
    }
  } catch (error) {
    console.error('保存失败:', error);
    alert('保存失败，请重试');
  }
};
```

### 导出Markdown

```typescript
// 在 api.ts 中添加
async exportTemplateMarkdown(templateId: string, options?: any): Promise<{ success: boolean; download_url: string }> {
  const response = await fetch(`${API_BASE_URL}/api/template/${templateId}/export-markdown`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(options || {}),
  });
  return response.json();
}

// 在 TemplateManagement.tsx 中调用
const handleExportMarkdown = async () => {
  if (!selectedTemplate) return;
  
  try {
    const result = await api.exportTemplateMarkdown(selectedTemplate.id, {
      include_metadata: true,
      include_format_section: true,
      include_creator_info: true
    });
    
    if (result.download_url) {
      window.open(`${API_BASE_URL}${result.download_url}`, '_blank');
    }
  } catch (error) {
    console.error('导出失败:', error);
    alert('导出失败，请重试');
  }
};
```

---

**文档版本**: v1.0  
**最后更新**: 2026-04-10  
**维护者**: 后端开发团队
