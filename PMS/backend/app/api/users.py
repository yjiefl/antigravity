"""
用户管理 API 路由

处理用户 CRUD 和组织架构管理
"""
import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import get_db, get_password_hash
from app.models import User, Organization, Department, Position, UserRole, UserRoleBinding, AuditModule, AuditAction
from app.schemas import (
    UserCreate, UserUpdate, UserResponse, UserBrief, PasswordReset,
)
from app.api.auth import get_current_user, get_current_admin
from app.services import log_audit

router = APIRouter()


# ============ 用户管理 ============

@router.get("", response_model=List[UserBrief])
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    department_id: uuid.UUID = Query(None, description="按部门过滤"),
    role: UserRole = Query(None, description="按角色过滤"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """
    获取用户列表
    
    支持按部门和角色过滤
    """
    query = select(User).where(User.is_active == True)
    
    if department_id:
        query = query.where(User.department_id == department_id)
    if role:
        # 使用 any() 查询关联表
        query = query.where(User.roles_binding.any(role=role))
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    
    return result.unique().scalars().all()


@router.get("/manage", response_model=List[UserResponse])
async def manage_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    keyword: str = Query(None, description="搜索用户名或姓名"),
):
    """
    管理用户列表（包含禁用用户，仅管理员）
    """
    query = select(User)
    
    if keyword:
        query = query.where(
            (User.username.ilike(f"%{keyword}%")) | 
            (User.real_name.ilike(f"%{keyword}%"))
        )
    
    query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    
    return result.unique().scalars().all()


@router.get("/manage", response_model=List[UserResponse])
async def manage_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    keyword: str = Query(None, description="搜索用户名或姓名"),
):
    """
    管理用户列表（包含禁用用户，仅管理员）
    """
    query = select(User)
    
    if keyword:
        query = query.where(
            (User.username.ilike(f"%{keyword}%")) | 
            (User.real_name.ilike(f"%{keyword}%"))
        )
    
    query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    
    return result.unique().scalars().all()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin)],
    request: Request,
):
    """
    创建用户（仅管理员）
    """
    # 检查用户名是否已存在
    result = await db.execute(
        select(User).where(User.username == user_in.username)
    )
    if result.unique().scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 创建用户
    user = User(
        username=user_in.username,
        password_hash=get_password_hash(user_in.password),
        real_name=user_in.real_name,
        department_id=user_in.department_id,
        position_id=user_in.position_id,
    )
    
    db.add(user)
    await db.flush()
    
    # 绑定角色
    for role in user_in.roles:
        binding = UserRoleBinding(user_id=user.id, role=role)
        db.add(binding)
    
    # 记录审计日志
    await log_audit(
        db=db,
        user=current_user,
        module=AuditModule.USER,
        action=AuditAction.USER_CREATE,
        request=request,
        target_type="user",
        target_id=str(user.id),
        target_name=user.real_name,
        description=f"创建用户 {user.real_name} ({user.username})",
    )
        
    await db.flush()
    await db.refresh(user)
    
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    获取用户详情
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.unique().scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    user_in: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin)],
):
    """
    更新用户信息（仅管理员）
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.unique().scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if hasattr(user_in, 'roles') and user_in.roles is not None:
        # 清除旧角色
        stmt = select(UserRoleBinding).where(UserRoleBinding.user_id == user.id)
        result = await db.execute(stmt)
        old_bindings = result.scalars().all()
        for binding in old_bindings:
            await db.delete(binding)
        
        # 添加新角色
        for role in user_in.roles:
            binding = UserRoleBinding(user_id=user.id, role=role)
            db.add(binding)
    
    # 更新其他字段
    update_data = user_in.model_dump(exclude_unset=True)
    if 'roles' in update_data:
        del update_data['roles']
    
    for field, value in update_data.items():
        setattr(user, field, value)
            
    await db.flush()
    await db.refresh(user)
    
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin)],
):
    """
    删除用户（软删除，设置 is_active=False）
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.unique().scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    user.is_active = False
    await db.flush()


@router.patch("/{user_id}/status", response_model=UserResponse)
async def toggle_status(
    user_id: uuid.UUID,
    active: bool,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin)],
    request: Request,
):
    """
    启用/禁用用户
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.unique().scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
        
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能修改自己的状态")
    
    old_status = user.is_active
    user.is_active = active
    
    # 记录审计日志
    await log_audit(
        db=db,
        user=current_user,
        module=AuditModule.USER,
        action=AuditAction.USER_ENABLE if active else AuditAction.USER_DISABLE,
        request=request,
        target_type="user",
        target_id=str(user.id),
        target_name=user.real_name,
        description=f"{'启用' if active else '禁用'}用户 {user.real_name}",
        details={"old_status": old_status, "new_status": active},
    )
    
    await db.flush()
    await db.refresh(user)
    return user


@router.post("/{user_id}/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    user_id: uuid.UUID,
    password_in: PasswordReset,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin)],
    request: Request,
):
    """
    重置用户密码（仅管理员）
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.unique().scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
        
    user.password_hash = get_password_hash(password_in.new_password)
    
    # 记录审计日志
    await log_audit(
        db=db,
        user=current_user,
        module=AuditModule.USER,
        action=AuditAction.PASSWORD_RESET,
        request=request,
        target_type="user",
        target_id=str(user.id),
        target_name=user.real_name,
        description=f"重置用户 {user.real_name} 的密码",
    )
    
    await db.flush()
    
    return {"message": "密码重置成功"}


