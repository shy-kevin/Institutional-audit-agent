"""
审查相关数据模型
"""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Boolean, JSON
from db.mysql_session import Base


class AuditType(enum.Enum):
    DRAFT = "draft"
    REVISION = "revision"
    CURRENT = "current"


class TaskStatus(enum.Enum):
    PENDING = "pending"
    PARSING = "parsing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class RiskLevel(enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssueType(enum.Enum):
    COMPLIANCE = "compliance"
    CONSISTENCY = "consistency"
    FORMAT = "format"


class IssueStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PARTIAL_ACCEPTED = "partial_accepted"


class ResultStatus(enum.Enum):
    PENDING_REVIEW = "pending_review"
    REVIEWING = "reviewing"
    COMPLETED = "completed"


class ChecklistCategory(enum.Enum):
    GENERAL = "general"
    SPECIAL = "special"
    SCENARIO = "scenario"


class AuditTask(Base):
    __tablename__ = "audit_tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_name = Column(String(255), nullable=False, comment="文档名称")
    document_path = Column(String(500), nullable=False, comment="文档路径")
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, comment="任务状态")
    audit_type = Column(Enum(AuditType), default=AuditType.DRAFT, comment="审查类型")
    progress = Column(Integer, default=0, comment="进度百分比")
    config_id = Column(Integer, ForeignKey("audit_configs.id"), nullable=True, comment="审查配置ID")
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True, comment="关联对话ID")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    completed_at = Column(DateTime, nullable=True, comment="完成时间")


class AuditConfig(Base):
    __tablename__ = "audit_configs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment="配置名称")
    audit_dimensions = Column(JSON, comment="审查维度列表")
    focus_keywords = Column(JSON, comment="关注关键词列表")
    checklist_ids = Column(JSON, comment="审查清单ID列表")
    is_default = Column(Boolean, default=False, comment="是否默认配置")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class AuditChecklist(Base):
    __tablename__ = "audit_checklists"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment="清单名称")
    category = Column(Enum(ChecklistCategory), default=ChecklistCategory.GENERAL, comment="清单分类")
    items = Column(JSON, comment="清单项列表")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class AuditResult(Base):
    __tablename__ = "audit_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("audit_tasks.id"), nullable=False, comment="任务ID")
    document_name = Column(String(255), nullable=False, comment="文档名称")
    risk_level = Column(Enum(RiskLevel), nullable=True, comment="风险等级")
    total_issues = Column(Integer, default=0, comment="问题总数")
    compliance_issues = Column(Integer, default=0, comment="合规性问题数")
    consistency_issues = Column(Integer, default=0, comment="一致性问题数")
    format_issues = Column(Integer, default=0, comment="形式问题数")
    status = Column(Enum(ResultStatus), default=ResultStatus.PENDING_REVIEW, comment="结果状态")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class AuditIssue(Base):
    __tablename__ = "audit_issues"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    result_id = Column(Integer, ForeignKey("audit_results.id"), nullable=False, comment="结果ID")
    issue_type = Column(Enum(IssueType), nullable=False, comment="问题类型")
    severity = Column(Enum(RiskLevel), default=RiskLevel.MEDIUM, comment="严重程度")
    location = Column(String(255), comment="问题位置")
    original_text = Column(Text, comment="原文内容")
    issue_description = Column(Text, comment="问题描述")
    legal_basis = Column(Text, comment="法律依据")
    suggestion = Column(Text, comment="修改建议")
    status = Column(Enum(IssueStatus), default=IssueStatus.PENDING, comment="问题状态")
    reject_reason = Column(Text, comment="拒绝原因")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class AuditTrail(Base):
    __tablename__ = "audit_trails"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("audit_tasks.id"), nullable=False, comment="任务ID")
    action = Column(String(255), nullable=False, comment="操作动作")
    actor = Column(String(100), comment="操作人")
    details = Column(Text, comment="操作详情")
    created_at = Column(DateTime, default=datetime.now)


class VersionCompareTask(Base):
    __tablename__ = "version_compare_tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    old_document_path = Column(String(500), nullable=False, comment="旧文档路径")
    new_document_path = Column(String(500), nullable=False, comment="新文档路径")
    old_document_name = Column(String(255), comment="旧文档名称")
    new_document_name = Column(String(255), comment="新文档名称")
    config_id = Column(Integer, ForeignKey("audit_configs.id"), nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    additions = Column(JSON, comment="新增内容列表")
    deletions = Column(JSON, comment="删除内容列表")
    modifications = Column(JSON, comment="修改内容列表")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
