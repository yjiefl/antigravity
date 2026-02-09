"""
审计日志 Pydantic 模式
"""
import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from app.models.audit import AuditModule, AuditAction


class AuditLogCreate(BaseModel):
    """创建审计日志（内部使用）"""
    user_id: Optional[uuid.UUID] = None
    username: str
    module: AuditModule
    action: AuditAction
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    target_name: Optional[str] = None
    description: Optional[str] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLogResponse(BaseModel):
    """审计日志响应"""
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    username: str
    module: AuditModule
    action: AuditAction
    target_type: Optional[str]
    target_id: Optional[str]
    target_name: Optional[str]
    description: Optional[str]
    details: Optional[dict]
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogQuery(BaseModel):
    """审计日志查询参数"""
    module: Optional[AuditModule] = None
    action: Optional[AuditAction] = None
    username: Optional[str] = None
    target_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=200)
