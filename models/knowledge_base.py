"""
知识库实体类
用于存储知识库基本信息
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from db.mysql_session import Base


class KnowledgeBase(Base):
    """
    知识库实体类
    存储知识库的基本信息，包括名称、描述、文件路径等
    
    Attributes:
        id: 知识库唯一标识
        name: 知识库名称
        description: 知识库描述
        file_path: 上传文件存储路径
        file_name: 原始文件名
        file_size: 文件大小（字节）
        status: 知识库状态（processing/completed/failed）
        created_at: 创建时间
        updated_at: 更新时间
    """
    
    __tablename__ = "knowledge_bases"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="知识库ID")
    name = Column(String(255), nullable=False, comment="知识库名称")
    description = Column(Text, nullable=True, comment="知识库描述")
    file_path = Column(String(500), nullable=False, comment="文件存储路径")
    file_name = Column(String(255), nullable=False, comment="原始文件名")
    file_size = Column(Integer, nullable=True, comment="文件大小（字节）")
    status = Column(String(50), default="processing", comment="状态：processing/completed/failed")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    def to_dict(self) -> dict:
        """
        将实体转换为字典格式
        
        Returns:
            dict: 包含实体属性的字典
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
