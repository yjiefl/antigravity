"""
Pydantic 模式定义 - 认证相关
"""
import uuid
from typing import Optional, List

from pydantic import BaseModel, Field

from app.models.user import UserRole


class Token(BaseModel):
    """JWT 令牌响应"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """令牌数据（从 JWT 解析）"""
    user_id: Optional[uuid.UUID] = None
    username: Optional[str] = None
    roles: Optional[List[UserRole]] = None


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    username: str
    real_name: str
    roles: List[UserRole]
