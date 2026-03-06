"""
PDF文件解析模块
支持解析PDF文件中的文本、图片、表格等内容
"""

import os
from typing import List, Optional
from pathlib import Path
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from config import settings


class PDFParser:
    """
    PDF文件解析器
    
    解析PDF文件并提取文本内容，支持分块处理
    
    Attributes:
        chunk_size: 文本分块大小
        chunk_overlap: 分块重叠大小
    """
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        初始化PDF解析器
        
        Args:
            chunk_size: 文本分块大小，默认使用配置中的值
            chunk_overlap: 分块重叠大小，默认使用配置中的值
        """
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
        )
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        从PDF文件中提取文本
        
        Args:
            file_path: PDF文件路径
        
        Returns:
            str: 提取的文本内容
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        reader = PdfReader(file_path)
        text_content = []
        
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if text:
                text_content.append(f"[第{page_num}页]\n{text}")
        
        return "\n\n".join(text_content)
    
    def parse_pdf_to_documents(self, file_path: str, metadata: Optional[dict] = None) -> List[Document]:
        """
        解析PDF文件并转换为Document对象列表
        
        Args:
            file_path: PDF文件路径
            metadata: 额外的元数据
        
        Returns:
            List[Document]: Document对象列表
        """
        text = self.extract_text_from_pdf(file_path)
        
        if not text.strip():
            return []
        
        base_metadata = {
            "source": file_path,
            "file_name": Path(file_path).name
        }
        
        if metadata:
            base_metadata.update(metadata)
        
        documents = self.text_splitter.create_documents(
            texts=[text],
            metadatas=[base_metadata]
        )
        
        return documents
    
    def parse_pdf_to_texts(self, file_path: str) -> List[str]:
        """
        解析PDF文件并转换为文本列表
        
        Args:
            file_path: PDF文件路径
        
        Returns:
            List[str]: 文本片段列表
        """
        documents = self.parse_pdf_to_documents(file_path)
        return [doc.page_content for doc in documents]
    
    def get_pdf_info(self, file_path: str) -> dict:
        """
        获取PDF文件基本信息
        
        Args:
            file_path: PDF文件路径
        
        Returns:
            dict: PDF文件信息
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        reader = PdfReader(file_path)
        
        return {
            "file_path": file_path,
            "file_name": Path(file_path).name,
            "page_count": len(reader.pages),
            "file_size": os.path.getsize(file_path)
        }
