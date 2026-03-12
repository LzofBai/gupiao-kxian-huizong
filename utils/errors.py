"""
统一错误处理模块
提供标准化的API错误响应和异常处理
"""

from typing import Optional, Any, Dict
from flask import jsonify


class APIError(Exception):
    """API错误异常基类"""
    
    def __init__(self, 
                 message: str, 
                 status_code: int = 500,
                 error_code: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        """
        初始化API错误
        
        Args:
            message: 错误消息
            status_code: HTTP状态码
            error_code: 错误代码（可选）
            details: 额外错误详情（可选）
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        error_dict = {
            'success': False,
            'error': {
                'message': self.message,
                'code': self.error_code or f'ERR_{self.status_code}',
                'status': self.status_code
            }
        }
        if self.details:
            error_dict['error']['details'] = self.details
        return error_dict
    
    def to_response(self):
        """转换为Flask JSON响应"""
        return jsonify(self.to_dict()), self.status_code


class ValidationError(APIError):
    """数据验证错误（400 Bad Request）"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 400, 'VALIDATION_ERROR', details)


class NotFoundError(APIError):
    """资源未找到错误（404 Not Found）"""
    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} '{resource_id}' 未找到"
        super().__init__(message, 404, 'NOT_FOUND_ERROR')


class ExternalAPIError(APIError):
    """外部API调用错误（502 Bad Gateway）"""
    def __init__(self, service: str, message: str, details: Optional[Dict[str, Any]] = None):
        error_message = f"外部API '{service}' 调用失败: {message}"
        super().__init__(error_message, 502, 'EXTERNAL_API_ERROR', details)


class RateLimitError(APIError):
    """请求频率限制错误（429 Too Many Requests）"""
    def __init__(self, limit: int, window: str, retry_after: Optional[int] = None):
        message = f"请求频率超过限制: {limit} 次/{window}"
        details = {'limit': limit, 'window': window}
        if retry_after:
            details['retry_after'] = retry_after
        super().__init__(message, 429, 'RATE_LIMIT_ERROR', details)


class DatabaseError(APIError):
    """数据库操作错误（500 Internal Server Error）"""
    def __init__(self, operation: str, message: str, details: Optional[Dict[str, Any]] = None):
        error_message = f"数据库操作 '{operation}' 失败: {message}"
        super().__init__(error_message, 500, 'DATABASE_ERROR', details)


def success_response(data: Any = None, 
                    message: str = "操作成功",
                    status_code: int = 200) -> tuple:
    """
    生成标准成功响应
    
    Args:
        data: 响应数据
        message: 成功消息
        status_code: HTTP状态码
    
    Returns:
        Flask JSON响应元组 (response, status_code)
    """
    response = {
        'success': True,
        'message': message,
        'data': data or {}
    }
    return jsonify(response), status_code


def error_response(error: APIError):
    """
    生成标准错误响应
    
    Args:
        error: APIError实例
    
    Returns:
        Flask JSON响应元组 (response, status_code)
    """
    return error.to_response()


def handle_exception(e: Exception):
    """
    统一异常处理
    
    Args:
        e: 异常实例
    
    Returns:
        Flask JSON响应元组 (response, status_code)
    """
    if isinstance(e, APIError):
        return e.to_response()
    
    # 处理未知异常
    error = APIError(
        message=f"服务器内部错误: {str(e)}",
        status_code=500,
        error_code='INTERNAL_ERROR'
    )
    return error.to_response()


def api_endpoint(func):
    """
    API端点装饰器，统一处理异常和响应格式
    
    Usage:
        @app.route('/api/endpoint')
        @api_endpoint
        def endpoint():
            # 返回数据或引发APIError
            return {'key': 'value'}
    """
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            
            # 如果函数返回的是APIError，转换为错误响应
            if isinstance(result, APIError):
                return result.to_response()
            
            # 如果函数返回的是元组(数据, 状态码)
            if isinstance(result, tuple) and len(result) == 2:
                data, status_code = result
                if isinstance(data, dict):
                    return success_response(data, status_code=status_code)
            
            # 默认返回成功响应
            if isinstance(result, dict):
                return success_response(result)
            
            # 其他情况返回原结果
            return result
            
        except Exception as e:
            return handle_exception(e)
    
    return wrapper