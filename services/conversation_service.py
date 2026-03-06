"""
对话服务模块
提供对话的CRUD操作
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from models.conversation import Conversation


class ConversationService:
    """
    对话服务类
    
    提供对话的创建、查询、更新、删除等操作
    
    Attributes:
        db: 数据库会话
    """
    
    def __init__(self, db: Session):
        """
        初始化对话服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def create_conversation(
        self,
        title: str = "新对话",
        description: Optional[str] = None
    ) -> Conversation:
        """
        创建新对话
        
        Args:
            title: 对话标题
            description: 对话描述
        
        Returns:
            Conversation: 创建的对话对象
        """
        conversation = Conversation(
            title=title,
            description=description
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        
        return conversation
    
    def get_conversation_by_id(self, conversation_id: int) -> Optional[Conversation]:
        """
        根据ID获取对话
        
        Args:
            conversation_id: 对话ID
        
        Returns:
            Optional[Conversation]: 对话对象，不存在则返回None
        """
        return self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
    
    def get_all_conversations(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> tuple[List[Conversation], int]:
        """
        获取所有对话列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            status: 按状态筛选
        
        Returns:
            tuple[List[Conversation], int]: (对话列表, 总数)
        """
        query = self.db.query(Conversation)
        
        if status:
            query = query.filter(Conversation.status == status)
        
        total = query.count()
        conversations = query.order_by(
            Conversation.updated_at.desc()
        ).offset(skip).limit(limit).all()
        
        return conversations, total
    
    def update_conversation(
        self,
        conversation_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[Conversation]:
        """
        更新对话信息
        
        Args:
            conversation_id: 对话ID
            title: 新标题
            description: 新描述
        
        Returns:
            Optional[Conversation]: 更新后的对话对象
        """
        conversation = self.get_conversation_by_id(conversation_id)
        if not conversation:
            return None
        
        if title is not None:
            conversation.title = title
        if description is not None:
            conversation.description = description
        
        self.db.commit()
        self.db.refresh(conversation)
        return conversation
    
    def delete_conversation(self, conversation_id: int) -> bool:
        """
        删除对话
        
        Args:
            conversation_id: 对话ID
        
        Returns:
            bool: 删除是否成功
        """
        conversation = self.get_conversation_by_id(conversation_id)
        if not conversation:
            return False
        
        try:
            self.db.delete(conversation)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False
    
    def archive_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """
        归档对话
        
        Args:
            conversation_id: 对话ID
        
        Returns:
            Optional[Conversation]: 更新后的对话对象
        """
        conversation = self.get_conversation_by_id(conversation_id)
        if not conversation:
            return None
        
        conversation.status = "archived"
        self.db.commit()
        self.db.refresh(conversation)
        return conversation
