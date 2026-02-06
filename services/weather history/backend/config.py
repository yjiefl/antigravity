"""
配置文件
包含应用程序的所有配置参数
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# 数据库配置
DATABASE_PATH = os.path.join(BASE_DIR, 'data', 'weather.db')

# Open-Meteo API配置
OPEN_METEO_BASE_URL = 'https://archive-api.open-meteo.com/v1/archive'
OPEN_METEO_FORECAST_URL = 'https://api.open-meteo.com/v1/forecast'

# 缓存配置
CACHE_EXPIRE_HOURS = 720  # 30天（历史数据不会改变）

# 日志配置
LOG_DIR = os.path.join(BASE_DIR, 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'debug.log')

# Flask配置
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5001
FLASK_DEBUG = True

# 时区配置
TIMEZONE = 'Asia/Shanghai'

# 广西主要城市配置
GUANGXI_CITIES = [
    # 核心默认城市
    {'id': 1, 'city_name': '贵港', 'longitude': 109.5986, 'latitude': 23.1115, 'region': '广西'},
    {'id': 2, 'city_name': '南宁', 'longitude': 108.3661, 'latitude': 22.8172, 'region': '广西'},
    {'id': 3, 'city_name': '宁明', 'longitude': 107.07, 'latitude': 22.14, 'region': '广西'},
    {'id': 4, 'city_name': '江州', 'longitude': 107.3645, 'latitude': 22.3769, 'region': '广西'},
    {'id': 5, 'city_name': '扶绥', 'longitude': 107.90, 'latitude': 22.63, 'region': '广西'},
    {'id': 6, 'city_name': '天等', 'longitude': 107.13, 'latitude': 23.08, 'region': '广西'},
    {'id': 7, 'city_name': '大新', 'longitude': 107.20, 'latitude': 22.83, 'region': '广西'},
    
    # 默认自定义场站
    {'id': 50, 'city_name': '峙书', 'longitude': 107.2879, 'latitude': 22.1235, 'region': '自定义场站'},
    {'id': 51, 'city_name': '守旗', 'longitude': 107.6518, 'latitude': 22.4539, 'region': '自定义场站'},
    {'id': 52, 'city_name': '弄滩', 'longitude': 107.2668, 'latitude': 22.2477, 'region': '自定义场站'},
    {'id': 53, 'city_name': '派岸', 'longitude': 107.2720, 'latitude': 22.3027, 'region': '自定义场站'},
    {'id': 54, 'city_name': '寨安', 'longitude': 107.0092, 'latitude': 22.0386, 'region': '自定义场站'},
    {'id': 55, 'city_name': '强胜', 'longitude': 107.5495, 'latitude': 22.3185, 'region': '自定义场站'},
    {'id': 56, 'city_name': '康宁', 'longitude': 107.2714, 'latitude': 22.0870, 'region': '自定义场站'},
    {'id': 57, 'city_name': '驮堪', 'longitude': 107.2574, 'latitude': 23.1326, 'region': '自定义场站'},
    {'id': 58, 'city_name': '浦峙', 'longitude': 107.3855, 'latitude': 22.1573, 'region': '自定义场站'},
    {'id': 59, 'city_name': '岑凡', 'longitude': 107.8472, 'latitude': 22.3392, 'region': '自定义场站'},
    {'id': 60, 'city_name': '樟木', 'longitude': 109.3785, 'latitude': 23.3790, 'region': '自定义场站'},
    {'id': 61, 'city_name': '榕木', 'longitude': 109.4940, 'latitude': 22.9408, 'region': '自定义场站'},
    {'id': 62, 'city_name': '那小', 'longitude': 107.4159, 'latitude': 22.1853, 'region': '自定义场站'},
]

# 可用的天气数据字段
AVAILABLE_FIELDS = {
    'basic': {
        'temperature_2m': {'name': '温度', 'unit': '°C', 'description': '2米高度气温'},
        'relative_humidity_2m': {'name': '相对湿度', 'unit': '%', 'description': '2米高度相对湿度'},
        'dew_point_2m': {'name': '露点温度', 'unit': '°C', 'description': '2米高度露点温度'},
        'precipitation': {'name': '降水量', 'unit': 'mm', 'description': '小时降水量'},
        'rain': {'name': '降雨量', 'unit': 'mm', 'description': '小时降雨量'},
        'snowfall': {'name': '降雪量', 'unit': 'cm', 'description': '小时降雪量'},
        'surface_pressure': {'name': '地面气压', 'unit': 'hPa', 'description': '地面气压'},
        'cloud_cover': {'name': '云量', 'unit': '%', 'description': '总云量'},
        'weather_code': {'name': '天气情况', 'unit': '代码', 'description': 'WMO天气代码'},
    },
    'wind': {
        'wind_speed_10m': {'name': '10米风速', 'unit': 'km/h', 'description': '10米高度风速'},
        'wind_direction_10m': {'name': '10米风向', 'unit': '°', 'description': '10米高度风向'},
        'wind_gusts_10m': {'name': '10米阵风', 'unit': 'km/h', 'description': '10米高度阵风'},
        'wind_speed_100m': {'name': '100米风速', 'unit': 'km/h', 'description': '100米高度风速'},
        'wind_direction_100m': {'name': '100米风向', 'unit': '°', 'description': '100米高度风向'},
    },
    'radiation': {
        'shortwave_radiation': {'name': '短波辐射', 'unit': 'W/m²', 'description': '短波太阳辐射'},
        'direct_radiation': {'name': '直接辐射', 'unit': 'W/m²', 'description': '直接太阳辐射'},
        'diffuse_radiation': {'name': '散射辐射', 'unit': 'W/m²', 'description': '散射太阳辐射'},
        'direct_normal_irradiance': {'name': '直接法向辐照度', 'unit': 'W/m²', 'description': 'DNI'},
    },
    'other': {
        'evapotranspiration': {
            'name': '蒸发蒸腾量', 
            'unit': 'mm', 
            'description': 'ET0参考蒸散发', 
            'api_param': 'et0_fao_evapotranspiration'
        },
        'soil_temperature_0_to_7cm': {'name': '土壤温度', 'unit': '°C', 'description': '0-7cm土壤温度'},
        'soil_moisture_0_to_7cm': {'name': '土壤湿度', 'unit': 'm³/m³', 'description': '0-7cm土壤湿度'},
    }
}

# 默认查询字段
DEFAULT_FIELDS = [
    'temperature_2m',
    'relative_humidity_2m',
    'precipitation',
    'wind_speed_10m',
    'wind_direction_10m',
    'shortwave_radiation',
    'weather_code',
]
