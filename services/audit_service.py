"""
审查服务模块
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.audit import (
    AuditTask, AuditConfig, AuditChecklist, AuditResult, AuditIssue, AuditTrail,
    VersionCompareTask, AuditType, TaskStatus, RiskLevel, IssueType, IssueStatus,
    ResultStatus, ChecklistCategory
)


class AuditService:
    """审查服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 统计相关 ====================
    
    def get_statistics(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """获取审查统计数据"""
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        task_query = self.db.query(AuditTask)
        if user_id:
            task_query = task_query.filter(AuditTask.user_id == user_id)
        
        today_count = task_query.filter(
            AuditTask.created_at >= today_start
        ).count()
        
        batch_count = task_query.filter(
            AuditTask.audit_type == AuditType.REVISION
        ).count()
        
        issue_query = self.db.query(AuditIssue)
        if user_id:
            task_ids = [t.id for t in task_query.all()]
            result_ids = [r.id for r in self.db.query(AuditResult).filter(AuditResult.task_id.in_(task_ids)).all()]
            issue_query = issue_query.filter(AuditIssue.result_id.in_(result_ids))
        
        risk_count = issue_query.filter(
            AuditIssue.severity == RiskLevel.HIGH
        ).count()
        
        completed_count = task_query.filter(
            AuditTask.status == TaskStatus.COMPLETED
        ).count()
        
        total_issues = issue_query.count()
        compliance_count = issue_query.filter(
            AuditIssue.issue_type == IssueType.COMPLIANCE
        ).count()
        consistency_count = issue_query.filter(
            AuditIssue.issue_type == IssueType.CONSISTENCY
        ).count()
        format_count = issue_query.filter(
            AuditIssue.issue_type == IssueType.FORMAT
        ).count()
        
        if total_issues > 0:
            compliance_ratio = round(compliance_count / total_issues * 100)
            consistency_ratio = round(consistency_count / total_issues * 100)
            format_ratio = round(format_count / total_issues * 100)
        else:
            compliance_ratio = 0
            consistency_ratio = 0
            format_ratio = 0
        
        return {
            "today_count": today_count,
            "batch_count": batch_count,
            "risk_count": risk_count,
            "completed_count": completed_count,
            "compliance_ratio": compliance_ratio,
            "consistency_ratio": consistency_ratio,
            "format_ratio": format_ratio
        }
    
    # ==================== 任务相关 ====================
    
    def create_task(
        self,
        document_path: str,
        document_name: str,
        audit_type: str = "draft",
        config_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> AuditTask:
        """创建审查任务"""
        audit_type_enum = AuditType(audit_type) if audit_type in [e.value for e in AuditType] else AuditType.DRAFT
        
        task = AuditTask(
            document_name=document_name,
            document_path=document_path,
            status=TaskStatus.PENDING,
            audit_type=audit_type_enum,
            progress=0,
            config_id=config_id,
            conversation_id=conversation_id,
            user_id=user_id
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        self._add_trail(task.id, "创建审查任务", "系统", f"上传文档：{document_name}", user_id=user_id)
        
        return task
    
    def get_task_by_id(self, task_id: int) -> Optional[AuditTask]:
        """根据ID获取任务"""
        return self.db.query(AuditTask).filter(AuditTask.id == task_id).first()
    
    def get_tasks(
        self,
        limit: int = 10,
        status: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取任务列表"""
        query = self.db.query(AuditTask)
        
        if user_id:
            query = query.filter(AuditTask.user_id == user_id)
        
        if status:
            status_enum = TaskStatus(status) if status in [e.value for e in TaskStatus] else None
            if status_enum:
                query = query.filter(AuditTask.status == status_enum)
        
        total = query.count()
        items = query.order_by(desc(AuditTask.created_at)).limit(limit).all()
        
        return {"total": total, "items": items}
    
    def update_task_status(
        self,
        task_id: int,
        status: str,
        progress: Optional[int] = None
    ) -> Optional[AuditTask]:
        """更新任务状态"""
        task = self.get_task_by_id(task_id)
        if not task:
            return None
        
        status_enum = TaskStatus(status) if status in [e.value for e in TaskStatus] else task.status
        task.status = status_enum
        
        if progress is not None:
            task.progress = progress
        
        if status == "completed":
            task.completed_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    def start_task(self, task_id: int, config_id: Optional[int] = None) -> Optional[AuditTask]:
        """启动审查任务"""
        task = self.get_task_by_id(task_id)
        if not task:
            return None
        
        if config_id:
            task.config_id = config_id
        
        task.status = TaskStatus.ANALYZING
        task.progress = 0
        self.db.commit()
        self.db.refresh(task)
        
        self._add_trail(task_id, "启动审查", "系统", f"使用配置ID：{config_id or '默认'}")
        
        return task
    
    def pause_task(self, task_id: int) -> Optional[AuditTask]:
        """暂停任务"""
        return self.update_task_status(task_id, "paused")
    
    def cancel_task(self, task_id: int) -> Optional[AuditTask]:
        """取消任务"""
        task = self.update_task_status(task_id, "cancelled")
        if task:
            self._add_trail(task_id, "取消审查", "系统", "任务已取消")
        return task
    
    # ==================== 结果相关 ====================
    
    def create_result(
        self,
        task_id: int,
        document_name: str,
        risk_level: Optional[str] = None,
        reviewer_id: Optional[int] = None
    ) -> AuditResult:
        """创建审查结果"""
        existing_result = self.get_result_by_task_id(task_id)
        if existing_result:
            return existing_result
        
        risk_enum = RiskLevel(risk_level) if risk_level in [e.value for e in RiskLevel] else None
        
        result = AuditResult(
            task_id=task_id,
            document_name=document_name,
            risk_level=risk_enum,
            status=ResultStatus.PENDING_REVIEW,
            reviewer_id=reviewer_id
        )
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        
        return result
    
    def get_or_create_result(
        self,
        task_id: int,
        document_name: str,
        risk_level: Optional[str] = None
    ) -> AuditResult:
        """获取或创建审查结果"""
        return self.create_result(
            task_id=task_id,
            document_name=document_name,
            risk_level=risk_level
        )
    
    def get_result_by_id(self, result_id: int) -> Optional[AuditResult]:
        """根据ID获取结果"""
        return self.db.query(AuditResult).filter(AuditResult.id == result_id).first()
    
    def get_result_by_task_id(self, task_id: int) -> Optional[AuditResult]:
        """根据任务ID获取结果"""
        return self.db.query(AuditResult).filter(AuditResult.task_id == task_id).first()
    
    def update_result_statistics(self, result_id: int) -> None:
        """更新结果统计"""
        result = self.get_result_by_id(result_id)
        if not result:
            return
        
        issues = self.db.query(AuditIssue).filter(AuditIssue.result_id == result_id).all()
        
        result.total_issues = len(issues)
        result.compliance_issues = len([i for i in issues if i.issue_type == IssueType.COMPLIANCE])
        result.consistency_issues = len([i for i in issues if i.issue_type == IssueType.CONSISTENCY])
        result.format_issues = len([i for i in issues if i.issue_type == IssueType.FORMAT])
        
        high_count = len([i for i in issues if i.severity == RiskLevel.HIGH])
        medium_count = len([i for i in issues if i.severity == RiskLevel.MEDIUM])
        
        if high_count > 0:
            result.risk_level = RiskLevel.HIGH
        elif medium_count > 0:
            result.risk_level = RiskLevel.MEDIUM
        else:
            result.risk_level = RiskLevel.LOW
        
        self.db.commit()
    
    # ==================== 问题相关 ====================
    
    def create_issue(
        self,
        result_id: int,
        issue_type: str,
        severity: str,
        location: Optional[str] = None,
        original_text: Optional[str] = None,
        issue_description: Optional[str] = None,
        legal_basis: Optional[str] = None,
        suggestion: Optional[str] = None
    ) -> AuditIssue:
        """创建审查问题"""
        issue_type_enum = IssueType(issue_type) if issue_type in [e.value for e in IssueType] else IssueType.COMPLIANCE
        severity_enum = RiskLevel(severity) if severity in [e.value for e in RiskLevel] else RiskLevel.MEDIUM
        
        issue = AuditIssue(
            result_id=result_id,
            issue_type=issue_type_enum,
            severity=severity_enum,
            location=location,
            original_text=original_text,
            issue_description=issue_description,
            legal_basis=legal_basis,
            suggestion=suggestion,
            status=IssueStatus.PENDING
        )
        self.db.add(issue)
        self.db.commit()
        self.db.refresh(issue)
        
        self.update_result_statistics(result_id)
        
        return issue
    
    def get_issues_by_result_id(
        self,
        result_id: int,
        issue_type: Optional[str] = None,
        severity: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取结果的问题列表"""
        query = self.db.query(AuditIssue).filter(AuditIssue.result_id == result_id)
        
        if issue_type:
            issue_type_enum = IssueType(issue_type) if issue_type in [e.value for e in IssueType] else None
            if issue_type_enum:
                query = query.filter(AuditIssue.issue_type == issue_type_enum)
        
        if severity:
            severity_enum = RiskLevel(severity) if severity in [e.value for e in RiskLevel] else None
            if severity_enum:
                query = query.filter(AuditIssue.severity == severity_enum)
        
        total = query.count()
        items = query.order_by(desc(AuditIssue.severity), desc(AuditIssue.created_at)).all()
        
        return {"total": total, "items": items}
    
    def update_issue_status(
        self,
        issue_id: int,
        status: str,
        suggestion: Optional[str] = None,
        reject_reason: Optional[str] = None
    ) -> Optional[AuditIssue]:
        """更新问题状态"""
        issue = self.db.query(AuditIssue).filter(AuditIssue.id == issue_id).first()
        if not issue:
            return None
        
        status_enum = IssueStatus(status) if status in [e.value for e in IssueStatus] else issue.status
        issue.status = status_enum
        
        if suggestion:
            issue.suggestion = suggestion
        if reject_reason:
            issue.reject_reason = reject_reason
        
        self.db.commit()
        self.db.refresh(issue)
        
        return issue
    
    def batch_update_issues(
        self,
        result_id: int,
        issue_ids: List[int],
        status: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """批量更新问题状态"""
        status_enum = IssueStatus(status) if status in [e.value for e in IssueStatus] else None
        if not status_enum:
            return {"success": False, "message": "无效的状态值"}
        
        query = self.db.query(AuditIssue).filter(
            AuditIssue.result_id == result_id,
            AuditIssue.id.in_(issue_ids)
        )
        
        updated_count = query.update({"status": status_enum}, synchronize_session=False)
        self.db.commit()
        
        result = self.get_result_by_id(result_id)
        if result:
            self._add_trail(
                task_id=result.task_id,
                action="批量更新问题状态",
                actor="用户",
                details=f"批量将 {updated_count} 个问题状态更新为 {status}",
                user_id=user_id
            )
        
        return {
            "success": True,
            "updated_count": updated_count,
            "message": f"成功更新 {updated_count} 个问题状态"
        }
    
    def get_issue_by_id(self, issue_id: int) -> Optional[AuditIssue]:
        """根据ID获取问题"""
        return self.db.query(AuditIssue).filter(AuditIssue.id == issue_id).first()
    
    # ==================== 审核确认相关 ====================
    
    def start_review(
        self,
        result_id: int,
        reviewer_id: int
    ) -> Optional[AuditResult]:
        """开始审核 - 将结果状态改为审核中"""
        result = self.get_result_by_id(result_id)
        if not result:
            return None
        
        if result.status != ResultStatus.PENDING_REVIEW:
            return None
        
        result.status = ResultStatus.REVIEWING
        result.reviewer_id = reviewer_id
        self.db.commit()
        self.db.refresh(result)
        
        self._add_trail(
            task_id=result.task_id,
            action="开始审核",
            actor="审核人",
            details="审核人开始审核审查结果",
            user_id=reviewer_id
        )
        
        return result
    
    def confirm_result(
        self,
        result_id: int,
        reviewer_id: int,
        comment: Optional[str] = None
    ) -> Optional[AuditResult]:
        """确认审查结果 - 将状态改为已完成"""
        result = self.get_result_by_id(result_id)
        if not result:
            return None
        
        if result.status == ResultStatus.COMPLETED:
            return result
        
        result.status = ResultStatus.COMPLETED
        result.reviewer_id = reviewer_id
        self.db.commit()
        self.db.refresh(result)
        
        self.update_result_statistics(result_id)
        
        detail_msg = "审查结果已确认"
        if comment:
            detail_msg += f"，审核意见：{comment}"
        
        self._add_trail(
            task_id=result.task_id,
            action="确认审查结果",
            actor="审核人",
            details=detail_msg,
            user_id=reviewer_id
        )
        
        return result
    
    def reject_result(
        self,
        result_id: int,
        reviewer_id: int,
        reason: str
    ) -> Optional[AuditResult]:
        """驳回审查结果 - 需要重新审查"""
        result = self.get_result_by_id(result_id)
        if not result:
            return None
        
        result.status = ResultStatus.PENDING_REVIEW
        result.reviewer_id = reviewer_id
        self.db.commit()
        self.db.refresh(result)
        
        self._add_trail(
            task_id=result.task_id,
            action="驳回审查结果",
            actor="审核人",
            details=f"驳回原因：{reason}",
            user_id=reviewer_id
        )
        
        return result
    
    def get_review_statistics(self, result_id: int) -> Dict[str, Any]:
        """获取审核统计信息"""
        result = self.get_result_by_id(result_id)
        if not result:
            return {}
        
        issues = self.db.query(AuditIssue).filter(AuditIssue.result_id == result_id).all()
        
        total = len(issues)
        pending = len([i for i in issues if i.status == IssueStatus.PENDING])
        accepted = len([i for i in issues if i.status == IssueStatus.ACCEPTED])
        rejected = len([i for i in issues if i.status == IssueStatus.REJECTED])
        partial = len([i for i in issues if i.status == IssueStatus.PARTIAL_ACCEPTED])
        
        return {
            "total_issues": total,
            "pending_issues": pending,
            "accepted_issues": accepted,
            "rejected_issues": rejected,
            "partial_accepted_issues": partial,
            "review_progress": round((accepted + rejected + partial) / total * 100) if total > 0 else 0,
            "all_reviewed": pending == 0
        }
    
    # ==================== 配置相关 ====================
    
    def create_config(
        self,
        name: str,
        audit_dimensions: Optional[List[str]] = None,
        focus_keywords: Optional[List[str]] = None,
        checklist_ids: Optional[List[int]] = None,
        is_default: bool = False
    ) -> AuditConfig:
        """创建审查配置"""
        if is_default:
            self.db.query(AuditConfig).filter(AuditConfig.is_default == True).update({"is_default": False})
        
        config = AuditConfig(
            name=name,
            audit_dimensions=audit_dimensions,
            focus_keywords=focus_keywords,
            checklist_ids=checklist_ids,
            is_default=is_default
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        
        return config
    
    def get_config_by_id(self, config_id: int) -> Optional[AuditConfig]:
        """根据ID获取配置"""
        return self.db.query(AuditConfig).filter(AuditConfig.id == config_id).first()
    
    def get_configs(self) -> List[AuditConfig]:
        """获取所有配置"""
        return self.db.query(AuditConfig).order_by(desc(AuditConfig.is_default), desc(AuditConfig.created_at)).all()
    
    def get_default_config(self) -> Optional[AuditConfig]:
        """获取默认配置"""
        return self.db.query(AuditConfig).filter(AuditConfig.is_default == True).first()
    
    # ==================== 清单相关 ====================
    
    def create_checklist(
        self,
        name: str,
        category: str = "general",
        items: Optional[List[Dict]] = None,
        is_active: bool = True
    ) -> AuditChecklist:
        """创建审查清单"""
        category_enum = ChecklistCategory(category) if category in [e.value for e in ChecklistCategory] else ChecklistCategory.GENERAL
        
        checklist = AuditChecklist(
            name=name,
            category=category_enum,
            items=items,
            is_active=is_active
        )
        self.db.add(checklist)
        self.db.commit()
        self.db.refresh(checklist)
        
        return checklist
    
    def get_checklists(self, is_active: Optional[bool] = None) -> Dict[str, Any]:
        """获取审查清单列表"""
        query = self.db.query(AuditChecklist)
        
        if is_active is not None:
            query = query.filter(AuditChecklist.is_active == is_active)
        
        total = query.count()
        items = query.order_by(desc(AuditChecklist.created_at)).all()
        
        return {"total": total, "items": items}
    
    def get_checklist_by_id(self, checklist_id: int) -> Optional[AuditChecklist]:
        """根据ID获取清单"""
        return self.db.query(AuditChecklist).filter(AuditChecklist.id == checklist_id).first()
    
    # ==================== 轨迹相关 ====================
    
    def _add_trail(
        self,
        task_id: int,
        action: str,
        actor: str = "系统",
        details: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> AuditTrail:
        """添加审查轨迹"""
        trail = AuditTrail(
            task_id=task_id,
            action=action,
            actor=actor,
            details=details,
            user_id=user_id
        )
        self.db.add(trail)
        self.db.commit()
        self.db.refresh(trail)
        
        return trail
    
    def get_trails_by_task_id(self, task_id: int) -> Dict[str, Any]:
        """获取任务的审查轨迹"""
        query = self.db.query(AuditTrail).filter(AuditTrail.task_id == task_id)
        
        total = query.count()
        items = query.order_by(AuditTrail.created_at).all()
        
        return {"total": total, "items": items}
    
    # ==================== 历史记录相关 ====================
    
    def get_history(
        self,
        date_range: Optional[str] = None,
        audit_type: Optional[str] = None,
        risk_level: Optional[str] = None,
        keyword: Optional[str] = None,
        limit: int = 20,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取审查历史记录"""
        query = self.db.query(AuditResult).join(AuditTask)
        
        if user_id:
            query = query.filter(AuditTask.user_id == user_id)
        
        if audit_type:
            audit_type_enum = AuditType(audit_type) if audit_type in [e.value for e in AuditType] else None
            if audit_type_enum:
                query = query.filter(AuditTask.audit_type == audit_type_enum)
        
        if risk_level:
            risk_enum = RiskLevel(risk_level) if risk_level in [e.value for e in RiskLevel] else None
            if risk_enum:
                query = query.filter(AuditResult.risk_level == risk_enum)
        
        if keyword:
            query = query.filter(AuditResult.document_name.like(f"%{keyword}%"))
        
        total = query.count()
        items = query.order_by(desc(AuditResult.created_at)).limit(limit).all()
        
        return {"total": total, "items": items}
    
    # ==================== 版本比对相关 ====================
    
    def create_version_compare_task(
        self,
        old_document_path: str,
        new_document_path: str,
        old_document_name: Optional[str] = None,
        new_document_name: Optional[str] = None,
        config_id: Optional[int] = None
    ) -> VersionCompareTask:
        """创建版本比对任务"""
        task = VersionCompareTask(
            old_document_path=old_document_path,
            new_document_path=new_document_path,
            old_document_name=old_document_name,
            new_document_name=new_document_name,
            config_id=config_id,
            status=TaskStatus.PENDING
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    def get_version_compare_task(self, task_id: int) -> Optional[VersionCompareTask]:
        """获取版本比对任务"""
        return self.db.query(VersionCompareTask).filter(VersionCompareTask.id == task_id).first()
    
    def update_version_compare_result(
        self,
        task_id: int,
        additions: Optional[List[str]] = None,
        deletions: Optional[List[str]] = None,
        modifications: Optional[List[str]] = None,
        consistency_issues: Optional[List[Dict]] = None
    ) -> Optional[VersionCompareTask]:
        """更新版本比对结果"""
        task = self.get_version_compare_task(task_id)
        if not task:
            return None
        
        task.additions = additions
        task.deletions = deletions
        task.modifications = modifications
        task.status = TaskStatus.COMPLETED
        self.db.commit()
        self.db.refresh(task)
        
        return task
