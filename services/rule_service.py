"""
规则服务模块
提供规则的CRUD操作
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models.rule import Rule, RuleType
from utils.logger import setup_logger

logger = setup_logger(__name__)


class RuleService:
    """
    规则服务类
    
    提供规则的创建、查询、更新、删除等操作
    
    Attributes:
        db: 数据库会话
    """
    
    def __init__(self, db: Session):
        """
        初始化规则服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        logger.debug("规则服务初始化完成")
    
    def create_rule(
        self,
        title: str,
        content: str,
        rule_type: str = "global",
        conversation_id: Optional[int] = None,
        category: Optional[str] = None,
        priority: int = 0
    ) -> Rule:
        """
        创建规则
        
        Args:
            title: 规则标题
            content: 规则内容
            rule_type: 规则类型（conversation/global）
            conversation_id: 关联的对话ID（仅对话规则有效）
            category: 规则分类
            priority: 优先级
        
        Returns:
            Rule: 创建的规则对象
        """
        logger.info(f"创建规则 - 标题: {title}, 类型: {rule_type}")
        
        rule_type_enum = RuleType.CONVERSATION if rule_type == "conversation" else RuleType.GLOBAL
        
        rule = Rule(
            title=title,
            content=content,
            rule_type=rule_type_enum,
            conversation_id=conversation_id if rule_type == "conversation" else None,
            category=category,
            priority=priority,
            is_active=1
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        
        logger.info(f"规则创建成功 - ID: {rule.id}")
        return rule
    
    def get_rule_by_id(self, rule_id: int) -> Optional[Rule]:
        """
        根据ID获取规则
        
        Args:
            rule_id: 规则ID
        
        Returns:
            Optional[Rule]: 规则对象，不存在则返回None
        """
        logger.debug(f"查询规则 - ID: {rule_id}")
        
        result = self.db.query(Rule).filter(Rule.id == rule_id).first()
        
        if result:
            logger.debug(f"规则查询成功 - ID: {rule_id}")
        else:
            logger.debug(f"规则不存在 - ID: {rule_id}")
        
        return result
    
    def get_all_rules(
        self,
        skip: int = 0,
        limit: int = 100,
        rule_type: Optional[str] = None,
        conversation_id: Optional[int] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> tuple[List[Rule], int]:
        """
        获取规则列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            rule_type: 按规则类型筛选
            conversation_id: 按对话ID筛选
            category: 按分类筛选
            is_active: 按启用状态筛选
        
        Returns:
            tuple[List[Rule], int]: (规则列表, 总数)
        """
        logger.debug(f"查询规则列表 - skip: {skip}, limit: {limit}, type: {rule_type}")
        
        query = self.db.query(Rule)
        
        if rule_type:
            rule_type_enum = RuleType.CONVERSATION if rule_type == "conversation" else RuleType.GLOBAL
            query = query.filter(Rule.rule_type == rule_type_enum)
        
        if conversation_id is not None:
            query = query.filter(Rule.conversation_id == conversation_id)
        
        if category:
            query = query.filter(Rule.category == category)
        
        if is_active is not None:
            query = query.filter(Rule.is_active == (1 if is_active else 0))
        
        total = query.count()
        rules = query.order_by(
            Rule.priority.desc(),
            Rule.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        logger.info(f"规则列表查询成功 - 总数: {total}, 返回: {len(rules)}")
        return rules, total
    
    def get_active_rules_for_conversation(
        self,
        conversation_id: Optional[int] = None
    ) -> List[Rule]:
        """
        获取对话的活跃规则（包括全局规则和对话规则）
        
        Args:
            conversation_id: 对话ID
        
        Returns:
            List[Rule]: 规则列表
        """
        logger.debug(f"获取对话的活跃规则 - 对话ID: {conversation_id}")
        
        query = self.db.query(Rule).filter(Rule.is_active == 1)
        
        if conversation_id:
            query = query.filter(
                (Rule.rule_type == RuleType.GLOBAL) |
                (Rule.conversation_id == conversation_id)
            )
        else:
            query = query.filter(Rule.rule_type == RuleType.GLOBAL)
        
        rules = query.order_by(
            Rule.priority.desc(),
            Rule.created_at.desc()
        ).all()
        
        logger.info(f"活跃规则查询成功 - 数量: {len(rules)}")
        return rules
    
    def update_rule(
        self,
        rule_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        rule_type: Optional[str] = None,
        conversation_id: Optional[int] = None,
        category: Optional[str] = None,
        priority: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Rule]:
        """
        更新规则
        
        Args:
            rule_id: 规则ID
            title: 新标题
            content: 新内容
            rule_type: 新类型
            conversation_id: 新对话ID
            category: 新分类
            priority: 新优先级
            is_active: 新启用状态
        
        Returns:
            Optional[Rule]: 更新后的规则对象
        """
        logger.info(f"更新规则 - ID: {rule_id}")
        
        rule = self.get_rule_by_id(rule_id)
        if not rule:
            logger.error(f"规则不存在 - ID: {rule_id}")
            return None
        
        if title is not None:
            rule.title = title
        if content is not None:
            rule.content = content
        if rule_type is not None:
            rule.rule_type = RuleType.CONVERSATION if rule_type == "conversation" else RuleType.GLOBAL
        if conversation_id is not None:
            rule.conversation_id = conversation_id if rule.rule_type == RuleType.CONVERSATION else None
        if category is not None:
            rule.category = category
        if priority is not None:
            rule.priority = priority
        if is_active is not None:
            rule.is_active = 1 if is_active else 0
        
        self.db.commit()
        self.db.refresh(rule)
        
        logger.info(f"规则更新成功 - ID: {rule_id}")
        return rule
    
    def delete_rule(self, rule_id: int) -> bool:
        """
        删除规则
        
        Args:
            rule_id: 规则ID
        
        Returns:
            bool: 删除是否成功
        """
        logger.info(f"删除规则 - ID: {rule_id}")
        
        rule = self.get_rule_by_id(rule_id)
        if not rule:
            logger.error(f"规则不存在 - ID: {rule_id}")
            return False
        
        try:
            self.db.delete(rule)
            self.db.commit()
            
            logger.info(f"规则删除成功 - ID: {rule_id}")
            return True
        except Exception as e:
            logger.error(f"规则删除失败 - ID: {rule_id}, 错误: {str(e)}", exc_info=True)
            self.db.rollback()
            return False
    
    def batch_create_rules(
        self,
        rules_data: List[dict],
        conversation_id: Optional[int] = None
    ) -> List[Rule]:
        """
        批量创建规则
        
        Args:
            rules_data: 规则数据列表
            conversation_id: 对话ID
        
        Returns:
            List[Rule]: 创建的规则列表
        """
        logger.info(f"批量创建规则 - 数量: {len(rules_data)}")
        
        created_rules = []
        for rule_data in rules_data:
            rule = self.create_rule(
                title=rule_data.get("title"),
                content=rule_data.get("content"),
                rule_type=rule_data.get("rule_type", "global"),
                conversation_id=conversation_id or rule_data.get("conversation_id"),
                category=rule_data.get("category"),
                priority=rule_data.get("priority", 0)
            )
            created_rules.append(rule)
        
        logger.info(f"批量创建规则成功 - 数量: {len(created_rules)}")
        return created_rules
    
    def toggle_rule_status(self, rule_id: int) -> Optional[Rule]:
        """
        切换规则启用状态
        
        Args:
            rule_id: 规则ID
        
        Returns:
            Optional[Rule]: 更新后的规则对象
        """
        logger.info(f"切换规则状态 - ID: {rule_id}")
        
        rule = self.get_rule_by_id(rule_id)
        if not rule:
            logger.error(f"规则不存在 - ID: {rule_id}")
            return None
        
        rule.is_active = 0 if rule.is_active else 1
        self.db.commit()
        self.db.refresh(rule)
        
        logger.info(f"规则状态切换成功 - ID: {rule_id}, 新状态: {'启用' if rule.is_active else '禁用'}")
        return rule
