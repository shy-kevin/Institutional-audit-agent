"""
对话实体类
用于存储对话基本信息
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from db.mysql_session import Base


class Conversation(Base):
    """
    对话实体类
    存储对话的基本信息，包括对话标题、状态等
    
    Attributes:
        id: 对话唯一标识
        title: 对话标题
        description: 对话描述
        status: 对话状态（active/archived/deleted）
        created_at: 创建时间
        updated_at: 更新时间
    """
    
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="对话ID")
    title = Column(String(255), nullable=False, default="新对话", comment="对话标题")
    description = Column(Text, nullable=True, comment="对话描述")
    status = Column(String(50), default="active", comment="状态：active/archived/deleted")
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
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
