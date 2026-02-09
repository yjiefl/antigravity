"""
Pydantic 模式定义 - 用户相关

用于 API 请求/响应的数据验证
"""
import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


# ============ 基础模式 ============

class PositionBase(BaseModel):
    """岗位基础模式"""
    name: str = Field(..., max_length=100, description="岗位名称")
    code: Optional[str] = Field(None, max_length=50, description="岗位编码")
    can_assign_task: bool = Field(False, description="是否可分配任务")
    can_transfer_task: bool = Field(False, description="是否可转办任务")


class DepartmentBase(BaseModel):
    """部门基础模式"""
    name: str = Field(..., max_length=100, description="部门名称")
    code: Optional[str] = Field(None, max_length=50, description="部门编码")
    parent_id: Optional[uuid.UUID] = Field(None, description="上级部门ID")


class OrganizationBase(BaseModel):
    """公司基础模式"""
    name: str = Field(..., max_length=100, description="公司名称")
    code: Optional[str] = Field(None, max_length=50, description="公司编码")


class UserBase(BaseModel):
    """用户基础模式"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    real_name: str = Field(..., max_length=50, description="真实姓名")
    roles: List[UserRole] = Field(default=[UserRole.STAFF], description="用户角色")
    department_id: Optional[uuid.UUID] = Field(None, description="所属部门")
    position_id: Optional[uuid.UUID] = Field(None, description="岗位")


# ============ 创建模式 ============

class PositionCreate(PositionBase):
    """创建岗位"""
    department_id: uuid.UUID = Field(..., description="所属部门ID")


class DepartmentCreate(DepartmentBase):
    """创建部门"""
    organization_id: uuid.UUID = Field(..., description="所属公司ID")


class OrganizationCreate(OrganizationBase):
    """创建公司"""
    pass


class UserCreate(UserBase):
    """创建用户"""
    password: str = Field(..., min_length=6, description="密码")


# ============ 更新模式 ============

class PositionUpdate(BaseModel):
    """更新岗位"""
    name: Optional[str] = Field(None, max_length=100)
    code: Optional[str] = Field(None, max_length=50)
    can_assign_task: Optional[bool] = None
    can_transfer_task: Optional[bool] = None


class DepartmentUpdate(BaseModel):
    """更新部门"""
    name: Optional[str] = Field(None, max_length=100)
    code: Optional[str] = Field(None, max_length=50)
    parent_id: Optional[uuid.UUID] = None


class OrganizationUpdate(BaseModel):
    """更新公司"""
    name: Optional[str] = Field(None, max_length=100)
    code: Optional[str] = Field(None, max_length=50)


class UserUpdate(BaseModel):
    """更新用户"""
    real_name: Optional[str] = Field(None, max_length=50)
    roles: Optional[List[UserRole]] = None
    department_id: Optional[uuid.UUID] = None
    position_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class PasswordChange(BaseModel):
    """修改密码（用户自己）"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, description="新密码")


class PasswordReset(BaseModel):
    """重置密码（管理员）"""
    new_password: str = Field(..., min_length=6, description="新密码")


# ============ 响应模式 ============

class PositionResponse(PositionBase):
    """岗位响应"""
    id: uuid.UUID
    department_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class DepartmentResponse(DepartmentBase):
    """部门响应"""
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    positions: List[PositionResponse] = []

    class Config:
        from_attributes = True


class OrganizationResponse(OrganizationBase):
    """公司响应"""
    id: uuid.UUID
    created_at: datetime
    departments: List[DepartmentResponse] = []

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    """用户响应"""
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserBrief(BaseModel):
    """用户简要信息（用于列表/选择器）"""
    id: uuid.UUID
    username: str
    real_name: str
    roles: List[UserRole]

    class Config:
        from_attributes = True
