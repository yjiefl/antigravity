"""
储能自动调节系统 - 数据库操作层

使用SQLite存储历史记录和配置
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Optional
from pathlib import Path
from contextlib import contextmanager

from app.models.schemas import HistoryRecord, ConfigModel


# 数据库文件路径
DB_PATH = Path(__file__).parent.parent.parent / "data" / "storage_regulation.db"


@contextmanager
def get_connection():
    """
    获取数据库连接的上下文管理器
    
    自动处理连接的创建和关闭
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """
    初始化数据库，创建所需的表
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 创建历史记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                storage_power REAL NOT NULL,
                dispatch_target REAL NOT NULL,
                pv_power REAL NOT NULL,
                soc REAL NOT NULL,
                total_power REAL NOT NULL,
                adjustment_result TEXT NOT NULL,
                target_power REAL,
                feature_code TEXT NOT NULL,
                actual_storage_power REAL,
                actual_pv_power REAL,
                ideal_target_power REAL
            )
        """)
        
        # 创建配置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                dead_zone REAL DEFAULT 1.2,
                charge_limit REAL DEFAULT -50.0,
                discharge_limit REAL DEFAULT 50.0,
                soc_min REAL DEFAULT 8.0,
                soc_max REAL DEFAULT 100.0,
                step_size REAL DEFAULT 2.0,
                adjust_interval REAL DEFAULT 300.0,
                agc_min_limit REAL DEFAULT 3.0
            )
        """)
        
        # 插入默认配置（如果不存在）
        cursor.execute("""
            INSERT OR IGNORE INTO config (id) VALUES (1)
        """)
        
        conn.commit()


def save_history(record: HistoryRecord) -> int:
    """
    保存一条历史记录
    
    Args:
        record: 历史记录对象
        
    Returns:
        int: 新记录的ID
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO history (
                timestamp, storage_power, dispatch_target, pv_power,
                soc, total_power, adjustment_result, target_power, feature_code,
                actual_storage_power, actual_pv_power, ideal_target_power
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.timestamp.isoformat(),
            record.storage_power,
            record.dispatch_target,
            record.pv_power,
            record.soc,
            record.total_power,
            record.adjustment_result,
            record.target_power,
            record.feature_code,
            record.actual_storage_power,
            record.actual_pv_power,
            record.ideal_target_power
        ))
        conn.commit()
        return cursor.lastrowid


def get_history(limit: int = 50, offset: int = 0) -> List[HistoryRecord]:
    """
    获取历史记录列表
    
    Args:
        limit: 返回记录数量限制
        offset: 偏移量，用于分页
        
    Returns:
        List[HistoryRecord]: 历史记录列表
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM history
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        rows = cursor.fetchall()
        records = []
        for row in rows:
            records.append(HistoryRecord(
                id=row["id"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                storage_power=row["storage_power"],
                dispatch_target=row["dispatch_target"],
                pv_power=row["pv_power"],
                soc=row["soc"],
                total_power=row["total_power"],
                adjustment_result=row["adjustment_result"],
                target_power=row["target_power"],
                feature_code=row["feature_code"],
                actual_storage_power=row["actual_storage_power"],
                actual_pv_power=row["actual_pv_power"],
                ideal_target_power=row["ideal_target_power"]
            ))
        return records


def get_config() -> ConfigModel:
    """
    获取当前配置
    
    Returns:
        ConfigModel: 配置对象
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM config WHERE id = 1")
        row = cursor.fetchone()
        
        if row:
            return ConfigModel(
                dead_zone=row["dead_zone"],
                charge_limit=row["charge_limit"],
                discharge_limit=row["discharge_limit"],
                soc_min=row["soc_min"],
                soc_max=row["soc_max"],
                step_size=row["step_size"],
                adjust_interval=row["adjust_interval"],
                agc_min_limit=row["agc_min_limit"]
            )
        return ConfigModel()


def update_config(config: ConfigModel) -> ConfigModel:
    """
    更新配置
    
    Args:
        config: 新的配置对象
        
    Returns:
        ConfigModel: 更新后的配置
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE config SET
                dead_zone = ?,
                charge_limit = ?,
                discharge_limit = ?,
                soc_min = ?,
                soc_max = ?,
                step_size = ?,
                adjust_interval = ?,
                agc_min_limit = ?
            WHERE id = 1
        """, (
            config.dead_zone,
            config.charge_limit,
            config.discharge_limit,
            config.soc_min,
            config.soc_max,
            config.step_size,
            config.adjust_interval,
            config.agc_min_limit
        ))
        conn.commit()
    return config


def delete_history(record_id: int) -> bool:
    """
    删除一条历史记录
    
    Args:
        record_id: 记录ID
        
    Returns:
        bool: 是否删除成功
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM history WHERE id = ?", (record_id,))
        conn.commit()
        return cursor.rowcount > 0


def clear_history() -> int:
    """
    清空所有历史记录
    
    Returns:
        int: 删除的记录数
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM history")
        conn.commit()
        return cursor.rowcount
