"""
用户服务模块
提供用户的CRUD操作和认证功能
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
import bcrypt
from models.user import User, UserRole
from utils.logger import setup_logger

logger = setup_logger(__name__)


class UserService:
    """
    用户服务类
    
    提供用户的创建、查询、更新、删除等操作，
    以及密码加密、验证等认证功能
    """
    
    def __init__(self, db: Session):
        """
        初始化用户服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        logger.debug("用户服务初始化完成")
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        加密密码
        
        Args:
            password: 明文密码
        
        Returns:
            str: 加密后的密码
        """
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        验证密码
        
        Args:
            plain_password: 明文密码
            hashed_password: 加密后的密码
        
        Returns:
            bool: 密码是否正确
        """
        try:
            password_bytes = plain_password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception as e:
            logger.error(f"密码验证失败: {str(e)}")
            return False
    
    def create_user(
        self,
        username: str,
        account: str,
        password: str,
        phone: Optional[str] = None,
        department: Optional[str] = None,
        role: str = UserRole.USER.value
    ) -> User:
        """
        创建用户
        
        Args:
            username: 用户名
            account: 登录账号
            password: 密码（明文，会自动加密）
            phone: 手机号
            department: 部门
            role: 用户角色
        
        Returns:
            User: 创建的用户对象
        
        Raises:
            ValueError: 账号已存在时抛出异常
        """
        logger.info(f"创建用户 - 账号: {account}, 用户名: {username}")
        
        existing_user = self.get_user_by_account(account)
        if existing_user:
            logger.error(f"账号已存在 - 账号: {account}")
            raise ValueError("账号已存在")
        
        hashed_password = self.hash_password(password)
        
        user = User(
            username=username,
            account=account,
            password=hashed_password,
            phone=phone,
            department=department,
            role=role
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"用户创建成功 - ID: {user.id}, 账号: {account}")
        return user
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        根据ID获取用户
        
        Args:
            user_id: 用户ID
        
        Returns:
            Optional[User]: 用户对象，不存在则返回None
        """
        logger.debug(f"查询用户 - ID: {user_id}")
        
        result = self.db.query(User).filter(
            User.id == user_id,
            User.is_active == True
        ).first()
        
        if result:
            logger.debug(f"用户查询成功 - ID: {user_id}")
        else:
            logger.debug(f"用户不存在 - ID: {user_id}")
        
        return result
    
    def get_user_by_account(self, account: str) -> Optional[User]:
        """
        根据账号获取用户
        
        Args:
            account: 登录账号
        
        Returns:
            Optional[User]: 用户对象，不存在则返回None
        """
        logger.debug(f"查询用户 - 账号: {account}")
        
        result = self.db.query(User).filter(
            User.account == account
        ).first()
        
        return result
    
    def get_all_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
        department: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> tuple[List[User], int]:
        """
        获取所有用户列表
        
        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数
            role: 按角色筛选
            department: 按部门筛选
            is_active: 按激活状态筛选
        
        Returns:
            tuple[List[User], int]: (用户列表, 总数)
        """
        logger.debug(f"查询用户列表 - skip: {skip}, limit: {limit}")
        
        query = self.db.query(User)
        
        if role:
            query = query.filter(User.role == role)
        if department:
            query = query.filter(User.department == department)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        total = query.count()
        users = query.order_by(
            User.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        logger.info(f"用户列表查询完成 - 总数: {total}, 返回: {len(users)}")
        return users, total
    
    def update_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        phone: Optional[str] = None,
        department: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[User]:
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            username: 新用户名
            phone: 新手机号
            department: 新部门
            role: 新角色
            is_active: 是否激活
        
        Returns:
            Optional[User]: 更新后的用户对象
        """
        logger.info(f"更新用户 - ID: {user_id}")
        
        user = self.get_user_by_id(user_id)
        if not user:
            logger.error(f"用户不存在 - ID: {user_id}")
            return None
        
        if username is not None:
            user.username = username
        if phone is not None:
            user.phone = phone
        if department is not None:
            user.department = department
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"用户更新成功 - ID: {user_id}")
        return user
    
    def update_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        修改密码
        
        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码
        
        Returns:
            bool: 修改是否成功
        """
        logger.info(f"修改密码 - 用户ID: {user_id}")
        
        user = self.get_user_by_id(user_id)
        if not user:
            logger.error(f"用户不存在 - ID: {user_id}")
            return False
        
        if not self.verify_password(old_password, user.password):
            logger.error(f"旧密码错误 - 用户ID: {user_id}")
            return False
        
        user.password = self.hash_password(new_password)
        self.db.commit()
        
        logger.info(f"密码修改成功 - 用户ID: {user_id}")
        return True
    
    def reset_password(
        self,
        user_id: int,
        new_password: str
    ) -> bool:
        """
        重置密码（管理员操作）
        
        Args:
            user_id: 用户ID
            new_password: 新密码
        
        Returns:
            bool: 重置是否成功
        """
        logger.info(f"重置密码 - 用户ID: {user_id}")
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"用户不存在 - ID: {user_id}")
            return False
        
        user.password = self.hash_password(new_password)
        self.db.commit()
        
        logger.info(f"密码重置成功 - 用户ID: {user_id}")
        return True
    
    def update_last_login(self, user_id: int) -> None:
        """
        更新最后登录时间
        
        Args:
            user_id: 用户ID
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.last_login = datetime.now()
            self.db.commit()
    
    def delete_user(self, user_id: int) -> bool:
        """
        删除用户（软删除，设置is_active为False）
        
        Args:
            user_id: 用户ID
        
        Returns:
            bool: 删除是否成功
        """
        logger.info(f"删除用户 - ID: {user_id}")
        
        user = self.get_user_by_id(user_id)
        if not user:
            logger.error(f"用户不存在 - ID: {user_id}")
            return False
        
        user.is_active = False
        self.db.commit()
        
        logger.info(f"用户删除成功 - ID: {user_id}")
        return True
    
    def authenticate(self, account: str, password: str) -> Optional[User]:
        """
        用户认证
        
        Args:
            account: 登录账号
            password: 密码
        
        Returns:
            Optional[User]: 认证成功返回用户对象，失败返回None
        """
        logger.info(f"用户认证 - 账号: {account}")
        
        user = self.get_user_by_account(account)
        
        if not user:
            logger.warning(f"用户不存在 - 账号: {account}")
            return None
        
        if not user.is_active:
            logger.warning(f"用户已禁用 - 账号: {account}")
            return None
        
        if not self.verify_password(password, user.password):
            logger.warning(f"密码错误 - 账号: {account}")
            return None
        
        self.update_last_login(user.id)
        
        logger.info(f"用户认证成功 - 账号: {account}")
        return user
    
    def is_admin(self, user_id: int) -> bool:
        """
        判断用户是否为管理员
        
        Args:
            user_id: 用户ID
        
        Returns:
            bool: 是否为管理员
        """
        user = self.get_user_by_id(user_id)
        return user is not None and user.role == UserRole.ADMIN.value
