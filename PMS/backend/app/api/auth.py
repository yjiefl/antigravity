"""
认证 API 路由

处理用户登录、登出和当前用户信息
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Optional

from app.core import get_db, verify_password, create_access_token, decode_access_token
from app.models import User, UserRole
from app.schemas import LoginRequest, LoginResponse, Token, TokenData, UserResponse

router = APIRouter()

# OAuth2 密码模式 (不强制 header，以便支持 query token)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[Optional[str], Depends(oauth2_scheme)] = None,
    token_query: Annotated[Optional[str], Query(alias="token")] = None,
) -> User:
    """
    获取当前登录用户
    
    从 JWT 令牌解析用户信息并验证
    
    Args:
        token: JWT 访问令牌
        db: 数据库会话
        
    Returns:
        User: 当前用户对象
        
    Raises:
        HTTPException: 401 令牌无效或用户不存在
    """
    final_token = token or token_query
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not final_token:
        raise credentials_exception
    
    payload = decode_access_token(final_token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    return user


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    获取当前管理员用户
    
    验证当前用户是否为管理员角色
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def get_current_manager_or_admin(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    获取当前主管或管理员用户
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要主管或管理员权限"
        )
    return current_user


@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    用户登录
    
    验证用户名和密码，返回 JWT 访问令牌
    """
    # 查找用户
    result = await db.execute(
        select(User).where(User.username == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    if user is None or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    # 创建访问令牌
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value}
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        real_name=user.real_name,
        role=user.role,
    )


@router.post("/logout")
async def logout(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    用户登出
    
    注意：JWT 是无状态的，这里仅返回成功消息。
    客户端应删除本地存储的令牌。
    如需真正的令牌失效，需要使用 Redis 黑名单。
    """
    return {"message": "登出成功"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    获取当前用户信息
    """
    return current_user
