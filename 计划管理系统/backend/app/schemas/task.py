"""
Pydantic 模式定义 - 任务相关

用于 API 请求/响应的数据验证
"""
import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator

from app.models.task import TaskStatus, TaskType, TaskCategory


# ============ 基础模式 ============

class TaskBase(BaseModel):
    """任务基础模式"""
    title: str = Field(..., max_length=200, description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")
    task_type: TaskType = Field(TaskType.PERFORMANCE, description="任务类型")
    category: TaskCategory = Field(TaskCategory.OTHER, description="计划分类")
    sub_category: Optional[str] = Field(None, max_length=50, description="小类")
    tags: Optional[str] = Field(None, max_length=200, description="标签")
    plan_start: Optional[datetime] = Field(None, description="计划开始时间")
    plan_end: Optional[datetime] = Field(None, description="计划完成时间")


class TaskCoefficients(BaseModel):
    """任务系数模式"""
    importance_i: float = Field(1.0, ge=0.5, le=1.5, description="重要性系数 I")
    difficulty_d: float = Field(1.0, ge=0.8, le=1.5, description="难度系数 D")
    
    @field_validator('importance_i', 'difficulty_d')
    @classmethod
    def validate_coefficient(cls, v):
        """验证系数精度"""
        return round(v, 2)


# ============ 创建模式 ============

class TaskCreate(TaskBase):
    """创建任务"""
    owner_id: Optional[uuid.UUID] = Field(None, description="负责人ID")
    executor_id: Optional[uuid.UUID] = Field(None, description="实施人ID")
    parent_id: Optional[uuid.UUID] = Field(None, description="父任务ID")
    weight: float = Field(1.0, ge=0.0, le=10.0, description="权重")


class SubTaskCreate(BaseModel):
    """创建子任务"""
    title: str = Field(..., max_length=200, description="子任务标题")
    description: Optional[str] = Field(None, description="描述")
    executor_id: Optional[uuid.UUID] = Field(None, description="实施人ID")
    plan_end: Optional[datetime] = Field(None, description="截止时间")
    weight: float = Field(1.0, ge=0.0, le=10.0, description="权重")


# ============ 更新模式 ============

class TaskUpdate(BaseModel):
    """更新任务"""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    category: Optional[TaskCategory] = None
    sub_category: Optional[str] = Field(None, max_length=50)
    tags: Optional[str] = Field(None, max_length=200)
    plan_start: Optional[datetime] = None
    plan_end: Optional[datetime] = None
    owner_id: Optional[uuid.UUID] = None
    executor_id: Optional[uuid.UUID] = None


class TaskApprove(TaskCoefficients):
    """审批任务（设定 I/D 系数）"""
    pass


class TaskReview(BaseModel):
    """验收评分"""
    quality_q: float = Field(..., ge=0.0, le=1.2, description="质量系数 Q")
    comment: Optional[str] = Field(None, description="验收评语")


class TaskProgress(BaseModel):
    """更新进展"""
    progress: int = Field(..., ge=0, le=100, description="进度百分比")
    content: Optional[str] = Field(None, description="进展说明")
    evidence_url: Optional[str] = Field(None, description="证据链接")


class TaskComplete(BaseModel):
    """提交验收"""
    evidence_url: Optional[str] = Field(None, description="验收证据链接")
    comment: Optional[str] = Field(None, description="完成备注")


class TaskTransfer(BaseModel):
    """任务转移"""
    new_executor_id: uuid.UUID = Field(..., description="新实施人ID")
    lock_progress: bool = Field(True, description="是否锁定已完成进度的积分")
    reason: Optional[str] = Field(None, description="转移原因")


# ============ 响应模式 ============

class TaskBrief(BaseModel):
    """任务简要信息"""
    id: uuid.UUID
    title: str
    status: TaskStatus
    progress: int
    plan_end: Optional[datetime]
    executor_id: Optional[uuid.UUID]

    class Config:
        from_attributes = True


class TaskResponse(TaskBase):
    """任务详情响应"""
    id: uuid.UUID
    status: TaskStatus
    importance_i: Optional[float]
    difficulty_d: Optional[float]
    quality_q: Optional[float]
    progress: int
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    creator_id: uuid.UUID
    owner_id: Optional[uuid.UUID]
    executor_id: Optional[uuid.UUID]
    parent_id: Optional[uuid.UUID]
    weight: float
    final_score: Optional[float]
    evidence_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskWithSubtasks(TaskResponse):
    """任务详情（含子任务）"""
    subtasks: List[TaskBrief] = []


class TaskScorePreview(BaseModel):
    """任务得分预览"""
    task_id: uuid.UUID
    base_score: int
    importance_i: float
    difficulty_d: float
    quality_q: Optional[float]
    timeliness_t: float
    penalty_p: float
    current_score: float
    max_possible_score: float
    is_overdue: bool
    overdue_days: Optional[int]


# ============ 查询模式 ============

class TaskFilter(BaseModel):
    """任务过滤条件"""
    status: Optional[TaskStatus] = None
    task_type: Optional[TaskType] = None
    category: Optional[TaskCategory] = None
    creator_id: Optional[uuid.UUID] = None
    owner_id: Optional[uuid.UUID] = None
    executor_id: Optional[uuid.UUID] = None
    keyword: Optional[str] = Field(None, description="关键字搜索")
    is_overdue: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
