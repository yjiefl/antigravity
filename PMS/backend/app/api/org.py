"""
组织架构管理 API 路由

处理公司、部门、岗位的 CRUD 及树形结构获取
"""
import uuid
from typing import Annotated, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import get_db
from app.models import User, Organization, Department, Position
from app.schemas import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    DepartmentCreate, DepartmentUpdate, DepartmentResponse,
    PositionCreate, PositionUpdate, PositionResponse,
)
from app.api.auth import get_current_user, get_current_admin

router = APIRouter()


@router.get("/tree")
async def get_org_tree(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    获取组织架构树
    
    返回：公司 -> 部门 (递归) -> 岗位
    """
    # 获取所有公司，预加载部门和岗位
    result = await db.execute(
        select(Organization).options(
            selectinload(Organization.departments).selectinload(Department.positions),
            selectinload(Organization.departments).selectinload(Department.children)
        )
    )
    orgs = result.scalars().all()
    
    def build_dept_tree(dept: Department) -> Dict[str, Any]:
        return {
            "id": str(dept.id),
            "name": dept.name,
            "type": "department",
            "children": [
                *([build_dept_tree(child) for child in dept.children] if dept.children else []),
                *[{
                    "id": str(pos.id),
                    "name": pos.name,
                    "type": "position",
                    "can_assign": pos.can_assign_task
                } for pos in dept.positions]
            ]
        }
    
    tree = []
    for org in orgs:
        org_node = {
            "id": str(org.id),
            "name": org.name,
            "type": "organization",
            "children": []
        }
        # 只添加顶级部门（没有 parent_id 的）
        top_depts = [d for d in org.departments if d.parent_id is None]
        for dept in top_depts:
            org_node["children"].append(build_dept_tree(dept))
        tree.append(org_node)
        
    return tree


@router.get("/organizations", response_model=List[OrganizationResponse])
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


@router.post("/organizations", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
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


@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
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


@router.put("/departments/{dept_id}", response_model=DepartmentResponse)
async def update_department(
    dept_id: uuid.UUID,
    dept_in: DepartmentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin)],
):
    """
    更新部门（仅管理员）
    """
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalar_one_or_none()
    
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
        
    for field, value in dept_in.model_dump(exclude_unset=True).items():
        setattr(dept, field, value)
        
    await db.flush()
    await db.refresh(dept)
    return dept


@router.delete("/departments/{dept_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    dept_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin)],
):
    """
    删除部门（仅管理员）
    
    如果部门下有子部门、岗位或员工，则无法删除
    """
    # 检查是否存在
    result = await db.execute(
        select(Department)
        .where(Department.id == dept_id)
        .options(
            selectinload(Department.children),
            selectinload(Department.positions),
            selectinload(Department.users)  # 假设 Department 有 users 关系，需在 model 确认
        )
    )
    dept = result.scalar_one_or_none()
    
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
        
    # 检查关联数据
    # 注意：selectinload 可能未加载所有数据，最好用 count 查询确认
    # 这里简单检查已加载的 relationships
    if dept.children:
        raise HTTPException(status_code=400, detail="Cannot delete department with sub-departments")
    if dept.positions:
        raise HTTPException(status_code=400, detail="Cannot delete department with positions")
    
    # 检查用户关联
    # 需根据 User model 定义。User.department_id 是外键。
    user_check = await db.execute(select(User).where(User.department_id == dept_id).limit(1))
    if user_check.scalar_one_or_none():
         raise HTTPException(status_code=400, detail="Cannot delete department with assigned users")

    await db.delete(dept)
    await db.flush()


@router.post("/positions", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
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
