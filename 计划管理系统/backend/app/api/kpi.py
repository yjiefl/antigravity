"""
绩效统计 API 路由

处理绩效计算、KPI 统计、报表生成
"""
import uuid
from datetime import datetime, timezone
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db, get_settings
from app.models import User, Task, TaskStatus, TaskType, PenaltyCard, CardType, UserRole
from app.schemas import TaskScorePreview
from app.api.auth import get_current_user, get_current_manager_or_admin
from app.services.kpi_service import calculate_timeliness, calculate_score

router = APIRouter()
settings = get_settings()


@router.get("/preview/{task_id}", response_model=TaskScorePreview)
async def preview_task_score(
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    任务得分预览
    
    实时计算当前预计得分（分值预测制）
    """
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        return None
    
    # 计算时效系数
    timeliness_t = calculate_timeliness(task)
    
    # 计算罚分
    penalty_result = await db.execute(
        select(func.sum(PenaltyCard.penalty_score))
        .where(PenaltyCard.task_id == task_id)
        .where(PenaltyCard.card_type == CardType.RED)
    )
    penalty_p = penalty_result.scalar() or 0.0
    
    # 当前得分（Q 默认 1.0）
    quality_q = task.quality_q or 1.0
    base = settings.base_score * (task.importance_i or 1.0) * (task.difficulty_d or 1.0)
    current_score = max(0, base * quality_q * timeliness_t - penalty_p)
    
    # 最高可能得分（Q=1.2, T=1.0）
    max_possible_score = base * 1.2 * 1.0
    
    # 是否逾期
    is_overdue = False
    overdue_days = None
    if task.plan_end:
        now = datetime.now(timezone.utc)
        if now > task.plan_end and task.status in [TaskStatus.IN_PROGRESS, TaskStatus.PENDING_REVIEW]:
            is_overdue = True
            overdue_days = (now - task.plan_end).days
    
    return TaskScorePreview(
        task_id=task.id,
        base_score=settings.base_score,
        importance_i=task.importance_i or 1.0,
        difficulty_d=task.difficulty_d or 1.0,
        quality_q=task.quality_q,
        timeliness_t=timeliness_t,
        penalty_p=penalty_p,
        current_score=current_score,
        max_possible_score=max_possible_score,
        is_overdue=is_overdue,
        overdue_days=overdue_days,
    )


@router.get("/personal/{user_id}")
async def get_personal_kpi(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    start_date: datetime = Query(None, description="开始日期"),
    end_date: datetime = Query(None, description="结束日期"),
):
    """
    获取个人绩效统计
    
    包含：总得分、任务数、准时率、质量稳定性、红牌率
    """
    # 基础查询
    query = select(Task).where(
        Task.executor_id == user_id,
        Task.status == TaskStatus.COMPLETED,
        Task.task_type == TaskType.PERFORMANCE,
    )
    
    if start_date:
        query = query.where(Task.actual_end >= start_date)
    if end_date:
        query = query.where(Task.actual_end <= end_date)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    if not tasks:
        return {
            "user_id": str(user_id),
            "total_score": 0,
            "task_count": 0,
            "timeliness_index": 0,
            "quality_avg": 0,
            "quality_variance": 0,
            "red_card_rate": 0,
        }
    
    # 计算指标
    total_score = sum(t.final_score or 0 for t in tasks)
    task_count = len(tasks)
    
    # 平均时效系数
    timeliness_values = [calculate_timeliness(t) for t in tasks]
    timeliness_index = sum(timeliness_values) / len(timeliness_values)
    
    # 质量系数统计
    quality_values = [t.quality_q for t in tasks if t.quality_q is not None]
    quality_avg = sum(quality_values) / len(quality_values) if quality_values else 1.0
    
    # 质量方差
    if len(quality_values) > 1:
        mean = quality_avg
        variance = sum((q - mean) ** 2 for q in quality_values) / len(quality_values)
        quality_variance = variance ** 0.5
    else:
        quality_variance = 0
    
    # 红牌率
    red_card_result = await db.execute(
        select(func.count(PenaltyCard.id))
        .where(PenaltyCard.user_id == user_id)
        .where(PenaltyCard.card_type == CardType.RED)
    )
    red_card_count = red_card_result.scalar() or 0
    
    all_tasks_result = await db.execute(
        select(func.count(Task.id))
        .where(Task.executor_id == user_id)
        .where(Task.task_type == TaskType.PERFORMANCE)
    )
    all_task_count = all_tasks_result.scalar() or 1
    
    red_card_rate = red_card_count / all_task_count
    
    return {
        "user_id": str(user_id),
        "total_score": round(total_score, 1),
        "task_count": task_count,
        "timeliness_index": round(timeliness_index, 2),
        "quality_avg": round(quality_avg, 2),
        "quality_variance": round(quality_variance, 3),
        "red_card_rate": round(red_card_rate, 3),
    }


@router.get("/department/{dept_id}")
async def get_department_kpi(
    dept_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_manager_or_admin)],
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
):
    """
    获取部门绩效统计
    
    汇总部门内所有成员的绩效数据
    """
    # 获取部门成员
    user_result = await db.execute(
        select(User.id).where(User.department_id == dept_id, User.is_active == True)
    )
    user_ids = [u for u in user_result.scalars().all()]
    
    if not user_ids:
        return {
            "department_id": str(dept_id),
            "total_score": 0,
            "task_count": 0,
            "member_count": 0,
            "contributions": [],
        }
    
    # 查询已完成的绩效任务
    query = select(Task).where(
        Task.executor_id.in_(user_ids),
        Task.status == TaskStatus.COMPLETED,
        Task.task_type == TaskType.PERFORMANCE,
    )
    
    if start_date:
        query = query.where(Task.actual_end >= start_date)
    if end_date:
        query = query.where(Task.actual_end <= end_date)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    # 部门总分
    total_score = sum(t.final_score or 0 for t in tasks)
    
    # 个人贡献度
    user_scores = {}
    for task in tasks:
        uid = str(task.executor_id)
        user_scores[uid] = user_scores.get(uid, 0) + (task.final_score or 0)
    
    contributions = [
        {
            "user_id": uid,
            "score": round(score, 1),
            "contribution_rate": round(score / total_score * 100, 1) if total_score > 0 else 0,
        }
        for uid, score in sorted(user_scores.items(), key=lambda x: x[1], reverse=True)
    ]
    
    return {
        "department_id": str(dept_id),
        "total_score": round(total_score, 1),
        "task_count": len(tasks),
        "member_count": len(user_ids),
        "contributions": contributions,
    }


@router.get("/ranking")
async def get_ranking(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_manager_or_admin)],
    limit: int = Query(10, ge=1, le=50),
):
    """
    获取难度贡献榜
    
    展示谁承接了最难的任务（难度系数加权后的总分）
    """
    result = await db.execute(
        select(
            Task.executor_id,
            func.sum(Task.final_score).label("total_score"),
            func.count(Task.id).label("task_count"),
            func.avg(Task.difficulty_d).label("avg_difficulty"),
        )
        .where(
            Task.status == TaskStatus.COMPLETED,
            Task.task_type == TaskType.PERFORMANCE,
            Task.executor_id.isnot(None),
        )
        .group_by(Task.executor_id)
        .order_by(func.sum(Task.final_score).desc())
        .limit(limit)
    )
    
    rankings = []
    for row in result:
        # 获取用户信息
        user_result = await db.execute(
            select(User.real_name).where(User.id == row.executor_id)
        )
        real_name = user_result.scalar() or "未知"
        
        rankings.append({
            "user_id": str(row.executor_id),
            "real_name": real_name,
            "total_score": round(row.total_score or 0, 1),
            "task_count": row.task_count,
            "avg_difficulty": round(row.avg_difficulty or 1.0, 2),
        })
    
    return rankings
