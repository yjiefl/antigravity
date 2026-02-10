"""
系统审计日志模型

记录系统关键操作的审计追踪
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import String, Text, ForeignKey, DateTime, func, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid as UUID

from app.core.database import Base


class AuditModule(str, Enum):
    """
    审计模块枚举
    """
    AUTH = "auth"  # 认证模块
    USER = "user"  # 用户管理
    TASK = "task"  # 任务管理
    ORG = "org"  # 组织架构
    SYSTEM = "system"  # 系统设置


class AuditAction(str, Enum):
    """
    审计操作类型枚举
    """
    # 认证
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    
    # 用户管理
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_ENABLE = "user_enable"
    USER_DISABLE = "user_disable"
    PASSWORD_RESET = "password_reset"
    PASSWORD_CHANGE = "password_change"
    
    # 任务管理
    TASK_CREATE = "task_create"
    TASK_UPDATE = "task_update"
    TASK_DELETE = "task_delete"
    TASK_ASSIGN = "task_assign"
    TASK_STATUS_CHANGE = "task_status_change"
    
    # 组织架构
    ORG_CREATE = "org_create"
    ORG_UPDATE = "org_update"
    ORG_DELETE = "org_delete"
    DEPT_CREATE = "dept_create"
    DEPT_UPDATE = "dept_update"
    DEPT_DELETE = "dept_delete"


class AuditLog(Base):
    """
    系统审计日志模型
    
    记录系统中的所有关键操作
    """
    __tablename__ = "audit_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # 操作人信息
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="操作人ID"
    )
    username: Mapped[str] = mapped_column(
        String(50),
        comment="操作人用户名（冗余存储，防止用户删除后丢失）"
    )
    
    # 操作信息
    module: Mapped[AuditModule] = mapped_column(comment="操作模块")
    action: Mapped[AuditAction] = mapped_column(comment="操作类型")
    
    # 目标对象
    target_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="目标对象类型（user/task/department等）"
    )
    target_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="目标对象ID"
    )
    target_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="目标对象名称（冗余存储）"
    )
    
    # 详情
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="操作描述"
    )
    details: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="操作详情（JSON格式，记录变更前后的值）"
    )
    
    # 请求信息
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="客户端IP地址"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="客户端User-Agent"
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="操作时间"
    )
    
    # 关联关系（可选，用于查询）
    user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="selectin"
    )


# 避免循环导入
from app.models.user import User

class CoefficientAudit(Base):
    """
    系数调整审计表
    
    记录 I/D 系数的变更历史
    """
    __tablename__ = "coefficient_audits"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        comment="任务ID"
    )
    
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="修改人ID"
    )
    
    field: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="修改字段 (importance_i / difficulty_d)"
    )
    
    old_value: Mapped[float] = mapped_column(
        Float,
        comment="旧值"
    )
    
    new_value: Mapped[float] = mapped_column(
        Float,
        comment="新值"
    )
    
    reason: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="修改原因/Reason Code"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="修改时间"
    )
    
    # 关联
    task = relationship("Task", backref="coefficient_audits")
    user = relationship("User")
