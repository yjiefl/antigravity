"""
储能自动调节系统 - Pydantic数据模型

定义API请求和响应的数据结构
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RegulationRequest(BaseModel):
    """
    调节计算请求模型
    
    包含储能系统调节所需的所有输入参数
    """
    # 储能当前出力（MW），正值表示放电，负值表示充电
    storage_power: float = Field(..., description="储能当前出力（MW），正值放电，负值充电")
    
    # 调度指令值（MW），AGC下达的发电计划
    dispatch_target: float = Field(..., description="调度指令值（MW）")
    
    # 光伏出力（MW），光伏电站当前发电功率
    pv_power: float = Field(..., description="光伏出力（MW）")
    
    # 储能充电上限（MW），负值，表示最大充电功率
    charge_limit: float = Field(default=-50.0, description="储能充电上限（MW），负值")
    
    # 储能放电上限（MW），正值，表示最大放电功率
    discharge_limit: float = Field(default=50.0, description="储能放电上限（MW），正值")
    
    # 死区值（MW），调度目标与实际出力差值小于此值时不调节
    dead_zone: float = Field(default=1.2, description="死区值（MW）")
    
    # 当前SOC（%），储能系统剩余电量百分比
    soc: float = Field(default=50.0, ge=0, le=100, description="当前SOC（%）")
    
    # SOC下限（%），低于此值停止放电
    soc_min: float = Field(default=8.0, ge=0, le=100, description="SOC下限（%）")
    
    # SOC上限（%），高于此值停止充电
    soc_max: float = Field(default=100.0, ge=0, le=100, description="SOC上限（%）")
    
    # 调节步长（MW），每次调节的功率变化量
    step_size: float = Field(default=2.0, description="调节步长（MW）")

    # 实际值（用于比对）
    actual_storage_power: Optional[float] = Field(None, description="储能实际出力（MW）")
    actual_pv_power: Optional[float] = Field(None, description="光伏实际出力（MW）")


class ConditionFlags(BaseModel):
    """
    条件判断结果模型
    
    包含4个条件的判断结果，用于生成特征码
    """
    # 条件1：是否限电（实际出力 < 调度指令）
    is_curtailed: bool = Field(..., description="是否限电")
    
    # 条件2：是否在死区（差值小于死区值）
    in_dead_zone: bool = Field(..., description="是否在死区")
    
    # 条件3：充电速率等级（0-3）
    charge_rate_level: int = Field(..., ge=0, le=9, description="充电速率等级")
    
    # 条件4：是否在限值内
    in_limit: bool = Field(..., description="是否在限值内")


class RegulationResponse(BaseModel):
    """
    调节计算响应模型
    
    包含调节计算的完整结果
    """
    # 计算时间戳
    timestamp: datetime = Field(default_factory=datetime.now, description="计算时间")
    
    # 透传字段
    soc: float = Field(..., description="当前SOC")
    dispatch_target: float = Field(..., description="调度指令")
    
    # 当前总有功（MW）= 光伏出力 + 储能出力
    total_power: float = Field(..., description="当前总有功（MW）")
    
    # 调节结果描述
    adjustment_result: str = Field(..., description="调节结果描述")
    
    # 储能调节目标（MW），建议的储能出力值（已应用步长和约束）
    target_power: Optional[float] = Field(None, description="储能调节目标（MW）")
    
    # 理论理想目标（MW），未应用步长前的完全对齐调度指令的理论值
    ideal_target_power: Optional[float] = Field(None, description="理论理想目标（MW）")
    
    # 特征码，由4个条件值组成
    feature_code: str = Field(..., description="特征码")
    
    # 条件判断详情
    conditions: ConditionFlags = Field(..., description="条件判断详情")
    
    # 偏差值（MW）= 调度指令 - 当前总有功
    deviation: float = Field(..., description="偏差值（MW）")
    
    # 是否需要调节
    need_adjust: bool = Field(..., description="是否需要调节")

    # 实际值对比结果（用于展示）
    actual_comparison: Optional[dict] = Field(None, description="实际值与理论值对比")

    # 建议下次调节时间（秒）
    next_adjust_delay: Optional[int] = Field(None, description="建议下一次调节的时延（秒）")

    # 告警信息列表
    warnings: list[str] = Field(default_factory=list, description="告警信息")


class HistoryRecord(BaseModel):
    """
    历史记录模型
    
    用于存储和查询历史调节记录
    """
    id: Optional[int] = Field(None, description="记录ID")
    timestamp: datetime = Field(..., description="记录时间")
    
    # 输入参数
    storage_power: float = Field(..., description="储能当前出力（MW）")
    dispatch_target: float = Field(..., description="调度指令值（MW）")
    pv_power: float = Field(..., description="光伏出力（MW）")
    soc: float = Field(..., description="当前SOC（%）")
    
    # 计算结果
    total_power: float = Field(..., description="当前总有功（MW）")
    adjustment_result: str = Field(..., description="调节结果")
    target_power: Optional[float] = Field(None, description="储能调节目标（MW）")
    feature_code: str = Field(..., description="特征码")
    
    # 新增字段（比对用）
    actual_storage_power: Optional[float] = Field(None, description="储能实际出力（MW）")
    actual_pv_power: Optional[float] = Field(None, description="光伏实际出力（MW）")
    ideal_target_power: Optional[float] = Field(None, description="理论理想目标（MW）")


class ConfigModel(BaseModel):
    """
    配置参数模型
    
    系统配置参数，可通过API修改
    """
    # 死区值（MW）
    dead_zone: float = Field(default=1.2, description="死区值（MW）")
    
    # 储能充电上限（MW）
    charge_limit: float = Field(default=-50.0, description="储能充电上限（MW）")
    
    # 储能放电上限（MW）
    discharge_limit: float = Field(default=50.0, description="储能放电上限（MW）")
    
    # SOC下限（%）
    soc_min: float = Field(default=8.0, description="SOC下限（%）")
    
    # SOC上限（%）
    soc_max: float = Field(default=100.0, description="SOC上限（%）")
    
    # 调节步长（MW）
    step_size: float = Field(default=2.0, description="调节步长（MW）")
    
    # 调节时延（秒）
    adjust_interval: float = Field(default=300.0, description="调节时延（秒）")
    
    # AGC最小出力限制（MW），低于此值不进行储能充电
    agc_min_limit: float = Field(default=3.0, description="AGC最小出力限制（MW）")
