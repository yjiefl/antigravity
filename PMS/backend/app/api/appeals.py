"""
申诉管理 API
"""
from datetime import datetime, timezone
from typing import Annotated, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models import User, Appeal, AppealStatus, PenaltyCard, UserRole, Task, AppealReason
from pydantic import BaseModel

router = APIRouter()

# --- Schemas ---

class AppealSubmit(BaseModel):
    reason_type: AppealReason
    reason_detail: str
    evidence_urls: Optional[str] = None

class AppealReview(BaseModel):
    status: AppealStatus  # 只能是 approved 或 rejected
    review_comment: str

class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    real_name: Optional[str]

    class Config:
        from_attributes = True

class PenaltyCardResponse(BaseModel):
    id: uuid.UUID
    card_type: str
    penalty_score: float
    reason_analysis: Optional[str]
    triggered_at: datetime

    class Config:
        from_attributes = True

class AppealResponse(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    penalty_card_id: uuid.UUID
    user_id: uuid.UUID
    status: AppealStatus
    reason_type: Optional[AppealReason]
    reason_detail: Optional[str]
    evidence_urls: Optional[str]
    expires_at: datetime
    created_at: datetime
    reviewed_at: Optional[datetime]
    review_comment: Optional[str]
    task_title: Optional[str] = None

    class Config:
        from_attributes = True

# --- API Endpoints ---

@router.get("/my-cards")
async def get_my_cards(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """获取当前用户的罚单历史（含红牌申诉状态）"""
    # 查询用户的所有罚单
    stmt = select(PenaltyCard).where(
        PenaltyCard.user_id == current_user.id
    ).options(selectinload(PenaltyCard.task)).order_by(PenaltyCard.triggered_at.desc())
    
    result = await db.execute(stmt)
    cards = result.scalars().all()
    
    # 手动关联申诉状态
    # 这里为了效率，可以先查询该用户的所有申诉
    appeal_stmt = select(Appeal).where(Appeal.user_id == current_user.id)
    appeal_result = await db.execute(appeal_stmt)
    appeals = {a.penalty_card_id: a for a in appeal_result.scalars().all()}
    
    formatted_cards = []
    for c in cards:
        appeal = appeals.get(c.id)
        formatted_cards.append({
            "id": c.id,
            "task_id": c.task_id,
            "task_title": c.task.title if c.task else "未知任务",
            "card_type": c.card_type,
            "penalty_score": c.penalty_score,
            "reason_analysis": c.reason_analysis,
            "triggered_at": c.triggered_at,
            "appeal_id": appeal.id if appeal else None,
            "appeal_status": appeal.status.value if appeal else None
        })
        
    return formatted_cards

@router.get("/my", response_model=List[AppealResponse])
async def get_my_appeals(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """获取当前用户的申诉列表"""
    stmt = select(Appeal).where(
        Appeal.user_id == current_user.id
    ).options(selectinload(Appeal.task)).order_by(Appeal.created_at.desc())
    
    result = await db.execute(stmt)
    appeals = result.scalars().all()
    
    # 填充任务标题
    for a in appeals:
        # 这里的 hack 是因为 pydantic 模型里定义了 task_title
        # 我们手动把 a.task.title 赋给它（虽然在 SQLAlchemy 对象上不存在该属性，但 Pydantic 转换时会取）
        setattr(a, "task_title", a.task.title if a.task else "未知任务")
        
    return appeals

@router.put("/{appeal_id}/submit", response_model=AppealResponse)
async def submit_appeal(
    appeal_id: uuid.UUID,
    appeal_data: AppealSubmit,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """提交申诉详情"""
    stmt = select(Appeal).where(
        Appeal.id == appeal_id,
        Appeal.user_id == current_user.id
    ).options(selectinload(Appeal.task))
    
    result = await db.execute(stmt)
    appeal = result.scalar_one_or_none()
    
    if not appeal:
        raise HTTPException(status_code=404, detail="申诉记录未找到")
        
    if appeal.status != AppealStatus.PENDING:
        raise HTTPException(status_code=400, detail="该申诉已提交或已处理")
        
    # 检查是否过期
    now = datetime.now(timezone.utc)
    # 确保 appeal.expires_at 带时区
    expires_at = appeal.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
        
    if now > expires_at:
        raise HTTPException(status_code=400, detail="申诉已过有效期")
        
    appeal.reason_type = appeal_data.reason_type
    appeal.reason_detail = appeal_data.reason_detail
    appeal.evidence_urls = appeal_data.evidence_urls
    appeal.status = AppealStatus.REVIEWING
    
    await db.commit()
    await db.refresh(appeal)
    
    setattr(appeal, "task_title", appeal.task.title if appeal.task else "未知任务")
    return appeal

@router.get("/admin/pending", response_model=List[AppealResponse])
async def get_pending_appeals(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """管理员获取待审核的申诉列表"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="权限不足")
        
    stmt = select(Appeal).where(
        Appeal.status == AppealStatus.REVIEWING
    ).options(selectinload(Appeal.task)).order_by(Appeal.created_at.asc())
    
    result = await db.execute(stmt)
    appeals = result.scalars().all()
    
    for a in appeals:
        setattr(a, "task_title", a.task.title if a.task else "未知任务")
        
    return appeals

@router.post("/{appeal_id}/review", response_model=AppealResponse)
async def review_appeal(
    appeal_id: uuid.UUID,
    review_data: AppealReview,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """管理员审核申诉"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="权限不足")
        
    if review_data.status not in [AppealStatus.APPROVED, AppealStatus.REJECTED]:
        raise HTTPException(status_code=400, detail="审核状态无效")

    stmt = select(Appeal).where(
        Appeal.id == appeal_id
    ).options(selectinload(Appeal.task))
    
    result = await db.execute(stmt)
    appeal = result.scalar_one_or_none()
    
    if not appeal:
        raise HTTPException(status_code=404, detail="申诉记录未找到")
        
    if appeal.status != AppealStatus.REVIEWING:
        raise HTTPException(status_code=400, detail="申诉不是待审核状态")
        
    appeal.status = review_data.status
    appeal.review_comment = review_data.review_comment
    appeal.reviewer_id = current_user.id
    appeal.reviewed_at = datetime.now(timezone.utc)
    
    # 如果审核通过，撤销罚分
    if appeal.status == AppealStatus.APPROVED:
        penalty_card_stmt = select(PenaltyCard).where(
            PenaltyCard.id == appeal.penalty_card_id
        )
        p_result = await db.execute(penalty_card_stmt)
        card = p_result.scalar_one_or_none()
        if card:
            card.penalty_score = 0.0  # 撤销罚分
            
    await db.commit()
    await db.refresh(appeal)
    
    setattr(appeal, "task_title", appeal.task.title if appeal.task else "未知任务")
    return appeal
