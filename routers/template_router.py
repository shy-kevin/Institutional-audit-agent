"""
模板管理API路由
提供模板的增删改查、导出导入等接口
"""

import os
import json
import math
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from db import get_db
from models.schemas import (
    TemplateCreateRequest,
    TemplateUpdateRequest,
    TemplateResponse,
    TemplateListResponse,
    TemplateCategoryListResponse,
    TemplateCategoryResponse,
    TemplateTagListResponse,
    TemplateTagResponse,
    TemplateExportMarkdownRequest,
    TemplateExportResponse,
    ApiResponse
)
from services.template_service import TemplateService
from routers.auth_router import get_current_user
from utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


@router.post("/create", summary="创建模板")
def create_template(
    request: TemplateCreateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    创建新模板
    
    Args:
        request: 创建请求
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        dict: 创建的模板信息
    """
    logger.info(f"创建模板请求 - 名称: {request.name}, 分类: {request.category}, 用户: {current_user.username}")
    
    service = TemplateService(db)
    
    sections_data = [section.model_dump() for section in request.sections]
    
    template = service.create_template(
        name=request.name,
        category=request.category,
        description=request.description,
        format=request.format.model_dump(),
        creator_id=current_user.id,
        creator_name=current_user.username,
        sections=sections_data,
        is_public=request.is_public,
        tags=request.tags
    )
    
    logger.info(f"模板创建成功 - ID: {template.id}")
    
    return {
        "success": True,
        "message": "模板创建成功",
        "template": template.to_dict()
    }


@router.get("/list", summary="获取模板列表")
def get_template_list(
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    creator_id: Optional[int] = None,
    is_public: Optional[bool] = None,
    tags: Optional[str] = None,
    sort_by: str = "updated_at",
    sort_order: str = "desc",
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取模板列表
    
    支持按关键词、分类、创建者、公开状态、标签筛选
    
    Args:
        keyword: 搜索关键词
        category: 分类筛选
        creator_id: 创建者ID筛选
        is_public: 是否公开筛选
        tags: 标签筛选（多个标签用逗号分隔）
        sort_by: 排序字段
        sort_order: 排序方向
        skip: 分页偏移量
        limit: 每页数量
        db: 数据库会话
    
    Returns:
        dict: 模板列表响应
    """
    logger.info(f"获取模板列表请求 - keyword: {keyword}, category: {category}, skip: {skip}, limit: {limit}")
    
    service = TemplateService(db)
    templates, total = service.get_template_list(
        keyword=keyword,
        category=category,
        creator_id=creator_id,
        is_public=is_public,
        tags=tags,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=min(limit, 100)
    )
    
    page = (skip // limit) + 1 if limit > 0 else 1
    total_pages = math.ceil(total / limit) if limit > 0 else 1
    
    logger.info(f"模板列表查询成功 - 总数: {total}, 返回: {len(templates)}")
    
    return {
        "success": True,
        "total": total,
        "items": [template.to_dict() for template in templates],
        "page": page,
        "page_size": limit,
        "total_pages": total_pages
    }


@router.get("/categories", summary="获取模板分类列表")
def get_template_categories(
    db: Session = Depends(get_db)
):
    """
    获取所有模板分类
    
    Args:
        db: 数据库会话
    
    Returns:
        dict: 分类列表
    """
    logger.info("获取模板分类列表请求")
    
    service = TemplateService(db)
    categories = service.get_categories()
    
    logger.info(f"模板分类查询成功 - 数量: {len(categories)}")
    
    return {
        "success": True,
        "categories": categories
    }


@router.get("/popular-tags", summary="获取热门标签")
def get_popular_tags(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取热门标签
    
    Args:
        limit: 返回标签数量
        db: 数据库会话
    
    Returns:
        dict: 标签列表
    """
    logger.info(f"获取热门标签请求 - limit: {limit}")
    
    service = TemplateService(db)
    tags = service.get_popular_tags(limit=limit)
    
    logger.info(f"热门标签查询成功 - 数量: {len(tags)}")
    
    return {
        "success": True,
        "tags": tags
    }


@router.post("/import-json", summary="导入模板（从JSON文件）")
async def import_template_json(
    file: UploadFile = File(...),
    overwrite: bool = Form(False),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    从JSON文件导入模板
    
    Args:
        file: JSON文件
        overwrite: 是否覆盖已存在的模板
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        dict: 导入结果
    
    Raises:
        HTTPException: 文件格式错误或导入失败时抛出错误
    """
    logger.info(f"导入模板请求 - 文件名: {file.filename}, 用户: {current_user.username}")
    
    if not file.filename.endswith(".json"):
        logger.error(f"文件格式不支持 - 文件名: {file.filename}")
        raise HTTPException(status_code=422, detail="仅支持JSON格式的模板文件")
    
    try:
        content = await file.read()
        template_data = json.loads(content.decode("utf-8"))
    except Exception as e:
        logger.error(f"文件解析失败 - 错误: {str(e)}")
        raise HTTPException(status_code=422, detail="文件格式错误")
    
    service = TemplateService(db)
    
    template = service.import_template_from_json(
        template_data=template_data,
        creator_id=current_user.id,
        creator_name=current_user.username,
        overwrite=overwrite
    )
    
    if not template:
        logger.warning(f"模板导入失败或已存在 - 文件名: {file.filename}")
        return {
            "success": False,
            "message": "模板已存在，跳过导入"
        }
    
    logger.info(f"模板导入成功 - ID: {template.id}")
    
    return {
        "success": True,
        "message": "模板导入成功",
        "template": template.to_dict()
    }


@router.get("/download/{file_name}", summary="下载模板文件")
def download_template_file(
    file_name: str
):
    """
    下载模板文件
    
    Args:
        file_name: 文件名
    
    Returns:
        FileResponse: 文件响应
    
    Raises:
        HTTPException: 文件不存在时抛出404错误
    """
    logger.info(f"下载模板文件请求 - 文件名: {file_name}")
    
    upload_dir = os.path.join(os.getcwd(), "uploads", "templates")
    file_path = os.path.join(upload_dir, file_name)
    
    if not os.path.exists(file_path):
        logger.error(f"文件不存在 - 文件名: {file_name}")
        raise HTTPException(status_code=404, detail="文件不存在")
    
    logger.info(f"文件下载成功 - 文件名: {file_name}")
    
    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type="application/octet-stream"
    )


@router.get("/{template_id}", summary="获取模板详情")
def get_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """
    获取模板详情
    
    Args:
        template_id: 模板ID
        db: 数据库会话
    
    Returns:
        dict: 模板详情
    
    Raises:
        HTTPException: 模板不存在时抛出404错误
    """
    logger.info(f"获取模板详情请求 - ID: {template_id}")
    
    service = TemplateService(db)
    template = service.get_template_by_id(template_id)
    
    if not template:
        logger.error(f"模板不存在 - ID: {template_id}")
        raise HTTPException(status_code=404, detail="模板不存在")
    
    logger.debug(f"模板详情查询成功 - ID: {template_id}")
    
    return {
        "success": True,
        "template": template.to_dict()
    }


@router.put("/{template_id}", summary="更新模板")
def update_template(
    template_id: str,
    request: TemplateUpdateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    更新模板信息
    
    Args:
        template_id: 模板ID
        request: 更新请求
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        dict: 更新后的模板信息
    
    Raises:
        HTTPException: 模板不存在或无权限时抛出错误
    """
    logger.info(f"更新模板请求 - ID: {template_id}, 用户: {current_user.username}")
    
    service = TemplateService(db)
    template = service.get_template_by_id(template_id)
    
    if not template:
        logger.error(f"模板不存在 - ID: {template_id}")
        raise HTTPException(status_code=404, detail="模板不存在")
    
    if template.creator_id != current_user.id and current_user.role != "admin":
        logger.error(f"无权限修改模板 - ID: {template_id}, 用户: {current_user.id}")
        raise HTTPException(status_code=403, detail="无权限修改此模板")
    
    update_data = {}
    if request.name is not None:
        update_data["name"] = request.name
    if request.category is not None:
        update_data["category"] = request.category
    if request.description is not None:
        update_data["description"] = request.description
    if request.format is not None:
        update_data["format"] = request.format.model_dump()
    if request.sections is not None:
        update_data["sections"] = [section.model_dump() for section in request.sections]
    if request.is_public is not None:
        update_data["is_public"] = request.is_public
    if request.tags is not None:
        update_data["tags"] = request.tags
    
    template = service.update_template(template_id, **update_data)
    
    logger.info(f"模板更新成功 - ID: {template_id}")
    
    return {
        "success": True,
        "message": "模板更新成功",
        "template": template.to_dict()
    }


@router.delete("/{template_id}", summary="删除模板")
def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    删除模板
    
    Args:
        template_id: 模板ID
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        dict: 操作结果
    
    Raises:
        HTTPException: 模板不存在或无权限时抛出错误
    """
    logger.info(f"删除模板请求 - ID: {template_id}, 用户: {current_user.username}")
    
    service = TemplateService(db)
    template = service.get_template_by_id(template_id)
    
    if not template:
        logger.error(f"模板不存在 - ID: {template_id}")
        raise HTTPException(status_code=404, detail="模板不存在")
    
    if template.creator_id != current_user.id and current_user.role != "admin":
        logger.error(f"无权限删除模板 - ID: {template_id}, 用户: {current_user.id}")
        raise HTTPException(status_code=403, detail="无权限删除此模板")
    
    if not service.delete_template(template_id):
        logger.error(f"模板删除失败 - ID: {template_id}")
        raise HTTPException(status_code=500, detail="删除失败")
    
    logger.info(f"模板删除成功 - ID: {template_id}")
    
    return {
        "success": True,
        "message": "模板删除成功",
        "deleted_template_id": template_id
    }


@router.post("/{template_id}/export-markdown", summary="导出模板为Markdown文件")
def export_template_markdown(
    template_id: str,
    request: TemplateExportMarkdownRequest = TemplateExportMarkdownRequest(),
    db: Session = Depends(get_db)
):
    """
    导出模板为Markdown格式
    
    Args:
        template_id: 模板ID
        request: 导出选项
        db: 数据库会话
    
    Returns:
        dict: 导出结果
    
    Raises:
        HTTPException: 模板不存在时抛出404错误
    """
    logger.info(f"导出模板为Markdown请求 - ID: {template_id}")
    
    service = TemplateService(db)
    
    markdown_content = service.export_template_to_markdown(
        template_id=template_id,
        include_metadata=request.include_metadata,
        include_format_section=request.include_format_section,
        include_creator_info=request.include_creator_info
    )
    
    if not markdown_content:
        logger.error(f"模板不存在 - ID: {template_id}")
        raise HTTPException(status_code=404, detail="模板不存在")
    
    template = service.get_template_by_id(template_id)
    
    upload_dir = os.path.join(os.getcwd(), "uploads", "templates")
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    file_name = f"{template.name}.md"
    file_path = os.path.join(upload_dir, f"{template_id}.md")
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    
    file_size = os.path.getsize(file_path)
    expires_at = datetime.now() + timedelta(hours=24)
    
    logger.info(f"模板导出为Markdown成功 - ID: {template_id}, 文件大小: {file_size}")
    
    return {
        "success": True,
        "download_url": f"/api/template/download/{template_id}.md",
        "file_name": file_name,
        "file_size": file_size,
        "expires_at": expires_at.isoformat()
    }


@router.post("/{template_id}/export-json", summary="导出模板为JSON文件")
def export_template_json(
    template_id: str,
    db: Session = Depends(get_db)
):
    """
    导出模板为JSON格式
    
    Args:
        template_id: 模板ID
        db: 数据库会话
    
    Returns:
        dict: 导出结果
    
    Raises:
        HTTPException: 模板不存在时抛出404错误
    """
    logger.info(f"导出模板为JSON请求 - ID: {template_id}")
    
    service = TemplateService(db)
    
    template_data = service.export_template_to_json(template_id)
    
    if not template_data:
        logger.error(f"模板不存在 - ID: {template_id}")
        raise HTTPException(status_code=404, detail="模板不存在")
    
    template = service.get_template_by_id(template_id)
    
    upload_dir = os.path.join(os.getcwd(), "uploads", "templates")
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    file_name = f"{template.name}.json"
    file_path = os.path.join(upload_dir, f"{template_id}.json")
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(template_data, f, ensure_ascii=False, indent=2)
    
    file_size = os.path.getsize(file_path)
    expires_at = datetime.now() + timedelta(hours=24)
    
    logger.info(f"模板导出为JSON成功 - ID: {template_id}, 文件大小: {file_size}")
    
    return {
        "success": True,
        "download_url": f"/api/template/download/{template_id}.json",
        "file_name": file_name,
        "file_size": file_size,
        "expires_at": expires_at.isoformat()
    }
