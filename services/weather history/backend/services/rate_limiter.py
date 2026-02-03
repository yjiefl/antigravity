import time
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    简单的 API 请求频率限制器
    """
    def __init__(self, db_manager):
        self.db = db_manager
        self.visits: Dict[str, list] = {} # {ip: [timestamp1, timestamp2, ...]}
        self.default_limit = 60 # 每分钟默认 60 次
        self.limit_period = 60 # 60 秒
        
    def get_limit_config(self) -> int:
        """从数据库获取频率限制设置"""
        try:
            sql = "SELECT value FROM system_settings WHERE key = 'api_rate_limit'"
            res = self.db.execute_query(sql)
            if res:
                return int(res[0]['value'])
        except Exception:
            pass
        return self.default_limit

    def is_allowed(self, ip: str) -> Tuple[bool, int]:
        """
        检查指定 IP 是否允许访问
        Returns: (is_allowed, remaining_requests)
        """
        limit = self.get_limit_config()
        now = time.time()
        
        if ip not in self.visits:
            self.visits[ip] = [now]
            return True, limit - 1
            
        # 移除过期的 visit
        self.visits[ip] = [t for t in self.visits[ip] if now - t < self.limit_period]
        
        if len(self.visits[ip]) >= limit:
            logger.warning(f"IP {ip} 触发频率限制: {limit} requests/min")
            # 记录到事件日志
            self.db.log_event("WARNING", "RATE_LIMITER", f"IP {ip} 触发频率限制", f"限制值: {limit}/min")
            return False, 0
            
        self.visits[ip].append(now)
        return True, limit - len(self.visits[ip])
