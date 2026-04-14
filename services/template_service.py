"""
模板服务模块
提供模板的CRUD操作和导出功能
"""

import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from models.template import Template, TemplateSection
from utils.logger import setup_logger

logger = setup_logger(__name__)


class TemplateService:
    """
    模板服务类
    
    提供模板的创建、查询、更新、删除、导出等操作
    
    Attributes:
        db: 数据库会话
    """
    
    def __init__(self, db: Session):
        """
        初始化模板服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        logger.debug("模板服务初始化完成")
    
    def _generate_template_id(self) -> str:
        """
        生成模板唯一标识
        
        Returns:
            str: 模板ID，格式为 template_YYYYMMDD_随机字符串
        """
        import random
        import string
        timestamp = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return f"template_{timestamp}_{random_str}"
    
    def _generate_section_id(self) -> str:
        """
        生成章节唯一标识
        
        Returns:
            str: 章节ID，格式为 section_随机字符串
        """
        import random
        import string
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"section_{random_str}"
    
    def _save_sections(
        self,
        template_id: str,
        sections: List[Dict[str, Any]],
        parent_id: Optional[str] = None,
        sort_order: int = 0
    ) -> List[TemplateSection]:
        """
        递归保存章节结构
        
        Args:
            template_id: 模板ID
            sections: 章节数据列表
            parent_id: 父章节ID
            sort_order: 排序顺序
        
        Returns:
            List[TemplateSection]: 创建的章节列表
        """
        created_sections = []
        
        for idx, section_data in enumerate(sections):
            section_id = section_data.get("id") or self._generate_section_id()
            
            section = TemplateSection(
                id=section_id,
                template_id=template_id,
                parent_id=parent_id,
                level=section_data.get("level", 1),
                title=section_data.get("title", ""),
                description=section_data.get("description"),
                sort_order=sort_order + idx
            )
            
            self.db.add(section)
            self.db.flush()
            
            created_sections.append(section)
            
            if section_data.get("children"):
                children = self._save_sections(
                    template_id=template_id,
                    sections=section_data["children"],
                    parent_id=section_id,
                    sort_order=0
                )
                created_sections.extend(children)
        
        return created_sections
    
    def create_template(
        self,
        name: str,
        category: str,
        format: Dict[str, str],
        creator_id: int,
        creator_name: str,
        sections: List[Dict[str, Any]],
        description: Optional[str] = None,
        is_public: bool = False,
        tags: Optional[List[str]] = None
    ) -> Template:
        """
        创建模板
        
        Args:
            name: 模板名称
            category: 模板分类
            format: 格式设置
            creator_id: 创建者用户ID
            creator_name: 创建者姓名
            sections: 章节结构列表
            description: 模板描述
            is_public: 是否公开
            tags: 标签列表
        
        Returns:
            Template: 创建的模板对象
        """
        logger.info(f"创建模板 - 名称: {name}, 分类: {category}, 创建者: {creator_name}")
        
        template_id = self._generate_template_id()
        
        template = Template(
            id=template_id,
            name=name,
            category=category,
            description=description,
            format=format,
            creator_id=creator_id,
            creator_name=creator_name,
            is_public=is_public,
            tags=tags or [],
            usage_count=0
        )
        
        self.db.add(template)
        self.db.flush()
        
        if sections:
            self._save_sections(template_id=template_id, sections=sections)
        
        self.db.commit()
        self.db.refresh(template)
        
        logger.info(f"模板创建成功 - ID: {template.id}")
        return template
    
    def get_template_by_id(self, template_id: str) -> Optional[Template]:
        """
        根据ID获取模板
        
        Args:
            template_id: 模板ID
        
        Returns:
            Optional[Template]: 模板对象，不存在则返回None
        """
        logger.debug(f"查询模板 - ID: {template_id}")
        
        result = self.db.query(Template).filter(
            Template.id == template_id,
            Template.is_deleted == False
        ).first()
        
        if result:
            logger.debug(f"模板查询成功 - ID: {template_id}")
        else:
            logger.debug(f"模板不存在 - ID: {template_id}")
        
        return result
    
    def get_template_list(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        creator_id: Optional[int] = None,
        is_public: Optional[bool] = None,
        tags: Optional[str] = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[Template], int]:
        """
        获取模板列表
        
        Args:
            keyword: 搜索关键词（匹配名称、描述）
            category: 分类筛选
            creator_id: 创建者ID筛选
            is_public: 是否公开筛选
            tags: 标签筛选（多个标签用逗号分隔）
            sort_by: 排序字段
            sort_order: 排序方向
            skip: 分页偏移量
            limit: 每页数量
        
        Returns:
            tuple[List[Template], int]: (模板列表, 总数)
        """
        logger.debug(f"查询模板列表 - keyword: {keyword}, category: {category}")
        
        query = self.db.query(Template).filter(Template.is_deleted == False)
        
        if keyword:
            query = query.filter(
                or_(
                    Template.name.contains(keyword),
                    Template.description.contains(keyword)
                )
            )
        
        if category:
            query = query.filter(Template.category == category)
        
        if creator_id is not None:
            query = query.filter(Template.creator_id == creator_id)
        
        if is_public is not None:
            query = query.filter(Template.is_public == is_public)
        
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
            for tag in tag_list:
                query = query.filter(Template.tags.contains(tag))
        
        total = query.count()
        
        order_column = getattr(Template, sort_by, Template.updated_at)
        if sort_order == "desc":
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())
        
        templates = query.offset(skip).limit(limit).all()
        
        logger.info(f"模板列表查询成功 - 总数: {total}, 返回: {len(templates)}")
        return templates, total
    
    def update_template(
        self,
        template_id: str,
        name: Optional[str] = None,
        category: Optional[str] = None,
        description: Optional[str] = None,
        format: Optional[Dict[str, str]] = None,
        sections: Optional[List[Dict[str, Any]]] = None,
        is_public: Optional[bool] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[Template]:
        """
        更新模板
        
        Args:
            template_id: 模板ID
            name: 模板名称
            category: 模板分类
            description: 模板描述
            format: 格式设置
            sections: 章节结构
            is_public: 是否公开
            tags: 标签列表
        
        Returns:
            Optional[Template]: 更新后的模板对象
        """
        logger.info(f"更新模板 - ID: {template_id}")
        
        template = self.get_template_by_id(template_id)
        if not template:
            logger.error(f"模板不存在 - ID: {template_id}")
            return None
        
        if name is not None:
            template.name = name
        if category is not None:
            template.category = category
        if description is not None:
            template.description = description
        if format is not None:
            template.format = format
        if is_public is not None:
            template.is_public = is_public
        if tags is not None:
            template.tags = tags
        
        if sections is not None:
            self.db.query(TemplateSection).filter(
                TemplateSection.template_id == template_id
            ).delete()
            
            self._save_sections(template_id=template_id, sections=sections)
        
        self.db.commit()
        self.db.refresh(template)
        
        logger.info(f"模板更新成功 - ID: {template_id}")
        return template
    
    def delete_template(self, template_id: str, hard_delete: bool = False) -> bool:
        """
        删除模板
        
        Args:
            template_id: 模板ID
            hard_delete: 是否硬删除（默认软删除）
        
        Returns:
            bool: 删除是否成功
        """
        logger.info(f"删除模板 - ID: {template_id}, 硬删除: {hard_delete}")
        
        template = self.get_template_by_id(template_id)
        if not template:
            logger.error(f"模板不存在 - ID: {template_id}")
            return False
        
        try:
            if hard_delete:
                self.db.delete(template)
            else:
                template.is_deleted = True
                template.deleted_at = datetime.now()
            
            self.db.commit()
            
            logger.info(f"模板删除成功 - ID: {template_id}")
            return True
        except Exception as e:
            logger.error(f"模板删除失败 - ID: {template_id}, 错误: {str(e)}", exc_info=True)
            self.db.rollback()
            return False
    
    def increment_usage_count(self, template_id: str) -> bool:
        """
        增加模板使用次数
        
        Args:
            template_id: 模板ID
        
        Returns:
            bool: 操作是否成功
        """
        logger.debug(f"增加模板使用次数 - ID: {template_id}")
        
        template = self.get_template_by_id(template_id)
        if not template:
            logger.error(f"模板不存在 - ID: {template_id}")
            return False
        
        template.usage_count += 1
        self.db.commit()
        
        logger.debug(f"模板使用次数更新成功 - ID: {template_id}, 新次数: {template.usage_count}")
        return True
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """
        获取所有模板分类及统计信息
        
        Returns:
            List[Dict[str, Any]]: 分类列表
        """
        logger.debug("查询模板分类列表")
        
        from sqlalchemy import func
        
        results = self.db.query(
            Template.category,
            func.count(Template.id).label("count")
        ).filter(
            Template.is_deleted == False
        ).group_by(Template.category).all()
        
        categories = []
        category_descriptions = {
            "人事管理": "包含招聘、考勤、薪酬等人事相关制度模板",
            "财务管理": "包含预算、报销、采购等财务相关制度模板",
            "行政管理": "包含办公、会议、档案等行政相关制度模板",
            "业务流程": "包含审批、执行、监督等业务流程模板",
            "安全管理": "包含信息安全、生产安全等安全管理模板",
            "自定义": "用户自定义模板"
        }
        
        for category, count in results:
            categories.append({
                "name": category,
                "count": count,
                "description": category_descriptions.get(category, "")
            })
        
        logger.info(f"模板分类查询成功 - 数量: {len(categories)}")
        return categories
    
    def get_popular_tags(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取热门标签
        
        Args:
            limit: 返回标签数量
        
        Returns:
            List[Dict[str, Any]]: 标签列表
        """
        logger.debug(f"查询热门标签 - limit: {limit}")
        
        templates = self.db.query(Template.tags).filter(
            Template.is_deleted == False,
            Template.tags.isnot(None)
        ).all()
        
        tag_count = {}
        for template in templates:
            if template.tags:
                for tag in template.tags:
                    tag_count[tag] = tag_count.get(tag, 0) + 1
        
        sorted_tags = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        tags = [{"name": tag, "count": count} for tag, count in sorted_tags]
        
        logger.info(f"热门标签查询成功 - 数量: {len(tags)}")
        return tags
    
    def export_template_to_markdown(
        self,
        template_id: str,
        include_metadata: bool = True,
        include_format_section: bool = True,
        include_creator_info: bool = True
    ) -> Optional[str]:
        """
        导出模板为Markdown格式
        
        Args:
            template_id: 模板ID
            include_metadata: 是否包含元数据
            include_format_section: 是否包含格式设置
            include_creator_info: 是否包含创建者信息
        
        Returns:
            Optional[str]: Markdown内容
        """
        logger.info(f"导出模板为Markdown - ID: {template_id}")
        
        template = self.get_template_by_id(template_id)
        if not template:
            logger.error(f"模板不存在 - ID: {template_id}")
            return None
        
        lines = []
        
        lines.append(f"# {template.name}")
        lines.append("")
        
        if include_metadata:
            lines.append("## 模板信息")
            lines.append("")
            lines.append(f"- **模板ID**: {template.id}")
            lines.append(f"- **分类**: {template.category}")
            
            if include_creator_info:
                lines.append(f"- **创建者**: {template.creator_name}")
            
            lines.append(f"- **创建时间**: {template.created_at.strftime('%Y-%m-%d %H:%M:%S') if template.created_at else ''}")
            lines.append(f"- **最后更新**: {template.updated_at.strftime('%Y-%m-%d %H:%M:%S') if template.updated_at else ''}")
            lines.append(f"- **使用次数**: {template.usage_count}次")
            
            if template.tags:
                lines.append(f"- **标签**: {', '.join(template.tags)}")
            
            lines.append("")
        
        if include_format_section and template.format:
            lines.append("## 格式设置")
            lines.append("")
            
            font_size_map = {"12px": "小五", "14px": "小四", "16px": "四号", "18px": "小三"}
            margin_map = {"2.54cm": "标准", "2cm": "较窄", "3cm": "较宽"}
            
            lines.append(f"- **字号**: {template.format.get('fontSize', '')} ({font_size_map.get(template.format.get('fontSize', ''), '')})")
            lines.append(f"- **字体**: {template.format.get('fontFamily', '')}")
            lines.append(f"- **行距**: {template.format.get('lineHeight', '')}倍")
            lines.append(f"- **页边距**: {template.format.get('margin', '')} ({margin_map.get(template.format.get('margin', ''), '')})")
            lines.append("")
            lines.append("---")
            lines.append("")
        
        def render_sections(sections: List[TemplateSection], level: int = 1):
            for section in sections:
                if section.level == level:
                    prefix = "#" * (level + 1)
                    lines.append(f"{prefix} {section.title}")
                    lines.append("")
                    
                    if section.description:
                        if level == 1:
                            lines.append(f"> {section.description}")
                        else:
                            lines.append(f"{section.description}")
                        lines.append("")
                    
                    if section.children:
                        render_sections(section.children, level + 1)
                    
                    lines.append("---")
                    lines.append("")
        
        if template.sections:
            root_sections = [s for s in template.sections if s.parent_id is None]
            root_sections.sort(key=lambda x: x.sort_order)
            render_sections(root_sections)
        
        lines.append("## 模板使用说明")
        lines.append("")
        lines.append("1. 本模板为制度编制提供标准结构参考")
        lines.append("2. 请根据实际情况调整章节内容和描述")
        lines.append("3. 建议在使用前咨询相关部门意见")
        lines.append("4. 模板内容仅供参考，具体条款需符合法律法规要求")
        
        markdown_content = "\n".join(lines)
        
        logger.info(f"模板导出为Markdown成功 - ID: {template_id}, 内容长度: {len(markdown_content)}")
        return markdown_content
    
    def export_template_to_json(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        导出模板为JSON格式
        
        Args:
            template_id: 模板ID
        
        Returns:
            Optional[Dict[str, Any]]: JSON数据
        """
        logger.info(f"导出模板为JSON - ID: {template_id}")
        
        template = self.get_template_by_id(template_id)
        if not template:
            logger.error(f"模板不存在 - ID: {template_id}")
            return None
        
        template_dict = template.to_dict()
        
        logger.info(f"模板导出为JSON成功 - ID: {template_id}")
        return template_dict
    
    def import_template_from_json(
        self,
        template_data: Dict[str, Any],
        creator_id: int,
        creator_name: str,
        overwrite: bool = False
    ) -> Optional[Template]:
        """
        从JSON导入模板
        
        Args:
            template_data: 模板数据
            creator_id: 创建者用户ID
            creator_name: 创建者姓名
            overwrite: 是否覆盖已存在的模板
        
        Returns:
            Optional[Template]: 导入的模板对象
        """
        logger.info(f"导入模板 - 名称: {template_data.get('name')}")
        
        template_id = template_data.get("id")
        
        if template_id:
            existing_template = self.get_template_by_id(template_id)
            if existing_template:
                if overwrite:
                    logger.info(f"模板已存在，将覆盖 - ID: {template_id}")
                    self.delete_template(template_id, hard_delete=True)
                else:
                    logger.warning(f"模板已存在，跳过导入 - ID: {template_id}")
                    return None
        
        template = self.create_template(
            name=template_data.get("name", "未命名模板"),
            category=template_data.get("category", "自定义"),
            format=template_data.get("format", {
                "fontSize": "14px",
                "fontFamily": "仿宋_GB2312",
                "lineHeight": "1.75",
                "margin": "2.54cm"
            }),
            creator_id=creator_id,
            creator_name=creator_name,
            sections=template_data.get("sections", []),
            description=template_data.get("description"),
            is_public=template_data.get("is_public", False),
            tags=template_data.get("tags", [])
        )
        
        logger.info(f"模板导入成功 - ID: {template.id}")
        return template
