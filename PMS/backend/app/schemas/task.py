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
    category: str = Field(TaskCategory.OTHER.value, description="计划分类")
    sub_category: Optional[str] = Field(None, max_length=50, description="小类")
    tags: Optional[str] = Field(None, max_length=200, description="标签")
    plan_start: Optional[datetime] = Field(None, description="计划开始时间")
    plan_end: Optional[datetime] = Field(None, description="计划完成时间")
    
    @field_validator('plan_start', 'plan_end', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        """支持 YYYY-MM-DD 和 ISO 格式"""
        if isinstance(v, str):
            # 如果是 YYYY-MM-DD
            if len(v) == 10:
                try:
                    from datetime import datetime
                    return datetime.strptime(v, '%Y-%m-%d')
                except ValueError:
                    pass
            # 尝试 ISO 格式 (带 T)
            try:
                from datetime import datetime
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                pass
        return v

    @field_validator('plan_end')
    @classmethod
    def validate_end_date(cls, v, info):
        """验证结束时间不能早于开始时间"""
        if v and info.data.get('plan_start'):
            start = info.data['plan_start']
            # Pydantic 验证顺序可能导致 start 还没被处理成 datetime? 
            # 通常 validator 是按字段顺序。plan_end 在后，所以 info.data['plan_start'] 应该是处理过的。
            # 如果 plan_start 也是 None 或非法则跳过
            if start and v < start:
                 raise ValueError('计划完成时间不能早于计划开始时间')
        return v


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
    reviewer_id: Optional[uuid.UUID] = Field(None, description="审批人ID")
    parent_id: Optional[uuid.UUID] = Field(None, description="父任务ID")
    weight: float = Field(1.0, ge=0.0, le=10.0, description="权重")

    @field_validator('plan_end')
    @classmethod
    def validate_end_date_create(cls, v, info):
        if v and info.data.get('plan_start'):
            if v < info.data['plan_start']:
                raise ValueError('计划完成时间不能早于计划开始时间')
        return v


class SubTaskCreate(BaseModel):
    """创建子任务"""
    title: str = Field(..., max_length=200, description="子任务标题")
    description: Optional[str] = Field(None, description="描述")
    executor_id: Optional[uuid.UUID] = Field(None, description="实施人ID")
    plan_end: Optional[datetime] = Field(None, description="截止时间")
    weight: float = Field(1.0, ge=0.0, le=10.0, description="权重")

    @field_validator('plan_end', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        if isinstance(v, str):
            if len(v) == 10:
                from datetime import datetime
                try:
                    return datetime.strptime(v, '%Y-%m-%d')
                except ValueError:
                    pass
            try:
                from datetime import datetime
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                pass
        return v


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
    reviewer_id: Optional[uuid.UUID] = None

    @field_validator('plan_start', 'plan_end', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        if isinstance(v, str):
            if len(v) == 10:
                from datetime import datetime
                try:
                    return datetime.strptime(v, '%Y-%m-%d')
                except ValueError:
                    pass
            try:
                from datetime import datetime
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                pass
        return v

    @field_validator('plan_end')
    @classmethod
    def validate_end_date_update(cls, v, info):
         # 更新时可能只更新了 plan_end 没有 plan_start，或者反之。
         # 这是一个 partial update，验证比较麻烦，因为不知道数据库里的 plan_start 是什么。
         # 简单的做法是：如果 payload 里同时有 plan_start 和 plan_end，则验证。
         # 如果只有其中一个，我们在 Service 层或 API 层结合 DB 数据验证更稳妥，或者在这里跳过。
         # 为了满足“后端兜底”的要求，我们可以尽量验证。但这需要 task 上下文。Pydantic 这里只有输入数据。
         # 暂且只验证“如果同时提供了两者”。
         if v and info.data.get('plan_start'):
             if v < info.data['plan_start']:
                 raise ValueError('计划完成时间不能早于计划开始时间')
         return v


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


class TaskExtensionRequest(BaseModel):
    """申请延期"""
    extension_reason: str = Field(..., description="延期理由")
    extension_date: datetime = Field(..., description="申请延期至")

    @field_validator('extension_date', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        if isinstance(v, str):
            try:
                from datetime import datetime
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                pass
        return v



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
    plan_start: Optional[datetime]
    plan_end: Optional[datetime]
    executor_id: Optional[uuid.UUID]
    description: Optional[str]
    parent_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime

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
    # 延期字段
    extension_status: Optional[str] = None
    extension_reason: Optional[str] = None
    extension_date: Optional[datetime] = None
    reviewer_id: Optional[uuid.UUID] = None
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
    category: str = Field(TaskCategory.OTHER.value, description="计划分类")
    creator_id: Optional[uuid.UUID] = None
    owner_id: Optional[uuid.UUID] = None
    executor_id: Optional[uuid.UUID] = None
    keyword: Optional[str] = Field(None, description="关键字搜索")
    is_overdue: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        if isinstance(v, str) and len(v) == 10:
            from datetime import datetime
            try:
                return datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                return v
        return v
