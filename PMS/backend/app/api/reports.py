"""
报表导出 API
"""
from datetime import datetime, timezone
from io import BytesIO
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import openpyxl

from app.core import get_db
from app.api.auth import get_current_user
from app.models import User, Task, TaskStatus, TaskType, UserRole

router = APIRouter()


@router.get("/export/tasks")
async def export_tasks(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    status_filter: Optional[TaskStatus] = Query(None, alias="status"),
    task_type: Optional[TaskType] = Query(None),
    executor_id: Optional[str] = Query(None),
    owner_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
):
    """
    导出任务报表 (Excel)
    """
    # 构建查询
    query = select(Task).options(
        selectinload(Task.owner),
        selectinload(Task.executor)
    )
    
    # 权限过滤
    if current_user.role == UserRole.STAFF:
        query = query.where(
            or_(
                Task.creator_id == current_user.id,
                Task.owner_id == current_user.id,
                Task.executor_id == current_user.id,
            )
        )
    
    # 条件过滤
    if status_filter:
        query = query.where(Task.status == status_filter)
    if task_type:
        query = query.where(Task.task_type == task_type)
    if executor_id:
        query = query.where(Task.executor_id == executor_id)
    if owner_id:
        query = query.where(Task.owner_id == owner_id)
        
    # 时间范围过滤 (按创建时间或计划结束时间?)
    # 通常报表按计划结束时间筛选，或者创建时间。
    # 这里假设按创建时间
    if start_date:
        query = query.where(Task.created_at >= start_date)
    if end_date:
        query = query.where(Task.created_at <= end_date)
        
    query = query.order_by(Task.created_at.desc())
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    # 生成 Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "任务列表"
    
    # 表头
    headers = [
        "任务ID", "标题", "类型", "状态", "进度",
        "负责人", "实施人",
        "计划开始", "计划结束", "实际开始", "实际结束",
        "I系数", "D系数", "Q系数", "最终得分",
        "创建时间"
    ]
    ws.append(headers)
    
    for task in tasks:
        ws.append([
            str(task.id),
            task.title,
            task.task_type.value if hasattr(task.task_type, 'value') else str(task.task_type),
            task.status.value if hasattr(task.status, 'value') else str(task.status),
            f"{task.progress}%",
            task.owner.real_name if task.owner else "",
            task.executor.real_name if task.executor else "",
            format_date(task.plan_start),
            format_date(task.plan_end),
            format_date(task.actual_start),
            format_date(task.actual_end),
            task.importance_i,
            task.difficulty_d,
            task.quality_q,
            task.final_score,
            format_date(task.created_at)
        ])
        
    # 调整列宽
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column].width = min(adjusted_width, 50)  # 限制最大宽度
        
    # 保存到内存
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    filename = f"tasks_export_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def format_date(dt: Optional[datetime]) -> str:
    if not dt:
        return ""
    # 转为本地时间显示? 
    # 简单起见，显示 YYYY-MM-DD HH:MM
    return dt.strftime("%Y-%m-%d %H:%M")
