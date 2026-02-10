"""
任务管理 API 路由

处理任务 CRUD、状态机流转、子任务管理
"""
import uuid
from datetime import datetime, timezone
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Form
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import get_db
from app.models import User, Task, TaskLog, TaskStatus, TaskType, LogAction, UserRole
from app.schemas import (
    TaskCreate, TaskUpdate, TaskResponse, TaskBrief, TaskWithSubtasks,
    TaskApprove, TaskReview, TaskProgress, TaskComplete, TaskTransfer,
    TaskFilter, SubTaskCreate, TaskExtensionRequest,
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


async def add_task_log(
    db: AsyncSession,
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    action: LogAction,
    content: Optional[str] = None,
    progress_before: Optional[int] = None,
    progress_after: Optional[int] = None,
    evidence_url: Optional[str] = None,
    attachments_meta: Optional[list[dict]] = None,
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
    # 如果有附件元数据，创建 Attachment 记录
    if attachments_meta:
        from app.models.attachment import Attachment
        for meta in attachments_meta:
            attachment = Attachment(
                task_id=task_id,
                # log_id=log.id,  # 通过关系自动关联
                uploader_id=user_id,
                filename=meta["filename"],
                file_path=meta["file_path"],
                file_type=meta["file_type"],
                file_size=meta["file_size"],
            )
            log.attachments.append(attachment)
            db.add(attachment)
    
    return log


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
    query = select(Task)  # 不再强制过滤子任务，以便让执行人看到分配给自己的子任务
    
    # 权限过滤：普通员工只能看到自己相关的任务
    if UserRole.STAFF in current_user.roles and UserRole.ADMIN not in current_user.roles and UserRole.MANAGER not in current_user.roles:
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
        department_id=current_user.department_id,
        status=TaskStatus.DRAFT,
    )
    
    db.add(task)
    await db.flush()
    
    # 记录日志
    await add_task_log(db, task.id, current_user.id, LogAction.CREATED, "创建任务")
    
    # await db.refresh(task)
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
    
    草稿和待提交状态可编辑基本信息
    """
    task = await get_task_or_404(task_id, db)
    
    if task.status not in (TaskStatus.DRAFT, TaskStatus.PENDING_SUBMISSION):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有草稿或待提交状态的任务可以编辑"
        )
    
    for field, value in task_in.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    
    await db.flush()
    # await db.refresh(task)
    
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
    
    草稿/待提交 → 待审批
    """
    task = await get_task_or_404(task_id, db)
    
    if task.status not in (TaskStatus.DRAFT, TaskStatus.PENDING_SUBMISSION):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有草稿或待提交状态的任务可以提交审批"
        )
    
    task.status = TaskStatus.PENDING_APPROVAL
    await add_task_log(db, task.id, current_user.id, LogAction.SUBMITTED, "提交审批")
    
    await db.flush()
    # await db.refresh(task)
    
    return task


@router.post("/{task_id}/mark-pending", response_model=TaskResponse)
async def mark_pending_submission(
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    标记任务为待提交状态
    
    草稿 → 待提交
    """
    task = await get_task_or_404(task_id, db)
    
    if task.status != TaskStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有草稿状态的任务可以标记为待提交"
        )
    
    task.status = TaskStatus.PENDING_SUBMISSION
    await add_task_log(db, task.id, current_user.id, LogAction.SUBMITTED, "标记为待提交")
    
    await db.flush()
    return task


@router.post("/{task_id}/withdraw", response_model=TaskResponse)
async def withdraw_task(
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    撤回任务审批
    
    待审批 → 草稿
    """
    task = await get_task_or_404(task_id, db)
    
    if task.status != TaskStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有待审批状态的任务可以撤回"
        )
    
    # 权限检查：仅创建者或负责人可撤回
    if task.creator_id != current_user.id and task.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有任务创建者或负责人可以撤回"
        )
    
    task.status = TaskStatus.DRAFT
    await add_task_log(db, task.id, current_user.id, LogAction.WITHDRAWN, "撤回审批申请")
    
    await db.flush()
    return task


@router.post("/{task_id}/return", response_model=TaskResponse)
async def return_task(
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_manager_or_admin)],
    reason: str = Query(..., description="退回原因"),
):
    """
    退回任务 (主管操作)
    
    待审批 → 草稿
    待验收 → 进行中
    仅任务指定的审批人或管理员可操作
    """
    task = await get_task_or_404(task_id, db)
    
    # 校验审批权限
    if task.reviewer_id and task.reviewer_id != current_user.id and UserRole.ADMIN not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有该任务指定的审批人才能退回"
        )
    
    if task.status == TaskStatus.PENDING_APPROVAL:
        # 退回到草稿
        task.status = TaskStatus.DRAFT
        action = LogAction.REJECTED
        msg = f"退回任务（至草稿）：{reason}"
    elif task.status == TaskStatus.PENDING_REVIEW:
        # 退回到进行中
        task.status = TaskStatus.IN_PROGRESS
        action = LogAction.REVIEW_REJECTED
        msg = f"退回任务（至进行中）：{reason}"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前状态无法执行退回操作"
        )
    
    await add_task_log(db, task.id, current_user.id, action, msg)
    
    await db.flush()
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
    仅任务指定的审批人或管理员可操作
    """
    task = await get_task_or_404(task_id, db)
    
    if task.status != TaskStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有待审批状态的任务可以审批"
        )
    
    # 校验审批权限：必须是指定的 reviewer 或 admin
    if task.reviewer_id and task.reviewer_id != current_user.id and UserRole.ADMIN not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有该任务指定的审批人才能审批"
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
    # await db.refresh(task)
    
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
    仅任务指定的审批人或管理员可操作
    """
    task = await get_task_or_404(task_id, db)
    
    if task.status != TaskStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有待审批状态的任务可以驳回"
        )
    
    # 校验审批权限
    if task.reviewer_id and task.reviewer_id != current_user.id and UserRole.ADMIN not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有该任务指定的审批人才能驳回"
        )
    
    task.status = TaskStatus.DRAFT
    await add_task_log(db, task.id, current_user.id, LogAction.REJECTED, f"驳回原因：{reason}")
    
    await db.flush()
    # await db.refresh(task)
    
    return task


@router.post("/{task_id}/progress", response_model=TaskResponse)
async def update_progress(
    task_id: uuid.UUID,
    progress: int = Form(..., description="进度百分比", ge=0, le=100),
    content: Optional[str] = Form(None, description="进展说明"),
    files: List[UploadFile] = File(None, description="证明附件"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新任务进展 (支持附件上传)
    
    仅进行中状态可更新
    """
    from app.utils.file import save_upload_file
    
    task = await get_task_or_404(task_id, db)
    
    if task.status != TaskStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有进行中的任务可以更新进展"
        )
    
    progress_before = task.progress
    
    # 防止进度倒退 - 改为允许，但前端需提示确认
    # if progress < progress_before:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail=f"新进度 ({progress}%) 不能小于当前进度 ({progress_before}%)"
    #     )
    
    task.progress = progress
    
    # 处理文件上传
    attachments_meta = []
    if files:
        from app.utils.file import save_multiple_files
        attachments_meta = await save_multiple_files(files)
        # 为了兼容旧版字段，取第一个作为 evidence_url
        if attachments_meta:
            task.evidence_url = attachments_meta[0]["file_path"]
    
    await add_task_log(
        db, task.id, current_user.id, LogAction.PROGRESS_UPDATED,
        content,
        progress_before=progress_before,
        progress_after=progress,
        evidence_url=task.evidence_url,
        attachments_meta=attachments_meta,
    )
    
    await db.flush()
    # await db.refresh(task)
    
    return task


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: uuid.UUID,
    comment: Optional[str] = Form(None, description="完成备注"),
    files: List[UploadFile] = File(None, description="交付物/证据"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    提交验收 (支持附件上传)
    
    进行中 → 待验收
    """
    from app.utils.file import save_upload_file
    
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
    
    # 记录之前的进度
    progress_before = task.progress
    
    task.status = TaskStatus.PENDING_REVIEW
    task.progress = 100  # 强制设置为 100%
    
    # 处理文件上传
    attachments_meta = []
    if files:
        from app.utils.file import save_multiple_files
        attachments_meta = await save_multiple_files(files)
        if attachments_meta:
            task.evidence_url = attachments_meta[0]["file_path"]
    
    await add_task_log(
        db, task.id, current_user.id, LogAction.COMPLETED,
        comment,
        progress_before=progress_before,
        progress_after=100,
        evidence_url=task.evidence_url,
        attachments_meta=attachments_meta,
    )
    
    await db.flush()
    # await db.refresh(task)
    
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
    仅任务指定的审批人或管理员可操作
    """
    task = await get_task_or_404(task_id, db)
    
    if task.status != TaskStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有待验收的任务可以评分"
        )
    
    # 校验验收权限
    if task.reviewer_id and task.reviewer_id != current_user.id and UserRole.ADMIN not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有该任务指定的审批人才能验收评分"
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
    # await db.refresh(task)
    
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
    # await db.refresh(task)
    
    return task


@router.post("/{task_id}/rollback", response_model=TaskResponse)
async def rollback_task(
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    提交回退
    
    待验收 → 进行中
    """
    task = await get_task_or_404(task_id, db)
    
    if task.status != TaskStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有待验收的任务可以回退"
        )
    
    task.status = TaskStatus.IN_PROGRESS
    
    await add_task_log(db, task.id, current_user.id, LogAction.RESUMED, "申请回退")
    
    await db.flush()
    # await db.refresh(task)
    
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
    # await db.refresh(task)
    
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
        .options(selectinload(TaskLog.attachments))
        .where(TaskLog.task_id == task_id)
        .order_by(TaskLog.created_at.desc())
    )
    
    logs = result.scalars().all()
    
    return [
        {
            "id": str(log.id),
            "action": log.action,
            "content": log.content,
            "evidence_url": log.evidence_url,
            "progress_before": log.progress_before,
            "progress_after": log.progress_after,
            "created_at": log.created_at,
            "attachments": [
                {
                    "id": str(a.id),
                    "filename": a.filename,
                    "file_path": a.file_path,
                    "file_type": a.file_type,
                    "file_size": a.file_size,
                    "download_count": a.download_count,
                    "created_at": a.created_at,
                }
                for a in log.attachments
            ]
        }
        for log in logs
    ]
# ============ 延期管理 ============

@router.post("/{task_id}/request-extension", response_model=TaskResponse)
async def request_extension(
    task_id: uuid.UUID,
    ext_in: TaskExtensionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    申请任务延期
    """
    task = await get_task_or_404(task_id, db)
    
    if task.status not in [TaskStatus.IN_PROGRESS, TaskStatus.REJECTED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有进行中或驳回状态的任务可以申请延期"
        )
    
    if task.executor_id != current_user.id and task.owner_id != current_user.id:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有任务负责人或实施人可以申请延期"
        )

    task.extension_status = "pending"
    task.extension_reason = ext_in.extension_reason
    task.extension_date = ext_in.extension_date
    
    await add_task_log(
        db, task.id, current_user.id, LogAction.PROGRESS_UPDATED, 
        f"申请延期至 {ext_in.extension_date.strftime('%Y-%m-%d %H:%M')}, 原因: {ext_in.extension_reason}"
    )
    
    await db.flush()
    return task


@router.post("/{task_id}/approve-extension", response_model=TaskResponse)
async def approve_extension(
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_manager_or_admin)],
):
    """
    通过延期申请（仅主管/管理员）
    """
    task = await get_task_or_404(task_id, db)
    
    if task.extension_status != "pending":
        raise HTTPException(status_code=400, detail="没有待处理的延期申请")
    
    old_end = task.plan_end
    task.plan_end = task.extension_date
    task.extension_status = "approved"
    
    await add_task_log(
        db, task.id, current_user.id, LogAction.APPROVED, 
        f"通过延期申请。原截止: {old_end.strftime('%Y-%m-%d')}, 新截止: {task.plan_end.strftime('%Y-%m-%d')}"
    )
    
    await db.flush()
    return task


@router.post("/{task_id}/reject-extension", response_model=TaskResponse)
async def reject_extension(
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_manager_or_admin)],
):
    """
    驳回延期申请（仅主管/管理员）
    """
    task = await get_task_or_404(task_id, db)
    
    if task.extension_status != "pending":
        raise HTTPException(status_code=400, detail="没有待处理的延期申请")
    
    task.extension_status = "rejected"
    
    await add_task_log(db, task.id, current_user.id, LogAction.REJECTED, "驳回延期申请")
    
    await db.flush()
    return task
