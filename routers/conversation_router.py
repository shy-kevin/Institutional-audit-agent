"""
对话管理API路由
提供对话的创建、查询、删除等接口
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models.schemas import (
    ConversationCreateRequest,
    ConversationResponse,
    ConversationListResponse,
    MessageListResponse,
    ApiResponse
)
from services.conversation_service import ConversationService
from services.message_service import MessageService

router = APIRouter()


@router.post("/create", response_model=ConversationResponse, summary="创建新对话")
def create_conversation(
    request: ConversationCreateRequest,
    db: Session = Depends(get_db)
):
    """
    创建新对话
    
    创建一个新的对话会话
    
    Args:
        request: 创建请求
        db: 数据库会话
    
    Returns:
        ConversationResponse: 创建的对话信息
    """
    service = ConversationService(db)
    conversation = service.create_conversation(
        title=request.title,
        description=request.description
    )
    
    return ConversationResponse.model_validate(conversation)


@router.get("/list", response_model=ConversationListResponse, summary="获取对话列表")
def get_conversation_list(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取对话列表
    
    分页获取所有对话信息，可按状态筛选
    
    Args:
        skip: 跳过的记录数（分页偏移）
        limit: 返回的最大记录数
        status: 按状态筛选（active/archived/deleted）
        db: 数据库会话
    
    Returns:
        ConversationListResponse: 对话列表响应
    """
    service = ConversationService(db)
    conversations, total = service.get_all_conversations(skip, limit, status)
    
    return ConversationListResponse(
        total=total,
        items=[ConversationResponse.model_validate(conv) for conv in conversations]
    )


@router.get("/{conversation_id}", response_model=ConversationResponse, summary="获取对话详情")
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    获取对话详情
    
    根据ID获取指定对话的详细信息
    
    Args:
        conversation_id: 对话ID
        db: 数据库会话
    
    Returns:
        ConversationResponse: 对话详情
    
    Raises:
        HTTPException: 对话不存在时抛出404错误
    """
    service = ConversationService(db)
    conversation = service.get_conversation_by_id(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    return ConversationResponse.model_validate(conversation)


@router.put("/{conversation_id}", response_model=ConversationResponse, summary="更新对话信息")
def update_conversation(
    conversation_id: int,
    request: ConversationCreateRequest,
    db: Session = Depends(get_db)
):
    """
    更新对话信息
    
    更新指定对话的标题和描述
    
    Args:
        conversation_id: 对话ID
        request: 更新请求
        db: 数据库会话
    
    Returns:
        ConversationResponse: 更新后的对话信息
    
    Raises:
        HTTPException: 对话不存在时抛出404错误
    """
    service = ConversationService(db)
    conversation = service.update_conversation(
        conversation_id=conversation_id,
        title=request.title,
        description=request.description
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    return ConversationResponse.model_validate(conversation)


@router.delete("/{conversation_id}", response_model=ApiResponse, summary="删除对话")
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    删除对话
    
    删除指定对话及其所有消息记录
    
    Args:
        conversation_id: 对话ID
        db: 数据库会话
    
    Returns:
        ApiResponse: 操作结果
    
    Raises:
        HTTPException: 对话不存在或删除失败时抛出错误
    """
    service = ConversationService(db)
    
    if not service.get_conversation_by_id(conversation_id):
        raise HTTPException(status_code=404, detail="对话不存在")
    
    if not service.delete_conversation(conversation_id):
        raise HTTPException(status_code=500, detail="删除失败")
    
    return ApiResponse(code=200, message="对话删除成功")


@router.get("/{conversation_id}/messages", response_model=MessageListResponse, summary="获取对话消息列表")
def get_conversation_messages(
    conversation_id: int,
    limit: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    获取对话消息列表
    
    获取指定对话的所有消息记录
    
    Args:
        conversation_id: 对话ID
        limit: 返回的最大消息数量
        db: 数据库会话
    
    Returns:
        MessageListResponse: 消息列表响应
    
    Raises:
        HTTPException: 对话不存在时抛出404错误
    """
    conv_service = ConversationService(db)
    if not conv_service.get_conversation_by_id(conversation_id):
        raise HTTPException(status_code=404, detail="对话不存在")
    
    msg_service = MessageService(db)
    messages = msg_service.get_messages_by_conversation_id(conversation_id, limit)
    
    return MessageListResponse(
        total=len(messages),
        items=[{
            "id": msg.id,
            "conversation_id": msg.conversation_id,
            "role": msg.role,
            "content": msg.content,
            "file_paths": msg.file_paths,
            "knowledge_base_id": msg.knowledge_base_id,
            "created_at": msg.created_at
        } for msg in messages]
    )


@router.post("/{conversation_id}/archive", response_model=ConversationResponse, summary="归档对话")
def archive_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    归档对话
    
    将指定对话标记为归档状态
    
    Args:
        conversation_id: 对话ID
        db: 数据库会话
    
    Returns:
        ConversationResponse: 更新后的对话信息
    
    Raises:
        HTTPException: 对话不存在时抛出404错误
    """
    service = ConversationService(db)
    conversation = service.archive_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    return ConversationResponse.model_validate(conversation)
