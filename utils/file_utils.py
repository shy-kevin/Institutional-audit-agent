"""
文件处理工具模块
提供文件上传、保存、验证等功能
"""

import os
import aiofiles
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
from config import settings


class FileProcessor:
    """
    文件处理工具类
    
    提供文件验证、保存、删除等功能
    
    Attributes:
        upload_dir: 上传文件存储目录
        allowed_extensions: 允许的文件扩展名
        max_size: 最大文件大小
    """
    
    def __init__(self):
        """
        初始化文件处理器
        """
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.allowed_extensions = settings.ALLOWED_EXTENSIONS
        self.max_size = settings.MAX_UPLOAD_SIZE
        self._ensure_upload_dir()
    
    def _ensure_upload_dir(self):
        """
        确保上传目录存在
        """
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_file(self, file: UploadFile) -> tuple[bool, str]:
        """
        验证上传的文件
        
        Args:
            file: 上传的文件对象
        
        Returns:
            tuple[bool, str]: (是否验证通过, 错误消息)
        """
        if not file.filename:
            return False, "文件名不能为空"
        
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.allowed_extensions:
            return False, f"不支持的文件类型: {file_ext}，仅支持: {self.allowed_extensions}"
        
        return True, ""
    
    def get_file_path(self, filename: str, subfolder: Optional[str] = None) -> Path:
        """
        获取文件存储路径
        
        Args:
            filename: 文件名
            subfolder: 子文件夹名称
        
        Returns:
            Path: 文件完整路径
        """
        if subfolder:
            folder = self.upload_dir / subfolder
            folder.mkdir(parents=True, exist_ok=True)
            return folder / filename
        return self.upload_dir / filename
    
    async def save_file(self, file: UploadFile, subfolder: Optional[str] = None) -> tuple[str, int]:
        """
        异步保存上传的文件
        
        Args:
            file: 上传的文件对象
            subfolder: 子文件夹名称
        
        Returns:
            tuple[str, int]: (文件路径, 文件大小)
        """
        file_path = self.get_file_path(file.filename, subfolder)
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return str(file_path), len(content)
    
    def delete_file(self, file_path: str) -> bool:
        """
        删除文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            bool: 删除是否成功
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
            return True
        except Exception:
            return False
    
    def get_file_size(self, file_path: str) -> int:
        """
        获取文件大小
        
        Args:
            file_path: 文件路径
        
        Returns:
            int: 文件大小（字节）
        """
        try:
            return Path(file_path).stat().st_size
        except Exception:
            return 0


file_processor = FileProcessor()


async def save_upload_file(file: UploadFile, subfolder: Optional[str] = None) -> tuple[str, str, int]:
    """
    保存上传文件的便捷函数
    
    Args:
        file: 上传的文件对象
        subfolder: 子文件夹名称
    
    Returns:
        tuple[str, str, int]: (文件路径, 原始文件名, 文件大小)
    
    Raises:
        ValueError: 文件验证失败时抛出
    """
    is_valid, error_msg = file_processor.validate_file(file)
    if not is_valid:
        raise ValueError(error_msg)
    
    file_path, file_size = await file_processor.save_file(file, subfolder)
    return file_path, file.filename, file_size
