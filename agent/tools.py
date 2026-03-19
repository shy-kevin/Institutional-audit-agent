"""
LangChain 工具定义模块
定义智能体可使用的工具
"""

import os
import json
from typing import Optional, List, Dict, Any, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from utils.file_tools import file_tools
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


def extract_filename(path_or_filename: str) -> str:
    """
    从路径或文件名中提取文件名
    
    Args:
        path_or_filename: 路径或文件名
    
    Returns:
        str: 文件名
    """
    if not path_or_filename:
        return path_or_filename
    
    path_or_filename = path_or_filename.replace("/", "\\")
    
    if "\\" in path_or_filename:
        return os.path.basename(path_or_filename)
    
    return path_or_filename


def get_file_path(filename: str) -> str:
    """
    根据文件名获取完整文件路径
    
    Args:
        filename: 文件名或路径
    
    Returns:
        str: 完整文件路径
    """
    filename = extract_filename(filename)
    return os.path.join(settings.UPLOAD_DIR, "temp", filename)


def get_output_filename(filename: str, prefix: str = "") -> str:
    """
    生成输出文件名
    
    Args:
        filename: 原文件名
        prefix: 文件名前缀
    
    Returns:
        str: 输出文件名
    """
    filename = extract_filename(filename)
    name, ext = os.path.splitext(filename)
    if prefix:
        return f"{prefix}_{name}{ext}"
    return filename


def build_result(success: bool, message: str, output_filename: str = None, **kwargs) -> str:
    """
    构建工具返回结果，自动添加下载链接
    
    Args:
        success: 是否成功
        message: 消息
        output_filename: 输出文件名
        **kwargs: 其他参数
    
    Returns:
        str: JSON格式结果
    """
    result = {
        "success": success,
        "message": message
    }
    
    if output_filename:
        result["output_filename"] = output_filename
        result["download_url"] = f"/api/file/download/{output_filename}"
    
    result.update(kwargs)
    return json.dumps(result, ensure_ascii=False, indent=2)


class ReadFileInput(BaseModel):
    """
    读取文件工具的输入参数
    """
    filename: str = Field(description="要读取的文件名（只需文件名，不需要路径）")


class ReadFileTool(BaseTool):
    """
    读取文件工具
    
    用于读取PDF、Word、TXT等文件的内容
    """
    
    name: str = "read_file"
    description: str = "读取文件内容。支持PDF、Word(docx)、TXT等格式。只需输入文件名（如：document.pdf），不需要输入完整路径。"
    args_schema: Type[BaseModel] = ReadFileInput
    
    def _run(self, filename: str) -> str:
        """
        执行读取文件操作
        
        Args:
            filename: 文件名或路径
        
        Returns:
            str: 读取结果（JSON格式）
        """
        logger.info(f"工具调用: read_file - 输入参数: filename={filename}")
        
        file_path = get_file_path(filename)
        result = file_tools.read_file_content(file_path)
        
        if result.get("success"):
            result["message"] = f"文件读取成功，共{result.get('page_count', 0)}页"
            logger.info(f"工具调用成功: read_file - 文件: {filename}, 页数: {result.get('page_count', 0)}")
        else:
            logger.error(f"工具调用失败: read_file - 文件: {filename}, 错误: {result.get('error', '未知错误')}")
        
        logger.debug(f"工具调用结果: read_file - {json.dumps(result, ensure_ascii=False)[:200]}")
        return json.dumps(result, ensure_ascii=False, indent=2)


class HighlightTextInPDFInput(BaseModel):
    """
    PDF标注工具的输入参数
    """
    filename: str = Field(description="原PDF文件名（只需文件名，不需要路径）")
    highlight_texts: List[str] = Field(description="需要标注（标红）的文字列表")


class HighlightTextInPDFTool(BaseTool):
    """
    PDF文字标注工具
    
    用于在PDF文件中标注指定文字（标红显示）
    """
    
    name: str = "highlight_text_in_pdf"
    description: str = "在PDF文件中标注指定的文字，将文字以红色高亮显示。只需输入文件名（如：document.pdf），不需要输入完整路径。"
    args_schema: Type[BaseModel] = HighlightTextInPDFInput
    
    def _run(self, filename: str, highlight_texts: List[str]) -> str:
        """
        执行PDF标注操作
        
        Args:
            filename: 文件名或路径
            highlight_texts: 需要标注的文字列表
        
        Returns:
            str: 操作结果（JSON格式），包含下载链接
        """
        logger.info(f"工具调用: highlight_text_in_pdf - 输入参数: filename={filename}, highlight_texts={highlight_texts}")
        
        file_path = get_file_path(filename)
        output_filename = get_output_filename(filename, "highlighted")
        result = file_tools.highlight_text_in_pdf(file_path, highlight_texts, output_filename)
        
        if result.get("success"):
            logger.info(f"工具调用成功: highlight_text_in_pdf - 输出文件: {output_filename}")
            return build_result(
                success=True,
                message=f"PDF标注完成，已生成文件: {output_filename}",
                output_filename=output_filename,
                highlighted_texts=highlight_texts,
                original_filename=extract_filename(filename)
            )
        else:
            logger.error(f"工具调用失败: highlight_text_in_pdf - 错误: {result.get('error', 'PDF标注失败')}")
            return build_result(
                success=False,
                message=result.get("error", "PDF标注失败")
            )


class ModifyTextInPDFInput(BaseModel):
    """
    PDF修改工具的输入参数
    """
    filename: str = Field(description="原PDF文件名（只需文件名，不需要路径）")
    modifications: List[Dict[str, str]] = Field(
        description="修改列表，每项包含old_text（要修改的原文）和new_text（修改后的新文本）"
    )


class ModifyTextInPDFTool(BaseTool):
    """
    PDF文字修改工具
    
    用于修改PDF文件中的文字内容
    """
    
    name: str = "modify_text_in_pdf"
    description: str = "修改PDF文件中的文字内容。只需输入文件名（如：document.pdf），不需要输入完整路径。"
    args_schema: Type[BaseModel] = ModifyTextInPDFInput
    
    def _run(self, filename: str, modifications: List[Dict[str, str]]) -> str:
        """
        执行PDF修改操作
        
        Args:
            filename: 文件名或路径
            modifications: 修改列表
        
        Returns:
            str: 操作结果（JSON格式），包含下载链接
        """
        logger.info(f"工具调用: modify_text_in_pdf - 输入参数: filename={filename}, modifications={modifications}")
        
        file_path = get_file_path(filename)
        output_filename = get_output_filename(filename, "modified")
        result = file_tools.modify_text_in_pdf(file_path, modifications, output_filename)
        
        if result.get("success"):
            logger.info(f"工具调用成功: modify_text_in_pdf - 输出文件: {output_filename}")
            return build_result(
                success=True,
                message=f"PDF修改完成，已生成文件: {output_filename}",
                output_filename=output_filename,
                modifications=modifications,
                original_filename=extract_filename(filename)
            )
        else:
            logger.error(f"工具调用失败: modify_text_in_pdf - 错误: {result.get('error', 'PDF修改失败')}")
            return build_result(
                success=False,
                message=result.get("error", "PDF修改失败")
            )


class HighlightTextInDocxInput(BaseModel):
    """
    Word标注工具的输入参数
    """
    filename: str = Field(description="原Word文件名（只需文件名，不需要路径）")
    highlight_texts: List[str] = Field(description="需要标注（标红）的文字列表")


class HighlightTextInDocxTool(BaseTool):
    """
    Word文字标注工具
    
    用于在Word文件中标注指定文字（标红显示）
    """
    
    name: str = "highlight_text_in_docx"
    description: str = "在Word文件中标注指定的文字，将文字以红色高亮显示。只需输入文件名（如：document.docx），不需要输入完整路径。"
    args_schema: Type[BaseModel] = HighlightTextInDocxInput
    
    def _run(self, filename: str, highlight_texts: List[str]) -> str:
        """
        执行Word标注操作
        
        Args:
            filename: 文件名或路径
            highlight_texts: 需要标注的文字列表
        
        Returns:
            str: 操作结果（JSON格式），包含下载链接
        """
        logger.info(f"工具调用: highlight_text_in_docx - 输入参数: filename={filename}, highlight_texts={highlight_texts}")
        
        file_path = get_file_path(filename)
        output_filename = get_output_filename(filename, "highlighted")
        result = file_tools.create_highlighted_docx(file_path, highlight_texts, output_filename)
        
        if result.get("success"):
            logger.info(f"工具调用成功: highlight_text_in_docx - 输出文件: {output_filename}")
            return build_result(
                success=True,
                message=f"Word标注完成，已生成文件: {output_filename}",
                output_filename=output_filename,
                highlighted_texts=highlight_texts,
                original_filename=extract_filename(filename)
            )
        else:
            logger.error(f"工具调用失败: highlight_text_in_docx - 错误: {result.get('error', 'Word标注失败')}")
            return build_result(
                success=False,
                message=result.get("error", "Word标注失败")
            )


class ModifyTextInDocxInput(BaseModel):
    """
    Word修改工具的输入参数
    """
    filename: str = Field(description="原Word文件名（只需文件名，不需要路径）")
    modifications: List[Dict[str, str]] = Field(
        description="修改列表，每项包含old_text（要修改的原文）和new_text（修改后的新文本）"
    )


class ModifyTextInDocxTool(BaseTool):
    """
    Word文字修改工具
    
    用于修改Word文件中的文字内容
    """
    
    name: str = "modify_text_in_docx"
    description: str = "修改Word文件中的文字内容。只需输入文件名（如：document.docx），不需要输入完整路径。"
    args_schema: Type[BaseModel] = ModifyTextInDocxInput
    
    def _run(self, filename: str, modifications: List[Dict[str, str]]) -> str:
        """
        执行Word修改操作
        
        Args:
            filename: 文件名或路径
            modifications: 修改列表
        
        Returns:
            str: 操作结果（JSON格式），包含下载链接
        """
        logger.info(f"工具调用: modify_text_in_docx - 输入参数: filename={filename}, modifications={modifications}")
        
        file_path = get_file_path(filename)
        output_filename = get_output_filename(filename, "modified")
        result = file_tools.modify_text_in_docx(file_path, modifications, output_filename)
        
        if result.get("success"):
            logger.info(f"工具调用成功: modify_text_in_docx - 输出文件: {output_filename}")
            return build_result(
                success=True,
                message=f"Word修改完成，已生成文件: {output_filename}",
                output_filename=output_filename,
                modifications=modifications,
                original_filename=extract_filename(filename)
            )
        else:
            logger.error(f"工具调用失败: modify_text_in_docx - 错误: {result.get('error', 'Word修改失败')}")
            return build_result(
                success=False,
                message=result.get("error", "Word修改失败")
            )


class AddReviewCommentsInput(BaseModel):
    """
    添加审查意见工具的输入参数
    """
    filename: str = Field(description="原文件名（只需文件名，不需要路径）")
    comments: List[Dict[str, Any]] = Field(
        description="审查意见列表，每项包含text（原文内容）、comment（审查意见）、risk_level（风险等级：高/中/低）"
    )


class AddReviewCommentsTool(BaseTool):
    """
    添加审查意见工具
    
    用于生成包含审查意见的报告文档
    """
    
    name: str = "add_review_comments"
    description: str = "生成制度审查报告，包含审查意见汇总和原文标注。只需输入文件名（如：document.pdf），不需要输入完整路径。"
    args_schema: Type[BaseModel] = AddReviewCommentsInput
    
    def _run(self, filename: str, comments: List[Dict[str, Any]]) -> str:
        """
        执行添加审查意见操作
        
        Args:
            filename: 文件名或路径
            comments: 审查意见列表
        
        Returns:
            str: 操作结果（JSON格式），包含下载链接
        """
        logger.info(f"工具调用: add_review_comments - 输入参数: filename={filename}, comments_count={len(comments)}")
        
        file_path = get_file_path(filename)
        
        filename = extract_filename(filename)
        name, ext = os.path.splitext(filename)
        output_filename = f"reviewed_{name}.docx"
        
        result = file_tools.add_review_comments(file_path, comments, output_filename)
        
        if result.get("success"):
            logger.info(f"工具调用成功: add_review_comments - 输出文件: {output_filename}")
            return build_result(
                success=True,
                message=f"审查报告生成完成，已生成文件: {output_filename}",
                output_filename=output_filename,
                comments_count=len(comments),
                original_filename=extract_filename(filename)
            )
        else:
            logger.error(f"工具调用失败: add_review_comments - 错误: {result.get('error', '审查报告生成失败')}")
            return build_result(
                success=False,
                message=result.get("error", "审查报告生成失败")
            )


class AddRuleInput(BaseModel):
    """
    添加规则工具的输入参数
    """
    title: str = Field(description="规则标题，简短概括规则内容，如'科研成果处置规则'")
    content: str = Field(description="规则的详细内容描述，完整描述规则的具体要求")
    rule_type: str = Field(default="global", description="规则类型：global-全局规则（对所有对话生效），conversation-对话规则（仅对特定对话生效）")
    conversation_id: Optional[int] = Field(default=None, description="对话ID，仅当rule_type为conversation时需要提供")
    category: Optional[str] = Field(default=None, description="规则分类，如：审计规则、合规规则、科研规则、财务规则等")
    priority: Optional[int] = Field(default=0, description="优先级，数字越大优先级越高，默认为0")


class AddRuleTool(BaseTool):
    """
    添加规则工具
    
    用于添加单条规章或规则到数据库
    """
    
    name: str = "add_rule"
    description: str = """【重要】添加一条规章或规则到数据库。当用户提到"添加规则"、"添加规章"、"记录规则"、"保存规则"等关键词时，必须调用此工具。

参数要求：
- title: 规则标题（必填），简短概括
- content: 规则内容（必填），完整描述
- rule_type: global（全局规则）或 conversation（对话规则），默认 global
- category: 规则分类，如"科研规则"、"审计规则"等
- priority: 优先级，数字越大优先级越高

示例：
用户："帮我添加一个全局规章：科研成果由个人自行处置"
调用：add_rule(title="科研成果处置规则", content="科研成果由个人自行处置...", rule_type="global", category="科研规则")"""
    args_schema: Type[BaseModel] = AddRuleInput
    
    def _run(
        self,
        title: str,
        content: str,
        rule_type: str = "global",
        conversation_id: Optional[int] = None,
        category: Optional[str] = None,
        priority: int = 0
    ) -> str:
        """
        执行添加规则操作
        
        Args:
            title: 规则标题
            content: 规则内容
            rule_type: 规则类型
            conversation_id: 对话ID
            category: 规则分类
            priority: 优先级
        
        Returns:
            str: 操作结果（JSON格式）
        """
        logger.info(f"工具调用: add_rule - 输入参数: title={title}, content={content[:50]}..., rule_type={rule_type}, category={category}, priority={priority}")
        
        from db import get_db
        from services.rule_service import RuleService
        
        try:
            db = next(get_db())
            rule_service = RuleService(db)
            
            rule = rule_service.create_rule(
                title=title,
                content=content,
                rule_type=rule_type,
                conversation_id=conversation_id,
                category=category,
                priority=priority
            )
            
            result = {
                "success": True,
                "message": f"规则添加成功: {title}",
                "rule_id": rule.id,
                "rule_type": rule_type,
                "title": title
            }
            
            logger.info(f"工具调用成功: add_rule - ID: {rule.id}, 标题: {title}")
            
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"工具调用失败: add_rule - 错误: {str(e)}", exc_info=True)
            result = {
                "success": False,
                "message": f"规则添加失败: {str(e)}"
            }
            return json.dumps(result, ensure_ascii=False, indent=2)


class AddRulesInput(BaseModel):
    """
    批量添加规则工具的输入参数
    """
    rules: List[Dict[str, Any]] = Field(description="规则列表，每项包含 title（标题）、content（内容）、rule_type（类型）、category（分类）、priority（优先级）等字段")
    conversation_id: Optional[int] = Field(default=None, description="对话ID，用于对话规则")


class AddRulesTool(BaseTool):
    """
    批量添加规则工具
    
    用于批量添加多条规章或规则到数据库
    """
    
    name: str = "add_rules"
    description: str = """批量添加多条规章或规则到数据库。

使用场景：
- 用户要求一次性添加多条规章或规则
- 用户提到"添加这些规则"、"批量添加规章"等
- 需要将多个相关规定一起保存

参数说明：
- rules: 规则列表，每项包含 title、content、rule_type、category、priority
- conversation_id: 对话ID（可选）"""
    args_schema: Type[BaseModel] = AddRulesInput
    
    def _run(
        self,
        rules: List[Dict[str, Any]],
        conversation_id: Optional[int] = None
    ) -> str:
        """
        执行批量添加规则操作
        
        Args:
            rules: 规则列表
            conversation_id: 对话ID
        
        Returns:
            str: 操作结果（JSON格式）
        """
        logger.info(f"工具调用: add_rules - 输入参数: rules_count={len(rules)}, conversation_id={conversation_id}")
        
        from db import get_db
        from services.rule_service import RuleService
        
        try:
            db = next(get_db())
            rule_service = RuleService(db)
            
            created_rules = rule_service.batch_create_rules(rules, conversation_id)
            
            result = {
                "success": True,
                "message": f"成功添加 {len(created_rules)} 条规则",
                "count": len(created_rules),
                "rule_ids": [rule.id for rule in created_rules]
            }
            
            logger.info(f"工具调用成功: add_rules - 添加数量: {len(created_rules)}")
            
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"工具调用失败: add_rules - 错误: {str(e)}", exc_info=True)
            result = {
                "success": False,
                "message": f"批量规则添加失败: {str(e)}"
            }
            return json.dumps(result, ensure_ascii=False, indent=2)


def get_file_tools() -> List[BaseTool]:
    """
    获取所有文件操作工具
    
    Returns:
        List[BaseTool]: 工具列表
    """
    return [
        ReadFileTool(),
        HighlightTextInPDFTool(),
        ModifyTextInPDFTool(),
        HighlightTextInDocxTool(),
        ModifyTextInDocxTool(),
        AddReviewCommentsTool(),
        AddRuleTool(),
        AddRulesTool(),
    ]
