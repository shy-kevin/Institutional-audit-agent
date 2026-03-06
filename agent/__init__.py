"""
智能体模块初始化文件
"""

from .audit_agent import AuditAgent, create_audit_agent
from .tools import (
    get_file_tools,
    ReadFileTool,
    HighlightTextInPDFTool,
    ModifyTextInPDFTool,
    HighlightTextInDocxTool,
    ModifyTextInDocxTool,
    AddReviewCommentsTool
)

__all__ = [
    "AuditAgent",
    "create_audit_agent",
    "get_file_tools",
    "ReadFileTool",
    "HighlightTextInPDFTool",
    "ModifyTextInPDFTool",
    "HighlightTextInDocxTool",
    "ModifyTextInDocxTool",
    "AddReviewCommentsTool"
]
