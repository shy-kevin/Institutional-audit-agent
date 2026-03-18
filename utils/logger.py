"""
日志配置模块
提供统一的日志配置和管理功能
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime


class LogConfig:
    """
    日志配置类
    
    提供统一的日志配置，支持按级别分文件存储
    """
    
    _initialized = False
    
    @classmethod
    def setup_logging(cls, log_dir: str = "logs", log_level: str = "INFO"):
        """
        设置日志配置
        
        Args:
            log_dir: 日志目录
            log_level: 日志级别
        """
        if cls._initialized:
            return
        
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        formatter = logging.Formatter(log_format, datefmt=date_format)
        
        all_handler = RotatingFileHandler(
            log_path / 'all.log',
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        all_handler.setLevel(logging.DEBUG)
        all_handler.setFormatter(formatter)
        
        info_handler = RotatingFileHandler(
            log_path / 'info.log',
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        info_handler.setLevel(logging.INFO)
        info_handler.setFormatter(formatter)
        
        error_handler = RotatingFileHandler(
            log_path / 'error.log',
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        
        debug_handler = RotatingFileHandler(
            log_path / 'debug.log',
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(formatter)
        debug_handler.addFilter(lambda record: record.levelno == logging.DEBUG)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        root_logger.handlers.clear()
        
        root_logger.addHandler(all_handler)
        root_logger.addHandler(info_handler)
        root_logger.addHandler(error_handler)
        root_logger.addHandler(debug_handler)
        root_logger.addHandler(console_handler)
        
        cls._initialized = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        获取指定名称的logger
        
        Args:
            name: logger名称
        
        Returns:
            logging.Logger: logger实例
        """
        return logging.getLogger(name)


def setup_logger(name: str = None) -> logging.Logger:
    """
    设置并获取logger
    
    Args:
        name: logger名称，通常使用 __name__
    
    Returns:
        logging.Logger: logger实例
    """
    if not LogConfig._initialized:
        LogConfig.setup_logging()
    
    return LogConfig.get_logger(name or __name__)
