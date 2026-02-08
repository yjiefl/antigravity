"""
应用核心配置模块

使用 pydantic-settings 进行环境变量管理
"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    应用配置类
    
    从环境变量读取配置，支持 .env 文件
    """
    
    # 应用基础配置
    app_name: str = "Plan Management System"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 数据库配置
    database_url: str = "sqlite+aiosqlite:///./plan_management.db"
    
    # Redis 配置
    redis_url: str = "redis://localhost:6379/0"
    
    # JWT 认证配置
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 小时
    
    # 绩效算法参数（可动态调整）
    base_score: int = 100  # B - 任务基准分
    penalty_factor: float = 1.0  # f - 惩罚因子
    min_timeliness: float = 0.2  # 时效系数保底值
    
    # 红黄牌规则
    yellow_card_hours: int = 24  # 黄牌预警时间（小时）
    yellow_card_progress: int = 50  # 黄牌进度阈值（%）
    red_card_overdue_days: int = 3  # 红牌逾期天数
    
    # 申诉有效期（小时）
    appeal_expire_hours: int = 48
    
    # 强制评价期限（小时）
    force_review_hours: int = 48
    
    # 附件配置
    max_file_size: int = 20 * 1024 * 1024  # 默认 20MB
    allowed_file_types: list[str] = ["image/", "application/pdf", "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/zip", "text/plain"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """
    获取配置单例
    
    使用 lru_cache 确保全局只创建一个配置实例
    """
    return Settings()
