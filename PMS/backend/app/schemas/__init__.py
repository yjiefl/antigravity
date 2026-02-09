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
    UserBrief,
    PasswordChange,
    PasswordReset,
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
    TaskExtensionRequest,
)
from app.schemas.audit import (
    AuditLogCreate,
    AuditLogResponse,
    AuditLogQuery,
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
    "UserBrief",
    "PasswordChange",
    "PasswordReset",
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
    "TaskExtensionRequest",
    # 审计日志
    "AuditLogCreate",
    "AuditLogResponse",
    "AuditLogQuery",
]
