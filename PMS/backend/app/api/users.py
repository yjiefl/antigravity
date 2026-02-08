"""
用户管理 API 路由

处理用户 CRUD 和组织架构管理
"""
import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import get_db, get_password_hash
from app.models import User, Organization, Department, Position, UserRole, UserRoleBinding
from app.schemas import (
    UserCreate, UserUpdate, UserResponse, UserBrief,
)
from app.api.auth import get_current_user, get_current_admin

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
    
    return result.scalars().all()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin)],
):
    """
    创建用户（仅管理员）
    """
    # 检查用户名是否已存在
    result = await db.execute(
        select(User).where(User.username == user_in.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 创建用户
    user = User(
        username=user_in.username,
        password_hash=get_password_hash(user_in.password),
        real_name=user_in.real_name,
        email=user_in.email,
        phone=user_in.phone,
        department_id=user_in.department_id,
        position_id=user_in.position_id,
    )
    
    db.add(user)
    await db.flush()
    
    # 绑定角色
    for role in user_in.roles:
        binding = UserRoleBinding(user_id=user.id, role=role)
        db.add(binding)
        
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
    user = result.scalar_one_or_none()
    
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
    user = result.scalar_one_or_none()
    
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
    user = result.scalar_one_or_none()
    
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


