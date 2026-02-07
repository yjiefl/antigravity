"""
任务管理 API 路由

处理任务 CRUD、状态机流转、子任务管理
"""
import uuid
from datetime import datetime, timezone
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import get_db
from app.models import User, Task, TaskLog, TaskStatus, TaskType, LogAction, UserRole
from app.schemas import (
    TaskCreate, TaskUpdate, TaskResponse, TaskBrief, TaskWithSubtasks,
    TaskApprove, TaskReview, TaskProgress, TaskComplete, TaskTransfer,
    TaskFilter, SubTaskCreate,
)
from app.api.auth import get_current_user, get_current_manager_or_admin
from app.services.kpi_service import calculate_timeliness, calculate_score

router = APIRouter()


async def get_task_or_404(
    task_id: uuid.UUID,
    db: AsyncSession
) -> Task:
    """获取任务或返回 404"""
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    return task


async def add_task_log(
    db: AsyncSession,
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    action: LogAction,
    content: Optional[str] = None,
    progress_before: Optional[int] = None,
    progress_after: Optional[int] = None,
    evidence_url: Optional[str] = None,
):
    """添加任务日志"""
    log = TaskLog(
        task_id=task_id,
        user_id=user_id,
        action=action,
        content=content,
        progress_before=progress_before,
        progress_after=progress_after,
        evidence_url=evidence_url,
    )
    db.add(log)


# ============ 任务 CRUD ============

@router.get("", response_model=List[TaskBrief])
async def list_tasks(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    status_filter: TaskStatus = Query(None, alias="status"),
    task_type: TaskType = Query(None),
    executor_id: uuid.UUID = Query(None),
    owner_id: uuid.UUID = Query(None),
    keyword: str = Query(None),
    is_overdue: bool = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """
    获取任务列表
    
    支持多维度过滤：状态、类型、执行人、负责人、关键字、是否逾期
    """
    query = select(Task).where(Task.parent_id.is_(None))  # 只查主任务
    
    # 权限过滤：普通员工只能看到自己相关的任务
    if current_user.role == UserRole.STAFF:
        query = query.where(
            or_(
                Task.creator_id == current_user.id,
                Task.owner_id == current_user.id,
                Task.executor_id == current_user.id,
            )
        )
    
    # 状态过滤
    if status_filter:
        query = query.where(Task.status == status_filter)
    
    # 类型过滤
    if task_type:
        query = query.where(Task.task_type == task_type)
    
    # 执行人过滤
    if executor_id:
        query = query.where(Task.executor_id == executor_id)
    
    # 负责人过滤
    if owner_id:
        query = query.where(Task.owner_id == owner_id)
    
    # 关键字搜索
    if keyword:
        query = query.where(
            or_(
                Task.title.ilike(f"%{keyword}%"),
                Task.description.ilike(f"%{keyword}%"),
                Task.tags.ilike(f"%{keyword}%"),
            )
        )
    
    # 逾期过滤
    if is_overdue is not None:
        now = datetime.now(timezone.utc)
        if is_overdue:
            query = query.where(
                and_(
                    Task.plan_end < now,
                    Task.status.in_([TaskStatus.IN_PROGRESS, TaskStatus.PENDING_REVIEW])
                )
            )
    
    query = query.order_by(Task.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    
    return result.scalars().all()


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    创建任务
    
    创建后状态为草稿(draft)
    """
    task = Task(
        **task_in.model_dump(),
        creator_id=current_user.id,
        status=TaskStatus.DRAFT,
    )
    
    db.add(task)
    await db.flush()
    
    # 记录日志
    await add_task_log(db, task.id, current_user.id, LogAction.CREATED, "创建任务")
    
    await db.refresh(task)
    return task


@router.get("/{task_id}", response_model=TaskWithSubtasks)
async def get_task(
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    获取任务详情（含子任务）
    """
    result = await db.execute(
        select(Task)
        .where(Task.id == task_id)
        .options(selectinload(Task.subtasks))
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: uuid.UUID,
    task_in: TaskUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    更新任务
    
    仅草稿状态可编辑基本信息
    """
    task = await get_task_or_404(task_id, db)
    
    if task.status != TaskStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有草稿状态的任务可以编辑"
        )
    
    for field, value in task_in.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    
    await db.flush()
    await db.refresh(task)
    
    return task


# ============ 状态机流转 ============

@router.post("/{task_id}/submit", response_model=TaskResponse)
async def submit_task(
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    提交任务审批
    
    草稿 → 待审批
    """
    task = await get_task_or_404(task_id, db)
    
    if task.status != TaskStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有草稿状态的任务可以提交审批"
        )
    
    task.status = TaskStatus.PENDING_APPROVAL
    await add_task_log(db, task.id, current_user.id, LogAction.SUBMITTED, "提交审批")
    
    await db.flush()
    await db.refresh(task)
    
    return task


@router.post("/{task_id}/approve", response_model=TaskResponse)
async def approve_task(
    task_id: uuid.UUID,
    approve_in: TaskApprove,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_manager_or_admin)],
):
    """
    审批通过任务（设定 I/D 系数）
    
    待审批 → 进行中
    """
    task = await get_task_or_404(task_id, db)
    
    if task.status != TaskStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有待审批状态的任务可以审批"
        )
    
    task.status = TaskStatus.IN_PROGRESS
    task.importance_i = approve_in.importance_i
    task.difficulty_d = approve_in.difficulty_d
    task.actual_start = datetime.now(timezone.utc)
    
    await add_task_log(
        db, task.id, current_user.id, LogAction.APPROVED,
        f"审批通过，I={approve_in.importance_i}, D={approve_in.difficulty_d}"
    )
    
    await db.flush()
    await db.refresh(task)
    
    return task


@router.post("/{task_id}/reject", response_model=TaskResponse)
async def reject_task(
    task_id: uuid.UUID,
    reason: str = Query(..., description="驳回原因"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_manager_or_admin),
):
    """
    审批驳回任务
    
    待审批 → 草稿
    """
    task = await get_task_or_404(task_id, db)
    
    if task.status != TaskStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有待审批状态的任务可以驳回"
        )
    
    task.status = TaskStatus.DRAFT
    await add_task_log(db, task.id, current_user.id, LogAction.REJECTED, f"驳回原因：{reason}")
    
    await db.flush()
    await db.refresh(task)
    
    return task


@router.post("/{task_id}/progress", response_model=TaskResponse)
async def update_progress(
    task_id: uuid.UUID,
    progress_in: TaskProgress,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    更新任务进展
    
    仅进行中状态可更新
    """
    task = await get_task_or_404(task_id, db)
    
    if task.status != TaskStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有进行中的任务可以更新进展"
        )
    
    progress_before = task.progress
    task.progress = progress_in.progress
    
    await add_task_log(
        db, task.id, current_user.id, LogAction.PROGRESS_UPDATED,
        progress_in.content,
        progress_before=progress_before,
        progress_after=progress_in.progress,
        evidence_url=progress_in.evidence_url,
    )
    
    await db.flush()
    await db.refresh(task)
    
    return task


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: uuid.UUID,
    complete_in: TaskComplete,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    提交验收
    
    进行中 → 待验收
    """
    task = await get_task_or_404(task_id, db)
    
    if task.status != TaskStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有进行中的任务可以提交验收"
        )
    
    # 检查子任务是否全部完成
    if task.subtasks:
        for subtask in task.subtasks:
            if subtask.status != TaskStatus.COMPLETED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="所有子任务必须完成后才能提交验收"
                )
    
    task.status = TaskStatus.PENDING_REVIEW
    task.progress = 100
    task.evidence_url = complete_in.evidence_url
    
    await add_task_log(
        db, task.id, current_user.id, LogAction.COMPLETED,
        complete_in.comment,
        evidence_url=complete_in.evidence_url,
    )
    
    await db.flush()
    await db.refresh(task)
    
    return task


@router.post("/{task_id}/review", response_model=TaskResponse)
async def review_task(
    task_id: uuid.UUID,
    review_in: TaskReview,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_manager_or_admin)],
):
    """
    验收评分
    
    待验收 → 已完成（计算得分）
    """
    task = await get_task_or_404(task_id, db)
    
    if task.status != TaskStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有待验收的任务可以评分"
        )
    
    task.status = TaskStatus.COMPLETED
    task.quality_q = review_in.quality_q
    task.actual_end = datetime.now(timezone.utc)
    
    # 计算最终得分
    task.final_score = calculate_score(task)
    
    await add_task_log(
        db, task.id, current_user.id, LogAction.REVIEWED,
        f"验收通过，Q={review_in.quality_q}, 得分={task.final_score:.1f}，{review_in.comment or ''}"
    )
    
    await db.flush()
    await db.refresh(task)
    
    return task


@router.post("/{task_id}/review-reject", response_model=TaskResponse)
async def review_reject_task(
    task_id: uuid.UUID,
    reason: str = Query(..., description="驳回原因"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_manager_or_admin),
):
    """
    验收不通过
    
    待验收 → 已驳回（返工，工期不重置）
    """
    task = await get_task_or_404(task_id, db)
    
    if task.status != TaskStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有待验收的任务可以驳回"
        )
    
    task.status = TaskStatus.REJECTED
    
    await add_task_log(db, task.id, current_user.id, LogAction.REVIEW_REJECTED, f"验收不通过：{reason}")
    
    await db.flush()
    await db.refresh(task)
    
    return task


@router.post("/{task_id}/resume", response_model=TaskResponse)
async def resume_task(
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    返工继续
    
    已驳回 → 进行中
    """
    task = await get_task_or_404(task_id, db)
    
    if task.status != TaskStatus.REJECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有已驳回的任务可以返工"
        )
    
    task.status = TaskStatus.IN_PROGRESS
    
    await add_task_log(db, task.id, current_user.id, LogAction.RESUMED, "返工继续")
    
    await db.flush()
    await db.refresh(task)
    
    return task


# ============ 子任务管理 ============

@router.post("/{task_id}/subtasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_subtask(
    task_id: uuid.UUID,
    subtask_in: SubTaskCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    创建子任务
    """
    parent_task = await get_task_or_404(task_id, db)
    
    if parent_task.parent_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能为子任务创建子任务"
        )
    
    subtask = Task(
        title=subtask_in.title,
        description=subtask_in.description,
        executor_id=subtask_in.executor_id,
        plan_end=subtask_in.plan_end,
        weight=subtask_in.weight,
        parent_id=task_id,
        creator_id=current_user.id,
        task_type=parent_task.task_type,
        status=TaskStatus.DRAFT,
    )
    
    db.add(subtask)
    await db.flush()
    await db.refresh(subtask)
    
    return subtask


@router.get("/{task_id}/logs")
async def get_task_logs(
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    获取任务日志
    """
    await get_task_or_404(task_id, db)
    
    result = await db.execute(
        select(TaskLog)
        .where(TaskLog.task_id == task_id)
        .order_by(TaskLog.created_at.desc())
    )
    
    logs = result.scalars().all()
    
    return [
        {
            "id": str(log.id),
            "action": log.action.value,
            "content": log.content,
            "progress_before": log.progress_before,
            "progress_after": log.progress_after,
            "evidence_url": log.evidence_url,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
