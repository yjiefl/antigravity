"""
计划管理系统 FastAPI 主程序入口

启动命令: uvicorn app.main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import init_db
from app.api import auth, users, tasks, kpi, reports, appeals

settings = get_settings()


from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.jobs.overdue_check import check_overdue_tasks

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    启动时初始化数据库，关闭时清理资源
    """
    # 启动时执行
    print("🚀 正在启动计划管理系统...")
    await init_db()
    print("✅ 数据库初始化完成")
    
    # 启动定时任务
    scheduler.add_job(check_overdue_tasks, "interval", minutes=30)
    scheduler.start()
    print("⏰ 定时任务调度器已启动")
    
    yield
    
    # 关闭时执行
    scheduler.shutdown()
    print("👋 计划管理系统已关闭")


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="适配企业组织架构、覆盖任务全生命周期的轻量级管理工具",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# 配置 CORS（跨域资源共享）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册 API 路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/users", tags=["用户管理"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["任务管理"])
app.include_router(kpi.router, prefix="/api/kpi", tags=["绩效统计"])
app.include_router(reports.router, prefix="/api/reports", tags=["报表"])
app.include_router(appeals.router, prefix="/api/appeals", tags=["申诉管理"])


@app.get("/api/health", tags=["系统"])
async def health_check():
    """
    健康检查接口
    
    用于验证服务是否正常运行
    """
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/", tags=["系统"])
async def root():
    """
    根路径重定向到 API 文档
    """
    return {
        "message": f"欢迎使用{settings.app_name}",
        "docs": "/api/docs",
        "redoc": "/api/redoc",
    }
