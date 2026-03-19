"""
规则管理API路由
提供规则的增删改查等接口
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models.schemas import (
    RuleCreateRequest,
    RuleUpdateRequest,
    RuleResponse,
    RuleListResponse,
    ApiResponse,
    BatchAddRulesRequest
)
from services.rule_service import RuleService
from utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


@router.post("/create", response_model=RuleResponse, summary="创建规则")
def create_rule(
    request: RuleCreateRequest,
    db: Session = Depends(get_db)
):
    """
    创建新规则
    
    Args:
        request: 创建请求
        db: 数据库会话
    
    Returns:
        RuleResponse: 创建的规则信息
    """
    logger.info(f"创建规则请求 - 标题: {request.title}, 类型: {request.rule_type}")
    
    service = RuleService(db)
    rule = service.create_rule(
        title=request.title,
        content=request.content,
        rule_type=request.rule_type,
        conversation_id=request.conversation_id,
        category=request.category,
        priority=request.priority
    )
    
    logger.info(f"规则创建成功 - ID: {rule.id}")
    return RuleResponse(
        id=rule.id,
        title=rule.title,
        content=rule.content,
        rule_type=rule.rule_type.value,
        conversation_id=rule.conversation_id,
        category=rule.category,
        priority=rule.priority,
        is_active=bool(rule.is_active),
        created_at=rule.created_at,
        updated_at=rule.updated_at
    )


@router.post("/batch", response_model=ApiResponse, summary="批量创建规则")
def batch_create_rules(
    request: BatchAddRulesRequest,
    db: Session = Depends(get_db)
):
    """
    批量创建规则
    
    Args:
        request: 批量创建请求
        db: 数据库会话
    
    Returns:
        ApiResponse: 操作结果
    """
    logger.info(f"批量创建规则请求 - 数量: {len(request.rules)}")
    
    service = RuleService(db)
    
    rules_data = [rule.model_dump() for rule in request.rules]
    created_rules = service.batch_create_rules(rules_data, request.conversation_id)
    
    logger.info(f"批量规则创建成功 - 数量: {len(created_rules)}")
    
    return ApiResponse(
        code=200,
        message=f"成功创建 {len(created_rules)} 条规则",
        data={
            "count": len(created_rules),
            "rule_ids": [rule.id for rule in created_rules]
        }
    )


@router.get("/list", response_model=RuleListResponse, summary="获取规则列表")
def get_rule_list(
    skip: int = 0,
    limit: int = 100,
    rule_type: Optional[str] = None,
    conversation_id: Optional[int] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    获取规则列表
    
    支持按类型、对话ID、分类、状态筛选
    
    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        rule_type: 按规则类型筛选
        conversation_id: 按对话ID筛选
        category: 按分类筛选
        is_active: 按启用状态筛选
        db: 数据库会话
    
    Returns:
        RuleListResponse: 规则列表响应
    """
    logger.info(f"获取规则列表请求 - skip: {skip}, limit: {limit}, type: {rule_type}")
    
    service = RuleService(db)
    rules, total = service.get_all_rules(
        skip=skip,
        limit=limit,
        rule_type=rule_type,
        conversation_id=conversation_id,
        category=category,
        is_active=is_active
    )
    
    logger.info(f"规则列表查询成功 - 总数: {total}, 返回: {len(rules)}")
    
    return RuleListResponse(
        total=total,
        items=[
            RuleResponse(
                id=rule.id,
                title=rule.title,
                content=rule.content,
                rule_type=rule.rule_type.value,
                conversation_id=rule.conversation_id,
                category=rule.category,
                priority=rule.priority,
                is_active=bool(rule.is_active),
                created_at=rule.created_at,
                updated_at=rule.updated_at
            )
            for rule in rules
        ]
    )


@router.get("/{rule_id}", response_model=RuleResponse, summary="获取规则详情")
def get_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """
    获取规则详情
    
    Args:
        rule_id: 规则ID
        db: 数据库会话
    
    Returns:
        RuleResponse: 规则详情
    
    Raises:
        HTTPException: 规则不存在时抛出404错误
    """
    logger.info(f"获取规则详情请求 - ID: {rule_id}")
    
    service = RuleService(db)
    rule = service.get_rule_by_id(rule_id)
    
    if not rule:
        logger.error(f"规则不存在 - ID: {rule_id}")
        raise HTTPException(status_code=404, detail="规则不存在")
    
    logger.debug(f"规则详情查询成功 - ID: {rule_id}")
    
    return RuleResponse(
        id=rule.id,
        title=rule.title,
        content=rule.content,
        rule_type=rule.rule_type.value,
        conversation_id=rule.conversation_id,
        category=rule.category,
        priority=rule.priority,
        is_active=bool(rule.is_active),
        created_at=rule.created_at,
        updated_at=rule.updated_at
    )


@router.put("/{rule_id}", response_model=RuleResponse, summary="更新规则")
def update_rule(
    rule_id: int,
    request: RuleUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    更新规则信息
    
    Args:
        rule_id: 规则ID
        request: 更新请求
        db: 数据库会话
    
    Returns:
        RuleResponse: 更新后的规则信息
    
    Raises:
        HTTPException: 规则不存在时抛出404错误
    """
    logger.info(f"更新规则请求 - ID: {rule_id}")
    
    service = RuleService(db)
    rule = service.update_rule(
        rule_id=rule_id,
        title=request.title,
        content=request.content,
        rule_type=request.rule_type,
        conversation_id=request.conversation_id,
        category=request.category,
        priority=request.priority,
        is_active=request.is_active
    )
    
    if not rule:
        logger.error(f"规则不存在 - ID: {rule_id}")
        raise HTTPException(status_code=404, detail="规则不存在")
    
    logger.info(f"规则更新成功 - ID: {rule_id}")
    
    return RuleResponse(
        id=rule.id,
        title=rule.title,
        content=rule.content,
        rule_type=rule.rule_type.value,
        conversation_id=rule.conversation_id,
        category=rule.category,
        priority=rule.priority,
        is_active=bool(rule.is_active),
        created_at=rule.created_at,
        updated_at=rule.updated_at
    )


@router.delete("/{rule_id}", response_model=ApiResponse, summary="删除规则")
def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """
    删除规则
    
    Args:
        rule_id: 规则ID
        db: 数据库会话
    
    Returns:
        ApiResponse: 操作结果
    
    Raises:
        HTTPException: 规则不存在或删除失败时抛出错误
    """
    logger.info(f"删除规则请求 - ID: {rule_id}")
    
    service = RuleService(db)
    
    if not service.get_rule_by_id(rule_id):
        logger.error(f"规则不存在 - ID: {rule_id}")
        raise HTTPException(status_code=404, detail="规则不存在")
    
    if not service.delete_rule(rule_id):
        logger.error(f"规则删除失败 - ID: {rule_id}")
        raise HTTPException(status_code=500, detail="删除失败")
    
    logger.info(f"规则删除成功 - ID: {rule_id}")
    return ApiResponse(code=200, message="规则删除成功")


@router.post("/{rule_id}/toggle", response_model=RuleResponse, summary="切换规则启用状态")
def toggle_rule_status(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """
    切换规则启用状态
    
    Args:
        rule_id: 规则ID
        db: 数据库会话
    
    Returns:
        RuleResponse: 更新后的规则信息
    
    Raises:
        HTTPException: 规则不存在时抛出404错误
    """
    logger.info(f"切换规则状态请求 - ID: {rule_id}")
    
    service = RuleService(db)
    rule = service.toggle_rule_status(rule_id)
    
    if not rule:
        logger.error(f"规则不存在 - ID: {rule_id}")
        raise HTTPException(status_code=404, detail="规则不存在")
    
    logger.info(f"规则状态切换成功 - ID: {rule_id}")
    
    return RuleResponse(
        id=rule.id,
        title=rule.title,
        content=rule.content,
        rule_type=rule.rule_type.value,
        conversation_id=rule.conversation_id,
        category=rule.category,
        priority=rule.priority,
        is_active=bool(rule.is_active),
        created_at=rule.created_at,
        updated_at=rule.updated_at
    )


@router.get("/conversation/{conversation_id}/active", response_model=RuleListResponse, summary="获取对话的活跃规则")
def get_active_rules_for_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    获取对话的活跃规则（包括全局规则和对话规则）
    
    Args:
        conversation_id: 对话ID
        db: 数据库会话
    
    Returns:
        RuleListResponse: 规则列表响应
    """
    logger.info(f"获取对话活跃规则请求 - 对话ID: {conversation_id}")
    
    service = RuleService(db)
    rules = service.get_active_rules_for_conversation(conversation_id)
    
    logger.info(f"对话活跃规则查询成功 - 对话ID: {conversation_id}, 数量: {len(rules)}")
    
    return RuleListResponse(
        total=len(rules),
        items=[
            RuleResponse(
                id=rule.id,
                title=rule.title,
                content=rule.content,
                rule_type=rule.rule_type.value,
                conversation_id=rule.conversation_id,
                category=rule.category,
                priority=rule.priority,
                is_active=bool(rule.is_active),
                created_at=rule.created_at,
                updated_at=rule.updated_at
            )
            for rule in rules
        ]
    )
