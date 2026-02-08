"""
考核单与申诉模型

包含：PenaltyCard（红黄牌考核单）、Appeal（申诉）
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import String, Text, ForeignKey, DateTime, Float, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid as UUID

from app.core.database import Base


class CardType(str, Enum):
    """
    考核牌类型
    
    - YELLOW: 黄牌预警
    - RED: 红牌考核
    """
    YELLOW = "yellow"
    RED = "red"


class AppealStatus(str, Enum):
    """
    申诉状态枚举
    
    - PENDING: 待申诉（生成申诉入口）
    - REVIEWING: 申诉中
    - APPROVED: 已撤回考核
    - REJECTED: 申诉被驳回
    """
    PENDING = "pending"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    REJECTED = "rejected"


class AppealReason(str, Enum):
    """
    申诉原因类型
    """
    DEPENDENCY_BLOCKED = "dependency_blocked"  # 前序任务阻塞
    EXTERNAL_FACTOR = "external_factor"  # 外部因素
    REQUIREMENT_CHANGE = "requirement_change"  # 需求变更
    RESOURCE_SHORTAGE = "resource_shortage"  # 资源不足
    OTHER = "other"  # 其他


class PenaltyCard(Base):
    """
    考核单模型（红黄牌）
    
    - 黄牌：距截止 24h 且进度 < 50%，预警通知
    - 红牌：逾期 > 3 天或超期倍数 ≥ 1，扣除绩效分
    """
    __tablename__ = "penalty_cards"
    
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
        comment="责任人"
    )
    card_type: Mapped[CardType] = mapped_column(comment="考核牌类型")
    penalty_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        comment="罚分 P"
    )
    reason_analysis: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="原因分析（负责人填写）"
    )
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="触发时间"
    )
    is_archived: Mapped[bool] = mapped_column(
        default=False,
        comment="是否已归档（月度结算后）"
    )
    
    # 关联关系
    task: Mapped["Task"] = relationship("Task", back_populates="penalty_cards")


class Appeal(Base):
    """
    申诉模型
    
    红牌触发后自动生成申诉入口，有效期 48 小时
    """
    __tablename__ = "appeals"
    
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
    penalty_card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("penalty_cards.id", ondelete="CASCADE"),
        comment="关联考核单"
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="申诉人"
    )
    status: Mapped[AppealStatus] = mapped_column(
        default=AppealStatus.PENDING,
        comment="申诉状态"
    )
    reason_type: Mapped[Optional[AppealReason]] = mapped_column(comment="申诉原因类型")
    reason_detail: Mapped[Optional[str]] = mapped_column(Text, comment="申诉详细说明")
    evidence_urls: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="证明文件链接（逗号分隔）"
    )
    reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="审核人"
    )
    review_comment: Mapped[Optional[str]] = mapped_column(Text, comment="审核意见")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="申诉时间"
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        comment="申诉有效期"
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        comment="审核时间"
    )
    
    # 关联关系
    task: Mapped["Task"] = relationship("Task", back_populates="appeals")


# 避免循环导入
from app.models.task import Task
