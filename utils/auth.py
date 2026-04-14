"""
认证工具模块
提供JWT令牌生成、验证等功能
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from utils.logger import setup_logger

logger = setup_logger(__name__)

JWT_SECRET_KEY = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌
    
    Args:
        data: 要编码的数据（通常包含user_id）
        expires_delta: 过期时间间隔
    
    Returns:
        str: JWT令牌
    """
    to_encode = data.copy()
    
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    logger.debug(f"创建访问令牌成功，过期时间: {expire}")
    
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码令牌
    
    Args:
        token: JWT令牌
    
    Returns:
        Optional[Dict]: 解码后的数据，失败返回None
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        logger.debug("令牌解码成功")
        return payload
    except JWTError as e:
        logger.error(f"令牌解码失败: {str(e)}")
        return None


def verify_token(token: str) -> Optional[int]:
    """
    验证令牌并返回用户ID
    
    Args:
        token: JWT令牌
    
    Returns:
        Optional[int]: 用户ID，验证失败返回None
    """
    payload = decode_token(token)
    if payload is None:
        return None
    
    user_id = payload.get("sub") or payload.get("user_id")
    if user_id is None:
        logger.error("令牌中缺少用户ID")
        return None
    
    try:
        return int(user_id)
    except (ValueError, TypeError):
        logger.error(f"无效的用户ID: {user_id}")
        return None
