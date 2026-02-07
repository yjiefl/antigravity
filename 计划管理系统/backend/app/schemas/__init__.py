"""
模式模块初始化
"""
from app.schemas.auth import (
    Token,
    TokenData,
    LoginRequest,
    LoginResponse,
)
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserBrief,
    PasswordChange,
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    PositionCreate,
    PositionUpdate,
    PositionResponse,
)
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskBrief,
    TaskWithSubtasks,
    TaskApprove,
    TaskReview,
    TaskProgress,
    TaskComplete,
    TaskTransfer,
    TaskFilter,
    TaskScorePreview,
    SubTaskCreate,
)

__all__ = [
    # 认证
    "Token",
    "TokenData",
    "LoginRequest",
    "LoginResponse",
    # 用户
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserBrief",
    "PasswordChange",
    "OrganizationCreate",
    "OrganizationUpdate",
    "OrganizationResponse",
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentResponse",
    "PositionCreate",
    "PositionUpdate",
    "PositionResponse",
    # 任务
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "TaskBrief",
    "TaskWithSubtasks",
    "TaskApprove",
    "TaskReview",
    "TaskProgress",
    "TaskComplete",
    "TaskTransfer",
    "TaskFilter",
    "TaskScorePreview",
    "SubTaskCreate",
]
