"""
消息实体类
用于存储对话中的消息记录
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from db.mysql_session import Base


class Message(Base):
    """
    消息实体类
    存储对话中的消息记录，包括用户提问和模型回答
    
    Attributes:
        id: 消息唯一标识
        conversation_id: 所属对话ID
        role: 消息角色（user/assistant）
        content: 消息内容
        file_paths: 关联的文件路径（JSON格式存储）
        knowledge_base_id: 使用的知识库ID
        created_at: 创建时间
    """
    
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="消息ID")
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, comment="对话ID")
    role = Column(String(50), nullable=False, comment="角色：user/assistant")
    content = Column(Text, nullable=False, comment="消息内容")
    file_paths = Column(Text, nullable=True, comment="关联文件路径（JSON格式）")
    knowledge_base_id = Column(Integer, nullable=True, comment="使用的知识库ID")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    def to_dict(self) -> dict:
        """
        将实体转换为字典格式
        
        Returns:
            dict: 包含实体属性的字典
        """
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "file_paths": self.file_paths,
            "knowledge_base_id": self.knowledge_base_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
