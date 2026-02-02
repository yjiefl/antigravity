"""
储能自动调节系统 - FastAPI应用入口

光储电站储能AGC有功控制系统
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routers.api import router
from app.database import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    在应用启动时初始化数据库，在关闭时进行清理
    """
    # 启动时初始化数据库
    db.init_db()
    print("✅ 数据库初始化完成")
    
    yield
    
    # 关闭时的清理工作
    print("👋 应用关闭")


# 创建FastAPI应用实例
app = FastAPI(
    title="储能自动调节系统",
    description="""
## 光储电站储能AGC有功控制系统

根据调度AGC指令、光伏出力、储能当前状态等参数，
自动计算储能系统应如何调节出力。

### 核心功能
- 📊 **调节计算**: 根据输入参数计算储能调节目标
- 📝 **历史记录**: 保存和查询调节计算历史
- ⚙️ **配置管理**: 管理系统参数配置

### 业务公式
```
总有功 = 光伏出力 + 储能出力
储能调节目标 = 调度指令值 - 光伏出力
```
    """,
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS中间件，允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(router)


@app.get("/")
async def root():
    """
    根路径，返回系统信息
    """
    return {
        "name": "储能自动调节系统",
        "version": "1.0.0",
        "description": "光储电站储能AGC有功控制系统",
        "docs_url": "/docs",
        "api_prefix": "/api/v1"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
