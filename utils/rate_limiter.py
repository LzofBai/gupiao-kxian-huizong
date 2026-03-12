"""
API速率限制器
提供基于令牌桶算法的速率限制，防止API调用频率过高
"""

import time
import threading
from typing import Optional, Callable, Any
from datetime import datetime, timedelta
from collections import defaultdict


class RateLimiter:
    """基于令牌桶算法的速率限制器"""
    
    def __init__(self, 
                 calls_per_second: float = 1.0,
                 burst_size: Optional[int] = None):
        """
        初始化速率限制器
        
        Args:
            calls_per_second: 每秒允许的调用次数
            burst_size: 突发请求最大数量，默认为calls_per_second的2倍
        """
        self.calls_per_second = calls_per_second
        self.burst_size = burst_size or int(calls_per_second * 2)
        self.tokens = self.burst_size
        self.last_update = time.time()
        self.lock = threading.Lock()
    
    def _add_tokens(self):
        """根据时间流逝添加令牌"""
        now = time.time()
        elapsed = now - self.last_update
        
        # 每秒生成calls_per_second个令牌
        new_tokens = elapsed * self.calls_per_second
        self.tokens = min(self.burst_size, self.tokens + new_tokens)
        self.last_update = now
    
    def acquire(self, tokens: int = 1) -> float:
        """
        获取指定数量的令牌，如果不够则等待
        
        Args:
            tokens: 需要的令牌数量（默认1）
            
        Returns:
            float: 实际等待的时间（秒）
        """
        with self.lock:
            self._add_tokens()
            
            # 计算需要等待的时间
            if self.tokens >= tokens:
                self.tokens -= tokens
                return 0.0
            
            # 需要等待新令牌生成
            deficit = tokens - self.tokens
            wait_time = deficit / self.calls_per_second
            self.tokens = 0
            self.last_update += wait_time  # 提前更新时间，避免重复计算
            
            return wait_time
    
    def wait_if_needed(self, tokens: int = 1):
        """如果需要则等待，直到有足够的令牌"""
        wait_time = self.acquire(tokens)
        if wait_time > 0:
            time.sleep(wait_time)


class APIRateLimiter:
    """API专用的速率限制管理器，支持多端点不同限制"""
    
    def __init__(self):
        self.limiters = {}
        self.default_limits = {
            'eastmoney_batch': {'calls_per_second': 0.5, 'burst_size': 2},
            'eastmoney_single': {'calls_per_second': 2.0, 'burst_size': 5},
            'sina': {'calls_per_second': 5.0, 'burst_size': 10},
            'fund_position': {'calls_per_second': 1.0, 'burst_size': 3},
            'tencent': {'calls_per_second': 10.0, 'burst_size': 20},
        }
        self.lock = threading.Lock()
    
    def get_limiter(self, endpoint: str) -> RateLimiter:
        """获取指定端点的速率限制器"""
        with self.lock:
            if endpoint not in self.limiters:
                # 使用默认配置或创建新的限制器
                if endpoint in self.default_limits:
                    config = self.default_limits[endpoint]
                    self.limiters[endpoint] = RateLimiter(
                        calls_per_second=config['calls_per_second'],
                        burst_size=config['burst_size']
                    )
                else:
                    # 默认限制：1次/秒
                    self.limiters[endpoint] = RateLimiter(calls_per_second=1.0)
            
            return self.limiters[endpoint]
    
    def wait_for_endpoint(self, endpoint: str, tokens: int = 1):
        """等待指定端点有可用的调用配额"""
        limiter = self.get_limiter(endpoint)
        limiter.wait_if_needed(tokens)
    
    def decorate(self, endpoint: str, tokens: int = 1):
        """
        装饰器：为函数添加速率限制
        
        Args:
            endpoint: 端点名称
            tokens: 每次调用消耗的令牌数量
            
        Returns:
            装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs) -> Any:
                self.wait_for_endpoint(endpoint, tokens)
                return func(*args, **kwargs)
            return wrapper
        return decorator


# 全局速率限制器实例
api_rate_limiter = APIRateLimiter()


class RateLimitMiddleware:
    """速率限制中间件，用于包装requests.Session"""
    
    def __init__(self, session, endpoint: str, tokens_per_call: int = 1):
        """
        初始化中间件
        
        Args:
            session: requests.Session实例
            endpoint: 端点名称
            tokens_per_call: 每次调用消耗的令牌数量
        """
        self.session = session
        self.endpoint = endpoint
        self.tokens_per_call = tokens_per_call
    
    def request(self, method, url, **kwargs):
        """重写请求方法，添加速率限制"""
        api_rate_limiter.wait_for_endpoint(self.endpoint, self.tokens_per_call)
        return self.session.request(method, url, **kwargs)
    
    def get(self, url, **kwargs):
        """GET请求"""
        return self.request('GET', url, **kwargs)
    
    def post(self, url, **kwargs):
        """POST请求"""
        return self.request('POST', url, **kwargs)


def create_rate_limited_session(endpoint: str, tokens_per_call: int = 1):
    """
    创建带有速率限制的requests.Session
    
    Args:
        endpoint: 端点名称
        tokens_per_call: 每次调用消耗的令牌数量
        
    Returns:
        RateLimitMiddleware实例，可以像普通Session一样使用
    """
    import requests
    session = requests.Session()
    return RateLimitMiddleware(session, endpoint, tokens_per_call)