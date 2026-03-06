# 制度审查智能体 API 接口文档

## 项目概述

制度审查智能体是一个基于 LangChain 和 LangGraph 构建的智能问答系统，支持 PDF 文件解析、知识库管理和智能问答功能。

**技术栈：**
- 后端框架：FastAPI
- 大模型：Ollama (DeepSeek) / 阿里云百炼
- 向量数据库：PostgreSQL (PGVector)
- 关系数据库：MySQL
- 智能体框架：LangChain + LangGraph

**基础URL：** `http://localhost:8000`

---

## 目录

1. [知识库管理接口](#知识库管理接口)
2. [对话管理接口](#对话管理接口)
3. [智能问答接口](#智能问答接口)
4. [系统接口](#系统接口)

---

## 知识库管理接口

### 1. 上传知识库文件

**接口说明：** 上传 PDF 格式的制度文件作为知识库，系统会自动解析文件内容并进行向量化存储。

**请求方式：** `POST`

**接口地址：** `/api/knowledge-base/upload`

**请求类型：** `multipart/form-data`

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | file | 是 | PDF 文件 |
| name | string | 是 | 知识库名称 |
| description | string | 否 | 知识库描述 |

**响应示例：**

```json
{
  "code": 200,
  "message": "知识库文件上传成功，正在后台处理中",
  "data": {
    "id": 1,
    "name": "公司管理制度",
    "description": "包含公司各项管理制度",
    "file_path": "uploads/knowledge_base/xxx.pdf",
    "file_name": "管理制度.pdf",
    "file_size": 1024000,
    "status": "processing",
    "created_at": "2024-01-01T10:00:00",
    "updated_at": "2024-01-01T10:00:00"
  }
}
```

---

### 2. 获取知识库列表

**接口说明：** 分页获取所有知识库信息，可按状态筛选。

**请求方式：** `GET`

**接口地址：** `/api/knowledge-base/list`

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| skip | int | 否 | 跳过的记录数（分页偏移），默认 0 |
| limit | int | 否 | 返回的最大记录数，默认 100 |
| status | string | 否 | 按状态筛选：processing/completed/failed |

**响应示例：**

```json
{
  "total": 10,
  "items": [
    {
      "id": 1,
      "name": "公司管理制度",
      "description": "包含公司各项管理制度",
      "file_name": "管理制度.pdf",
      "file_size": 1024000,
      "status": "completed",
      "created_at": "2024-01-01T10:00:00",
      "updated_at": "2024-01-01T10:00:00"
    }
  ]
}
```

---

### 3. 获取知识库详情

**接口说明：** 根据 ID 获取指定知识库的详细信息。

**请求方式：** `GET`

**接口地址：** `/api/knowledge-base/{knowledge_base_id}`

**路径参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| knowledge_base_id | int | 是 | 知识库 ID |

**响应示例：**

```json
{
  "id": 1,
  "name": "公司管理制度",
  "description": "包含公司各项管理制度",
  "file_name": "管理制度.pdf",
  "file_size": 1024000,
  "status": "completed",
  "created_at": "2024-01-01T10:00:00",
  "updated_at": "2024-01-01T10:00:00"
}
```

---

### 4. 更新知识库信息

**接口说明：** 更新指定知识库的名称和描述。

**请求方式：** `PUT`

**接口地址：** `/api/knowledge-base/{knowledge_base_id}`

**路径参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| knowledge_base_id | int | 是 | 知识库 ID |

**请求体：**

```json
{
  "name": "更新后的名称",
  "description": "更新后的描述"
}
```

**响应示例：**

```json
{
  "id": 1,
  "name": "更新后的名称",
  "description": "更新后的描述",
  "file_name": "管理制度.pdf",
  "file_size": 1024000,
  "status": "completed",
  "created_at": "2024-01-01T10:00:00",
  "updated_at": "2024-01-01T11:00:00"
}
```

---

### 5. 删除知识库

**接口说明：** 删除指定知识库，包括其向量存储数据。

**请求方式：** `DELETE`

**接口地址：** `/api/knowledge-base/{knowledge_base_id}`

**路径参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| knowledge_base_id | int | 是 | 知识库 ID |

**响应示例：**

```json
{
  "code": 200,
  "message": "知识库删除成功",
  "data": null
}
```

---

### 6. 仅上传文件

**接口说明：** 上传 PDF 文件但不创建知识库，用于临时文件上传。

**请求方式：** `POST`

**接口地址：** `/api/knowledge-base/upload-file`

**请求类型：** `multipart/form-data`

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | file | 是 | PDF 文件 |

**响应示例：**

```json
{
  "file_path": "uploads/temp/xxx.pdf",
  "file_name": "文件名.pdf",
  "file_size": 1024000
}
```

---

## 对话管理接口

### 1. 创建新对话

**接口说明：** 创建一个新的对话会话。

**请求方式：** `POST`

**接口地址：** `/api/conversation/create`

**请求体：**

```json
{
  "title": "新对话",
  "description": "对话描述（可选）"
}
```

**响应示例：**

```json
{
  "id": 1,
  "title": "新对话",
  "description": "对话描述",
  "status": "active",
  "created_at": "2024-01-01T10:00:00",
  "updated_at": "2024-01-01T10:00:00"
}
```

---

### 2. 获取对话列表

**接口说明：** 分页获取所有对话信息，可按状态筛选。

**请求方式：** `GET`

**接口地址：** `/api/conversation/list`

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| skip | int | 否 | 跳过的记录数（分页偏移），默认 0 |
| limit | int | 否 | 返回的最大记录数，默认 100 |
| status | string | 否 | 按状态筛选：active/archived/deleted |

**响应示例：**

```json
{
  "total": 5,
  "items": [
    {
      "id": 1,
      "title": "制度审查对话",
      "description": "关于公司制度的审查",
      "status": "active",
      "created_at": "2024-01-01T10:00:00",
      "updated_at": "2024-01-01T11:00:00"
    }
  ]
}
```

---

### 3. 获取对话详情

**接口说明：** 根据 ID 获取指定对话的详细信息。

**请求方式：** `GET`

**接口地址：** `/api/conversation/{conversation_id}`

**路径参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| conversation_id | int | 是 | 对话 ID |

**响应示例：**

```json
{
  "id": 1,
  "title": "制度审查对话",
  "description": "关于公司制度的审查",
  "status": "active",
  "created_at": "2024-01-01T10:00:00",
  "updated_at": "2024-01-01T11:00:00"
}
```

---

### 4. 更新对话信息

**接口说明：** 更新指定对话的标题和描述。

**请求方式：** `PUT`

**接口地址：** `/api/conversation/{conversation_id}`

**路径参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| conversation_id | int | 是 | 对话 ID |

**请求体：**

```json
{
  "title": "更新后的标题",
  "description": "更新后的描述"
}
```

**响应示例：**

```json
{
  "id": 1,
  "title": "更新后的标题",
  "description": "更新后的描述",
  "status": "active",
  "created_at": "2024-01-01T10:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

---

### 5. 删除对话

**接口说明：** 删除指定对话及其所有消息记录。

**请求方式：** `DELETE`

**接口地址：** `/api/conversation/{conversation_id}`

**路径参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| conversation_id | int | 是 | 对话 ID |

**响应示例：**

```json
{
  "code": 200,
  "message": "对话删除成功",
  "data": null
}
```

---

### 6. 获取对话消息列表

**接口说明：** 获取指定对话的所有消息记录。

**请求方式：** `GET`

**接口地址：** `/api/conversation/{conversation_id}/messages`

**路径参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| conversation_id | int | 是 | 对话 ID |

**查询参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| limit | int | 否 | 返回的最大消息数量 |

**响应示例：**

```json
{
  "total": 4,
  "items": [
    {
      "id": 1,
      "conversation_id": 1,
      "role": "user",
      "content": "请帮我审查这份制度文件",
      "file_paths": "[\"uploads/temp/xxx.pdf\"]",
      "knowledge_base_id": 1,
      "created_at": "2024-01-01T10:00:00"
    },
    {
      "id": 2,
      "conversation_id": 1,
      "role": "assistant",
      "content": "好的，我来帮您审查这份制度文件...",
      "file_paths": null,
      "knowledge_base_id": null,
      "created_at": "2024-01-01T10:01:00"
    }
  ]
}
```

---

### 7. 归档对话

**接口说明：** 将指定对话标记为归档状态。

**请求方式：** `POST`

**接口地址：** `/api/conversation/{conversation_id}/archive`

**路径参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| conversation_id | int | 是 | 对话 ID |

**响应示例：**

```json
{
  "id": 1,
  "title": "制度审查对话",
  "description": "关于公司制度的审查",
  "status": "archived",
  "created_at": "2024-01-01T10:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

---

## 智能问答接口

### 1. 流式问答接口

**接口说明：** 接收用户问题，基于知识库和对话历史进行智能问答，以流式方式返回结果。

**请求方式：** `POST`

**接口地址：** `/api/chat/stream`

**请求体：**

```json
{
  "conversation_id": 1,
  "message": "请帮我审查这份制度文件中关于请假制度的内容",
  "knowledge_base_id": 1,
  "file_paths": ["uploads/temp/xxx.pdf"]
}
```

**请求参数说明：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| conversation_id | int | 是 | 对话 ID |
| message | string | 是 | 用户问题 |
| knowledge_base_id | int | 否 | 知识库 ID |
| file_paths | array | 否 | 上传文件路径列表 |

**响应格式：** `text/event-stream`

**响应示例：**

```
data: {"content": "好的", "is_end": false}

data: {"content": "，我来", "is_end": false}

data: {"content": "帮您审查", "is_end": false}

data: {"content": "", "is_end": true}
```

---

### 2. 同步问答接口

**接口说明：** 接收用户问题，基于知识库和对话历史进行智能问答，同步返回完整结果。

**请求方式：** `POST`

**接口地址：** `/api/chat/sync`

**请求体：**

```json
{
  "conversation_id": 1,
  "message": "请帮我审查这份制度文件中关于请假制度的内容",
  "knowledge_base_id": 1,
  "file_paths": ["uploads/temp/xxx.pdf"]
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "response": "好的，我来帮您审查这份制度文件中关于请假制度的内容..."
  }
}
```

---

### 3. 快速问答接口

**接口说明：** 不保存历史记录的快速问答，适用于单次查询。

**请求方式：** `POST`

**接口地址：** `/api/chat/quick`

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| message | string | 是 | 用户问题 |
| knowledge_base_id | int | 否 | 知识库 ID |

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "response": "这是对您问题的回答..."
  }
}
```

---

## 系统接口

### 1. 根路径

**接口说明：** 返回应用基本信息。

**请求方式：** `GET`

**接口地址：** `/`

**响应示例：**

```json
{
  "name": "制度审查智能体",
  "version": "1.0.0",
  "status": "running"
}
```

---

### 2. 健康检查

**接口说明：** 用于检查服务是否正常运行。

**请求方式：** `GET`

**接口地址：** `/health`

**响应示例：**

```json
{
  "status": "healthy"
}
```

---

## 错误响应

当请求发生错误时，API 会返回相应的 HTTP 状态码和错误信息：

**响应格式：**

```json
{
  "detail": "错误描述信息"
}
```

**常见错误码：**

| 状态码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 使用流程示例

### 完整问答流程

1. **创建对话**
   ```
   POST /api/conversation/create
   {
     "title": "制度审查"
   }
   ```

2. **上传知识库（可选）**
   ```
   POST /api/knowledge-base/upload
   file: 制度文件.pdf
   name: 公司制度
   ```

3. **上传临时文件（可选）**
   ```
   POST /api/knowledge-base/upload-file
   file: 待审查文件.pdf
   ```

4. **发起问答**
   ```
   POST /api/chat/stream
   {
     "conversation_id": 1,
     "message": "请审查这份文件",
     "knowledge_base_id": 1,
     "file_paths": ["uploads/temp/xxx.pdf"]
   }
   ```

5. **查看历史消息**
   ```
   GET /api/conversation/1/messages
   ```

---

## 项目结构

```
Institutional-audit-agent/
├── agent/                    # 智能体模块
│   ├── __init__.py
│   └── audit_agent.py        # LangGraph 智能体实现
├── config/                   # 配置模块
│   ├── __init__.py
│   └── settings.py           # 系统配置
├── db/                       # 数据库模块
│   ├── __init__.py
│   ├── mysql_session.py      # MySQL 会话管理
│   └── postgres_session.py   # PostgreSQL 向量存储管理
├── models/                   # 实体类模块
│   ├── __init__.py
│   ├── conversation.py       # 对话实体
│   ├── knowledge_base.py     # 知识库实体
│   ├── message.py            # 消息实体
│   └── schemas.py            # API 请求响应模型
├── routers/                  # API 路由模块
│   ├── __init__.py
│   ├── chat_router.py        # 智能问答路由
│   ├── conversation_router.py # 对话管理路由
│   └── knowledge_base_router.py # 知识库管理路由
├── services/                 # 服务模块
│   ├── __init__.py
│   ├── conversation_service.py # 对话服务
│   ├── knowledge_base_service.py # 知识库服务
│   └── message_service.py    # 消息服务
├── utils/                    # 工具模块
│   ├── __init__.py
│   ├── file_utils.py         # 文件处理工具
│   └── pdf_parser.py         # PDF 解析工具
├── uploads/                  # 文件上传目录
├── .env                      # 环境变量配置
├── main.py                   # 应用入口
└── requirements.txt          # 依赖列表
```

---

## 启动方式

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 配置环境变量（修改 `.env` 文件）

3. 启动服务：
   ```bash
   python main.py
   ```

4. 访问 API 文档：
   ```
   http://localhost:8000/docs
   ```

---

## 注意事项

1. 确保 MySQL 和 PostgreSQL 数据库已启动并创建相应数据库
2. 确保 Ollama 服务已启动并下载了 deepseek 模型
3. 文件上传大小限制为 50MB
4. 仅支持 PDF 格式文件上传
5. 知识库文件处理为异步后台任务，上传后需等待状态变为 `completed`
