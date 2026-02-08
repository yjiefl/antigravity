"""
任务日志模型

记录任务全生命周期的操作历史
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid as UUID

from app.core.database import Base


class LogAction(str, Enum):
    """
    日志操作类型枚举
    """
    CREATED = "created"  # 创建任务
    SUBMITTED = "submitted"  # 提交审批
    APPROVED = "approved"  # 审批通过
    REJECTED = "rejected"  # 审批驳回
    ASSIGNED = "assigned"  # 分配任务
    TRANSFERRED = "transferred"  # 任务转移
    PROGRESS_UPDATED = "progress_updated"  # 更新进展
    COMPLETED = "completed"  # 提交验收
    REVIEWED = "reviewed"  # 验收评分
    REVIEW_REJECTED = "review_rejected"  # 验收不通过
    CANCELLED = "cancelled"  # 取消任务
    SUSPENDED = "suspended"  # 挂起任务
    RESUMED = "resumed"  # 恢复任务
    SYSTEM_NOTICE = "system_notice"  # 系统通知


class TaskLog(Base):
    """
    任务日志模型
    
    自动记录任务从"发布-接收-进展更新-验收"的每一个时间戳及操作人
    """
    __tablename__ = "task_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        comment="关联任务"
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="操作人"
    )
    action: Mapped[LogAction] = mapped_column(comment="操作类型")
    content: Mapped[Optional[str]] = mapped_column(Text, comment="日志内容/备注")
    evidence_url: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="证据链接（超链接形式）"
    )
    progress_before: Mapped[Optional[int]] = mapped_column(comment="操作前进度")
    progress_after: Mapped[Optional[int]] = mapped_column(comment="操作后进度")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="操作时间"
    )
    
    # 关联关系
    task: Mapped["Task"] = relationship("Task", back_populates="logs")


# 避免循环导入
from app.models.task import Task
