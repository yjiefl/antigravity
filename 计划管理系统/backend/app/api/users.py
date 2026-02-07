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
from app.models import User, Organization, Department, Position, UserRole
from app.schemas import (
    UserCreate, UserUpdate, UserResponse, UserBrief,
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    DepartmentCreate, DepartmentUpdate, DepartmentResponse,
    PositionCreate, PositionUpdate, PositionResponse,
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
        query = query.where(User.role == role)
    
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
        role=user_in.role,
        department_id=user_in.department_id,
        position_id=user_in.position_id,
    )
    
    db.add(user)
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
    
    # 更新字段
    for field, value in user_in.model_dump(exclude_unset=True).items():
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


# ============ 组织架构管理 ============

@router.get("/org/organizations", response_model=List[OrganizationResponse])
async def list_organizations(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    获取公司列表
    """
    result = await db.execute(
        select(Organization).options(
            selectinload(Organization.departments).selectinload(Department.positions)
        )
    )
    return result.scalars().all()


@router.post("/org/organizations", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_in: OrganizationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin)],
):
    """
    创建公司（仅管理员）
    """
    org = Organization(**org_in.model_dump())
    db.add(org)
    await db.flush()
    await db.refresh(org)
    return org


@router.post("/org/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    dept_in: DepartmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin)],
):
    """
    创建部门（仅管理员）
    """
    dept = Department(**dept_in.model_dump())
    db.add(dept)
    await db.flush()
    await db.refresh(dept)
    return dept


@router.post("/org/positions", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
async def create_position(
    pos_in: PositionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin)],
):
    """
    创建岗位（仅管理员）
    """
    pos = Position(**pos_in.model_dump())
    db.add(pos)
    await db.flush()
    await db.refresh(pos)
    return pos
