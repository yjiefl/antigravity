"""
数据库连接与会话管理模块

使用 SQLAlchemy 2.0 异步引擎
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

# SQLite 需要特殊配置
if "sqlite" in settings.database_url:
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # 调试模式下打印 SQL
    future=True,
    connect_args=connect_args,
)

# 创建异步会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """
    SQLAlchemy 声明式基类
    
    所有模型都应继承此类
    """
    pass


async def get_db() -> AsyncSession:
    """
    获取数据库会话的依赖注入函数
    
    用于 FastAPI 路由依赖
    
    Yields:
        AsyncSession: 异步数据库会话
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    初始化数据库（创建所有表）
    
    仅在开发环境使用，生产环境应使用 Alembic 迁移
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
