"""
认证API路由
提供用户登录、注册、信息获取等接口
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from db import get_db
from models.user import User, UserRole
from services.user_service import UserService
from utils.auth import create_access_token, verify_token
from utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


class RegisterRequest(BaseModel):
    """注册请求模型"""
    username: str = Field(..., description="用户名", min_length=2, max_length=50)
    account: str = Field(..., description="登录账号", min_length=3, max_length=50)
    password: str = Field(..., description="密码", min_length=6, max_length=50)
    phone: Optional[str] = Field(None, description="手机号", max_length=20)
    department: Optional[str] = Field(None, description="部门", max_length=100)


class LoginRequest(BaseModel):
    """登录请求模型"""
    account: str = Field(..., description="登录账号")
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    account: str
    phone: Optional[str]
    department: Optional[str]
    role: str
    is_active: bool
    
    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UpdateUserRequest(BaseModel):
    """更新用户请求模型"""
    username: Optional[str] = Field(None, description="用户名", min_length=2, max_length=50)
    phone: Optional[str] = Field(None, description="手机号", max_length=20)
    department: Optional[str] = Field(None, description="部门", max_length=100)


class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., description="新密码", min_length=6, max_length=50)


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前登录用户
    
    Args:
        authorization: Authorization头
        db: 数据库会话
    
    Returns:
        User: 当前用户
    
    Raises:
        HTTPException: 未登录或令牌无效时抛出401错误
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="未登录")
    
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    else:
        token = authorization
    
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="令牌无效或已过期")
    
    service = UserService(db)
    user = service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前管理员用户
    
    Args:
        current_user: 当前用户
    
    Returns:
        User: 当前管理员用户
    
    Raises:
        HTTPException: 非管理员时抛出403错误
    """
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    return current_user


@router.post("/register", response_model=UserResponse, summary="用户注册")
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    用户注册
    
    创建新用户账号
    
    Args:
        request: 注册请求
        db: 数据库会话
    
    Returns:
        UserResponse: 用户信息
    """
    logger.info(f"用户注册 - 账号: {request.account}")
    
    service = UserService(db)
    
    try:
        user = service.create_user(
            username=request.username,
            account=request.account,
            password=request.password,
            phone=request.phone,
            department=request.department,
            role=UserRole.USER.value
        )
        
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=LoginResponse, summary="用户登录")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    用户登录
    
    验证账号密码，返回访问令牌
    
    Args:
        request: 登录请求
        db: 数据库会话
    
    Returns:
        LoginResponse: 登录响应（包含令牌和用户信息）
    """
    logger.info(f"用户登录 - 账号: {request.account}")
    
    service = UserService(db)
    user = service.authenticate(request.account, request.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="账号或密码错误")
    
    access_token = create_access_token({"user_id": user.id, "sub": user.id})
    
    return LoginResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户信息
    
    Args:
        current_user: 当前用户
    
    Returns:
        UserResponse: 用户信息
    """
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse, summary="更新当前用户信息")
def update_current_user_info(
    request: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新当前用户信息
    
    Args:
        request: 更新请求
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        UserResponse: 更新后的用户信息
    """
    service = UserService(db)
    user = service.update_user(
        user_id=current_user.id,
        username=request.username,
        phone=request.phone,
        department=request.department
    )
    
    return UserResponse.model_validate(user)


@router.post("/change-password", summary="修改密码")
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改密码
    
    Args:
        request: 修改密码请求
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        dict: 操作结果
    """
    service = UserService(db)
    success = service.update_password(
        user_id=current_user.id,
        old_password=request.old_password,
        new_password=request.new_password
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="旧密码错误")
    
    return {"message": "密码修改成功"}


@router.get("/list", response_model=dict, summary="获取用户列表（管理员）")
def get_user_list(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    department: Optional[str] = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    获取用户列表（管理员）
    
    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        role: 按角色筛选
        department: 按部门筛选
        current_user: 当前管理员用户
        db: 数据库会话
    
    Returns:
        dict: 用户列表
    """
    service = UserService(db)
    users, total = service.get_all_users(skip, limit, role, department)
    
    return {
        "total": total,
        "items": [UserResponse.model_validate(u) for u in users]
    }


@router.put("/{user_id}/reset-password", summary="重置用户密码（管理员）")
def reset_user_password(
    user_id: int,
    new_password: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    重置用户密码（管理员）
    
    Args:
        user_id: 用户ID
        new_password: 新密码
        current_user: 当前管理员用户
        db: 数据库会话
    
    Returns:
        dict: 操作结果
    """
    service = UserService(db)
    success = service.reset_password(user_id, new_password)
    
    if not success:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {"message": "密码重置成功"}


@router.put("/{user_id}/status", summary="启用/禁用用户（管理员）")
def toggle_user_status(
    user_id: int,
    is_active: bool,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    启用/禁用用户（管理员）
    
    Args:
        user_id: 用户ID
        is_active: 是否激活
        current_user: 当前管理员用户
        db: 数据库会话
    
    Returns:
        dict: 操作结果
    """
    service = UserService(db)
    user = service.update_user(user_id, is_active=is_active)
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {"message": "用户状态更新成功"}
