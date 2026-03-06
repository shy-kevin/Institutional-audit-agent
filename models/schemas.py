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
        id: 知识库ID
        name: 知识库名称
        description: 知识库描述
        file_name: 文件名
        file_size: 文件大小
        status: 状态
        created_at: 创建时间
        updated_at: 更新时间
    """
    id: int
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
