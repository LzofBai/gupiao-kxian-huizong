"""
错误处理模块单元测试
测试统一的API错误响应格式
"""

import unittest
from flask import Flask, jsonify
from utils.errors import (
    APIError, ValidationError, NotFoundError, ExternalAPIError,
    RateLimitError, DatabaseError, success_response, error_response,
    handle_exception
)


class TestAPIErrors(unittest.TestCase):
    """API错误类测试"""
    
    def test_api_error_basic(self):
        """测试基础APIError"""
        error = APIError("测试错误", 400, "TEST_ERROR")
        
        self.assertEqual(error.message, "测试错误")
        self.assertEqual(error.status_code, 400)
        self.assertEqual(error.error_code, "TEST_ERROR")
        self.assertEqual(error.details, {})
        
        # 转换为字典
        error_dict = error.to_dict()
        self.assertEqual(error_dict['success'], False)
        self.assertEqual(error_dict['error']['message'], "测试错误")
        self.assertEqual(error_dict['error']['code'], "TEST_ERROR")
        self.assertEqual(error_dict['error']['status'], 400)
    
    def test_api_error_with_details(self):
        """测试带详情的APIError"""
        details = {'field': 'username', 'constraint': 'required'}
        error = APIError("验证失败", 400, "VALIDATION_ERROR", details)
        
        error_dict = error.to_dict()
        self.assertEqual(error_dict['error']['details'], details)
    
    def test_validation_error(self):
        """测试ValidationError"""
        details = {'field': 'email', 'reason': '格式无效'}
        error = ValidationError("邮箱格式错误", details)
        
        self.assertEqual(error.status_code, 400)
        self.assertEqual(error.error_code, "VALIDATION_ERROR")
        self.assertEqual(error.details, details)
    
    def test_not_found_error(self):
        """测试NotFoundError"""
        error = NotFoundError("基金", "025209")
        
        self.assertEqual(error.message, "基金 '025209' 未找到")
        self.assertEqual(error.status_code, 404)
        self.assertEqual(error.error_code, "NOT_FOUND_ERROR")
    
    def test_external_api_error(self):
        """测试ExternalAPIError"""
        details = {'url': 'https://api.example.com', 'status_code': 502}
        error = ExternalAPIError("东方财富", "服务不可用", details)
        
        self.assertIn("外部API '东方财富' 调用失败", error.message)
        self.assertEqual(error.status_code, 502)
        self.assertEqual(error.error_code, "EXTERNAL_API_ERROR")
        self.assertEqual(error.details, details)
    
    def test_rate_limit_error(self):
        """测试RateLimitError"""
        error = RateLimitError(10, "分钟", 60)
        
        self.assertEqual(error.message, "请求频率超过限制: 10 次/分钟")
        self.assertEqual(error.status_code, 429)
        self.assertEqual(error.error_code, "RATE_LIMIT_ERROR")
        self.assertEqual(error.details['limit'], 10)
        self.assertEqual(error.details['window'], "分钟")
        self.assertEqual(error.details['retry_after'], 60)
    
    def test_database_error(self):
        """测试DatabaseError"""
        details = {'sql': 'SELECT * FROM funds', 'params': []}
        error = DatabaseError("查询", "连接超时", details)
        
        self.assertIn("数据库操作 '查询' 失败", error.message)
        self.assertEqual(error.status_code, 500)
        self.assertEqual(error.error_code, "DATABASE_ERROR")
        self.assertEqual(error.details, details)


class TestResponseHelpers(unittest.TestCase):
    """响应辅助函数测试"""
    
    def test_success_response(self):
        """测试成功响应"""
        app = Flask(__name__)
        with app.app_context():
            data = {'fund_code': '025209', 'name': '测试基金'}
            response, status_code = success_response(data, "操作成功", 201)
            
            response_data = response.get_json()
            self.assertEqual(response_data['success'], True)
            self.assertEqual(response_data['message'], "操作成功")
            self.assertEqual(response_data['data'], data)
            self.assertEqual(status_code, 201)
    
    def test_success_response_defaults(self):
        """测试成功响应默认值"""
        app = Flask(__name__)
        with app.app_context():
            response, status_code = success_response()
            
            response_data = response.get_json()
            self.assertEqual(response_data['success'], True)
            self.assertEqual(response_data['message'], "操作成功")
            self.assertEqual(response_data['data'], {})
            self.assertEqual(status_code, 200)
    
    def test_error_response(self):
        """测试错误响应"""
        app = Flask(__name__)
        with app.app_context():
            error = ValidationError("验证失败")
            response, status_code = error_response(error)
            
            response_data = response.get_json()
            self.assertEqual(response_data['success'], False)
            self.assertEqual(response_data['error']['message'], "验证失败")
            self.assertEqual(status_code, 400)


class TestExceptionHandling(unittest.TestCase):
    """异常处理测试"""
    
    def test_handle_api_error(self):
        """测试处理APIError"""
        app = Flask(__name__)
        with app.app_context():
            error = ValidationError("验证失败")
            response, status_code = handle_exception(error)
            
            response_data = response.get_json()
            self.assertEqual(response_data['success'], False)
            self.assertEqual(status_code, 400)
    
    def test_handle_generic_exception(self):
        """测试处理通用异常"""
        app = Flask(__name__)
        with app.app_context():
            exception = ValueError("无效的值")
            response, status_code = handle_exception(exception)
            
            response_data = response.get_json()
            self.assertEqual(response_data['success'], False)
            self.assertIn("服务器内部错误", response_data['error']['message'])
            self.assertEqual(status_code, 500)
            self.assertEqual(response_data['error']['code'], 'INTERNAL_ERROR')


if __name__ == '__main__':
    unittest.main()