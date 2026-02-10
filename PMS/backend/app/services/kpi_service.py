"""
绩效计算服务

实现绩效评价公式 S = max(0, (B×I×D)×Q×T − P)
"""
from datetime import datetime, timezone
from typing import Optional

from app.core.config import get_settings
from app.models.task import Task, TaskStatus

settings = get_settings()


def calculate_timeliness(task: Task) -> float:
    """
    计算时效系数 T
    
    公式：
    - T = 1.0, 当 Δt ≤ 0（准时或提前完成）
    - T = max(0.2, 1.0 - Δt/D × f), 当 Δt > 0（逾期）
    
    其中：
    - Δt = 实际完成时间 - 计划完成时间
    - D = 计划总工期
    - f = 惩罚因子（默认 1.0）
    
    Args:
        task: 任务对象
        
    Returns:
        float: 时效系数 (0.2 - 1.0)
    """
    if not task.plan_end or not task.plan_start:
        return 1.0
    
    # 计算实际完成时间（如果未完成，使用当前时间）
    actual_end = task.actual_end or datetime.now(timezone.utc)
    
    # 如果任务还未开始或处于草稿状态，返回 1.0
    if task.status in [TaskStatus.DRAFT, TaskStatus.PENDING_APPROVAL]:
        return 1.0
    
    # 计算超期时长 Δt（天）
    delta_t = (actual_end - task.plan_end).total_seconds() / (24 * 60 * 60)
    
    # 准时或提前完成
    if delta_t <= 0:
        return 1.0
    
    # 计划总工期 D_duration（天）
    planned_duration = (task.plan_end - task.plan_start).total_seconds() / (24 * 60 * 60)
    
    # 防止除零
    if planned_duration <= 0:
        planned_duration = 1.0
    
    # 计算时效系数
    penalty_factor = settings.penalty_factor
    min_timeliness = settings.min_timeliness
    
    # T = max(0.2, 1.0 - (Delta_t / Duration) * f)
    # 逾期计算公式更新：
    # if delta_t > 0: T = max(0.2, 1.0 - (delta_t / planned_duration) * penalty_factor)
    timeliness = 1.0 - (delta_t / planned_duration) * penalty_factor
    
    # 保底 0.2
    return max(min_timeliness, timeliness)


def calculate_score(task: Task, penalty: float = 0.0) -> float:
    """
    计算任务最终得分 S
    
    公式：S = max(0, (B × I × D) × Q × T − P)
    
    Args:
        task: 任务对象
        penalty: 罚分 P（红牌触发）
        
    Returns:
        float: 最终得分
    """
    # 子任务工作量 B_sub (Sub-workload)
    # 如果是子任务且设置了 workload_b，则使用 workload_b
    # 否则使用 settings.base_score (兼容旧数据或主任务)
    workload_b = task.workload_b if task.workload_b > 0 else settings.base_score
    
    # 重要性系数 I & 难度系数 D
    # "性质继承"：如果存在父任务，则继承父任务的 I/D
    if task.parent:
        importance_i = task.parent.importance_i or 1.0
        difficulty_d = task.parent.difficulty_d or 1.0
    else:
        importance_i = task.importance_i or 1.0
        difficulty_d = task.difficulty_d or 1.0
    
    # 质量系数 Q_sub（如果未评分，默认 1.0）
    quality_q = task.quality_q or 1.0
    
    # 时效系数 T_sub
    timeliness_t = calculate_timeliness(task)
    
    # 计算得分 S_exec = B_sub * I_main * D_main * Q_sub * T_sub
    # 注意：不再减去 Penalty，Penalty 建议单独记录 or 在最终结算时扣除。
    # 这里遵照原逻辑先减去 penalty 参数
    # 新公式：Score = B * I * D * Q * T
    raw_score = workload_b * importance_i * difficulty_d * quality_q * timeliness_t
    
    # 暂时保留 completion_rate 逻辑，虽然公式只针对 Completed 任务
    completion_rate = (task.progress or 0) / 100.0
    
    score = raw_score * completion_rate - penalty
    
    # 最低为 0
    return max(0, score)


def check_kpi_eligibility(task: Task) -> bool:
    """
    检查任务是否符合绩效池准入规则
    
    规则：只有 I × D > 0.5 的任务才进入绩效榜单
    
    Args:
        task: 任务对象
        
    Returns:
        bool: 是否符合条件
    """
    importance_i = task.importance_i or 1.0
    difficulty_d = task.difficulty_d or 1.0
    
    return (importance_i * difficulty_d) > 0.5


def calculate_overdue_ratio(task: Task) -> Optional[float]:
    """
    计算超期倍数
    
    超期倍数 = 超期时长 / 计划工期
    
    Args:
        task: 任务对象
        
    Returns:
        Optional[float]: 超期倍数，如果未逾期返回 None
    """
    if not task.plan_end or not task.plan_start:
        return None
    
    now = datetime.now(timezone.utc)
    actual_end = task.actual_end or now
    
    # 计算超期时长（天）
    delta_t = (actual_end - task.plan_end).total_seconds() / (24 * 60 * 60)
    
    if delta_t <= 0:
        return None
    
    # 计划工期（天）
    total_duration = (task.plan_end - task.plan_start).total_seconds() / (24 * 60 * 60)
    
    if total_duration <= 0:
        return delta_t  # 工期为 0 时，返回超期天数
    
    return delta_t / total_duration
