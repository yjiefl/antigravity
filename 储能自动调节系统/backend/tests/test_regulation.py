"""
储能自动调节系统 - 单元测试

测试核心调节逻辑
"""

import pytest
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.schemas import RegulationRequest, ConfigModel
from app.services.regulation_engine import RegulationEngine


class TestRegulationEngine:
    """调节引擎测试类"""
    
    def setup_method(self):
        """每个测试方法前初始化引擎"""
        self.engine = RegulationEngine()
    
    def test_basic_calculation(self):
        """测试基本调节计算"""
        # 使用Excel中的示例数据
        request = RegulationRequest(
            storage_power=-12.0,  # 充电12MW
            dispatch_target=63.0,
            pv_power=73.0,
            charge_limit=-30.0,
            dead_zone=1.2,
            soc=50.0
        )
        
        result = self.engine.calculate(request)
        
        # 验证总有功计算
        assert result.total_power == 61.0  # 73 + (-12) = 61
        
        # 验证偏差值
        assert result.deviation == 2.0  # 63 - 61 = 2
        
        # 验证需要调节（偏差>死区）
        assert result.need_adjust is True
        
    def test_dead_zone(self):
        """测试死区判断"""
        # 偏差小于死区，不应调节
        request = RegulationRequest(
            storage_power=-10.0,
            dispatch_target=64.0,
            pv_power=73.0,
            charge_limit=-50.0,
            dead_zone=1.2,
            soc=50.0
        )
        
        result = self.engine.calculate(request)
        
        # 总有功 = 73 + (-10) = 63
        # 偏差 = 64 - 63 = 1，小于死区1.2
        assert result.total_power == 63.0
        assert result.deviation == 1.0
        assert result.conditions.in_dead_zone is True
        assert result.need_adjust is False
        assert result.target_power is None
    
    def test_curtailment_detection(self):
        """测试限电检测"""
        # 实际出力远小于调度指令
        request = RegulationRequest(
            storage_power=0.0,
            dispatch_target=100.0,
            pv_power=50.0,
            charge_limit=-50.0,
            dead_zone=1.2,
            soc=50.0
        )
        
        result = self.engine.calculate(request)
        
        # 总有功 = 50，调度指令 = 100
        # 偏差 = 50，远大于死区
        assert result.conditions.is_curtailed is True
        assert "限电" in result.adjustment_result or "放电" in result.adjustment_result
    
    def test_charge_limit_constraint(self):
        """测试充电上限约束"""
        request = RegulationRequest(
            storage_power=-30.0,
            dispatch_target=20.0,
            pv_power=100.0,
            charge_limit=-50.0,
            dead_zone=1.2,
            soc=50.0
        )
        
        result = self.engine.calculate(request)
        
        # 理想目标 = 20 - 100 = -80，但受充电上限-50约束
        if result.target_power is not None:
            assert result.target_power >= -50.0
    
    def test_discharge_limit_constraint(self):
        """测试放电上限约束"""
        request = RegulationRequest(
            storage_power=30.0,
            dispatch_target=200.0,
            pv_power=50.0,
            charge_limit=-50.0,
            discharge_limit=50.0,
            dead_zone=1.2,
            soc=50.0
        )
        
        result = self.engine.calculate(request)
        
        # 理想目标 = 200 - 50 = 150，但受放电上限50约束
        if result.target_power is not None:
            assert result.target_power <= 50.0
    
    def test_soc_low_warning(self):
        """测试SOC过低告警"""
        request = RegulationRequest(
            storage_power=10.0,
            dispatch_target=80.0,
            pv_power=70.0,
            soc=9.0  # SOC低于10%
        )
        
        result = self.engine.calculate(request)
        
        # 应该有SOC过低的告警
        assert len(result.warnings) > 0
        assert any("SOC" in w for w in result.warnings)
    
    def test_soc_min_stop_discharge(self):
        """测试SOC达到下限时停止放电"""
        request = RegulationRequest(
            storage_power=10.0,
            dispatch_target=100.0,
            pv_power=50.0,
            soc=8.0,  # SOC等于下限
            soc_min=8.0
        )
        
        result = self.engine.calculate(request)
        
        # 在SOC等于下限时，放电目标应为0
        if result.target_power is not None:
            assert result.target_power <= 0
    
    def test_feature_code_generation(self):
        """测试特征码生成"""
        request = RegulationRequest(
            storage_power=-12.0,
            dispatch_target=63.0,
            pv_power=73.0,
            charge_limit=-30.0,
            dead_zone=1.2,
            soc=50.0
        )
        
        result = self.engine.calculate(request)
        
        # 验证特征码格式：4位字符串
        assert len(result.feature_code) == 4
        assert result.feature_code.isdigit() or all(c in "0123456789" for c in result.feature_code)
    
    def test_charge_rate_level(self):
        """测试充电速率等级计算"""
        # 测试不同充电功率对应的等级
        
        # 未充电（放电状态）
        request1 = RegulationRequest(
            storage_power=10.0,
            dispatch_target=80.0,
            pv_power=70.0,
            charge_limit=-50.0
        )
        result1 = self.engine.calculate(request1)
        assert result1.conditions.charge_rate_level == 0
        
        # 低速充电（<33%）
        request2 = RegulationRequest(
            storage_power=-10.0,  # 充电10MW，占上限50的20%
            dispatch_target=60.0,
            pv_power=70.0,
            charge_limit=-50.0
        )
        result2 = self.engine.calculate(request2)
        assert result2.conditions.charge_rate_level == 1
        
        # 高速充电（>66%）
        request3 = RegulationRequest(
            storage_power=-40.0,  # 充电40MW，占上限50的80%
            dispatch_target=30.0,
            pv_power=70.0,
            charge_limit=-50.0
        )
        result3 = self.engine.calculate(request3)
        assert result3.conditions.charge_rate_level == 3
    
    def test_agc_min_limit_warning(self):
        """测试AGC最小出力限制告警"""
        engine = RegulationEngine(ConfigModel(agc_min_limit=3.0))
        
        request = RegulationRequest(
            storage_power=-10.0,
            dispatch_target=2.0,  # AGC指令低于3MW
            pv_power=12.0,
            soc=50.0
        )
        
        result = engine.calculate(request)
        
        # 应该有AGC限制告警
        assert any("AGC" in w or "3MW" in w for w in result.warnings)


class TestTotalPowerCalculation:
    """总有功计算测试"""
    
    def test_charging_scenario(self):
        """测试充电场景的总有功"""
        engine = RegulationEngine()
        request = RegulationRequest(
            storage_power=-20.0,  # 充电20MW
            dispatch_target=50.0,
            pv_power=70.0
        )
        result = engine.calculate(request)
        
        # 总有功 = 70 + (-20) = 50
        assert result.total_power == 50.0
    
    def test_discharging_scenario(self):
        """测试放电场景的总有功"""
        engine = RegulationEngine()
        request = RegulationRequest(
            storage_power=20.0,  # 放电20MW
            dispatch_target=90.0,
            pv_power=70.0
        )
        result = engine.calculate(request)
        
        # 总有功 = 70 + 20 = 90
        assert result.total_power == 90.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
