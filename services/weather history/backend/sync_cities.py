"""
同步城市配置脚本
根据 config.py 中的 GUANGXI_CITIES 列表更新数据库
将不再列表中的城市设为不可用，列表中的城市设为可用
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.database import DatabaseManager
from backend.models.city import CityManager
from backend.config import DATABASE_PATH, GUANGXI_CITIES

def sync_cities():
    print(f"正在同步城市配置至数据库: {DATABASE_PATH}")
    
    try:
        db_manager = DatabaseManager(DATABASE_PATH)
        city_manager = CityManager(db_manager)
        
        # 1. 先将所有现有城市设为禁用
        print("禁用所有现有城市...")
        db_manager.execute_update("UPDATE city_config SET is_active = 0")
        
        # 2. 同步 config.py 中的城市
        print(f"正在同步 {len(GUANGXI_CITIES)} 个默认城市/场站...")
        # 确保每个城市都有 is_active=1
        for city in GUANGXI_CITIES:
            city['is_active'] = 1
            
        city_manager.init_cities(GUANGXI_CITIES)
        
        # 3. 验证
        active_cities = city_manager.get_all_cities()
        print(f"同步完成！当前启用城市数量: {len(active_cities)}")
        for city in active_cities:
            print(f"  - {city['city_name']} ({city['region']})")
            
        return True
    except Exception as e:
        print(f"同步失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = sync_cities()
    sys.exit(0 if success else 1)
