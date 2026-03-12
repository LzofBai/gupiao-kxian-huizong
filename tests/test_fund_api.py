"""
基金API模块单元测试
测试FundValuationAPI的核心功能
"""

import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock
from api.FundValuationAPI import FundValuationAPI


class TestFundValuationAPI(unittest.TestCase):
    """FundValuationAPI单元测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时数据库文件
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # 初始化API（不实际调用外部API）
        self.api = FundValuationAPI(db_path=self.db_path)
    
    def tearDown(self):
        """测试后清理"""
        # FundDatabase使用上下文管理器管理连接，不需要显式关闭
        # 只需删除临时文件
        os.unlink(self.db_path)
    
    @patch('api.FundValuationAPI.requests.Session.get')
    @patch('api.FundValuationAPI.api_rate_limiter.wait_for_endpoint')
    def test_get_fund_basic_info(self, mock_rate_limit, mock_get):
        """测试获取基金基本信息（模拟网络请求）"""
        # 模拟速率限制器立即返回
        mock_rate_limit.return_value = None
        
        # 模拟天天基金网响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.text = 'jsonpgz({"fundcode":"025209","name":"永赢先锋半导体智选混合发起C","jzrq":"2026-02-07","dwjz":"1.6050","gsz":"1.6447","gszzl":"+2.47","gztime":"2026-02-09 14:58"});'
        mock_get.return_value = mock_response
        
        # 调用方法
        result = self.api.get_fund_basic_info('025209')
        
        # 验证结果
        self.assertIsNotNone(result, "get_fund_basic_info应返回有效结果")
        if result:
            self.assertEqual(result['基金代码'], '025209')
            self.assertEqual(result['基金名称'], '永赢先锋半导体智选混合发起C')
            self.assertIn('估值', result)
            self.assertIn('日涨跌幅', result)
        
        # 验证请求URL
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        url = args[0]
        self.assertIn('fundgz.1234567.com.cn', url)
        self.assertIn('025209', url)
        
        # 验证速率限制器被调用
        mock_rate_limit.assert_called_once_with('fund_position')
    
    @patch('api.FundValuationAPI.requests.Session.get')
    @patch('api.FundValuationAPI.api_rate_limiter.wait_for_endpoint')
    def test_get_fund_top_holdings(self, mock_rate_limit, mock_get):
        """测试获取基金持仓（模拟网络请求）"""
        # 模拟速率限制器立即返回
        mock_rate_limit.return_value = None
        
        # 模拟东方财富网响应（简化HTML，匹配实际正则表达式模式）
        mock_response = MagicMock()
        mock_response.text = '''
        <table>
            <tr><td>1</td><td><a>300750</a></td><td><a>宁德时代</a></td><td class='tor'>11.44%</td></tr>
            <tr><td>2</td><td><a>600519</a></td><td><a>贵州茅台</a></td><td class='tor'>10.25%</td></tr>
            <tr><td>3</td><td><a>000858</a></td><td><a>五粮液</a></td><td class='tor'>9.87%</td></tr>
            <tr><td>4</td><td><a>002415</a></td><td><a>海康威视</a></td><td class='tor'>8.75%</td></tr>
            <tr><td>5</td><td><a>000333</a></td><td><a>美的集团</a></td><td class='tor'>7.65%</td></tr>
            <tr><td>6</td><td><a>000001</a></td><td><a>平安银行</a></td><td class='tor'>6.55%</td></tr>
            <tr><td>7</td><td><a>000002</a></td><td><a>万科A</a></td><td class='tor'>5.45%</td></tr>
            <tr><td>8</td><td><a>000063</a></td><td><a>中兴通讯</a></td><td class='tor'>4.35%</td></tr>
            <tr><td>9</td><td><a>000066</a></td><td><a>长城电脑</a></td><td class='tor'>3.25%</td></tr>
            <tr><td>10</td><td><a>000069</a></td><td><a>华侨城A</a></td><td class='tor'>2.15%</td></tr>
        </table>
        '''
        mock_get.return_value = mock_response
        
        # 调用方法
        holdings = self.api._fetch_fund_holdings_online('025209')
        
        # 验证结果
        self.assertIsNotNone(holdings, "_fetch_fund_holdings_online应返回有效持仓列表")
        if holdings:
            self.assertEqual(len(holdings), 10, "应解析出10个持仓记录")
            
            # 验证第一个持仓
            first = holdings[0]
            self.assertEqual(first['股票代码'], '300750')
            self.assertEqual(first['股票名称'], '宁德时代')
            self.assertEqual(first['持仓比例'], 11.44)
        
        # 验证请求参数
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn('fundf10.eastmoney.com', args[0])
        self.assertIn('jjcc', kwargs.get('params', {}).get('type', ''))
        
        # 验证速率限制器被调用
        mock_rate_limit.assert_called_once_with('fund_position')
    
    def test_cache_mechanism(self):
        """测试缓存机制"""
        fund_code = '025209'
        
        # 模拟估值结果
        mock_valuation = {
            '基金代码': fund_code,
            '基金名称': '测试基金',
            '估算涨跌幅': 2.5,
            '重仓股数量': 10,
            '计算时间': '2026-02-09 15:00:00'
        }
        
        # 手动添加到缓存（正确的缓存结构：元组 (result, timestamp)）
        import time
        self.api._valuation_cache[fund_code] = (mock_valuation, time.time())
        
        # 模拟get_fund_basic_info和get_fund_top_holdings方法
        # 如果缓存生效，这些方法不会被调用
        with patch.object(self.api, 'get_fund_basic_info') as mock_basic, \
             patch.object(self.api, 'get_fund_top_holdings') as mock_holdings:
            
            # 调用估值计算（应使用缓存）
            result = self.api.calculate_fund_valuation(fund_code)
            
            # 验证使用了缓存，没有调用实际获取数据的方法
            mock_basic.assert_not_called()
            mock_holdings.assert_not_called()
            
            # 验证返回了缓存数据
            self.assertIsNotNone(result, "缓存应返回有效结果")
            if result:
                self.assertEqual(result['基金代码'], fund_code)
                self.assertEqual(result['估算涨跌幅'], 2.5)
    
    @patch('api.FundValuationAPI.requests.Session.get')
    def test_batch_stock_quotes_success(self, mock_get):
        """测试批量获取股票行情（成功情况）"""
        mock_response = MagicMock()
        mock_response.text = 'v_sh600519="1~贵州茅台~600519~1750.00~1708.00~1720.00~10000~5000~5000~1750.00~100~1749.00~200~1748.00~300~1747.00~400~1746.00~500~1751.00~600~1752.00~700~1753.00~800~1754.00~900~1755.00~1000~15:00:00/1750.00/1000/S/1750000/10000|14:59:55/1749.00/200/B/349800/9999~20260210~42.00~2.50~1760.00~1700.00~1750.00/10000/17500000~10000~5000~0.50~15.00~~1760.00~1700.00~3.50~20000.00~20000.00~5.00~1900.00~1500.00";v_sz000858="1~五粮液~000858~152.00~154.30~153.00~20000~10000~10000~152.00~500~151.99~600~151.98~700~151.97~800~151.96~900~152.01~1000~152.02~1100~152.03~1200~152.04~1300~152.05~1400~15:00:00/152.00/500/S/76000/20000|14:59:55/151.99/600/B/91194/19999~20260210~-2.30~-1.50~155.00~151.00~152.00/20000/3040000~20000~10000~1.00~25.00~~155.00~151.00~2.60~5000.00~5000.00~3.00~170.00~140.00";'
        mock_response.encoding = 'gbk'
        mock_get.return_value = mock_response
        
        # 调用方法
        stock_codes = ['600519', '000858']
        results = self.api.get_batch_stock_quotes(stock_codes)
        
        # 验证结果
        self.assertEqual(len(results), 2, "应返回2个股票行情")
        
        # 验证贵州茅台
        maotai = results['600519']
        self.assertEqual(maotai['股票名称'], '贵州茅台')
        self.assertEqual(maotai['最新价'], 1750.00)
        self.assertEqual(maotai['涨跌幅'], 2.50)
        
        # 验证五粮液
        wuliangye = results['000858']
        self.assertEqual(wuliangye['股票名称'], '五粮液')
        self.assertEqual(wuliangye['最新价'], 152.00)
        self.assertEqual(wuliangye['涨跌幅'], -1.50)
        
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn('qt.gtimg.cn', args[0])
        self.assertIn('sh600519', args[0])
        self.assertIn('sz000858', args[0])
    
    @patch('api.FundValuationAPI.requests.Session.get')
    def test_batch_stock_quotes_fallback(self, mock_get):
        """测试批量接口失败时的回退机制"""
        # 模拟批量接口失败
        mock_get.side_effect = Exception("API调用失败")
        
        # 模拟单线程获取
        with patch.object(self.api, '_get_stock_quote_sina') as mock_sina:
            mock_sina.side_effect = [
                {'股票代码': '600519', '股票名称': '贵州茅台', '最新价': 1750.0, '涨跌幅': 2.5},
                {'股票代码': '000858', '股票名称': '五粮液', '最新价': 152.0, '涨跌幅': -1.5}
            ]
            
            # 调用方法
            stock_codes = ['600519', '000858']
            results = self.api.get_batch_stock_quotes(stock_codes)
            
            # 验证回退到单线程
            self.assertEqual(mock_sina.call_count, 2, "应调用2次单线程获取")
            self.assertEqual(len(results), 2, "应返回2个股票行情")
    
    def test_is_weekend_detection(self):
        """测试周末检测逻辑"""
        # 这里无法直接测试，因为is_weekend是基于当前时间的
        # 但我们可以验证属性存在
        self.assertTrue(hasattr(self.api, 'is_weekend'))
        self.assertIsInstance(self.api.is_weekend, bool)
    
    def test_session_configuration(self):
        """测试Session配置"""
        self.assertTrue(hasattr(self.api, 'session'))
        
        # 验证请求头
        headers = self.api.session.headers
        self.assertIn('User-Agent', headers)
        self.assertIn('Referer', headers)
        
        # 验证重试策略
        adapters = self.api.session.adapters
        self.assertIn('http://', adapters)
        self.assertIn('https://', adapters)


if __name__ == '__main__':
    unittest.main()