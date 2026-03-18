"""
消息服务模块
提供消息的CRUD操作
"""

from typing import List, Optional
import json
from sqlalchemy.orm import Session
from models.message import Message
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


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
        logger.debug("消息服务初始化完成")
    
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
        logger.debug(f"创建消息 - 对话ID: {conversation_id}, 角色: {role}")
        
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
        
        logger.info(f"消息创建成功 - ID: {message.id}, 对话ID: {conversation_id}")
        return message
    
    def get_message_by_id(self, message_id: int) -> Optional[Message]:
        """
        根据ID获取消息
        
        Args:
            message_id: 消息ID
        
        Returns:
            Optional[Message]: 消息对象，不存在则返回None
        """
        logger.debug(f"查询消息 - ID: {message_id}")
        
        result = self.db.query(Message).filter(
            Message.id == message_id
        ).first()
        
        if result:
            logger.debug(f"消息查询成功 - ID: {message_id}")
        else:
            logger.debug(f"消息不存在 - ID: {message_id}")
        
        return result
    
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
        logger.debug(f"查询对话消息列表 - 对话ID: {conversation_id}, limit: {limit}")
        
        if limit is None:
            limit = settings.MAX_HISTORY_LENGTH
        
        messages = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            Message.created_at.asc()
        ).limit(limit).all()
        
        logger.info(f"对话消息列表查询成功 - 对话ID: {conversation_id}, 消息数: {len(messages)}")
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
        logger.debug(f"获取对话历史记录 - 对话ID: {conversation_id}")
        
        messages = self.get_messages_by_conversation_id(conversation_id, limit)
        
        history = [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in messages
        ]
        
        logger.debug(f"对话历史记录格式化完成 - 对话ID: {conversation_id}, 记录数: {len(history)}")
        return history
    
    def delete_messages_by_conversation_id(self, conversation_id: int) -> bool:
        """
        删除对话的所有消息
        
        Args:
            conversation_id: 对话ID
        
        Returns:
            bool: 删除是否成功
        """
        logger.info(f"删除对话的所有消息 - 对话ID: {conversation_id}")
        
        try:
            count = self.db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).delete()
            self.db.commit()
            
            logger.info(f"对话消息删除成功 - 对话ID: {conversation_id}, 删除数: {count}")
            return True
        except Exception as e:
            logger.error(f"对话消息删除失败 - 对话ID: {conversation_id}, 错误: {str(e)}", exc_info=True)
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
        logger.info(f"删除消息 - ID: {message_id}")
        
        message = self.get_message_by_id(message_id)
        if not message:
            logger.error(f"消息不存在 - ID: {message_id}")
            return False
        
        try:
            self.db.delete(message)
            self.db.commit()
            
            logger.info(f"消息删除成功 - ID: {message_id}")
            return True
        except Exception as e:
            logger.error(f"消息删除失败 - ID: {message_id}, 错误: {str(e)}", exc_info=True)
            self.db.rollback()
            return False
