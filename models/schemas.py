"""
API请求和响应模型
定义所有API接口的请求参数和响应格式
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class KnowledgeBaseCreateRequest(BaseModel):
    """
    创建知识库请求模型
    
    Attributes:
        name: 知识库名称
        description: 知识库描述
    """
    name: str = Field(..., description="知识库名称", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="知识库描述")


class KnowledgeBaseResponse(BaseModel):
    """
    知识库响应模型
    
    Attributes:
        id: 知识库ID（外部API的UUID）
        name: 知识库名称
        description: 知识库描述
        file_name: 文件名
        file_size: 文件大小
        status: 状态
        created_at: 创建时间
        updated_at: 更新时间
    """
    id: str
    name: str
    description: Optional[str]
    file_name: str
    file_size: Optional[int]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class KnowledgeBaseListResponse(BaseModel):
    """
    知识库列表响应模型
    
    Attributes:
        total: 总数
        items: 知识库列表
    """
    total: int
    items: List[KnowledgeBaseResponse]


class ConversationCreateRequest(BaseModel):
    """
    创建对话请求模型
    
    Attributes:
        title: 对话标题
        description: 对话描述
    """
    title: Optional[str] = Field("新对话", description="对话标题", max_length=255)
    description: Optional[str] = Field(None, description="对话描述")


class ConversationResponse(BaseModel):
    """
    对话响应模型
    
    Attributes:
        id: 对话ID
        title: 对话标题
        description: 对话描述
        status: 状态
        created_at: 创建时间
        updated_at: 更新时间
    """
    id: int
    title: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """
    对话列表响应模型
    
    Attributes:
        total: 总数
        items: 对话列表
    """
    total: int
    items: List[ConversationResponse]


class MessageResponse(BaseModel):
    """
    消息响应模型
    
    Attributes:
        id: 消息ID
        conversation_id: 对话ID
        role: 角色
        content: 内容
        file_paths: 文件路径
        knowledge_base_id: 知识库ID
        created_at: 创建时间
    """
    id: int
    conversation_id: int
    role: str
    content: str
    file_paths: Optional[str]
    knowledge_base_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """
    消息列表响应模型
    
    Attributes:
        total: 总数
        items: 消息列表
    """
    total: int
    items: List[MessageResponse]


class ChatRequest(BaseModel):
    """
    聊天请求模型
    
    Attributes:
        conversation_id: 对话ID
        message: 用户消息
        knowledge_base_id: 知识库ID（可选）
        file_paths: 上传文件路径列表（可选）
    """
    conversation_id: int = Field(..., description="对话ID")
    message: str = Field(..., description="用户消息", min_length=1)
    knowledge_base_id: Optional[int] = Field(None, description="知识库ID")
    file_paths: Optional[List[str]] = Field(None, description="上传文件路径列表")


class ChatStreamResponse(BaseModel):
    """
    聊天流式响应模型
    
    Attributes:
        content: 响应内容片段
        is_end: 是否结束
    """
    content: str
    is_end: bool = False


class ApiResponse(BaseModel):
    """
    通用API响应模型
    
    Attributes:
        code: 状态码
        message: 响应消息
        data: 响应数据
    """
    code: int = 200
    message: str = "success"
    data: Optional[dict] = None


class FileUploadResponse(BaseModel):
    """
    文件上传响应模型
    
    Attributes:
        file_path: 文件存储路径
        file_name: 原始文件名
        file_size: 文件大小
    """
    file_path: str
    file_name: str
    file_size: int


class RuleCreateRequest(BaseModel):
    """
    创建规则请求模型
    
    Attributes:
        title: 规则标题
        content: 规则内容
        rule_type: 规则类型
        conversation_id: 对话ID
        category: 规则分类
        priority: 优先级
    """
    title: str = Field(..., description="规则标题", min_length=1, max_length=255)
    content: str = Field(..., description="规则内容", min_length=1)
    rule_type: str = Field(default="global", description="规则类型：global-全局规则，conversation-对话规则")
    conversation_id: Optional[int] = Field(None, description="对话ID（仅对话规则有效）")
    category: Optional[str] = Field(None, description="规则分类", max_length=100)
    priority: int = Field(default=0, description="优先级（数字越大优先级越高）")


class RuleUpdateRequest(BaseModel):
    """
    更新规则请求模型
    
    Attributes:
        title: 规则标题
        content: 规则内容
        rule_type: 规则类型
        conversation_id: 对话ID
        category: 规则分类
        priority: 优先级
        is_active: 是否启用
    """
    title: Optional[str] = Field(None, description="规则标题", min_length=1, max_length=255)
    content: Optional[str] = Field(None, description="规则内容", min_length=1)
    rule_type: Optional[str] = Field(None, description="规则类型：global-全局规则，conversation-对话规则")
    conversation_id: Optional[int] = Field(None, description="对话ID（仅对话规则有效）")
    category: Optional[str] = Field(None, description="规则分类", max_length=100)
    priority: Optional[int] = Field(None, description="优先级（数字越大优先级越高）")
    is_active: Optional[bool] = Field(None, description="是否启用")


class RuleResponse(BaseModel):
    """
    规则响应模型
    
    Attributes:
        id: 规则ID
        title: 规则标题
        content: 规则内容
        rule_type: 规则类型
        conversation_id: 对话ID
        category: 规则分类
        priority: 优先级
        is_active: 是否启用
        created_at: 创建时间
        updated_at: 更新时间
    """
    id: int
    title: str
    content: str
    rule_type: str
    conversation_id: Optional[int]
    category: Optional[str]
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RuleListResponse(BaseModel):
    """
    规则列表响应模型
    
    Attributes:
        total: 总数
        items: 规则列表
    """
    total: int
    items: List[RuleResponse]


class BatchAddRulesRequest(BaseModel):
    """
    批量添加规则请求模型
    
    Attributes:
        rules: 规则列表
        conversation_id: 对话ID
    """
    rules: List[RuleCreateRequest] = Field(..., description="规则列表")
    conversation_id: Optional[int] = Field(None, description="对话ID（用于对话规则）")


class UserResponse(BaseModel):
    """
    用户响应模型
    
    Attributes:
        id: 用户ID
        username: 用户名
        account: 登录账号
        phone: 手机号
        department: 部门
        role: 角色
        is_active: 是否激活
        last_login: 最后登录时间
        created_at: 创建时间
    """
    id: int
    username: str
    account: str
    phone: Optional[str]
    department: Optional[str]
    role: str
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """
    用户列表响应模型
    
    Attributes:
        total: 总数
        items: 用户列表
    """
    total: int
    items: List[UserResponse]


class LoginRequest(BaseModel):
    """
    登录请求模型
    
    Attributes:
        account: 登录账号
        password: 密码
    """
    account: str = Field(..., description="登录账号")
    password: str = Field(..., description="密码")


class RegisterRequest(BaseModel):
    """
    注册请求模型
    
    Attributes:
        username: 用户名
        account: 登录账号
        password: 密码
        phone: 手机号
        department: 部门
    """
    username: str = Field(..., description="用户名", min_length=2, max_length=50)
    account: str = Field(..., description="登录账号", min_length=3, max_length=50)
    password: str = Field(..., description="密码", min_length=6, max_length=50)
    phone: Optional[str] = Field(None, description="手机号", max_length=20)
    department: Optional[str] = Field(None, description="部门", max_length=100)


class LoginResponse(BaseModel):
    """
    登录响应模型
    
    Attributes:
        access_token: 访问令牌
        token_type: 令牌类型
        user: 用户信息
    """
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UpdateUserRequest(BaseModel):
    """
    更新用户请求模型
    
    Attributes:
        username: 用户名
        phone: 手机号
        department: 部门
    """
    username: Optional[str] = Field(None, description="用户名", min_length=2, max_length=50)
    phone: Optional[str] = Field(None, description="手机号", max_length=20)
    department: Optional[str] = Field(None, description="部门", max_length=100)


class ChangePasswordRequest(BaseModel):
    """
    修改密码请求模型
    
    Attributes:
        old_password: 旧密码
        new_password: 新密码
    """
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., description="新密码", min_length=6, max_length=50)


class TemplateSectionModel(BaseModel):
    """
    模板章节模型
    
    Attributes:
        id: 章节唯一标识
        level: 层级（1=一级标题/章，2=二级标题/条）
        title: 章节标题
        description: 章节描述
        children: 子章节列表
    """
    id: Optional[str] = Field(None, description="章节唯一标识")
    level: int = Field(..., description="层级：1=章，2=条")
    title: str = Field(..., description="章节标题", max_length=200)
    description: Optional[str] = Field(None, description="章节描述")
    children: Optional[List["TemplateSectionModel"]] = Field(None, description="子章节列表")


class TemplateFormatModel(BaseModel):
    """
    模板格式设置模型
    
    Attributes:
        fontSize: 字号
        fontFamily: 字体
        lineHeight: 行距
        margin: 页边距
    """
    fontSize: str = Field(..., description="字号：12px/14px/16px/18px")
    fontFamily: str = Field(..., description="字体：仿宋_GB2312/宋体/黑体/楷体")
    lineHeight: str = Field(..., description="行距：1.5/1.75/2")
    margin: str = Field(..., description="页边距：2.54cm/2cm/3cm")


class TemplateCreateRequest(BaseModel):
    """
    创建模板请求模型
    
    Attributes:
        name: 模板名称
        category: 模板分类
        description: 模板描述
        format: 格式设置
        sections: 章节结构列表
        is_public: 是否公开
        tags: 标签列表
    """
    name: str = Field(..., description="模板名称", min_length=1, max_length=100)
    category: str = Field(..., description="模板分类")
    description: Optional[str] = Field(None, description="模板描述", max_length=500)
    format: TemplateFormatModel = Field(..., description="格式设置")
    sections: List[TemplateSectionModel] = Field(..., description="章节结构列表", min_length=1)
    is_public: bool = Field(default=False, description="是否公开")
    tags: Optional[List[str]] = Field(None, description="标签列表", max_length=10)


class TemplateUpdateRequest(BaseModel):
    """
    更新模板请求模型
    
    Attributes:
        name: 模板名称
        category: 模板分类
        description: 模板描述
        format: 格式设置
        sections: 章节结构列表
        is_public: 是否公开
        tags: 标签列表
    """
    name: Optional[str] = Field(None, description="模板名称", min_length=1, max_length=100)
    category: Optional[str] = Field(None, description="模板分类")
    description: Optional[str] = Field(None, description="模板描述", max_length=500)
    format: Optional[TemplateFormatModel] = Field(None, description="格式设置")
    sections: Optional[List[TemplateSectionModel]] = Field(None, description="章节结构列表", min_length=1)
    is_public: Optional[bool] = Field(None, description="是否公开")
    tags: Optional[List[str]] = Field(None, description="标签列表", max_length=10)


class TemplateResponse(BaseModel):
    """
    模板响应模型
    
    Attributes:
        id: 模板唯一标识
        name: 模板名称
        category: 模板分类
        description: 模板描述
        format: 格式设置
        sections: 章节结构列表
        creator_id: 创建者用户ID
        creator_name: 创建者姓名
        created_at: 创建时间
        updated_at: 更新时间
        is_public: 是否公开模板
        usage_count: 使用次数
        tags: 标签列表
    """
    id: str
    name: str
    category: str
    description: Optional[str]
    format: dict
    sections: List[dict]
    creator_id: int
    creator_name: str
    created_at: datetime
    updated_at: datetime
    is_public: bool
    usage_count: int
    tags: List[str]
    
    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    """
    模板列表响应模型
    
    Attributes:
        total: 总数
        items: 模板列表
        page: 当前页码
        page_size: 每页数量
        total_pages: 总页数
    """
    total: int
    items: List[TemplateResponse]
    page: int
    page_size: int
    total_pages: int


class TemplateCategoryResponse(BaseModel):
    """
    模板分类响应模型
    
    Attributes:
        name: 分类名称
        count: 模板数量
        description: 分类描述
    """
    name: str
    count: int
    description: str


class TemplateCategoryListResponse(BaseModel):
    """
    模板分类列表响应模型
    
    Attributes:
        success: 是否成功
        categories: 分类列表
    """
    success: bool
    categories: List[TemplateCategoryResponse]


class TemplateTagResponse(BaseModel):
    """
    模板标签响应模型
    
    Attributes:
        name: 标签名称
        count: 使用次数
    """
    name: str
    count: int


class TemplateTagListResponse(BaseModel):
    """
    模板标签列表响应模型
    
    Attributes:
        success: 是否成功
        tags: 标签列表
    """
    success: bool
    tags: List[TemplateTagResponse]


class TemplateExportMarkdownRequest(BaseModel):
    """
    导出模板为Markdown请求模型
    
    Attributes:
        include_metadata: 是否包含元数据
        include_format_section: 是否包含格式设置说明
        include_creator_info: 是否包含创建者信息
    """
    include_metadata: bool = Field(default=True, description="是否包含元数据")
    include_format_section: bool = Field(default=True, description="是否包含格式设置说明")
    include_creator_info: bool = Field(default=True, description="是否包含创建者信息")


class TemplateExportResponse(BaseModel):
    """
    模板导出响应模型
    
    Attributes:
        success: 是否成功
        download_url: 下载链接
        file_name: 文件名
        file_size: 文件大小
        expires_at: 过期时间
    """
    success: bool
    download_url: str
    file_name: str
    file_size: int
    expires_at: datetime


TemplateSectionModel.model_rebuild()
