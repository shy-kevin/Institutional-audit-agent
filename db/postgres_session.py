"""
PostgreSQL向量数据库会话管理模块
提供向量存储连接和管理
"""

from langchain_community.vectorstores import PGVector
from langchain_ollama import OllamaEmbeddings
from typing import Optional
from config import settings


class VectorStoreManager:
    """
    向量存储管理器
    
    管理PostgreSQL向量数据库的连接和操作
    
    Attributes:
        connection_string: PostgreSQL连接字符串
        embedding_model: 嵌入模型
    """
    
    _instance: Optional['VectorStoreManager'] = None
    _vector_stores: dict = {}
    
    def __new__(cls):
        """
        单例模式，确保只有一个实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """
        初始化向量存储管理器
        """
        if self._initialized:
            return
        
        self.connection_string = settings.POSTGRES_URL
        self.embedding_model = OllamaEmbeddings(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_EMBEDDING_MODEL
        )
        self._initialized = True
    
    def get_vector_store(self, collection_name: str) -> PGVector:
        """
        获取或创建向量存储
        
        Args:
            collection_name: 集合名称（通常使用知识库ID作为集合名）
        
        Returns:
            PGVector: 向量存储对象
        """
        if collection_name not in self._vector_stores:
            self._vector_stores[collection_name] = PGVector(
                embedding_function=self.embedding_model,
                connection_string=self.connection_string,
                collection_name=collection_name
            )
        return self._vector_stores[collection_name]
    
    def create_vector_store(self, collection_name: str, texts: list, metadatas: Optional[list] = None) -> PGVector:
        """
        创建新的向量存储并添加文档
        
        Args:
            collection_name: 集合名称
            texts: 文本列表
            metadatas: 元数据列表
        
        Returns:
            PGVector: 向量存储对象
        """
        vector_store = PGVector.from_texts(
            texts=texts,
            embedding=self.embedding_model,
            metadatas=metadatas,
            connection_string=self.connection_string,
            collection_name=collection_name
        )
        self._vector_stores[collection_name] = vector_store
        return vector_store
    
    def delete_vector_store(self, collection_name: str) -> bool:
        """
        删除向量存储
        
        Args:
            collection_name: 集合名称
        
        Returns:
            bool: 删除是否成功
        """
        try:
            if collection_name in self._vector_stores:
                del self._vector_stores[collection_name]
            return True
        except Exception:
            return False


vector_store_manager = VectorStoreManager()


def get_vector_store(collection_name: str) -> PGVector:
    """
    获取向量存储的便捷函数
    
    Args:
        collection_name: 集合名称
    
    Returns:
        PGVector: 向量存储对象
    """
    return vector_store_manager.get_vector_store(collection_name)
