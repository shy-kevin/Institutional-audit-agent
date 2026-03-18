"""
知识库管理API路由
提供知识库的上传、查询、删除等接口
"""

from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from db import get_db
from models.schemas import (
    KnowledgeBaseCreateRequest,
    KnowledgeBaseResponse,
    KnowledgeBaseListResponse,
    ApiResponse,
    FileUploadResponse
)
from services.knowledge_base_service import KnowledgeBaseService
from utils.file_utils import save_upload_file
from utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


@router.post("/upload", response_model=ApiResponse, summary="上传知识库文件")
async def upload_knowledge_base(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF文件"),
    name: str = Form(..., description="知识库名称"),
    description: Optional[str] = Form(None, description="知识库描述"),
    db: Session = Depends(get_db)
):
    """
    上传知识库文件
    
    上传PDF格式的制度文件作为知识库，系统会自动解析文件内容并进行向量化存储
    
    Args:
        background_tasks: 后台任务管理器
        file: 上传的PDF文件
        name: 知识库名称
        description: 知识库描述（可选）
        db: 数据库会话
    
    Returns:
        ApiResponse: 包含知识库信息的响应
    """
    try:
        file_path, file_name, file_size = await save_upload_file(file, subfolder="knowledge_base")
        
        service = KnowledgeBaseService(db)
        knowledge_base = service.create_knowledge_base(
            name=name,
            file_path=file_path,
            file_name=file_name,
            description=description,
            file_size=file_size
        )
        
        background_tasks.add_task(
            service.process_knowledge_base_file,
            knowledge_base.id
        )
        
        return ApiResponse(
            code=200,
            message="知识库文件上传成功，正在后台处理中",
            data=knowledge_base.to_dict()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/list", response_model=KnowledgeBaseListResponse, summary="获取知识库列表")
def get_knowledge_base_list(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取知识库列表
    
    分页获取所有知识库信息，可按状态筛选
    
    Args:
        skip: 跳过的记录数（分页偏移）
        limit: 返回的最大记录数
        status: 按状态筛选（processing/completed/failed）
        db: 数据库会话
    
    Returns:
        KnowledgeBaseListResponse: 知识库列表响应
    """
    service = KnowledgeBaseService(db)
    knowledge_bases, total = service.get_all_knowledge_bases(skip, limit, status)
    
    return KnowledgeBaseListResponse(
        total=total,
        items=[KnowledgeBaseResponse.model_validate(kb) for kb in knowledge_bases]
    )


@router.get("/{knowledge_base_id}", response_model=KnowledgeBaseResponse, summary="获取知识库详情")
def get_knowledge_base(
    knowledge_base_id: int,
    db: Session = Depends(get_db)
):
    """
    获取知识库详情
    
    根据ID获取指定知识库的详细信息
    
    Args:
        knowledge_base_id: 知识库ID
        db: 数据库会话
    
    Returns:
        KnowledgeBaseResponse: 知识库详情
    
    Raises:
        HTTPException: 知识库不存在时抛出404错误
    """
    service = KnowledgeBaseService(db)
    knowledge_base = service.get_knowledge_base_by_id(knowledge_base_id)
    
    if not knowledge_base:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    return KnowledgeBaseResponse.model_validate(knowledge_base)


@router.put("/{knowledge_base_id}", response_model=KnowledgeBaseResponse, summary="更新知识库信息")
def update_knowledge_base(
    knowledge_base_id: int,
    request: KnowledgeBaseCreateRequest,
    db: Session = Depends(get_db)
):
    """
    更新知识库信息
    
    更新指定知识库的名称和描述
    
    Args:
        knowledge_base_id: 知识库ID
        request: 更新请求
        db: 数据库会话
    
    Returns:
        KnowledgeBaseResponse: 更新后的知识库信息
    
    Raises:
        HTTPException: 知识库不存在时抛出404错误
    """
    service = KnowledgeBaseService(db)
    knowledge_base = service.update_knowledge_base(
        knowledge_base_id=knowledge_base_id,
        name=request.name,
        description=request.description
    )
    
    if not knowledge_base:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    return KnowledgeBaseResponse.model_validate(knowledge_base)


@router.delete("/{knowledge_base_id}", response_model=ApiResponse, summary="删除知识库")
def delete_knowledge_base(
    knowledge_base_id: int,
    db: Session = Depends(get_db)
):
    """
    删除知识库
    
    删除指定知识库，包括其向量存储数据
    
    Args:
        knowledge_base_id: 知识库ID
        db: 数据库会话
    
    Returns:
        ApiResponse: 操作结果
    
    Raises:
        HTTPException: 知识库不存在或删除失败时抛出错误
    """
    service = KnowledgeBaseService(db)
    
    if not service.get_knowledge_base_by_id(knowledge_base_id):
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    if not service.delete_knowledge_base(knowledge_base_id):
        raise HTTPException(status_code=500, detail="删除失败")
    
    return ApiResponse(code=200, message="知识库删除成功")


@router.post("/upload-file", response_model=FileUploadResponse, summary="仅上传文件（不创建知识库）")
async def upload_file_only(
    file: UploadFile = File(..., description="PDF文件")
):
    """
    仅上传文件
    
    上传PDF文件但不创建知识库，用于临时文件上传
    
    Args:
        file: 上传的PDF文件
    
    Returns:
        FileUploadResponse: 文件上传响应
    
    Raises:
        HTTPException: 文件验证失败时抛出错误
    """
    try:
        file_path, file_name, file_size = await save_upload_file(file, subfolder="temp")
        
        return FileUploadResponse(
            file_path=file_path,
            file_name=file_name,
            file_size=file_size
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")
