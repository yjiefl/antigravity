"""
任务与子任务模型

包含：Task（任务）、SubTask（子任务）及状态机枚举
"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List

from sqlalchemy import String, Text, ForeignKey, DateTime, Float, Integer, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid as UUID

from app.core.database import Base


class TaskStatus(str, Enum):
    """
    任务状态枚举（状态机）
    
    - DRAFT: 草稿，仅创建者可见
    - PENDING_SUBMISSION: 待提交，员工已准备好但未正式提交审批
    - PENDING_APPROVAL: 待审批，等待主管定级 I/D
    - IN_PROGRESS: 进行中，开始计时
    - PENDING_REVIEW: 待验收，停止计时
    - COMPLETED: 已完成，已评分归档
    - REJECTED: 已驳回，返工（工期不重置）
    - CANCELLED: 已取消
    - SUSPENDED: 已挂起
    """
    DRAFT = "draft"
    PENDING_SUBMISSION = "pending_submission"
    PENDING_LEADER_APPROVAL = "pending_leader_approval"  # 待组长审批
    PENDING_APPROVAL = "pending_approval"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


class TaskType(str, Enum):
    """
    任务类型枚举
    
    - PERFORMANCE: 绩效任务，参与积分计算
    - DAILY: 日常/行政任务，仅记录不计分
    """
    PERFORMANCE = "performance"
    DAILY = "daily"


class TaskCategory(str, Enum):
    """
    任务分类（可扩展）
    """
    PROJECT = "project"  # 项目类
    ROUTINE = "routine"  # 常规类
    URGENT = "urgent"  # 紧急类
    STAGED = "staged"  # 阶段性
    OTHER = "other"  # 其他


class Task(Base):
    """
    任务模型
    
    核心业务实体，支持层级结构（主任务/子任务）
    """
    __tablename__ = "tasks"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # 基本信息
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="任务标题")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="任务描述（5W2H/SMART）")
    
    # 分类体系
    task_type: Mapped[TaskType] = mapped_column(
        default=TaskType.PERFORMANCE,
        comment="任务类型"
    )
    category: Mapped[TaskCategory] = mapped_column(
        default=TaskCategory.OTHER,
        comment="计划分类"
    )
    sub_category: Mapped[Optional[str]] = mapped_column(String(50), comment="小类")
    tags: Mapped[Optional[str]] = mapped_column(String(200), comment="标签（逗号分隔）")
    
    # 状态
    status: Mapped[TaskStatus] = mapped_column(
        default=TaskStatus.DRAFT,
        comment="任务状态"
    )
    
    # 绩效系数（仅 PERFORMANCE 类型有效）
    importance_i: Mapped[Optional[float]] = mapped_column(
        Float,
        default=1.0,
        comment="重要性系数 I (0.5-1.5)"
    )
    difficulty_d: Mapped[Optional[float]] = mapped_column(
        Float,
        default=1.0,
        comment="难度系数 D (0.8-1.5)"
    )
    quality_q: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="质量系数 Q (0.0-1.2)，验收时填写"
    )
    
    # 时间维度
    plan_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        comment="计划开始时间"
    )
    plan_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        comment="计划完成时间"
    )
    actual_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        comment="实际开始时间（审批通过时记录）"
    )
    actual_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        comment="实际完成时间（验收通过时记录）"
    )
    
    # 进度
    progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="完成进度 (0-100)"
    )
    
    # 延期申请
    extension_status: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="延期状态: pending/approved/rejected"
    )
    extension_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="延期理由")
    extension_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="申请延期至"
    )
    
    # 责任矩阵
    creator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="编制人"
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        comment="归属部门"
    )
    reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="审批人/主管"
    )
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="负责人"
    )
    executor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="实施人"
    )
    
    # 层级结构（主任务/子任务）
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=True,
        comment="父任务ID（子任务时填写）"
    )
    weight: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        comment="权重（子任务用于计算主任务进度）"
    )
    
    # 得分（完成后计算）
    workload_b: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        comment="子任务工作量基准分 B (Sub-workload)"
    )
    final_score: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="最终得分 S"
    )
    
    # 证据链接
    evidence_url: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="验收证据链接"
    )
    
    # 时间戳
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间"
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="逻辑删除标记"
    )
    
    # 关联关系
    parent: Mapped[Optional["Task"]] = relationship(
        remote_side=[id],
        backref="subtasks"
    )
    logs: Mapped[List["TaskLog"]] = relationship(
        "TaskLog",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    appeals: Mapped[List["Appeal"]] = relationship(
        "Appeal",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    penalty_cards: Mapped[List["PenaltyCard"]] = relationship(
        "PenaltyCard",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    attachments: Mapped[List["Attachment"]] = relationship(
        "Attachment",
        back_populates="task",
        cascade="all, delete-orphan"
    )

    # 用户关联（用于 eager loading）
    creator: Mapped["User"] = relationship("User", foreign_keys=[creator_id])
    department: Mapped[Optional["Department"]] = relationship("Department")
    reviewer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reviewer_id])
    owner: Mapped[Optional["User"]] = relationship("User", foreign_keys=[owner_id])
    executor: Mapped[Optional["User"]] = relationship("User", foreign_keys=[executor_id])


# 导入避免循环引用
from app.models.log import TaskLog
from app.models.penalty import Appeal, PenaltyCard
from app.models.attachment import Attachment
