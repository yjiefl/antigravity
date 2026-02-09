"""
审计日志 API 路由

提供审计日志查询接口（仅管理员可访问）
"""
import uuid
from typing import Annotated, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.models import User, AuditLog, AuditModule, AuditAction
from app.schemas import AuditLogResponse
from app.api.auth import get_current_admin

router = APIRouter()


@router.get("", response_model=List[AuditLogResponse])
async def list_audit_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin)],
    module: Optional[AuditModule] = Query(None, description="按模块筛选"),
    action: Optional[AuditAction] = Query(None, description="按操作类型筛选"),
    username: Optional[str] = Query(None, description="按操作人筛选"),
    target_type: Optional[str] = Query(None, description="按目标类型筛选"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """
    查询审计日志列表（仅管理员）
    
    支持按模块、操作类型、操作人、时间范围筛选
    """
    query = select(AuditLog)
    
    conditions = []
    if module:
        conditions.append(AuditLog.module == module)
    if action:
        conditions.append(AuditLog.action == action)
    if username:
        conditions.append(AuditLog.username.ilike(f"%{username}%"))
    if target_type:
        conditions.append(AuditLog.target_type == target_type)
    if start_date:
        conditions.append(AuditLog.created_at >= start_date)
    if end_date:
        conditions.append(AuditLog.created_at <= end_date)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    
    return result.scalars().all()


@router.get("/stats")
async def get_audit_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin)],
    days: int = Query(7, ge=1, le=30, description="统计天数"),
):
    """
    获取审计日志统计信息
    """
    from datetime import timedelta
    from sqlalchemy import func
    
    start_date = datetime.now() - timedelta(days=days)
    
    # 按模块统计
    module_stats_query = (
        select(AuditLog.module, func.count(AuditLog.id).label("count"))
        .where(AuditLog.created_at >= start_date)
        .group_by(AuditLog.module)
    )
    module_result = await db.execute(module_stats_query)
    module_stats = {row.module.value: row.count for row in module_result}
    
    # 按操作类型统计（取前10）
    action_stats_query = (
        select(AuditLog.action, func.count(AuditLog.id).label("count"))
        .where(AuditLog.created_at >= start_date)
        .group_by(AuditLog.action)
        .order_by(func.count(AuditLog.id).desc())
        .limit(10)
    )
    action_result = await db.execute(action_stats_query)
    action_stats = {row.action.value: row.count for row in action_result}
    
    # 总数
    total_query = (
        select(func.count(AuditLog.id))
        .where(AuditLog.created_at >= start_date)
    )
    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0
    
    return {
        "period_days": days,
        "total": total,
        "by_module": module_stats,
        "by_action": action_stats,
    }
