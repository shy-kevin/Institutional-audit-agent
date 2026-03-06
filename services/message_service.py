"""
消息服务模块
提供消息的CRUD操作
"""

from typing import List, Optional
import json
from sqlalchemy.orm import Session
from models.message import Message
from config import settings


class MessageService:
    """
    消息服务类
    
    提供消息的创建、查询、删除等操作
    
    Attributes:
        db: 数据库会话
    """
    
    def __init__(self, db: Session):
        """
        初始化消息服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def create_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        file_paths: Optional[List[str]] = None,
        knowledge_base_id: Optional[int] = None
    ) -> Message:
        """
        创建消息
        
        Args:
            conversation_id: 对话ID
            role: 角色（user/assistant）
            content: 消息内容
            file_paths: 关联的文件路径列表
            knowledge_base_id: 使用的知识库ID
        
        Returns:
            Message: 创建的消息对象
        """
        file_paths_json = json.dumps(file_paths, ensure_ascii=False) if file_paths else None
        
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            file_paths=file_paths_json,
            knowledge_base_id=knowledge_base_id
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    def get_message_by_id(self, message_id: int) -> Optional[Message]:
        """
        根据ID获取消息
        
        Args:
            message_id: 消息ID
        
        Returns:
            Optional[Message]: 消息对象，不存在则返回None
        """
        return self.db.query(Message).filter(
            Message.id == message_id
        ).first()
    
    def get_messages_by_conversation_id(
        self,
        conversation_id: int,
        limit: int = None
    ) -> List[Message]:
        """
        获取对话的所有消息
        
        Args:
            conversation_id: 对话ID
            limit: 返回的最大消息数量，默认使用配置中的值
        
        Returns:
            List[Message]: 消息列表
        """
        if limit is None:
            limit = settings.MAX_HISTORY_LENGTH
        
        messages = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            Message.created_at.asc()
        ).limit(limit).all()
        
        return messages
    
    def get_conversation_history(
        self,
        conversation_id: int,
        limit: int = None
    ) -> List[dict]:
        """
        获取对话历史记录（格式化为LLM输入格式）
        
        Args:
            conversation_id: 对话ID
            limit: 返回的最大消息数量
        
        Returns:
            List[dict]: 格式化的消息列表
        """
        messages = self.get_messages_by_conversation_id(conversation_id, limit)
        
        return [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in messages
        ]
    
    def delete_messages_by_conversation_id(self, conversation_id: int) -> bool:
        """
        删除对话的所有消息
        
        Args:
            conversation_id: 对话ID
        
        Returns:
            bool: 删除是否成功
        """
        try:
            self.db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).delete()
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False
    
    def delete_message(self, message_id: int) -> bool:
        """
        删除单条消息
        
        Args:
            message_id: 消息ID
        
        Returns:
            bool: 删除是否成功
        """
        message = self.get_message_by_id(message_id)
        if not message:
            return False
        
        try:
            self.db.delete(message)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False
