"""
智能问答API路由
提供基于大模型的智能问答接口
"""

import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from db import get_db
from models.schemas import ChatRequest, ApiResponse
from services.conversation_service import ConversationService
from services.message_service import MessageService
from agent import create_audit_agent
from utils.pdf_parser import PDFParser
from utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


def format_download_links(output_files: list) -> str:
    """
    格式化下载链接
    
    Args:
        output_files: 输出文件列表
    
    Returns:
        str: 格式化后的下载链接文本
    """
    if not output_files:
        return ""
    
    links = []
    for file_info in output_files:
        filename = file_info.get("filename", "")
        download_url = file_info.get("download_url", "")
        
        if filename and download_url:
            if "highlighted" in filename:
                link_text = "查看带标注的原文"
            elif "reviewed" in filename:
                link_text = "下载审查报告"
            elif "modified" in filename:
                link_text = "下载修改后的文件"
            else:
                link_text = "下载文件"
            
            links.append(f"✅ **{link_text}**：[点击下载](http://localhost:8000{download_url})")
    
    if links:
        return "\n\n" + "\n".join(links)
    return ""


@router.post("/stream", summary="流式问答接口（支持工具调用）")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    流式问答接口
    
    接收用户问题，基于知识库和对话历史进行智能问答，支持工具调用，以流式方式返回结果
    
    Args:
        request: 聊天请求
        db: 数据库会话
    
    Returns:
        StreamingResponse: 流式响应
    
    Raises:
        HTTPException: 对话不存在时抛出404错误
    """
    logger.info(f"流式问答请求 - 对话ID: {request.conversation_id}, 消息: {request.message[:50]}...")
    
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
    
    file_content = None
    if request.file_paths:
        logger.debug(f"开始提取文件内容 - 文件数: {len(request.file_paths)}")
        pdf_parser = PDFParser()
        contents = []
        for file_path in request.file_paths:
            try:
                content = pdf_parser.extract_text_from_pdf(file_path)
                contents.append(content)
            except Exception as e:
                logger.warning(f"文件内容提取失败 - 文件: {file_path}, 错误: {str(e)}")
        if contents:
            file_content = "\n\n".join(contents)
            logger.info(f"文件内容提取成功 - 总字符数: {len(file_content)}")
    
    agent = create_audit_agent()
    
    async def generate():
        """
        生成器函数，用于流式输出
        """
        full_response = ""
        tool_calls_info = []
        output_files = []
        
        try:
            logger.debug(f"开始调用智能体 - 对话ID: {request.conversation_id}")
            result = agent.chat_with_tools(
                question=request.message,
                messages=history[:-1],
                knowledge_base_id=request.knowledge_base_id,
                file_content=file_content,
                file_paths=request.file_paths,
                conversation_id=request.conversation_id
            )
            
            if result.get("tool_calls"):
                logger.info(f"检测到工具调用 - 数量: {len(result['tool_calls'])}")
                for tool_call in result["tool_calls"]:
                    tool_info = {
                        "name": tool_call.get("name", ""),
                        "args": tool_call.get("args", {})
                    }
                    tool_calls_info.append(tool_info)
                    tool_name = tool_info["name"]
                    logger.debug(f"工具调用: {tool_name}")
                    yield f"data: {json.dumps({'type': 'tool_call', 'content': f'正在调用工具: {tool_name}', 'tool': tool_info}, ensure_ascii=False)}\n\n"
            
            if result.get("tool_results"):
                logger.debug(f"处理工具结果 - 数量: {len(result['tool_results'])}")
                for tool_result in result["tool_results"]:
                    try:
                        content = tool_result.get("content", "{}")
                        result_data = json.loads(content)
                        
                        if result_data.get("success") and result_data.get("download_url"):
                            output_file = result_data.get("output_filename", "")
                            download_url = result_data.get("download_url", "")
                            message = result_data.get("message", "")
                            
                            if output_file:
                                output_files.append({
                                    "filename": output_file,
                                    "download_url": download_url
                                })
                                logger.info(f"生成输出文件: {output_file}")
                                yield f"data: {json.dumps({'type': 'tool_result', 'content': message, 'output_file': output_file, 'download_url': download_url}, ensure_ascii=False)}\n\n"
                    except Exception as e:
                        logger.error(f"工具结果解析失败: {str(e)}")
            
            if result.get("response"):
                full_response = result["response"]
            
            download_links = format_download_links(output_files)
            final_response = full_response + download_links
            
            yield f"data: {json.dumps({'type': 'content', 'content': final_response, 'is_end': False}, ensure_ascii=False)}\n\n"
            
            msg_service.create_message(
                conversation_id=request.conversation_id,
                role="assistant",
                content=final_response
            )
            logger.info(f"助手消息已保存 - 对话ID: {request.conversation_id}")
            
            response_data = {
                'type': 'end', 
                'content': '', 
                'is_end': True,
                'tool_calls': tool_calls_info,
                'output_files': output_files
            }
            yield f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"流式问答异常 - 对话ID: {request.conversation_id}, 错误: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/sync", response_model=ApiResponse, summary="同步问答接口")
async def chat_sync(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    同步问答接口
    
    接收用户问题，基于知识库和对话历史进行智能问答，同步返回完整结果
    
    Args:
        request: 聊天请求
        db: 数据库会话
    
    Returns:
        ApiResponse: 包含回答的响应
    
    Raises:
        HTTPException: 对话不存在时抛出404错误
    """
    logger.info(f"同步问答请求 - 对话ID: {request.conversation_id}, 消息: {request.message[:50]}...")
    
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
    
    file_content = None
    if request.file_paths:
        logger.debug(f"开始提取文件内容 - 文件数: {len(request.file_paths)}")
        pdf_parser = PDFParser()
        contents = []
        for file_path in request.file_paths:
            try:
                content = pdf_parser.extract_text_from_pdf(file_path)
                contents.append(content)
            except Exception as e:
                logger.warning(f"文件内容提取失败 - 文件: {file_path}, 错误: {str(e)}")
        if contents:
            file_content = "\n\n".join(contents)
            logger.info(f"文件内容提取成功 - 总字符数: {len(file_content)}")
    
    agent = create_audit_agent()
    
    try:
        logger.debug(f"开始调用智能体 - 对话ID: {request.conversation_id}")
        result = agent.chat_with_tools(
            question=request.message,
            messages=history[:-1],
            knowledge_base_id=request.knowledge_base_id,
            file_content=file_content,
            file_paths=request.file_paths,
            conversation_id=request.conversation_id
        )
        
        response = result.get("response", "")
        
        output_files = []
        if result.get("tool_results"):
            logger.debug(f"处理工具结果 - 数量: {len(result['tool_results'])}")
            for tool_result in result["tool_results"]:
                try:
                    content = tool_result.get("content", "{}")
                    result_data = json.loads(content)
                    if result_data.get("success") and result_data.get("download_url"):
                        output_files.append({
                            "filename": result_data.get("output_filename"),
                            "download_url": result_data.get("download_url")
                        })
                        logger.info(f"生成输出文件: {result_data.get('output_filename')}")
                except Exception as e:
                    logger.error(f"工具结果解析失败: {str(e)}")
        
        download_links = format_download_links(output_files)
        final_response = response + download_links
        
        msg_service.create_message(
            conversation_id=request.conversation_id,
            role="assistant",
            content=final_response
        )
        logger.info(f"同步问答完成 - 对话ID: {request.conversation_id}")
        
        return ApiResponse(
            code=200,
            message="success",
            data={
                "response": final_response,
                "tool_calls": result.get("tool_calls", []),
                "output_files": output_files
            }
        )
    except Exception as e:
        logger.error(f"同步问答异常 - 对话ID: {request.conversation_id}, 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成回答失败: {str(e)}")


@router.post("/quick", response_model=ApiResponse, summary="快速问答接口（无历史记录）")
async def quick_chat(
    message: str,
    knowledge_base_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    快速问答接口
    
    不保存历史记录的快速问答，适用于单次查询
    
    Args:
        message: 用户问题
        knowledge_base_id: 知识库ID（可选）
        db: 数据库会话
    
    Returns:
        ApiResponse: 包含回答的响应
    """
    logger.info(f"快速问答请求 - 消息: {message[:50]}..., 知识库ID: {knowledge_base_id}")
    
    agent = create_audit_agent()
    
    try:
        logger.debug("开始调用智能体")
        result = agent.chat_with_tools(
            question=message,
            messages=[],
            knowledge_base_id=knowledge_base_id
        )
        
        output_files = []
        if result.get("tool_results"):
            logger.debug(f"处理工具结果 - 数量: {len(result['tool_results'])}")
            for tool_result in result["tool_results"]:
                try:
                    content = tool_result.get("content", "{}")
                    result_data = json.loads(content)
                    if result_data.get("success") and result_data.get("download_url"):
                        output_files.append({
                            "filename": result_data.get("output_filename"),
                            "download_url": result_data.get("download_url")
                        })
                        logger.info(f"生成输出文件: {result_data.get('output_filename')}")
                except Exception as e:
                    logger.error(f"工具结果解析失败: {str(e)}")
        
        download_links = format_download_links(output_files)
        final_response = result.get("response", "") + download_links
        
        logger.info(f"快速问答完成")
        
        return ApiResponse(
            code=200,
            message="success",
            data={
                "response": final_response,
                "tool_calls": result.get("tool_calls", []),
                "output_files": output_files
            }
        )
    except Exception as e:
        logger.error(f"快速问答异常 - 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成回答失败: {str(e)}")
