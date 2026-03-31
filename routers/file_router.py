"""
文件操作API路由
提供文件读取、修改、标注等接口
"""

from typing import Optional, List
from pathlib import Path
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from db import get_db
from models.schemas import ApiResponse
from utils.file_tools import file_tools
from utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


class ReadFileRequest(BaseModel):
    """
    读取文件请求
    """
    file_path: str = Field(..., description="文件路径")


class HighlightTextRequest(BaseModel):
    """
    标注文字请求
    """
    file_path: str = Field(..., description="原文件路径")
    highlight_texts: List[str] = Field(..., description="需要标注的文字列表")
    output_filename: Optional[str] = Field(None, description="输出文件名")


class ModifyTextRequest(BaseModel):
    """
    修改文字请求
    """
    file_path: str = Field(..., description="原文件路径")
    modifications: List[dict] = Field(
        ...,
        description="修改列表，每项包含old_text和new_text"
    )
    output_filename: Optional[str] = Field(None, description="输出文件名")


class AddCommentsRequest(BaseModel):
    """
    添加审查意见请求
    """
    file_path: str = Field(..., description="原文件路径")
    comments: List[dict] = Field(
        ...,
        description="审查意见列表，每项包含text、comment、risk_level"
    )
    output_filename: Optional[str] = Field(None, description="输出文件名")


class ChatWithToolsRequest(BaseModel):
    """
    带工具调用的聊天请求
    """
    conversation_id: int = Field(..., description="对话ID")
    message: str = Field(..., description="用户消息")
    knowledge_base_id: Optional[int] = Field(None, description="知识库ID")
    file_paths: Optional[List[str]] = Field(None, description="上传文件路径列表")


class ConvertToPdfRequest(BaseModel):
    """
    文件转PDF请求
    """
    file_path: str = Field(..., description="文件相对路径或完整URL")


@router.post("/read", summary="读取文件内容")
async def read_file(
    request: ReadFileRequest
):
    """
    读取文件内容
    
    支持PDF、Word、TXT等格式的文件读取
    
    Args:
        request: 读取文件请求
    
    Returns:
        dict: 文件内容和元数据
    """
    logger.info(f"读取文件请求 - 文件路径: {request.file_path}")
    
    result = file_tools.read_file_content(request.file_path)
    
    if not result.get("success"):
        logger.error(f"文件读取失败 - 文件: {request.file_path}, 错误: {result.get('error')}")
        raise HTTPException(status_code=400, detail=result.get("error", "读取文件失败"))
    
    logger.info(f"文件读取成功 - 文件: {request.file_path}")
    return result


@router.post("/highlight/pdf", summary="标注PDF文字")
async def highlight_pdf_text(
    request: HighlightTextRequest
):
    """
    在PDF中标注文字
    
    将指定的文字以红色高亮显示，生成新的PDF文件
    
    Args:
        request: 标注请求
    
    Returns:
        dict: 操作结果，包含输出文件路径
    """
    logger.info(f"PDF标注请求 - 文件: {request.file_path}, 标注文本数: {len(request.highlight_texts)}")
    
    result = file_tools.highlight_text_in_pdf(
        file_path=request.file_path,
        highlight_texts=request.highlight_texts,
        output_filename=request.output_filename
    )
    
    if not result.get("success"):
        logger.error(f"PDF标注失败 - 文件: {request.file_path}, 错误: {result.get('error')}")
        raise HTTPException(status_code=400, detail=result.get("error", "标注失败"))
    
    logger.info(f"PDF标注成功 - 输出文件: {result.get('output_filename')}")
    return result


@router.post("/modify/pdf", summary="修改PDF文字")
async def modify_pdf_text(
    request: ModifyTextRequest
):
    """
    修改PDF中的文字内容
    
    将指定的旧文本替换为新文本，生成新的PDF文件
    
    Args:
        request: 修改请求
    
    Returns:
        dict: 操作结果，包含输出文件路径和修改记录
    """
    logger.info(f"PDF修改请求 - 文件: {request.file_path}, 修改数: {len(request.modifications)}")
    
    result = file_tools.modify_text_in_pdf(
        file_path=request.file_path,
        modifications=request.modifications,
        output_filename=request.output_filename
    )
    
    if not result.get("success"):
        logger.error(f"PDF修改失败 - 文件: {request.file_path}, 错误: {result.get('error')}")
        raise HTTPException(status_code=400, detail=result.get("error", "修改失败"))
    
    logger.info(f"PDF修改成功 - 输出文件: {result.get('output_filename')}")
    return result


@router.post("/highlight/docx", summary="标注Word文字")
async def highlight_docx_text(
    request: HighlightTextRequest
):
    """
    在Word文档中标注文字
    
    将指定的文字以红色高亮显示，生成新的Word文件
    
    Args:
        request: 标注请求
    
    Returns:
        dict: 操作结果，包含输出文件路径
    """
    logger.info(f"Word标注请求 - 文件: {request.file_path}, 标注文本数: {len(request.highlight_texts)}")
    
    result = file_tools.create_highlighted_docx(
        file_path=request.file_path,
        highlight_texts=request.highlight_texts,
        output_filename=request.output_filename
    )
    
    if not result.get("success"):
        logger.error(f"Word标注失败 - 文件: {request.file_path}, 错误: {result.get('error')}")
        raise HTTPException(status_code=400, detail=result.get("error", "标注失败"))
    
    logger.info(f"Word标注成功 - 输出文件: {result.get('output_filename')}")
    return result


@router.post("/modify/docx", summary="修改Word文字")
async def modify_docx_text(
    request: ModifyTextRequest
):
    """
    修改Word文档中的文字内容
    
    将指定的旧文本替换为新文本，生成新的Word文件
    
    Args:
        request: 修改请求
    
    Returns:
        dict: 操作结果，包含输出文件路径和修改记录
    """
    logger.info(f"Word修改请求 - 文件: {request.file_path}, 修改数: {len(request.modifications)}")
    
    result = file_tools.modify_text_in_docx(
        file_path=request.file_path,
        modifications=request.modifications,
        output_filename=request.output_filename
    )
    
    if not result.get("success"):
        logger.error(f"Word修改失败 - 文件: {request.file_path}, 错误: {result.get('error')}")
        raise HTTPException(status_code=400, detail=result.get("error", "修改失败"))
    
    logger.info(f"Word修改成功 - 输出文件: {result.get('output_filename')}")
    return result


@router.post("/review-comments", summary="生成审查报告")
async def add_review_comments(
    request: AddCommentsRequest
):
    """
    生成制度审查报告
    
    包含审查意见汇总和原文标注
    
    Args:
        request: 审查意见请求
    
    Returns:
        dict: 操作结果，包含输出文件路径
    """
    logger.info(f"生成审查报告请求 - 文件: {request.file_path}, 审查意见数: {len(request.comments)}")
    
    result = file_tools.add_review_comments(
        file_path=request.file_path,
        comments=request.comments,
        output_filename=request.output_filename
    )
    
    if not result.get("success"):
        logger.error(f"审查报告生成失败 - 文件: {request.file_path}, 错误: {result.get('error')}")
        raise HTTPException(status_code=400, detail=result.get("error", "生成报告失败"))
    
    logger.info(f"审查报告生成成功 - 输出文件: {result.get('output_filename')}")
    return result


@router.get("/download/{filename:path}", summary="下载文件")
async def download_file(
    filename: str,
    preview: bool = False
):
    """
    下载或预览文件
    
    Args:
        filename: 文件名
        preview: 是否预览模式（True为预览，False为下载）
    
    Returns:
        FileResponse: 文件下载或预览响应
    """
    from fastapi.responses import FileResponse
    from urllib.parse import unquote
    
    decoded_filename = unquote(filename)
    logger.info(f"文件下载请求 - 原始文件名: {filename}, 解码后: {decoded_filename}, 预览模式: {preview}")
    
    file_path = file_tools.get_output_file(decoded_filename)
    
    if not file_path:
        logger.error(f"文件不存在 - 文件名: {decoded_filename}")
        raise HTTPException(status_code=404, detail="文件不存在")
    
    file_ext = Path(decoded_filename).suffix.lower()
    
    if file_ext == ".pdf":
        media_type = "application/pdf"
    elif file_ext in [".docx", ".doc"]:
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif file_ext == ".txt":
        media_type = "text/plain"
    else:
        media_type = "application/octet-stream"
    
    disposition = "inline" if preview else "attachment"
    
    encoded_filename = quote(decoded_filename, safe='')
    content_disposition = f"{disposition}; filename*=UTF-8''{encoded_filename}"
    
    logger.info(f"文件响应 - 路径: {file_path}, 类型: {media_type}, 模式: {disposition}")
    
    return FileResponse(
        path=file_path,
        filename=decoded_filename,
        media_type=media_type,
        headers={
            "Content-Disposition": content_disposition
        }
    )


@router.post("/convert-to-pdf", summary="文件转PDF")
async def convert_to_pdf(
    request: ConvertToPdfRequest
):
    """
    将文件转换为PDF格式
    
    支持 Word(.docx)、TXT 等格式转换为 PDF
    
    Args:
        request: 转换请求
    
    Returns:
        dict: 转换结果，包含 success 和 download_url 或 error
    """
    logger.info(f"文件转PDF请求 - 文件路径: {request.file_path}")
    
    result = file_tools.convert_to_pdf(request.file_path)
    
    if result.get("success"):
        logger.info(f"文件转换成功 - 输出文件: {result.get('download_url')}")
        return {
            "success": True,
            "download_url": result.get("download_url")
        }
    else:
        logger.error(f"文件转换失败 - 文件: {request.file_path}, 错误: {result.get('error')}")
        return {
            "success": False,
            "message": result.get("error", "转换失败")
        }


@router.post("/chat-with-tools", summary="带工具调用的智能问答")
async def chat_with_tools(
    request: ChatWithToolsRequest,
    db: Session = Depends(get_db)
):
    """
    带工具调用的智能问答接口
    
    模型可以根据用户需求调用文件操作工具，实现文件修改和标注
    
    Args:
        request: 聊天请求
        db: 数据库会话
    
    Returns:
        dict: 包含响应和工具调用结果
    """
    logger.info(f"带工具调用的智能问答请求 - 对话ID: {request.conversation_id}, 消息: {request.message[:50]}...")
    
    from services.conversation_service import ConversationService
    from services.message_service import MessageService
    from agent import create_audit_agent
    
    conv_service = ConversationService(db)
    conversation = conv_service.get_conversation_by_id(request.conversation_id)
    
    if not conversation:
        logger.error(f"对话不存在 - 对话ID: {request.conversation_id}")
        raise HTTPException(status_code=404, detail="对话不存在")
    
    msg_service = MessageService(db)
    
    msg_service.create_message(
        conversation_id=request.conversation_id,
        role="user",
        content=request.message,
        file_paths=request.file_paths,
        knowledge_base_id=request.knowledge_base_id
    )
    logger.debug(f"用户消息已保存 - 对话ID: {request.conversation_id}")
    
    history = msg_service.get_conversation_history(request.conversation_id)
    
    agent = create_audit_agent(enable_tools=True)
    
    try:
        logger.debug(f"开始调用智能体 - 对话ID: {request.conversation_id}")
        result = agent.chat_with_tools(
            question=request.message,
            messages=history[:-1],
            knowledge_base_id=request.knowledge_base_id,
            file_paths=request.file_paths
        )
        
        if result.get("response"):
            msg_service.create_message(
                conversation_id=request.conversation_id,
                role="assistant",
                content=result["response"]
            )
            logger.info(f"助手消息已保存 - 对话ID: {request.conversation_id}")
        
        logger.info(f"智能问答完成 - 对话ID: {request.conversation_id}")
        
        return {
            "code": 200,
            "message": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"智能问答异常 - 对话ID: {request.conversation_id}, 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
