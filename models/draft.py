"""
智能编制助手数据模型
包含草稿文档、模板、权限、关联关系、参考资料等实体
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Float, Enum as SQLEnum
from db.mysql_session import Base
import enum


class DocumentStatus(str, enum.Enum):
    DRAFTING = "drafting"
    PENDING_REVIEW = "pending_review"
    PUBLISHED = "published"
    NEEDS_REVISION = "needs_revision"
    ARCHIVED = "archived"


class DraftSessionStatus(str, enum.Enum):
    INITIALIZED = "initialized"
    COLLECTING_DATA = "collecting_data"
    GENERATING = "generating"
    OUTLINE_READY = "outline_ready"
    GENERATION_FAILED = "generation_failed"
    EDITING = "editing"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class RelationType(str, enum.Enum):
    LEGAL_BASIS = "legal_basis"
    SUPERIOR_REGULATION = "superior_regulation"
    SUBORDINATE = "subordinate"
    RELATED = "related"


class MaterialType(str, enum.Enum):
    REFERENCE = "reference"
    OLD_VERSION = "old_version"
    REGULATION = "regulation"
    OTHER = "other"


class DraftDocument(Base):
    """
    制度文档表
    存储制度文档的基本信息和内容
    """
    __tablename__ = "draft_documents"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="文档ID")
    name = Column(String(200), nullable=False, comment="制度名称")
    type = Column(String(100), nullable=True, comment="制度类型")
    status = Column(String(30), default=DocumentStatus.DRAFTING.value, comment="状态")
    author = Column(String(100), nullable=True, comment="起草人姓名")
    creator_id = Column(Integer, nullable=True, comment="创建者用户ID")
    content = Column(Text, nullable=True, comment="文档内容(Markdown)")
    content_format = Column(String(20), default="markdown", comment="内容格式")
    version = Column(Integer, default=1, comment="版本号")
    word_count = Column(Integer, default=0, comment="字数")
    last_edited_chapter = Column(String(200), nullable=True, comment="最后编辑章节")
    session_id = Column(String(100), nullable=True, comment="关联的草稿会话ID")
    priority = Column(String(20), default="normal", comment="优先级")
    review_deadline = Column(DateTime, nullable=True, comment="审核截止时间")
    submission_note = Column(Text, nullable=True, comment="提交说明")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "status": self.status,
            "author": self.author,
            "creator_id": self.creator_id,
            "version": self.version,
            "word_count": self.word_count,
            "session_id": self.session_id,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M") if self.updated_at else None,
        }


class DocumentTemplate(Base):
    """
    制度模板表
    存储系统预定义和用户自定义的制度模板
    """
    __tablename__ = "document_templates"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="模板ID")
    name = Column(String(200), nullable=False, comment="模板名称")
    type = Column(String(100), nullable=True, comment="模板所属领域分类")
    category = Column(String(100), nullable=True, comment="模板类别")
    description = Column(Text, nullable=True, comment="模板详细描述")
    icon = Column(String(50), nullable=True, comment="模板图标")
    version = Column(String(20), default="1.0", comment="模板版本号")
    usage_count = Column(Integer, default=0, comment="使用次数")
    content_structure = Column(JSON, nullable=True, comment="内容章节结构")
    sample_content = Column(Text, nullable=True, comment="示例内容(Markdown)")
    related_templates = Column(JSON, nullable=True, comment="相关模板ID列表")
    tags = Column(JSON, nullable=True, comment="标签列表")
    preview_url = Column(String(500), nullable=True, comment="预览内容URL")
    file_path = Column(String(500), nullable=True, comment="自定义模板文件路径")
    is_custom = Column(Boolean, default=False, comment="是否自定义模板")
    creator_id = Column(Integer, nullable=True, comment="创建者用户ID(自定义模板)")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "category": self.category,
            "description": self.description,
            "icon": self.icon,
            "version": self.version,
            "usage_count": self.usage_count,
            "preview_url": self.preview_url,
            "content_structure": self.content_structure,
            "sample_content": self.sample_content,
            "related_templates": self.related_templates,
            "tags": self.tags,
            "is_custom": self.is_custom,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class DocumentPermission(Base):
    """
    文档权限表
    存储用户对文档的访问权限
    """
    __tablename__ = "document_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="权限ID")
    doc_id = Column(Integer, nullable=False, index=True, comment="文档ID")
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")
    can_view = Column(Boolean, default=False, comment="是否可查看")
    can_edit = Column(Boolean, default=False, comment="是否可编辑")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "doc_id": self.doc_id,
            "user_id": self.user_id,
            "can_view": self.can_view,
            "can_edit": self.can_edit,
        }


class DocumentRelation(Base):
    """
    文档关联关系表
    存储制度文档之间的上下位关系
    """
    __tablename__ = "document_relations"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="关系ID")
    doc_id = Column(String(100), nullable=False, index=True, comment="当前文档ID")
    related_doc_id = Column(String(100), nullable=False, comment="关联文档ID")
    related_doc_name = Column(String(300), nullable=True, comment="关联文档名称")
    relation_type = Column(String(50), nullable=False, comment="关系类型")
    direction = Column(String(20), nullable=False, comment="方向: upper/lower")
    notes = Column(Text, nullable=True, comment="关系备注")
    workflow_notes = Column(Text, nullable=True, comment="整体工作流说明")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "doc_id": self.doc_id,
            "related_doc_id": self.related_doc_id,
            "related_doc_name": self.related_doc_name,
            "relation_type": self.relation_type,
            "direction": self.direction,
            "notes": self.notes,
        }


class DraftSession(Base):
    """
    草稿会话表
    存储制度编制的会话信息，贯穿整个编制流程
    """
    __tablename__ = "draft_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="会话自增ID")
    session_id = Column(String(100), unique=True, nullable=False, comment="会话ID")
    template_id = Column(Integer, nullable=True, comment="选择的模板ID")
    template_name = Column(String(200), nullable=True, comment="模板名称")
    document_type = Column(String(100), nullable=True, comment="制度类型分类")
    custom_name = Column(String(200), nullable=True, comment="自定义制度名称")
    creator_id = Column(Integer, nullable=False, comment="创建者用户ID")
    status = Column(String(30), default=DraftSessionStatus.INITIALIZED.value, comment="会话状态")
    outline_content = Column(Text, nullable=True, comment="生成的大纲内容(Markdown)")
    outline_id = Column(String(100), nullable=True, comment="大纲ID")
    draft_content = Column(Text, nullable=True, comment="编辑中的草稿内容(Markdown)")
    requirements = Column(Text, nullable=True, comment="需求说明")
    additional_notes = Column(Text, nullable=True, comment="补充备注")
    special_constraints = Column(JSON, nullable=True, comment="特殊约束条件列表")
    workflow_notes = Column(Text, nullable=True, comment="工作流说明")
    document_id = Column(Integer, nullable=True, comment="关联的文档ID")
    version = Column(Integer, default=1, comment="草稿版本号")
    word_count = Column(Integer, default=0, comment="字数")
    expires_at = Column(DateTime, nullable=True, comment="过期时间")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "template_id": self.template_id,
            "template_name": self.template_name,
            "document_type": self.document_type,
            "custom_name": self.custom_name,
            "creator_id": self.creator_id,
            "status": self.status,
            "outline_id": self.outline_id,
            "document_id": self.document_id,
            "version": self.version,
            "word_count": self.word_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class DraftMaterial(Base):
    """
    草稿参考资料表
    存储上传的参考文档、旧版本文件等
    """
    __tablename__ = "draft_materials"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="材料ID")
    session_id = Column(String(100), nullable=False, index=True, comment="草稿会话ID")
    file_id = Column(String(100), nullable=True, comment="文件唯一标识")
    file_name = Column(String(300), nullable=False, comment="文件名")
    file_path = Column(String(500), nullable=False, comment="文件存储路径")
    file_size = Column(Integer, nullable=True, comment="文件大小(字节)")
    file_type = Column(String(20), nullable=True, comment="文件类型")
    material_type = Column(String(30), default=MaterialType.REFERENCE.value, comment="材料类型")
    uploaded_at = Column(DateTime, default=datetime.now, comment="上传时间")

    def to_dict(self) -> dict:
        return {
            "file_id": self.file_id,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "file_path": self.file_path,
            "material_type": self.material_type,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }


class DraftAttachment(Base):
    """
    草稿附件表
    存储编辑器中上传的附件（图片、表格等）
    """
    __tablename__ = "draft_attachments"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="附件ID")
    session_id = Column(String(100), nullable=False, index=True, comment="草稿会话ID")
    attachment_id = Column(String(100), nullable=True, comment="附件唯一标识")
    file_name = Column(String(300), nullable=False, comment="文件名")
    file_path = Column(String(500), nullable=False, comment="文件存储路径")
    file_size = Column(Integer, nullable=True, comment="文件大小(字节)")
    file_type = Column(String(20), nullable=True, comment="文件类型")
    attachment_type = Column(String(30), nullable=True, comment="附件类型")
    file_url = Column(String(500), nullable=True, comment="文件访问URL")
    markdown_reference = Column(String(500), nullable=True, comment="Markdown引用语法")
    uploaded_at = Column(DateTime, default=datetime.now, comment="上传时间")

    def to_dict(self) -> dict:
        return {
            "attachment_id": self.attachment_id,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "file_url": self.file_url,
            "markdown_reference": self.markdown_reference,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }


class ComplianceCheck(Base):
    """
    合规检查结果表
    存储制度内容的合规检查结果
    """
    __tablename__ = "compliance_checks"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="检查ID")
    check_id = Column(String(100), nullable=True, comment="检查唯一标识")
    session_id = Column(String(100), nullable=False, index=True, comment="草稿会话ID")
    check_scope = Column(JSON, nullable=True, comment="检查范围")
    reference_documents = Column(JSON, nullable=True, comment="参考文档ID列表")
    overall_status = Column(String(20), nullable=True, comment="总体状态: pass/warning/fail")
    summary = Column(JSON, nullable=True, comment="检查摘要统计")
    issues = Column(JSON, nullable=True, comment="问题列表")
    passed_checks = Column(JSON, nullable=True, comment="通过的检查项")
    checked_at = Column(DateTime, default=datetime.now, comment="检查时间")

    def to_dict(self) -> dict:
        return {
            "check_id": self.check_id,
            "session_id": self.session_id,
            "check_scope": self.check_scope,
            "overall_status": self.overall_status,
            "summary": self.summary,
            "issues": self.issues,
            "passed_checks": self.passed_checks,
            "checked_at": self.checked_at.isoformat() if self.checked_at else None,
        }
