"""
储能自动调节系统 - 核心调节逻辑引擎

实现储能AGC有功控制的核心计算逻辑
"""

from typing import Optional, Tuple
from datetime import datetime
from app.models.schemas import (
    RegulationRequest,
    RegulationResponse,
    ConditionFlags,
    ConfigModel
)


class RegulationEngine:
    """
    储能调节逻辑引擎
    
    根据输入参数计算储能系统应如何调节出力
    """
    
    # 特征码与调节策略的映射表
    # 格式: 特征码 -> (调节结果描述, 调节方向)
    # 调节方向: "increase"=增加出力(放电), "decrease"=减少出力(充电), "hold"=保持
    STRATEGY_MAP = {
        # 未限电 + 不在死区 + 充电中 + 在限值内：可以调节充电功率
        "0030": ("放开限电，减少储能充电", "decrease_charge"),
        "0020": ("减少储能充电", "decrease_charge"),
        "0010": ("适度减少储能充电", "decrease_charge"),
        "0000": ("储能状态正常，微调充电", "decrease_charge"),
        
        # 未限电 + 在死区：不需要调节
        "0100": ("在死区范围内，保持当前出力", "hold"),
        "0110": ("在死区范围内，保持当前出力", "hold"),
        "0120": ("在死区范围内，保持当前出力", "hold"),
        "0130": ("在死区范围内，保持当前出力", "hold"),
        
        # 限电场景：需要增加储能放电或减少充电
        "1000": ("发生限电，增加储能放电", "increase_discharge"),
        "1010": ("发生限电，增加储能放电", "increase_discharge"),
        "1020": ("发生限电，增加储能放电", "increase_discharge"),
        "1030": ("发生限电，增加储能放电", "increase_discharge"),
        
        # 限电 + 在死区
        "1100": ("限电但在死区，观察", "hold"),
        "1110": ("限电但在死区，观察", "hold"),
        "1120": ("限电但在死区，观察", "hold"),
        "1130": ("限电但在死区，观察", "hold"),
        
        # 超限场景
        "0001": ("储能超出限值，回调", "limit"),
        "0011": ("储能超出限值，回调充电功率", "limit"),
        "0021": ("储能超出限值，回调充电功率", "limit"),
        "0031": ("储能超出限值，回调充电功率", "limit"),
        
        # 限电 + 超限
        "1001": ("限电且超限，紧急调节", "emergency"),
        "1011": ("限电且超限，紧急调节", "emergency"),
        "1021": ("限电且超限，紧急调节", "emergency"),
        "1031": ("限电且超限，紧急调节", "emergency"),
    }
    
    def __init__(self, config: Optional[ConfigModel] = None):
        """
        初始化调节引擎
        
        Args:
            config: 配置参数，如果未提供则使用默认值
        """
        self.config = config or ConfigModel()
    
    def calculate(self, request: RegulationRequest) -> RegulationResponse:
        """
        执行调节计算
        
        Args:
            request: 调节计算请求参数
            
        Returns:
            RegulationResponse: 调节计算结果
        """
        # 计算当前总有功
        total_power = self._calculate_total_power(
            request.pv_power, 
            request.storage_power
        )
        
        # 计算偏差值
        deviation = request.dispatch_target - total_power
        
        # 判断4个条件
        conditions = self._evaluate_conditions(
            request=request,
            total_power=total_power,
            deviation=deviation
        )
        
        # 生成特征码
        feature_code = self._generate_feature_code(conditions)
        
        # 根据特征码确定调节策略
        adjustment_result, strategy = self._get_strategy(feature_code)
        
        # 判断是否需要调节
        need_adjust = not conditions.in_dead_zone
        
        # 计算理想调节目标（不计步长，但计充放电限制）
        # 储能理想目标 = 调度指令 - 光伏出力
        ideal_target_power = self._apply_constraints(
            target=request.dispatch_target - request.pv_power,
            request=request
        )

        # 计算实际调节目标（包含步长控制）
        target_power = self._calculate_target(
            request=request,
            deviation=deviation,
            strategy=strategy,
            conditions=conditions,
            ideal_target=ideal_target_power
        )

        # 实际值对比
        actual_comparison = self._compare_actual_values(request, target_power)
        
        # 生成告警信息
        warnings = self._generate_warnings(request, conditions)
        
        return RegulationResponse(
            timestamp=datetime.now(),
            total_power=total_power,
            adjustment_result=adjustment_result,
            target_power=target_power,
            ideal_target_power=ideal_target_power,
            feature_code=feature_code,
            conditions=conditions,
            deviation=deviation,
            need_adjust=need_adjust,
            actual_comparison=actual_comparison,
            soc=request.soc,
            dispatch_target=request.dispatch_target,
            next_adjust_delay=int(self.config.adjust_interval),
            warnings=warnings
        )
    
    def _calculate_total_power(self, pv_power: float, storage_power: float) -> float:
        """
        计算总有功
        
        Args:
            pv_power: 光伏出力（MW）
            storage_power: 储能出力（MW）
            
        Returns:
            float: 总有功（MW）
        """
        return pv_power + storage_power
    
    def _evaluate_conditions(
        self,
        request: RegulationRequest,
        total_power: float,
        deviation: float
    ) -> ConditionFlags:
        """
        评估4个条件
        
        Args:
            request: 请求参数
            total_power: 当前总有功
            deviation: 偏差值
            
        Returns:
            ConditionFlags: 条件判断结果
        """
        # 条件1：是否限电（实际出力 < 调度指令 且差值超过死区）
        is_curtailed = deviation > request.dead_zone
        
        # 条件2：是否在死区
        in_dead_zone = abs(deviation) <= request.dead_zone
        
        # 条件3：充电速率等级
        charge_rate_level = self._calculate_charge_rate_level(
            request.storage_power,
            request.charge_limit
        )
        
        # 条件4：是否超出限值
        in_limit = self._check_in_limit(
            request.storage_power,
            request.charge_limit,
            request.discharge_limit
        )
        
        return ConditionFlags(
            is_curtailed=is_curtailed,
            in_dead_zone=in_dead_zone,
            charge_rate_level=charge_rate_level,
            in_limit=not in_limit  # in_limit为True表示超限
        )
    
    def _calculate_charge_rate_level(
        self,
        storage_power: float,
        charge_limit: float
    ) -> int:
        """
        计算充电速率等级
        
        等级划分（当储能在充电时）：
        - 0: 未充电或放电中
        - 1: 充电功率 < 33% 充电上限
        - 2: 充电功率 33%-66% 充电上限
        - 3: 充电功率 > 66% 充电上限
        
        Args:
            storage_power: 储能当前出力（负值为充电）
            charge_limit: 充电上限（负值）
            
        Returns:
            int: 充电速率等级 (0-3)
        """
        if storage_power >= 0:
            # 放电或未充电
            return 0
        
        # 充电中，计算充电比例
        charge_ratio = storage_power / charge_limit if charge_limit != 0 else 0
        
        if charge_ratio < 0.33:
            return 1
        elif charge_ratio < 0.66:
            return 2
        else:
            return 3
    
    def _check_in_limit(
        self,
        storage_power: float,
        charge_limit: float,
        discharge_limit: float
    ) -> bool:
        """
        检查储能是否在限值内
        
        Args:
            storage_power: 储能当前出力
            charge_limit: 充电上限（负值）
            discharge_limit: 放电上限（正值）
            
        Returns:
            bool: True表示在限值内，False表示超限
        """
        return charge_limit <= storage_power <= discharge_limit
    
    def _generate_feature_code(self, conditions: ConditionFlags) -> str:
        """
        生成特征码
        
        Args:
            conditions: 条件判断结果
            
        Returns:
            str: 4位特征码
        """
        code = ""
        code += "1" if conditions.is_curtailed else "0"
        code += "1" if conditions.in_dead_zone else "0"
        code += str(conditions.charge_rate_level)
        code += "1" if conditions.in_limit else "0"
        return code
    
    def _get_strategy(self, feature_code: str) -> Tuple[str, str]:
        """
        根据特征码获取调节策略
        
        Args:
            feature_code: 特征码
            
        Returns:
            Tuple[str, str]: (调节结果描述, 策略类型)
        """
        if feature_code in self.STRATEGY_MAP:
            return self.STRATEGY_MAP[feature_code]
        
        # 默认策略
        return ("未知状态，请手动评估", "unknown")
    
    def _calculate_target(
        self,
        request: RegulationRequest,
        deviation: float,
        strategy: str,
        conditions: ConditionFlags,
        ideal_target: float
    ) -> Optional[float]:
        """
        计算储能调节目标
        
        Args:
            request: 请求参数
            deviation: 偏差值
            strategy: 策略类型
            conditions: 条件判断结果
            ideal_target: 理想目标值
            
        Returns:
            Optional[float]: 储能调节目标，如果不需要调节则返回None
        """
        if conditions.in_dead_zone:
            # 在死区内，不需要调节
            return None
        
        # 计算理想的储能出力 (这里改由外部传入)
        # ideal_target = request.dispatch_target - request.pv_power
        
        # 应用步长控制
        # 变化量 = 理想目标 - 当前储能出力
        change = ideal_target - request.storage_power
        # 限制变化量在步长范围内
        clamped_change = max(-request.step_size, min(request.step_size, change))
        
        target = request.storage_power + clamped_change
        
        # 应用约束
        target = self._apply_constraints(
            target=target,
            request=request
        )
        
        return target

    def _compare_actual_values(self, request: RegulationRequest, target_power: Optional[float]) -> Optional[dict]:
        """
        对比实际值与理论/目标值的差异
        """
        if request.actual_storage_power is None and request.actual_pv_power is None:
            return None
            
        comparison = {}
        
        if request.actual_storage_power is not None:
            # 实际出力 vs 调节前出力 的偏差
            comparison["storage_deviation"] = request.actual_storage_power - request.storage_power
            if target_power is not None:
                # 实际出力 vs 调节目标 的差距（反应AGC执行到位情况）
                comparison["target_gap"] = request.actual_storage_power - target_power
        
        if request.actual_pv_power is not None:
            # 实际光伏 vs 系统测得光伏 的偏差
            comparison["pv_deviation"] = request.actual_pv_power - request.pv_power
            
        return comparison
    
    def _apply_constraints(
        self,
        target: float,
        request: RegulationRequest
    ) -> float:
        """
        应用约束条件
        
        Args:
            target: 理想目标值
            request: 请求参数
            
        Returns:
            float: 约束后的目标值
        """
        # 约束1：充放电限值
        if target < request.charge_limit:
            target = request.charge_limit
        elif target > request.discharge_limit:
            target = request.discharge_limit
        
        # 约束2：SOC限制
        if request.soc <= request.soc_min and target > 0:
            # SOC过低，限制放电
            target = 0
        elif request.soc >= request.soc_max and target < 0:
            # SOC过高，限制充电
            target = 0
        
        return target
    
    def _generate_warnings(
        self,
        request: RegulationRequest,
        conditions: ConditionFlags
    ) -> list[str]:
        """
        生成告警信息
        
        Args:
            request: 请求参数
            conditions: 条件判断结果
            
        Returns:
            list[str]: 告警信息列表
        """
        warnings = []
        
        # SOC告警
        if request.soc < 10:
            warnings.append(f"⚠️ SOC过低（{request.soc}%），接近下限，请特别关注！")
        elif request.soc <= request.soc_min:
            warnings.append(f"🚨 SOC已达下限（{request.soc}%），必须停止放电！")
        
        if request.soc >= 99:
            warnings.append(f"ℹ️ SOC接近上限（{request.soc}%），应结束充电并汇报。")
        
        # AGC限制告警
        if request.dispatch_target < self.config.agc_min_limit:
            warnings.append(
                f"⚠️ AGC指令低于{self.config.agc_min_limit}MW，"
                "不应进行储能充电操作。"
            )
        
        # 限电告警
        if conditions.is_curtailed:
            warnings.append("ℹ️ 当前发生限电，建议减少储能充电或增加放电。")
        
        return warnings


# 创建默认引擎实例
default_engine = RegulationEngine()


def calculate_regulation(request: RegulationRequest) -> RegulationResponse:
    """
    便捷函数：使用默认引擎计算调节结果
    
    Args:
        request: 调节计算请求
        
    Returns:
        RegulationResponse: 调节计算结果
    """
    return default_engine.calculate(request)
