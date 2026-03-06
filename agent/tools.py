"""
LangChain 工具定义模块
定义智能体可使用的工具
"""

import os
from typing import Optional, List, Dict, Any, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from utils.file_tools import file_tools
from config import settings


def get_file_path(filename: str) -> str:
    """
    根据文件名获取完整文件路径
    
    Args:
        filename: 文件名
    
    Returns:
        str: 完整文件路径
    """
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
    name, ext = os.path.splitext(filename)
    if prefix:
        return f"{prefix}_{name}{ext}"
    return filename


class ReadFileInput(BaseModel):
    """
    读取文件工具的输入参数
    """
    filename: str = Field(description="要读取的文件名（不含路径）")


class ReadFileTool(BaseTool):
    """
    读取文件工具
    
    用于读取PDF、Word、TXT等文件的内容
    """
    
    name: str = "read_file"
    description: str = "读取文件内容。支持PDF、Word(docx)、TXT等格式的文件。返回文件的完整内容和元数据信息。只需输入文件名即可。"
    args_schema: Type[BaseModel] = ReadFileInput
    
    def _run(self, filename: str) -> str:
        """
        执行读取文件操作
        
        Args:
            filename: 文件名
        
        Returns:
            str: 读取结果（JSON格式）
        """
        import json
        file_path = get_file_path(filename)
        result = file_tools.read_file_content(file_path)
        return json.dumps(result, ensure_ascii=False, indent=2)


class HighlightTextInPDFInput(BaseModel):
    """
    PDF标注工具的输入参数
    """
    filename: str = Field(description="原PDF文件名（不含路径）")
    highlight_texts: List[str] = Field(description="需要标注（标红）的文字列表")


class HighlightTextInPDFTool(BaseTool):
    """
    PDF文字标注工具
    
    用于在PDF文件中标注指定文字（标红显示）
    """
    
    name: str = "highlight_text_in_pdf"
    description: str = "在PDF文件中标注指定的文字，将文字以红色高亮显示。用于标记需要关注的内容或风险点。只需输入文件名即可。"
    args_schema: Type[BaseModel] = HighlightTextInPDFInput
    
    def _run(self, filename: str, highlight_texts: List[str]) -> str:
        """
        执行PDF标注操作
        
        Args:
            filename: 文件名
            highlight_texts: 需要标注的文字列表
        
        Returns:
            str: 操作结果（JSON格式）
        """
        import json
        file_path = get_file_path(filename)
        output_filename = get_output_filename(filename, "highlighted")
        result = file_tools.highlight_text_in_pdf(file_path, highlight_texts, output_filename)
        return json.dumps(result, ensure_ascii=False, indent=2)


class ModifyTextInPDFInput(BaseModel):
    """
    PDF修改工具的输入参数
    """
    filename: str = Field(description="原PDF文件名（不含路径）")
    modifications: List[Dict[str, str]] = Field(
        description="修改列表，每项包含old_text（要修改的原文）和new_text（修改后的新文本）"
    )


class ModifyTextInPDFTool(BaseTool):
    """
    PDF文字修改工具
    
    用于修改PDF文件中的文字内容
    """
    
    name: str = "modify_text_in_pdf"
    description: str = "修改PDF文件中的文字内容。将指定的旧文本替换为新文本。用于根据审查意见修改制度文件。只需输入文件名即可。"
    args_schema: Type[BaseModel] = ModifyTextInPDFInput
    
    def _run(self, filename: str, modifications: List[Dict[str, str]]) -> str:
        """
        执行PDF修改操作
        
        Args:
            filename: 文件名
            modifications: 修改列表
        
        Returns:
            str: 操作结果（JSON格式）
        """
        import json
        file_path = get_file_path(filename)
        output_filename = get_output_filename(filename, "modified")
        result = file_tools.modify_text_in_pdf(file_path, modifications, output_filename)
        return json.dumps(result, ensure_ascii=False, indent=2)


class HighlightTextInDocxInput(BaseModel):
    """
    Word标注工具的输入参数
    """
    filename: str = Field(description="原Word文件名（不含路径）")
    highlight_texts: List[str] = Field(description="需要标注（标红）的文字列表")


class HighlightTextInDocxTool(BaseTool):
    """
    Word文字标注工具
    
    用于在Word文件中标注指定文字（标红显示）
    """
    
    name: str = "highlight_text_in_docx"
    description: str = "在Word文件中标注指定的文字，将文字以红色高亮显示。用于标记需要关注的内容或风险点。只需输入文件名即可。"
    args_schema: Type[BaseModel] = HighlightTextInDocxInput
    
    def _run(self, filename: str, highlight_texts: List[str]) -> str:
        """
        执行Word标注操作
        
        Args:
            filename: 文件名
            highlight_texts: 需要标注的文字列表
        
        Returns:
            str: 操作结果（JSON格式）
        """
        import json
        file_path = get_file_path(filename)
        output_filename = get_output_filename(filename, "highlighted")
        result = file_tools.create_highlighted_docx(file_path, highlight_texts, output_filename)
        return json.dumps(result, ensure_ascii=False, indent=2)


class ModifyTextInDocxInput(BaseModel):
    """
    Word修改工具的输入参数
    """
    filename: str = Field(description="原Word文件名（不含路径）")
    modifications: List[Dict[str, str]] = Field(
        description="修改列表，每项包含old_text（要修改的原文）和new_text（修改后的新文本）"
    )


class ModifyTextInDocxTool(BaseTool):
    """
    Word文字修改工具
    
    用于修改Word文件中的文字内容
    """
    
    name: str = "modify_text_in_docx"
    description: str = "修改Word文件中的文字内容。将指定的旧文本替换为新文本。用于根据审查意见修改制度文件。只需输入文件名即可。"
    args_schema: Type[BaseModel] = ModifyTextInDocxInput
    
    def _run(self, filename: str, modifications: List[Dict[str, str]]) -> str:
        """
        执行Word修改操作
        
        Args:
            filename: 文件名
            modifications: 修改列表
        
        Returns:
            str: 操作结果（JSON格式）
        """
        import json
        file_path = get_file_path(filename)
        output_filename = get_output_filename(filename, "modified")
        result = file_tools.modify_text_in_docx(file_path, modifications, output_filename)
        return json.dumps(result, ensure_ascii=False, indent=2)


class AddReviewCommentsInput(BaseModel):
    """
    添加审查意见工具的输入参数
    """
    filename: str = Field(description="原文件名（不含路径）")
    comments: List[Dict[str, Any]] = Field(
        description="审查意见列表，每项包含text（原文内容）、comment（审查意见）、risk_level（风险等级：高/中/低）"
    )


class AddReviewCommentsTool(BaseTool):
    """
    添加审查意见工具
    
    用于生成包含审查意见的报告文档
    """
    
    name: str = "add_review_comments"
    description: str = "生成制度审查报告，包含审查意见汇总和原文标注。用于输出完整的审查结果报告。只需输入文件名即可。"
    args_schema: Type[BaseModel] = AddReviewCommentsInput
    
    def _run(self, filename: str, comments: List[Dict[str, Any]]) -> str:
        """
        执行添加审查意见操作
        
        Args:
            filename: 文件名
            comments: 审查意见列表
        
        Returns:
            str: 操作结果（JSON格式）
        """
        import json
        file_path = get_file_path(filename)
        output_filename = get_output_filename(filename, "reviewed")
        result = file_tools.add_review_comments(file_path, comments, output_filename)
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
    ]
