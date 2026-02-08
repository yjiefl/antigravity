"""
用户与组织架构模型

包含：Organization（公司）、Department（部门）、Position（岗位）、User（用户）
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlalchemy import String, ForeignKey, DateTime, func, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid as UUID

from app.core.database import Base


class UserRole(str, Enum):
    """
    用户角色枚举
    
    - ADMIN: 系统管理员，可配置系统参数
    - MANAGER: 主管，可下达任务、审核验收
    - STAFF: 普通员工，录入计划、更新进度
    """
    ADMIN = "admin"
    MANAGER = "manager"
    STAFF = "staff"


# 用户-角色关联模型
class UserRoleBinding(Base):
    """用户角色关联"""
    __tablename__ = "user_roles"
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole),
        primary_key=True
    )
    
    # 反向关联（可选）
    # user = relationship("User", back_populates="roles_binding")


class Organization(Base):
    """
    公司/组织模型
    
    顶层组织架构，管理全局数据
    """
    __tablename__ = "organizations"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="公司名称")
    code: Mapped[Optional[str]] = mapped_column(String(50), unique=True, comment="公司编码")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="创建时间"
    )
    
    # 关联关系
    departments: Mapped[List["Department"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan"
    )


class Department(Base):
    """
    部门模型
    
    管理部门内计划流转
    """
    __tablename__ = "departments"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="部门名称")
    code: Mapped[Optional[str]] = mapped_column(String(50), comment="部门编码")
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        comment="所属公司"
    )
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        comment="上级部门"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="创建时间"
    )
    
    # 关联关系
    organization: Mapped["Organization"] = relationship(back_populates="departments")
    positions: Mapped[List["Position"]] = relationship(
        back_populates="department",
        cascade="all, delete-orphan"
    )
    parent: Mapped[Optional["Department"]] = relationship(
        remote_side=[id],
        backref="children"
    )


class Position(Base):
    """
    岗位模型
    
    定义岗位及其权限（如主管可分发任务）
    """
    __tablename__ = "positions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="岗位名称")
    code: Mapped[Optional[str]] = mapped_column(String(50), comment="岗位编码")
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        comment="所属部门"
    )
    can_assign_task: Mapped[bool] = mapped_column(
        default=False,
        comment="是否可分配任务"
    )
    can_transfer_task: Mapped[bool] = mapped_column(
        default=False,
        comment="是否可转办任务"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="创建时间"
    )
    
    # 关联关系
    department: Mapped["Department"] = relationship(back_populates="positions")
    users: Mapped[List["User"]] = relationship(back_populates="position")


class User(Base):
    """
    用户模型
    
    系统用户，关联部门和岗位
    """
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="用户名"
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码哈希")
    real_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="真实姓名")
    email: Mapped[Optional[str]] = mapped_column(String(100), comment="邮箱")
    phone: Mapped[Optional[str]] = mapped_column(String(20), comment="手机号")
    # 角色关联
    roles_binding: Mapped[List["UserRoleBinding"]] = relationship(
        cascade="all, delete-orphan",
        lazy="joined"
    )
    
    @property
    def roles(self) -> List[UserRole]:
        """获取角色列表（只读）"""
        return [b.role for b in self.roles_binding]
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        comment="所属部门"
    )
    position_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("positions.id", ondelete="SET NULL"),
        nullable=True,
        comment="岗位"
    )
    is_active: Mapped[bool] = mapped_column(default=True, comment="是否启用")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )
    
    # 关联关系
    position: Mapped[Optional["Position"]] = relationship(back_populates="users")
