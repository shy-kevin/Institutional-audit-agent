"""
知识库管理API路由
提供知识库的上传、查询、删除等接口
调用外部知识库在线管理平台的API
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
    
    上传PDF格式的制度文件作为知识库，系统会自动解析文件内容并上传到外部知识库平台
    
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
        knowledge_base = await service.create_knowledge_base(
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
async def get_knowledge_base_list(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取知识库列表
    
    分页获取所有知识库信息，可按状态筛选
    调用外部知识库API获取文档列表
    
    Args:
        skip: 跳过的记录数（分页偏移）
        limit: 返回的最大记录数
        status: 按状态筛选（active/completed等）
        db: 数据库会话
    
    Returns:
        KnowledgeBaseListResponse: 知识库列表响应
    """
    service = KnowledgeBaseService(db)
    knowledge_bases, total = await service.get_all_knowledge_bases(skip, limit, status)
    
    from datetime import datetime
    items = []
    for kb in knowledge_bases:
        created_at = kb.get("created_at", "")
        updated_at = kb.get("updated_at", "")
        
        if isinstance(created_at, str) and created_at:
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except:
                created_at = datetime.now()
        else:
            created_at = datetime.now()
        
        if isinstance(updated_at, str) and updated_at:
            try:
                updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            except:
                updated_at = datetime.now()
        else:
            updated_at = datetime.now()
        
        items.append(KnowledgeBaseResponse(
            id=kb.get("id", ""),
            name=kb.get("name", ""),
            description=kb.get("description"),
            file_name=kb.get("file_name", ""),
            file_size=kb.get("file_size"),
            status=kb.get("status", "completed"),
            created_at=created_at,
            updated_at=updated_at
        ))
    
    return KnowledgeBaseListResponse(
        total=total,
        items=items
    )


@router.get("/detail/{doc_id}", summary="获取文档详情")
async def get_document_detail(
    doc_id: str,
    db: Session = Depends(get_db)
):
    """
    获取文档详情
    
    调用外部知识库API获取文档的详细信息，包括内容、切片、元数据等
    
    Args:
        doc_id: 外部文档ID（UUID格式）
        db: 数据库会话
    
    Returns:
        dict: 文档详情，包含内容、切片、元数据等
    """
    service = KnowledgeBaseService(db)
    doc_detail = await service.get_document_detail(doc_id)
    
    if not doc_detail:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return doc_detail


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
async def delete_knowledge_base(
    knowledge_base_id: int,
    db: Session = Depends(get_db)
):
    """
    删除知识库
    
    删除指定知识库，包括外部知识库平台的数据
    
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
    
    if not await service.delete_knowledge_base(knowledge_base_id):
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


@router.get("/{knowledge_base_id}/status", summary="获取任务状态")
async def get_task_status(
    knowledge_base_id: int,
    db: Session = Depends(get_db)
):
    """
    获取知识库处理任务状态
    
    查询外部知识库平台的文档解析任务状态
    
    Args:
        knowledge_base_id: 知识库ID
        db: 数据库会话
    
    Returns:
        dict: 任务状态信息
    """
    service = KnowledgeBaseService(db)
    knowledge_base = service.get_knowledge_base_by_id(knowledge_base_id)
    
    if not knowledge_base:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    if not knowledge_base.external_file_id:
        return {
            "status": knowledge_base.status,
            "message": "文件尚未上传到外部知识库平台"
        }
    
    task_status = await service.get_task_status(knowledge_base.external_file_id)
    return task_status


@router.post("/{knowledge_base_id}/search", summary="搜索知识库内容")
async def search_knowledge_base(
    knowledge_base_id: int,
    query: str = Form(..., description="搜索查询"),
    top_k: int = Form(5, description="返回结果数量"),
    db: Session = Depends(get_db)
):
    """
    在知识库中搜索相关内容
    
    调用外部知识库平台的智能检索接口
    
    Args:
        knowledge_base_id: 知识库ID
        query: 搜索查询语句
        top_k: 返回结果数量
        db: 数据库会话
    
    Returns:
        dict: 搜索结果列表
    """
    service = KnowledgeBaseService(db)
    
    if not service.get_knowledge_base_by_id(knowledge_base_id):
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    results = await service.search_similar_documents(
        knowledge_base_id=knowledge_base_id,
        query=query,
        k=top_k
    )
    
    return {
        "total": len(results),
        "items": results
    }


@router.post("/search", summary="全局知识检索")
async def global_search(
    query: str = Form(..., description="搜索查询"),
    top_k: int = Form(5, description="返回结果数量"),
    search_type: str = Form("hybrid", description="检索类型：semantic/keyword/hybrid")
):
    """
    全局知识检索
    
    调用外部知识库平台的智能检索接口，搜索所有知识库
    
    Args:
        query: 搜索查询语句
        top_k: 返回结果数量
        search_type: 检索类型
    
    Returns:
        dict: 搜索结果列表
    """
    from services.knowledge_api_client import knowledge_api_client
    
    results = await knowledge_api_client.search(
        query=query,
        top_k=top_k,
        search_type=search_type
    )
    
    if not results.get("success"):
        raise HTTPException(status_code=500, detail=results.get("error", "检索失败"))
    
    return {
        "total": len(results.get("results", results.get("items", []))),
        "items": results.get("results", results.get("items", []))
    }
