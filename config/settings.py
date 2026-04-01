"""
配置文件模块
包含所有系统配置信息，包括数据库连接、模型配置等
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    系统配置类
    使用pydantic进行配置管理，支持环境变量覆盖
    """
    
    # 应用配置
    APP_NAME: str = "制度审查智能体"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # MySQL数据库配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "123456"
    MYSQL_DATABASE: str = "institutional_audit"
    
    @property
    def MYSQL_URL(self) -> str:
        """
        获取MySQL数据库连接URL
        Returns:
            str: MySQL连接字符串
        """
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    # PostgreSQL数据库配置（用于向量存储）
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "123456"
    POSTGRES_DATABASE: str = "institutional_audit_vectors"
    
    @property
    def POSTGRES_URL(self) -> str:
        """
        获取PostgreSQL数据库连接URL
        Returns:
            str: PostgreSQL连接字符串
        """
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DATABASE}"
    
    # 模型配置
    # 模型提供商：ollama 或 alibaba
    MODEL_PROVIDER: str = "alibaba"
    
    # Ollama配置
    OLLAMA_BASE_URL: str = "http://192.168.110.241:11434"
    OLLAMA_MODEL: str = "deepseek-r1:70b"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    
    # 阿里云百炼配置
    ALIBABA_API_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    ALIBABA_API_KEY: Optional[str] = None
    ALIBABA_MODEL: str = "qwen-plus"
    
    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: set = {".pdf"}
    
    # 向量存储配置
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # 对话配置
    MAX_HISTORY_LENGTH: int = 20
    
    # 外部知识库API配置
    KNOWLEDGE_API_URL: str = "http://121.48.164.135:30700"
    KNOWLEDGE_API_TIMEOUT: int = 30
    KNOWLEDGE_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
