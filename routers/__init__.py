"""
API路由模块初始化文件
"""

from fastapi import APIRouter
from .knowledge_base_router import router as knowledge_base_router
from .conversation_router import router as conversation_router
from .chat_router import router as chat_router
from .file_router import router as file_router

api_router = APIRouter()

api_router.include_router(knowledge_base_router, prefix="/knowledge-base", tags=["知识库管理"])
api_router.include_router(conversation_router, prefix="/conversation", tags=["对话管理"])
api_router.include_router(chat_router, prefix="/chat", tags=["智能问答"])
api_router.include_router(file_router, prefix="/file", tags=["文件操作"])

__all__ = ["api_router"]
