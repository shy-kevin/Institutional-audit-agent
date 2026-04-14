"""
制度审查智能体主应用入口
"""

import os
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from config import settings
from db.mysql_session import init_db
from routers import api_router
from utils.logger import setup_logger, LogConfig

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    在应用启动时初始化数据库、上传目录和日志系统
    """
    LogConfig.setup_logging(log_dir="logs", log_level="INFO" if not settings.DEBUG else "DEBUG")
    logger.info("应用启动 - 初始化数据库和目录")
    
    init_db()
    
    upload_dir = settings.UPLOAD_DIR
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        os.makedirs(os.path.join(upload_dir, "knowledge_base"))
        os.makedirs(os.path.join(upload_dir, "temp"))
        logger.info(f"创建上传目录: {upload_dir}")
    
    logger.info(f"应用启动完成 - {settings.APP_NAME} v{settings.APP_VERSION}")
    
    yield
    
    logger.info("应用关闭")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于LangChain和LangGraph的制度审查智能体系统，支持PDF文件解析、知识库管理和智能问答",
    lifespan=lifespan
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理器
    
    捕获所有未处理的异常，记录错误日志并返回友好的错误信息
    """
    error_msg = f"全局异常 - URL: {request.url}, 方法: {request.method}, 错误: {str(exc)}"
    logger.error(error_msg, exc_info=True)
    logger.error(f"异常堆栈:\n{traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "服务器内部错误",
            "error": str(exc),
            "path": str(request.url)
        }
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/", summary="根路径")
async def root():
    """
    根路径接口
    
    返回应用基本信息
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health", summary="健康检查")
async def health_check():
    """
    健康检查接口
    
    用于检查服务是否正常运行
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
