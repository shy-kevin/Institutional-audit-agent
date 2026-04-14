"""
模板实体类
用于存储制度模板信息
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from db.mysql_session import Base


class Template(Base):
    """
    模板实体类
    存储制度模板的基本信息、格式设置和元数据
    
    Attributes:
        id: 模板唯一标识
        name: 模板名称
        category: 模板分类
        description: 模板描述
        format: 格式设置（JSON格式）
        creator_id: 创建者用户ID
        creator_name: 创建者姓名
        created_at: 创建时间
        updated_at: 更新时间
        is_public: 是否公开模板
        usage_count: 使用次数
        tags: 标签列表（JSON格式）
        is_deleted: 是否已删除（软删除）
        deleted_at: 删除时间
    """
    
    __tablename__ = "templates"
    
    id = Column(String(50), primary_key=True, comment="模板唯一标识")
    name = Column(String(100), nullable=False, comment="模板名称")
    category = Column(String(50), nullable=False, comment="模板分类")
    description = Column(Text, nullable=True, comment="模板描述")
    format = Column(JSON, nullable=False, comment="格式设置（JSON格式）")
    creator_id = Column(Integer, nullable=False, comment="创建者用户ID")
    creator_name = Column(String(100), nullable=False, comment="创建者姓名")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    is_public = Column(Boolean, default=False, comment="是否公开模板")
    usage_count = Column(Integer, default=0, comment="使用次数")
    tags = Column(JSON, nullable=True, comment="标签列表（JSON格式）")
    is_deleted = Column(Boolean, default=False, comment="是否已删除（软删除）")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")
    
    sections = relationship("TemplateSection", back_populates="template", cascade="all, delete-orphan")
    
    def to_dict(self) -> dict:
        """
        将实体转换为字典格式
        
        Returns:
            dict: 包含实体属性的字典
        """
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "format": self.format,
            "sections": [section.to_dict() for section in self.sections] if self.sections else [],
            "creator_id": self.creator_id,
            "creator_name": self.creator_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_public": self.is_public,
            "usage_count": self.usage_count,
            "tags": self.tags or []
        }


class TemplateSection(Base):
    """
    模板章节实体类
    存储模板的章节结构
    
    Attributes:
        id: 章节唯一标识
        template_id: 所属模板ID
        parent_id: 父章节ID（用于构建层级结构）
        level: 层级（1=一级标题/章，2=二级标题/条）
        title: 章节标题
        description: 章节描述
        sort_order: 排序顺序
    """
    
    __tablename__ = "template_sections"
    
    id = Column(String(50), primary_key=True, comment="章节唯一标识")
    template_id = Column(String(50), ForeignKey("templates.id", ondelete="CASCADE"), nullable=False, comment="所属模板ID")
    parent_id = Column(String(50), ForeignKey("template_sections.id", ondelete="CASCADE"), nullable=True, comment="父章节ID")
    level = Column(Integer, nullable=False, comment="层级：1=章，2=条")
    title = Column(String(200), nullable=False, comment="章节标题")
    description = Column(Text, nullable=True, comment="章节描述")
    sort_order = Column(Integer, nullable=False, default=0, comment="排序顺序")
    
    template = relationship("Template", back_populates="sections")
    children = relationship("TemplateSection", backref="parent", remote_side=[id], cascade="all, delete-orphan", single_parent=True)
    
    def to_dict(self) -> dict:
        """
        将实体转换为字典格式
        
        Returns:
            dict: 包含实体属性的字典
        """
        return {
            "id": self.id,
            "level": self.level,
            "title": self.title,
            "description": self.description,
            "children": [child.to_dict() for child in self.children] if self.children else []
        }
