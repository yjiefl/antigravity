"""
审计日志服务

提供记录和查询审计日志的工具函数
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request

from app.models import AuditLog, AuditModule, AuditAction, User


async def log_audit(
    db: AsyncSession,
    user: Optional[User],
    module: AuditModule,
    action: AuditAction,
    request: Optional[Request] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    target_name: Optional[str] = None,
    description: Optional[str] = None,
    details: Optional[dict] = None,
):
    """
    记录审计日志
    
    Args:
        db: 数据库会话
        user: 操作用户（可选，登录失败时为None）
        module: 操作模块
        action: 操作类型
        request: FastAPI Request对象（用于获取IP和User-Agent）
        target_type: 目标对象类型
        target_id: 目标对象ID
        target_name: 目标对象名称
        description: 操作描述
        details: 操作详情（变更前后的数据等）
    """
    # 获取IP和User-Agent
    ip_address = None
    user_agent = None
    if request:
        # 优先从X-Forwarded-For获取真实IP
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()
        else:
            ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")[:500]  # 限制长度
    
    # 构建日志记录
    log = AuditLog(
        user_id=user.id if user else None,
        username=user.username if user else "anonymous",
        module=module,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id else None,
        target_name=target_name,
        description=description,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    db.add(log)
    # 不立即flush，让调用方决定何时提交
