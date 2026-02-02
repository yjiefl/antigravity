"""
储能自动调节系统 - API路由

定义RESTful API接口
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from typing import List

from app.models.schemas import (
    RegulationRequest,
    RegulationResponse,
    HistoryRecord,
    ConfigModel
)
from app.services.regulation_engine import RegulationEngine
from app.database import db


# 创建API路由器
router = APIRouter(prefix="/api/v1", tags=["储能调节"])

# 创建调节引擎实例
engine = RegulationEngine()


@router.post("/calculate", response_model=RegulationResponse)
async def calculate_regulation(request: RegulationRequest):
    """
    计算储能调节结果
    
    根据输入的参数计算储能系统应如何调节出力
    
    - **storage_power**: 储能当前出力（MW），正值放电，负值充电
    - **dispatch_target**: 调度指令值（MW）
    - **pv_power**: 光伏出力（MW）
    - **charge_limit**: 储能充电上限（MW），负值
    - **discharge_limit**: 储能放电上限（MW），正值
    - **dead_zone**: 死区值（MW）
    - **soc**: 当前SOC（%）
    """
    try:
        # 执行调节计算
        result = engine.calculate(request)
        
        # 保存到历史记录
        history_record = HistoryRecord(
            timestamp=result.timestamp,
            storage_power=request.storage_power,
            dispatch_target=request.dispatch_target,
            pv_power=request.pv_power,
            soc=request.soc,
            total_power=result.total_power,
            adjustment_result=result.adjustment_result,
            target_power=result.target_power,
            feature_code=result.feature_code,
            actual_storage_power=request.actual_storage_power,
            actual_pv_power=request.actual_pv_power,
            ideal_target_power=result.ideal_target_power
        )
        db.save_history(history_record)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


@router.get("/history", response_model=List[HistoryRecord])
async def get_history(
    limit: int = Query(default=50, ge=1, le=200, description="返回记录数量"),
    offset: int = Query(default=0, ge=0, description="偏移量")
):
    """
    获取历史记录列表
    
    按时间倒序返回调节计算的历史记录
    """
    try:
        records = db.get_history(limit=limit, offset=offset)
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")


@router.delete("/history/{record_id}")
async def delete_history(record_id: int):
    """
    删除指定的历史记录
    """
    try:
        success = db.delete_history(record_id)
        if success:
            return {"message": "删除成功", "id": record_id}
        else:
            raise HTTPException(status_code=404, detail="记录不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.delete("/history")
async def clear_history():
    """
    清空所有历史记录
    """
    try:
        count = db.clear_history()
        return {"message": f"已清空 {count} 条记录"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空失败: {str(e)}")


@router.get("/config", response_model=ConfigModel)
async def get_config():
    """
    获取当前配置参数
    """
    try:
        config = db.get_config()
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.put("/config", response_model=ConfigModel)
async def update_config(config: ConfigModel):
    """
    更新配置参数
    
    - **dead_zone**: 死区值（MW）
    - **charge_limit**: 储能充电上限（MW）
    - **discharge_limit**: 储能放电上限（MW）
    - **soc_min**: SOC下限（%）
    - **soc_max**: SOC上限（%）
    - **step_size**: 调节步长（MW）
    - **adjust_interval**: 调节时延（秒）
    - **agc_min_limit**: AGC最小出力限制（MW）
    """
    try:
        # 更新引擎配置
        engine.config = config
        # 保存到数据库
        updated = db.update_config(config)
        return updated
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@router.get("/health")
async def health_check():
    """
    健康检查接口
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "储能自动调节系统"
    }
