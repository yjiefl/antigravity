"""
逾期检查与红黄牌发放任务
"""
import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, and_, exists
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.core.config import get_settings
from app.models import Task, TaskStatus, PenaltyCard, CardType, TaskLog, LogAction, Appeal, AppealStatus

settings = get_settings()


async def check_overdue_tasks():
    """
    检查所有未完成任务，发放红黄牌
    
    规则：
    1. 严重逾期（> red_card_overdue_days 天） -> 红牌
    2. 进度滞后（距截止 < yellow_card_hours 小时 且 进度 < yellow_card_progress） -> 黄牌
    3. 一般逾期（已逾期但未达红牌标准） -> 黄牌
    """
    # print(f"[{datetime.now()}] 执行逾期检查...")
    
    async with async_session_maker() as session:
        # 查询进行中或待验收的任务
        stmt = select(Task).where(
            Task.status.in_([TaskStatus.IN_PROGRESS, TaskStatus.PENDING_REVIEW]),
            Task.plan_end.is_not(None)
        )
        result = await session.execute(stmt)
        tasks = result.scalars().all()
        
        now = datetime.now(timezone.utc)
        
        for task in tasks:
            if not task.plan_end:
                continue
            
            # 确保 plan_end 是带时区的
            plan_end = task.plan_end
            if plan_end.tzinfo is None:
                plan_end = plan_end.replace(tzinfo=timezone.utc)
                
            # 计算相关时间差
            overdue_delta = now - plan_end
            remaining_delta = plan_end - now
            
            # 1. 检查红牌 (严重逾期)
            if overdue_delta.days >= settings.red_card_overdue_days:
                await issue_penalty(
                    session, task, CardType.RED, 
                    f"严重逾期超过 {settings.red_card_overdue_days} 天"
                )
                continue  # 已发红牌，不再发黄牌
                
            # 2. 检查黄牌 (一般逾期 或 进度滞后)
            is_yellow = False
            reason = ""
            
            # 情况 A: 已逾期 (但未达红牌)
            if overdue_delta.total_seconds() > 0:
                is_yellow = True
                reason = "任务已逾期"
                
            # 情况 B: 临近截止且进度滞后
            elif (remaining_delta.total_seconds() <= settings.yellow_card_hours * 3600 
                  and task.progress < settings.yellow_card_progress):
                is_yellow = True
                reason = f"临近截止 ({settings.yellow_card_hours}h内) 且进度落后 (<{settings.yellow_card_progress}%)"
            
            if is_yellow:
                await issue_penalty(session, task, CardType.YELLOW, reason)
        
        await session.commit()


async def issue_penalty(
    session: AsyncSession, 
    task: Task, 
    card_type: CardType, 
    reason: str
):
    """发放惩罚卡"""
    # 检查是否已存在同等级(或更高级)惩罚卡
    # 简化逻辑：如果不重复发同类型卡
    stmt = select(exists().where(
        and_(
            PenaltyCard.task_id == task.id,
            PenaltyCard.card_type == card_type
        )
    ))
    result = await session.execute(stmt)
    if result.scalar():
        return
    
    # 如果发黄牌，但已有红牌？
    if card_type == CardType.YELLOW:
        stmt_red = select(exists().where(
            and_(
                PenaltyCard.task_id == task.id,
                PenaltyCard.card_type == CardType.RED
            )
        ))
        if (await session.execute(stmt_red)).scalar():
            return  # 已有红牌，不发黄牌

    points = calculate_deduction(card_type)
    
    # 确定被惩罚人/记录人
    target_user_id = task.executor_id or task.owner_id or task.creator_id
    
    # 创建惩罚卡
    card = PenaltyCard(
        task_id=task.id,
        user_id=target_user_id,
        card_type=card_type,
        reason_analysis=f"系统自动触发：{reason}",
        penalty_score=points,
        is_archived=False
    )
    session.add(card)
    
    # 如果是红牌，自动创建申诉条目
    if card_type == CardType.RED:
        # 获取当前时间并设置 48 小时有效期
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=48)
        
        # 为了获取 card.id，如果是自动生成的 UUID，
        # 我们可以在这里手动生成一个，或者等待 flush
        # 这里为了简单，我们手动给 card 分配一个 ID 或者在 add 后 flush
        await session.flush()
        
        appeal = Appeal(
            task_id=task.id,
            penalty_card_id=card.id,
            user_id=target_user_id,  # 使用确定的 user_id
            status=AppealStatus.PENDING,
            expires_at=expires_at,
            created_at=now
        )
        session.add(appeal)
    
    # 记录日志
    log = TaskLog(
        task_id=task.id,
        user_id=target_user_id,  # 使用确定的 user_id
        action=LogAction.SYSTEM_NOTICE,
        content=f"系统自动发放{card_type.value}牌：{reason}，扣分：{points}",
    )
    session.add(log)
    
    # print(f"已对任务 {task.title} 发放 {card_type.value}")


def calculate_deduction(card_type: CardType) -> float:
    """计算扣分"""
    if card_type == CardType.RED:
        return 5.0  # 红牌扣5分
    elif card_type == CardType.YELLOW:
        return 0.0  # 黄牌仅预警，不扣分 (可配置)
    return 0.0
