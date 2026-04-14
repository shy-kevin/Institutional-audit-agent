"""
智能编制助手服务层
处理制度文档、模板、草稿会话、关联关系等业务逻辑
"""

import os
import uuid
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from models.draft import (
    DraftDocument, DocumentTemplate, DocumentPermission,
    DocumentRelation, DraftSession, DraftMaterial, DraftAttachment,
    ComplianceCheck, DocumentStatus, DraftSessionStatus, MaterialType
)
from models.user import User
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DraftService:
    """
    智能编制助手服务
    """

    def __init__(self, db: Session):
        self.db = db

    # ==================== 文档统计 ====================

    def get_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        获取文档统计数据

        业务逻辑：
        1. 统计用户可见文档的总数
        2. 按状态分类统计
        3. 计算本周新增和本月完成数
        """
        base_query = self.db.query(DraftDocument).filter(
            DraftDocument.creator_id == user_id
        )

        total = base_query.count()
        drafting_count = base_query.filter(
            DraftDocument.status == DocumentStatus.DRAFTING.value
        ).count()
        completed_count = base_query.filter(
            DraftDocument.status == DocumentStatus.PUBLISHED.value
        ).count()
        archived_count = base_query.filter(
            DraftDocument.status == DocumentStatus.ARCHIVED.value
        ).count()
        pending_review_count = base_query.filter(
            DraftDocument.status == DocumentStatus.PENDING_REVIEW.value
        ).count()

        now = datetime.now()
        week_start = now - timedelta(days=now.weekday())
        month_start = now.replace(day=1)

        drafting_week_new = base_query.filter(
            DraftDocument.status == DocumentStatus.DRAFTING.value,
            DraftDocument.created_at >= week_start
        ).count()

        completed_month_count = base_query.filter(
            DraftDocument.status == DocumentStatus.PUBLISHED.value,
            DraftDocument.updated_at >= month_start
        ).count()

        return {
            "total": total,
            "drafting_count": drafting_count,
            "drafting_week_new": drafting_week_new,
            "completed_count": completed_count,
            "completed_month_count": completed_month_count,
            "archived_count": archived_count,
            "pending_review_count": pending_review_count
        }

    # ==================== 文档列表 ====================

    def get_document_list(
        self,
        user_id: int,
        keyword: str = "",
        status: Optional[str] = None,
        doc_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        获取文档列表

        业务逻辑：
        1. 查询用户创建的文档 + 用户有权限查看的文档
        2. 支持关键词搜索（匹配名称）
        3. 支持状态和类型筛选
        4. 分页返回
        """
        query = self.db.query(DraftDocument).filter(
            DraftDocument.creator_id == user_id
        )

        perm_doc_ids = self.db.query(DocumentPermission.doc_id).filter(
            DocumentPermission.user_id == user_id,
            DocumentPermission.can_view == True
        ).subquery()

        query = self.db.query(DraftDocument).filter(
            (DraftDocument.creator_id == user_id) |
            (DraftDocument.id.in_(perm_doc_ids))
        )

        if keyword:
            query = query.filter(DraftDocument.name.like(f"%{keyword}%"))
        if status:
            query = query.filter(DraftDocument.status == status)
        if doc_type:
            query = query.filter(DraftDocument.type == doc_type)

        total = query.count()
        items = query.order_by(DraftDocument.updated_at.desc()).offset(skip).limit(limit).all()

        return {
            "total": total,
            "items": [item.to_dict() for item in items]
        }

    # ==================== 文档权限 ====================

    def get_available_users(
        self,
        doc_id: int,
        keyword: str = ""
    ) -> Dict[str, Any]:
        """
        获取可授权用户列表

        业务逻辑：
        1. 查询所有活跃用户
        2. 关联查询已有权限
        3. 支持关键词搜索
        """
        query = self.db.query(User).filter(User.is_active == True)

        if keyword:
            query = query.filter(
                (User.username.like(f"%{keyword}%")) |
                (User.department.like(f"%{keyword}%"))
            )

        users = query.all()

        existing_perms = self.db.query(DocumentPermission).filter(
            DocumentPermission.doc_id == doc_id
        ).all()
        perm_map = {p.user_id: p for p in existing_perms}

        items = []
        for user in users:
            perm = perm_map.get(user.id)
            items.append({
                "id": user.id,
                "username": user.username,
                "department": user.department,
                "role": user.role,
                "can_view": perm.can_view if perm else False,
                "can_edit": perm.can_edit if perm else False
            })

        return {
            "total": len(items),
            "items": items
        }

    def set_permissions(
        self,
        doc_id: int,
        user_permissions: List[Dict]
    ) -> Dict[str, Any]:
        """
        批量设置文档权限

        业务逻辑：
        1. 遍历权限列表
        2. 已有权限则更新，否则创建
        3. 返回受影响用户数
        """
        affected = 0
        for perm_data in user_permissions:
            user_id = perm_data.get("user_id")
            can_view = perm_data.get("can_view", False)
            can_edit = perm_data.get("can_edit", False)

            existing = self.db.query(DocumentPermission).filter(
                DocumentPermission.doc_id == doc_id,
                DocumentPermission.user_id == user_id
            ).first()

            if existing:
                existing.can_view = can_view
                existing.can_edit = can_edit
            else:
                new_perm = DocumentPermission(
                    doc_id=doc_id,
                    user_id=user_id,
                    can_view=can_view,
                    can_edit=can_edit
                )
                self.db.add(new_perm)
            affected += 1

        self.db.commit()
        return {
            "success": True,
            "message": "权限设置成功",
            "affected_users": affected
        }

    # ==================== 模板管理 ====================

    def get_template_list(
        self,
        template_type: Optional[str] = None,
        keyword: str = "",
        skip: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        获取模板列表

        业务逻辑：
        1. 查询所有模板（系统预定义 + 自定义）
        2. 支持类型筛选和关键词搜索
        3. 分页返回
        """
        query = self.db.query(DocumentTemplate)

        if template_type:
            query = query.filter(DocumentTemplate.category == template_type)
        if keyword:
            query = query.filter(
                (DocumentTemplate.name.like(f"%{keyword}%")) |
                (DocumentTemplate.description.like(f"%{keyword}%"))
            )

        total = query.count()
        items = query.order_by(DocumentTemplate.usage_count.desc()).offset(skip).limit(limit).all()

        return {
            "total": total,
            "items": [item.to_dict() for item in items]
        }

    def get_template_by_id(self, template_id: int) -> Optional[DocumentTemplate]:
        return self.db.query(DocumentTemplate).filter(DocumentTemplate.id == template_id).first()

    def create_custom_template(
        self,
        name: str,
        file_path: str,
        category: str = "自定义",
        description: str = "",
        creator_id: Optional[int] = None,
        content_structure: Optional[dict] = None
    ) -> DocumentTemplate:
        """
        创建自定义模板

        业务逻辑：
        1. 保存模板基本信息
        2. 如果有解析出的章节结构则保存
        """
        template = DocumentTemplate(
            name=name,
            category=category,
            description=description,
            file_path=file_path,
            is_custom=True,
            creator_id=creator_id,
            content_structure=content_structure,
            icon="📄"
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def increment_template_usage(self, template_id: int):
        template = self.get_template_by_id(template_id)
        if template:
            template.usage_count = (template.usage_count or 0) + 1
            self.db.commit()

    # ==================== 关联制度 ====================

    def search_upper_documents(
        self,
        keyword: str,
        document_type: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        搜索上位制度/法律依据

        业务逻辑：
        1. 在已有文档中搜索匹配关键词的已发布文档
        2. 同时搜索外部知识库
        3. 返回相关度排序的结果
        """
        query = self.db.query(DraftDocument).filter(
            DraftDocument.name.like(f"%{keyword}%"),
            DraftDocument.status == DocumentStatus.PUBLISHED.value
        )

        if document_type:
            query = query.filter(DraftDocument.type == document_type)

        docs = query.limit(limit).all()
        items = []
        for doc in docs:
            items.append({
                "id": f"doc_{doc.id}",
                "name": doc.name,
                "type": doc.type or "企业制度",
                "publish_date": doc.updated_at.strftime("%Y-%m-%d") if doc.updated_at else None,
                "effective_date": doc.completed_at.strftime("%Y-%m-%d") if doc.completed_at else None,
                "authority": doc.author or "",
                "summary": (doc.content[:200] if doc.content else ""),
                "relevance_score": 0.8,
                "related_articles": None
            })

        return {
            "total": len(items),
            "items": items
        }

    def search_lower_documents(
        self,
        keyword: str,
        parent_doc_type: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        搜索下位制度/执行手册

        业务逻辑：
        1. 搜索匹配关键词的文档
        2. 返回可作为下位制度的文档
        """
        query = self.db.query(DraftDocument).filter(
            DraftDocument.name.like(f"%{keyword}%")
        )

        docs = query.limit(limit).all()
        items = []
        for doc in docs:
            items.append({
                "id": f"doc_{doc.id}",
                "name": doc.name,
                "type": doc.type or "执行手册",
                "parent_document": "",
                "department": doc.author or "",
                "version": f"V{doc.version}" if doc.version else "V1.0",
                "status": doc.status,
                "summary": (doc.content[:200] if doc.content else "")
            })

        return {
            "total": len(items),
            "items": items
        }

    def save_document_relations(
        self,
        doc_id: str,
        upper_documents: List[Dict],
        lower_documents: List[Dict],
        workflow_notes: str = ""
    ) -> Dict[str, Any]:
        """
        保存制度关联关系

        业务逻辑：
        1. 先清除该文档的旧关联
        2. 批量插入新的关联关系
        3. 保存工作流说明
        """
        self.db.query(DocumentRelation).filter(
            DocumentRelation.doc_id == doc_id
        ).delete()

        for doc in upper_documents:
            relation = DocumentRelation(
                doc_id=doc_id,
                related_doc_id=doc.get("document_id", ""),
                related_doc_name=doc.get("document_name", ""),
                relation_type=doc.get("relation_type", "legal_basis"),
                direction="upper",
                notes=doc.get("notes", "")
            )
            self.db.add(relation)

        for doc in lower_documents:
            relation = DocumentRelation(
                doc_id=doc_id,
                related_doc_id=doc.get("document_id", ""),
                related_doc_name=doc.get("document_name", ""),
                relation_type=doc.get("relation_type", "subordinate"),
                direction="lower",
                notes=doc.get("notes", "")
            )
            self.db.add(relation)

        if workflow_notes:
            session = self.db.query(DraftSession).filter(
                DraftSession.session_id == doc_id
            ).first()
            if session:
                session.workflow_notes = workflow_notes

        self.db.commit()

        upper_count = len(upper_documents)
        lower_count = len(lower_documents)

        return {
            "success": True,
            "message": "关联关系保存成功",
            "saved_relations": {
                "upper_count": upper_count,
                "lower_count": lower_count
            }
        }

    def get_document_relations(self, doc_id: str) -> Dict[str, Any]:
        relations = self.db.query(DocumentRelation).filter(
            DocumentRelation.doc_id == doc_id
        ).all()

        upper_docs = []
        lower_docs = []
        for r in relations:
            data = r.to_dict()
            if r.direction == "upper":
                upper_docs.append(data)
            else:
                lower_docs.append(data)

        session = self.db.query(DraftSession).filter(
            DraftSession.session_id == doc_id
        ).first()

        return {
            "upper_documents": upper_docs,
            "lower_documents": lower_docs,
            "workflow_notes": session.workflow_notes if session else ""
        }

    # ==================== 草稿会话 ====================

    def create_session(
        self,
        template_id: int,
        template_name: str,
        document_type: str,
        creator_id: int,
        custom_name: str = ""
    ) -> DraftSession:
        """
        创建草稿会话

        业务逻辑：
        1. 生成唯一会话ID
        2. 创建会话记录
        3. 如果选择了模板，增加模板使用次数
        4. 同时创建关联的文档记录
        """
        session_id = f"draft_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"

        doc_name = custom_name if custom_name else template_name
        document = DraftDocument(
            name=doc_name,
            type=document_type,
            status=DocumentStatus.DRAFTING.value,
            creator_id=creator_id,
            session_id=session_id
        )
        self.db.add(document)
        self.db.flush()

        session = DraftSession(
            session_id=session_id,
            template_id=template_id if template_id != 0 else None,
            template_name=template_name,
            document_type=document_type,
            custom_name=custom_name,
            creator_id=creator_id,
            status=DraftSessionStatus.INITIALIZED.value,
            document_id=document.id,
            expires_at=datetime.now() + timedelta(days=7)
        )
        self.db.add(session)

        if template_id and template_id != 0:
            self.increment_template_usage(template_id)

        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: str) -> Optional[DraftSession]:
        return self.db.query(DraftSession).filter(
            DraftSession.session_id == session_id
        ).first()

    def update_session_status(self, session_id: str, status: str):
        session = self.get_session(session_id)
        if session:
            session.status = status
            self.db.commit()

    # ==================== 参考资料管理 ====================

    def upload_materials(
        self,
        session_id: str,
        files: List[Dict],
        material_type: str = "reference"
    ) -> Dict[str, Any]:
        """
        上传参考材料

        业务逻辑：
        1. 为每个文件创建材料记录
        2. 生成唯一文件ID
        3. 更新会话状态为收集数据中
        """
        uploaded = []
        for file_info in files:
            file_id = f"file_{uuid.uuid4().hex[:8]}"
            material = DraftMaterial(
                session_id=session_id,
                file_id=file_id,
                file_name=file_info.get("file_name", ""),
                file_path=file_info.get("file_path", ""),
                file_size=file_info.get("file_size", 0),
                file_type=file_info.get("file_type", ""),
                material_type=material_type
            )
            self.db.add(material)
            uploaded.append(material.to_dict())

        session = self.get_session(session_id)
        if session and session.status == DraftSessionStatus.INITIALIZED.value:
            session.status = DraftSessionStatus.COLLECTING_DATA.value

        self.db.commit()

        return {
            "success": True,
            "uploaded_files": uploaded,
            "total_files": len(uploaded)
        }

    def delete_material(self, session_id: str, file_id: str) -> bool:
        material = self.db.query(DraftMaterial).filter(
            DraftMaterial.session_id == session_id,
            DraftMaterial.file_id == file_id
        ).first()

        if not material:
            return False

        if material.file_path and os.path.exists(material.file_path):
            os.remove(material.file_path)

        self.db.delete(material)
        self.db.commit()
        return True

    def get_materials(self, session_id: str) -> List[Dict]:
        materials = self.db.query(DraftMaterial).filter(
            DraftMaterial.session_id == session_id
        ).all()
        return [m.to_dict() for m in materials]

    # ==================== 需求保存 ====================

    def save_requirements(
        self,
        session_id: str,
        requirements: str,
        additional_notes: str = "",
        special_constraints: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        保存需求和补充信息

        业务逻辑：
        1. 更新会话的需求字段
        2. 保存特殊约束条件
        """
        session = self.get_session(session_id)
        if not session:
            return {"success": False, "message": "会话不存在"}

        session.requirements = requirements
        session.additional_notes = additional_notes
        session.special_constraints = special_constraints

        if session.status == DraftSessionStatus.INITIALIZED.value:
            session.status = DraftSessionStatus.COLLECTING_DATA.value

        self.db.commit()

        return {
            "success": True,
            "message": "需求信息保存成功",
            "saved_at": datetime.now().isoformat()
        }

    # ==================== 大纲生成 ====================

    def save_outline(
        self,
        session_id: str,
        outline_content: str,
        outline_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        保存生成的大纲

        业务逻辑：
        1. 保存大纲内容到会话
        2. 更新会话状态为大纲就绪
        3. 同步更新关联文档的内容
        """
        session = self.get_session(session_id)
        if not session:
            return {"success": False, "message": "会话不存在"}

        if not outline_id:
            outline_id = f"outline_{uuid.uuid4().hex[:8]}"

        session.outline_content = outline_content
        session.outline_id = outline_id
        session.status = DraftSessionStatus.OUTLINE_READY.value

        if session.document_id:
            doc = self.db.query(DraftDocument).filter(
                DraftDocument.id == session.document_id
            ).first()
            if doc:
                doc.content = outline_content

        self.db.commit()

        return {
            "success": True,
            "outline_id": outline_id
        }

    def get_outline(
        self,
        session_id: str,
        format: str = "markdown"
    ) -> Dict[str, Any]:
        """
        获取已生成的大纲内容

        业务逻辑：
        1. 查询会话的大纲内容
        2. 根据format参数返回不同格式
        3. json格式时解析章节结构
        """
        session = self.get_session(session_id)
        if not session:
            return {}

        if format == "json":
            return self._parse_outline_to_json(session)
        else:
            return {
                "session_id": session_id,
                "outline_id": session.outline_id,
                "document_title": session.custom_name or session.template_name,
                "content": session.outline_content,
                "generated_at": session.updated_at.isoformat() if session.updated_at else None,
            }

    def _parse_outline_to_json(self, session: DraftSession) -> Dict[str, Any]:
        content = session.outline_content or ""
        chapters = []
        current_chapter = None

        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("## 第") and "章" in line:
                if current_chapter:
                    chapters.append(current_chapter)
                parts = line.replace("## ", "").split(" ", 1)
                chapter_number = parts[0] if parts else ""
                chapter_title = parts[1] if len(parts) > 1 else ""
                current_chapter = {
                    "chapter_number": chapter_number,
                    "chapter_title": chapter_title,
                    "order": len(chapters) + 1,
                    "articles": []
                }
            elif line.startswith("### 第") and "条" in line:
                if current_chapter is not None:
                    parts = line.replace("### ", "").split(" ", 1)
                    article_number = parts[0] if parts else ""
                    article_title = parts[1] if len(parts) > 1 else ""
                    current_chapter["articles"].append({
                        "article_number": article_number,
                        "article_title": article_title,
                        "order": len(current_chapter["articles"]) + 1
                    })

        if current_chapter:
            chapters.append(current_chapter)

        total_articles = sum(len(c["articles"]) for c in chapters)

        return {
            "session_id": session.session_id,
            "outline_id": session.outline_id,
            "document_title": session.custom_name or session.template_name,
            "generated_at": session.updated_at.isoformat() if session.updated_at else None,
            "chapters": chapters,
            "statistics": {
                "total_chapters": len(chapters),
                "total_articles": total_articles,
                "word_count": len(content),
                "estimated_reading_minutes": max(1, len(content) // 300)
            }
        }

    # ==================== 草稿保存 ====================

    def save_draft(
        self,
        session_id: str,
        content: str,
        content_format: str = "markdown",
        last_edited_chapter: str = "",
        auto_save: bool = False
    ) -> Dict[str, Any]:
        """
        保存制度草稿

        业务逻辑：
        1. 更新会话的草稿内容
        2. 更新关联文档内容
        3. 计算字数
        4. 更新版本号（手动保存时）
        """
        session = self.get_session(session_id)
        if not session:
            return {"success": False, "message": "会话不存在"}

        session.draft_content = content
        session.word_count = len(content)
        if last_edited_chapter:
            session.last_edited_chapter = last_edited_chapter

        if session.status == DraftSessionStatus.OUTLINE_READY.value:
            session.status = DraftSessionStatus.EDITING.value

        if not auto_save:
            session.version = (session.version or 0) + 1

        if session.document_id:
            doc = self.db.query(DraftDocument).filter(
                DraftDocument.id == session.document_id
            ).first()
            if doc:
                doc.content = content
                doc.word_count = len(content)
                if last_edited_chapter:
                    doc.last_edited_chapter = last_edited_chapter

        self.db.commit()

        return {
            "success": True,
            "message": "草稿保存成功",
            "saved_at": datetime.now().isoformat(),
            "version": session.version,
            "word_count": session.word_count
        }

    # ==================== 提交审核 ====================

    def submit_review(
        self,
        session_id: str,
        document_name: str,
        document_type: str,
        reviewers: List[int],
        review_deadline: Optional[str] = None,
        priority: str = "normal",
        submission_note: str = ""
    ) -> Dict[str, Any]:
        """
        提交制度审核

        业务逻辑：
        1. 更新会话状态为已提交
        2. 更新文档状态为待审核
        3. 设置审核人权限
        4. 返回审核任务信息
        """
        session = self.get_session(session_id)
        if not session:
            return {"success": False, "message": "会话不存在"}

        session.status = DraftSessionStatus.SUBMITTED.value

        if session.document_id:
            doc = self.db.query(DraftDocument).filter(
                DraftDocument.id == session.document_id
            ).first()
            if doc:
                doc.name = document_name
                doc.type = document_type
                doc.status = DocumentStatus.PENDING_REVIEW.value
                doc.priority = priority
                doc.submission_note = submission_note
                if review_deadline:
                    doc.review_deadline = datetime.fromisoformat(review_deadline.replace("Z", ""))

        for reviewer_id in reviewers:
            existing = self.db.query(DocumentPermission).filter(
                DocumentPermission.doc_id == session.document_id,
                DocumentPermission.user_id == reviewer_id
            ).first()

            if existing:
                existing.can_view = True
                existing.can_edit = True
            else:
                perm = DocumentPermission(
                    doc_id=session.document_id,
                    user_id=reviewer_id,
                    can_view=True,
                    can_edit=True
                )
                self.db.add(perm)

        self.db.commit()

        review_task_id = f"review_task_{uuid.uuid4().hex[:8]}"
        assigned_reviewers = []
        for rid in reviewers:
            user = self.db.query(User).filter(User.id == rid).first()
            assigned_reviewers.append({
                "user_id": rid,
                "username": user.username if user else "",
                "status": "pending"
            })

        return {
            "success": True,
            "message": "制度提交审核成功",
            "document_id": session.document_id,
            "review_task_id": review_task_id,
            "status": DocumentStatus.PENDING_REVIEW.value,
            "submitted_at": datetime.now().isoformat(),
            "review_deadline": review_deadline,
            "assigned_reviewers": assigned_reviewers
        }

    # ==================== 合规检查 ====================

    def save_compliance_check(
        self,
        session_id: str,
        check_scope: List[str],
        reference_documents: Optional[List[str]] = None,
        overall_status: str = "pass",
        summary: Optional[Dict] = None,
        issues: Optional[List[Dict]] = None,
        passed_checks: Optional[List[Dict]] = None
    ) -> ComplianceCheck:
        check_id = f"check_{uuid.uuid4().hex[:8]}"

        check = ComplianceCheck(
            check_id=check_id,
            session_id=session_id,
            check_scope=check_scope,
            reference_documents=reference_documents,
            overall_status=overall_status,
            summary=summary,
            issues=issues,
            passed_checks=passed_checks
        )
        self.db.add(check)
        self.db.commit()
        self.db.refresh(check)
        return check

    def get_compliance_checks(self, session_id: str) -> List[Dict]:
        checks = self.db.query(ComplianceCheck).filter(
            ComplianceCheck.session_id == session_id
        ).order_by(ComplianceCheck.checked_at.desc()).all()
        return [c.to_dict() for c in checks]

    # ==================== 附件管理 ====================

    def upload_attachment(
        self,
        session_id: str,
        file_info: Dict,
        attachment_type: str = "other"
    ) -> DraftAttachment:
        att_id = f"att_{uuid.uuid4().hex[:8]}"
        file_type = file_info.get("file_type", "")
        file_url = f"/api/files/{att_id}"

        markdown_ref = ""
        if attachment_type == "image" or file_type in ["jpg", "jpeg", "png", "gif", "svg"]:
            markdown_ref = f"![{file_info.get('file_name', '')}]({file_url})"
        else:
            markdown_ref = f"[{file_info.get('file_name', '')}]({file_url})"

        attachment = DraftAttachment(
            session_id=session_id,
            attachment_id=att_id,
            file_name=file_info.get("file_name", ""),
            file_path=file_info.get("file_path", ""),
            file_size=file_info.get("file_size", 0),
            file_type=file_type,
            attachment_type=attachment_type,
            file_url=file_url,
            markdown_reference=markdown_ref
        )
        self.db.add(attachment)
        self.db.commit()
        self.db.refresh(attachment)
        return attachment

    # ==================== 引用查看 ====================

    def get_references(self, session_id: str, reference_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取制度内容中引用的外部文档信息

        业务逻辑：
        1. 查询关联的上位文档
        2. 查询参考资料
        3. 返回引用详情
        """
        relations = self.db.query(DocumentRelation).filter(
            DocumentRelation.doc_id == session_id,
            DocumentRelation.direction == "upper"
        ).all()

        materials = self.db.query(DraftMaterial).filter(
            DraftMaterial.session_id == session_id
        ).all()

        references = []
        for r in relations:
            ref = {
                "ref_id": f"ref_{r.id}",
                "source_type": "law" if r.relation_type == "legal_basis" else "document",
                "source_id": r.related_doc_id,
                "source_name": r.related_doc_name,
                "cited_in": [],
                "cited_articles": None,
                "excerpt": r.notes or "",
                "validity": "current",
            }
            if reference_id and ref["source_id"] != reference_id:
                continue
            references.append(ref)

        for m in materials:
            ref = {
                "ref_id": f"ref_mat_{m.id}",
                "source_type": "document",
                "source_id": m.file_id,
                "source_name": m.file_name,
                "cited_in": [],
                "cited_articles": None,
                "excerpt": "",
                "validity": "current",
            }
            if reference_id and ref["source_id"] != reference_id:
                continue
            references.append(ref)

        return {
            "total_references": len(references),
            "references": references
        }
