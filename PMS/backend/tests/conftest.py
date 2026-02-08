"""
Pytest 配置与 Fixtures
"""
import asyncio
from typing import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.models import User, UserRole, UserRoleBinding

from sqlalchemy.pool import StaticPool

# 测试数据库（内存 SQLite）
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
    echo=False,
)

TestingSessionLocal = async_sessionmaker(
    engine_test,
    class_=AsyncSession,
    expire_on_commit=False,
)





@pytest.fixture(scope="function")
async def db_engine():
    """初始化数据库并创建表"""
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine_test
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """每个测试函数创建一个新的 Session，并在结束后回滚"""
    async with TestingSessionLocal() as session:
        yield session
        # 由于 session fixture 结束时会关闭 session，
        # 如果需要彻底清理数据，可以在这里手动 truncate 表，或者让 SQLAlchemy 事务回滚机制处理
        # 这里使用简单的 session 上下文管理


@pytest.fixture(scope="function")
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端，替换数据库依赖"""
    
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def admin_token(client, db_session):
    """创建管理员用户并获取 Token"""
    # 检查是否已存在（避免并发测试冲突，虽然这里是内存库）
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.username == "admin"))
    if not result.scalar_one_or_none():
        user = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            real_name="Admin",
            roles_binding=[UserRoleBinding(role=UserRole.ADMIN)],
        )
        db_session.add(user)
        await db_session.commit()
    
    response = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    return response.json()["access_token"]


@pytest.fixture(scope="function")
async def staff_token(client, db_session):
    """创建普通员工并获取 Token"""
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.username == "staff"))
    if not result.scalar_one_or_none():
        user = User(
            username="staff",
            password_hash=get_password_hash("staff123"),
            real_name="Staff",
            roles_binding=[UserRoleBinding(role=UserRole.STAFF)],
        )
        db_session.add(user)
        await db_session.commit()
    
    response = await client.post(
        "/api/auth/login",
        data={"username": "staff", "password": "staff123"}
    )
    return response.json()["access_token"]


@pytest.fixture(scope="function")
async def manager_token(client, db_session):
    """创建主管并获取 Token"""
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.username == "manager"))
    if not result.scalar_one_or_none():
        user = User(
            username="manager",
            password_hash=get_password_hash("manager123"),
            real_name="Manager",
            roles_binding=[UserRoleBinding(role=UserRole.MANAGER)],
        )
        db_session.add(user)
        await db_session.commit()
    
    response = await client.post(
        "/api/auth/login",
        data={"username": "manager", "password": "manager123"}
    )
    return response.json()["access_token"]
