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
    包含编辑所需的完整字段（code、parent_id、organization_id 等）
    """
    # 获取所有公司，预加载部门和岗位
    result = await db.execute(
        select(Organization).options(
            selectinload(Organization.departments).selectinload(Department.positions),
            selectinload(Organization.departments).selectinload(Department.children)
        )
    )
    orgs = result.scalars().all()

    def build_dept_tree(dept: Department, org_id: str) -> Dict[str, Any]:
        """递归构建部门树节点，包含编辑所需的完整字段"""
        return {
            "id": str(dept.id),
            "name": dept.name,
            "code": dept.code,
            "type": "department",
            "parent_id": str(dept.parent_id) if dept.parent_id else None,
            "organization_id": org_id,
            "children": [
                *([build_dept_tree(child, org_id) for child in dept.children] if dept.children else []),
                *[{
                    "id": str(pos.id),
                    "name": pos.name,
                    "code": pos.code,
                    "type": "position",
                    "department_id": str(pos.department_id),
                    "can_assign": pos.can_assign_task,
                    "can_transfer": pos.can_transfer_task,
                } for pos in dept.positions]
            ]
        }

    tree = []
    for org in orgs:
        org_id = str(org.id)
        org_node = {
            "id": org_id,
            "name": org.name,
            "code": org.code,
            "type": "organization",
            "children": []
        }
        # 只添加顶级部门（没有 parent_id 的）
        top_depts = [d for d in org.departments if d.parent_id is None]
        for dept in top_depts:
            org_node["children"].append(build_dept_tree(dept, org_id))
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
    await db.commit()
    # 重新查询并预加载关联关系
    result = await db.execute(
        select(Organization)
        .where(Organization.id == org.id)
        .options(selectinload(Organization.departments).selectinload(Department.positions))
    )
    return result.scalar_one()


@router.put("/organizations/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: uuid.UUID,
    org_in: OrganizationUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin)],
):
    """
    更新公司信息（仅管理员）
    """
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(status_code=404, detail="公司不存在")

    for field, value in org_in.model_dump(exclude_unset=True).items():
        setattr(org, field, value)

    await db.flush()
    await db.commit()
    # 重新查询并预加载关联关系
    result = await db.execute(
        select(Organization)
        .where(Organization.id == org_id)
        .options(selectinload(Organization.departments).selectinload(Department.positions))
    )
    return result.scalar_one()


@router.delete("/organizations/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin)],
):
    """
    删除公司（仅管理员）

    如果公司下有部门，则无法删除
    """
    result = await db.execute(
        select(Organization)
        .where(Organization.id == org_id)
        .options(selectinload(Organization.departments))
    )
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(status_code=404, detail="公司不存在")

    if org.departments:
        raise HTTPException(status_code=400, detail="无法删除有部门的公司，请先删除所有部门")

    await db.delete(org)
    await db.flush()
    await db.commit()


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
    await db.commit()
    # 重新查询并预加载岗位关系
    result = await db.execute(
        select(Department)
        .where(Department.id == dept.id)
        .options(selectinload(Department.positions))
    )
    return result.scalar_one()


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
        raise HTTPException(status_code=404, detail="部门不存在")

    for field, value in dept_in.model_dump(exclude_unset=True).items():
        setattr(dept, field, value)

    await db.flush()
    await db.commit()
    # 重新查询并预加载岗位关系
    result = await db.execute(
        select(Department)
        .where(Department.id == dept_id)
        .options(selectinload(Department.positions))
    )
    return result.scalar_one()


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
        )
    )
    dept = result.scalar_one_or_none()

    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")

    # 检查关联数据
    if dept.children:
        raise HTTPException(status_code=400, detail="无法删除有子部门的部门")
    if dept.positions:
        raise HTTPException(status_code=400, detail="无法删除有岗位的部门")

    # 检查用户关联
    user_check = await db.execute(select(User).where(User.department_id == dept_id).limit(1))
    if user_check.scalar_one_or_none():
         raise HTTPException(status_code=400, detail="无法删除有用户的部门")

    await db.delete(dept)
    await db.flush()
    await db.commit()


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
    await db.commit()
    return pos


@router.put("/positions/{pos_id}", response_model=PositionResponse)
async def update_position(
    pos_id: uuid.UUID,
    pos_in: PositionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin)],
):
    """
    更新岗位（仅管理员）
    """
    result = await db.execute(select(Position).where(Position.id == pos_id))
    pos = result.scalar_one_or_none()

    if not pos:
        raise HTTPException(status_code=404, detail="岗位不存在")

    for field, value in pos_in.model_dump(exclude_unset=True).items():
        setattr(pos, field, value)

    await db.flush()
    await db.refresh(pos)
    await db.commit()
    return pos


@router.delete("/positions/{pos_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_position(
    pos_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin)],
):
    """
    删除岗位（仅管理员）

    如果岗位下有员工，则无法删除
    """
    result = await db.execute(select(Position).where(Position.id == pos_id))
    pos = result.scalar_one_or_none()

    if not pos:
        raise HTTPException(status_code=404, detail="岗位不存在")

    # 检查用户关联
    user_check = await db.execute(select(User).where(User.position_id == pos_id).limit(1))
    if user_check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="无法删除有用户的岗位，请先将用户调离此岗位")

    await db.delete(pos)
    await db.flush()
    await db.commit()
