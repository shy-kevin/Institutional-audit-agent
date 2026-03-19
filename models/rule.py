"""
规则实体类
用于存储规章、规则信息
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum
from db.mysql_session import Base
import enum


class RuleType(enum.Enum):
    """
    规则类型枚举
    """
    CONVERSATION = "conversation"  # 对话规则
    GLOBAL = "global"              # 全局规则


class Rule(Base):
    """
    规则实体类
    存储规章、规则信息，支持对话规则和全局规则
    
    Attributes:
        id: 规则唯一标识
        title: 规则标题
        content: 规则内容
        rule_type: 规则类型（conversation/global）
        conversation_id: 关联的对话ID（仅对话规则有效）
        category: 规则分类（如：审计规则、合规规则等）
        priority: 优先级（数字越大优先级越高）
        is_active: 是否启用
        created_at: 创建时间
        updated_at: 更新时间
    """
    
    __tablename__ = "rules"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="规则ID")
    title = Column(String(255), nullable=False, comment="规则标题")
    content = Column(Text, nullable=False, comment="规则内容")
    rule_type = Column(
        Enum(RuleType),
        nullable=False,
        default=RuleType.GLOBAL,
        comment="规则类型：conversation-对话规则，global-全局规则"
    )
    conversation_id = Column(Integer, nullable=True, comment="关联的对话ID（仅对话规则有效）")
    category = Column(String(100), nullable=True, comment="规则分类")
    priority = Column(Integer, default=0, comment="优先级（数字越大优先级越高）")
    is_active = Column(Integer, default=1, comment="是否启用：1-启用，0-禁用")
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
            "content": self.content,
            "rule_type": self.rule_type.value if self.rule_type else None,
            "conversation_id": self.conversation_id,
            "category": self.category,
            "priority": self.priority,
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
