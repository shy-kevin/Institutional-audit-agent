"""
制度审查智能体主应用入口
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from db.mysql_session import init_db
from routers import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    在应用启动时初始化数据库和上传目录
    """
    init_db()
    
    upload_dir = settings.UPLOAD_DIR
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        os.makedirs(os.path.join(upload_dir, "knowledge_base"))
        os.makedirs(os.path.join(upload_dir, "temp"))
    
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于LangChain和LangGraph的制度审查智能体系统，支持PDF文件解析、知识库管理和智能问答",
    lifespan=lifespan
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
