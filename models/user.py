"""
用户实体类
用于存储用户信息
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
from db.mysql_session import Base
import enum


class UserRole(str, enum.Enum):
    """
    用户角色枚举
    """
    ADMIN = "admin"
    USER = "user"


class User(Base):
    """
    用户实体类
    存储用户的基本信息，包括用户名、账号、密码、手机号、部门等
    
    Attributes:
        id: 用户唯一标识
        username: 用户名（显示名称）
        account: 登录账号（唯一）
        password: 密码（加密存储）
        phone: 手机号
        department: 部门
        role: 用户角色（admin/user）
        is_active: 是否激活
        last_login: 最后登录时间
        created_at: 创建时间
        updated_at: 更新时间
    """
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="用户ID")
    username = Column(String(100), nullable=False, comment="用户名")
    account = Column(String(100), unique=True, nullable=False, comment="登录账号")
    password = Column(String(255), nullable=False, comment="密码（加密）")
    phone = Column(String(20), nullable=True, comment="手机号")
    department = Column(String(100), nullable=True, comment="部门")
    role = Column(String(20), default=UserRole.USER.value, comment="角色：admin/user")
    is_active = Column(Boolean, default=True, comment="是否激活")
    last_login = Column(DateTime, nullable=True, comment="最后登录时间")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    def to_dict(self) -> dict:
        """
        将实体转换为字典格式
        
        Returns:
            dict: 包含实体属性的字典（不包含密码）
        """
        return {
            "id": self.id,
            "username": self.username,
            "account": self.account,
            "phone": self.phone,
            "department": self.department,
            "role": self.role,
            "is_active": self.is_active,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
