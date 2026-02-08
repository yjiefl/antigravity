"""
附件模型
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, BigInteger, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid as UUID

from app.core.database import Base


class Attachment(Base):
    """
    附件模型
    
    存储上传文件的元数据，支持多文件关联与下载统计
    """
    __tablename__ = "attachments"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=True,
        comment="关联任务"
    )
    log_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("task_logs.id", ondelete="CASCADE"),
        nullable=True,
        comment="关联操作日志"
    )
    uploader_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="上传人"
    )
    
    filename: Mapped[str] = mapped_column(String(255), comment="原始文件名")
    file_path: Mapped[str] = mapped_column(String(512), comment="存储路径")
    file_type: Mapped[str] = mapped_column(String(100), comment="文件类型 (MIME)")
    file_size: Mapped[int] = mapped_column(BigInteger, comment="文件大小 (Bytes)")
    
    download_count: Mapped[int] = mapped_column(Integer, default=0, comment="下载次数")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="上传时间"
    )
    
    # 关联关系
    task: Mapped[Optional["Task"]] = relationship("Task", back_populates="attachments")
    log: Mapped[Optional["TaskLog"]] = relationship("TaskLog", back_populates="attachments")
    uploader: Mapped[Optional["User"]] = relationship("User")


# 避免循环导入
from app.models.task import Task
from app.models.log import TaskLog
from app.models.user import User
