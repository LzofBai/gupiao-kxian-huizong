"""
数据库模块单元测试
"""

import unittest
import tempfile
import os
import sqlite3
from database.FundDatabase import FundDatabase


class TestFundDatabase(unittest.TestCase):
    """FundDatabase单元测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时数据库文件
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # 初始化数据库
        self.db = FundDatabase(self.db_path)
    
    def tearDown(self):
        """测试后清理"""
        # FundDatabase没有close方法，连接由上下文管理器管理
        # 只需删除临时文件
        os.unlink(self.db_path)
    
    def test_init_database(self):
        """测试数据库初始化"""
        # 检查表是否存在
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 检查funds表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='funds'")
        self.assertIsNotNone(cursor.fetchone(), "funds表应存在")
        
        # 检查fund_holdings表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fund_holdings'")
        self.assertIsNotNone(cursor.fetchone(), "fund_holdings表应存在")
        
        conn.close()
    
    def test_add_fund(self):
        """测试添加基金"""
        fund_code = '025209'
        fund_name = '永赢先锋半导体智选混合发起C'
        position = 10000.0
        
        # 添加基金
        success = self.db.add_fund(fund_code, fund_name, position)
        self.assertTrue(success, "添加基金应成功")
        
        # 验证基金已添加
        funds = self.db.get_fund_codes()
        self.assertIn(fund_code, funds, "基金代码应在基金列表中")
        
        # 获取基金详情 - 通过get_all_funds获取
        all_funds = self.db.get_all_funds()
        fund_info = None
        for fund in all_funds:
            if fund['fund_code'] == fund_code:
                fund_info = fund
                break
        
        self.assertIsNotNone(fund_info, "应找到基金详情")
        if fund_info:
            self.assertEqual(fund_info['fund_code'], fund_code, "基金代码应匹配")
            self.assertEqual(fund_info['fund_name'], fund_name, "基金名称应匹配")
            self.assertEqual(fund_info['user_position'], position, "持仓金额应匹配")
    
    def test_update_fund_position(self):
        """测试更新基金持仓金额"""
        fund_code = '025209'
        fund_name = '测试基金'
        initial_position = 10000.0
        new_position = 20000.0
        
        # 先添加基金
        self.db.add_fund(fund_code, fund_name, initial_position)
        
        # 更新持仓金额
        success = self.db.update_user_position(fund_code, new_position)
        self.assertTrue(success, "更新持仓金额应成功")
        
        # 验证更新 - 从get_all_funds中过滤
        all_funds = self.db.get_all_funds()
        fund_info = None
        for fund in all_funds:
            if fund['fund_code'] == fund_code:
                fund_info = fund
                break
                
        self.assertIsNotNone(fund_info, "应找到基金信息")
        if fund_info:
            self.assertEqual(fund_info['user_position'], new_position, "持仓金额应已更新")
    
    def test_add_holdings(self):
        """测试添加持仓信息"""
        fund_code = '025209'
        
        # 先添加基金
        self.db.add_fund(fund_code, '测试基金', 10000.0)
        
        # 添加持仓
        holdings = [
            {'股票代码': '600519', '股票名称': '贵州茅台', '持仓比例': 10.5},
            {'股票代码': '000858', '股票名称': '五粮液', '持仓比例': 8.2},
            {'股票代码': '000333', '股票名称': '美的集团', '持仓比例': 7.8}
        ]
        
        success = self.db.save_fund_holdings(fund_code, holdings)
        self.assertTrue(success, "添加持仓应成功")
        
        # 验证持仓已添加
        db_holdings = self.db.get_fund_holdings(fund_code)
        self.assertIsNotNone(db_holdings, "持仓信息不应为None")
        if db_holdings:
            self.assertEqual(len(db_holdings), 3, "应添加3个持仓记录")
            
            # 检查持仓数据
            for i, holding in enumerate(db_holdings):
                self.assertEqual(holding['股票代码'], holdings[i]['股票代码'])
                self.assertEqual(holding['股票名称'], holdings[i]['股票名称'])
                self.assertEqual(holding['持仓比例'], holdings[i]['持仓比例'])
    
    def test_get_funds_with_holdings(self):
        """测试批量获取基金及持仓信息（JOIN查询）"""
        # 添加测试数据
        self.db.add_fund('025209', '基金A', 10000.0)
        self.db.add_fund('001593', '基金B', 5000.0)
        
        # 添加持仓
        holdings_a = [
            {'股票代码': '600519', '股票名称': '股票A1', '持仓比例': 10.0},
            {'股票代码': '000858', '股票名称': '股票A2', '持仓比例': 8.0}
        ]
        holdings_b = [
            {'股票代码': '000333', '股票名称': '股票B1', '持仓比例': 12.0},
            {'股票代码': '300750', '股票名称': '股票B2', '持仓比例': 9.0}
        ]
        
        self.db.save_fund_holdings('025209', holdings_a)
        self.db.save_fund_holdings('001593', holdings_b)
        
        # 批量获取
        funds_with_holdings = self.db.get_funds_with_holdings()
        
        # 验证结果
        self.assertIn('025209', funds_with_holdings, "应包含基金A")
        self.assertIn('001593', funds_with_holdings, "应包含基金B")
        
        # 验证基金A的持仓
        fund_a = funds_with_holdings['025209']
        self.assertEqual(fund_a['fund_name'], '基金A')
        self.assertEqual(len(fund_a['holdings']), 2)
        
        # 验证基金B的持仓
        fund_b = funds_with_holdings['001593']
        self.assertEqual(fund_b['fund_name'], '基金B')
        self.assertEqual(len(fund_b['holdings']), 2)
    
    def test_remove_fund(self):
        """测试删除基金"""
        fund_code = '025209'
        
        # 先添加基金
        self.db.add_fund(fund_code, '测试基金', 10000.0)
        
        # 添加持仓（测试级联删除）
        holdings = [
            {'股票代码': '600519', '股票名称': '贵州茅台', '持仓比例': 10.5}
        ]
        self.db.save_fund_holdings(fund_code, holdings)
        
        # 删除基金
        success = self.db.remove_fund(fund_code)
        self.assertTrue(success, "删除基金应成功")
        
        # 验证基金已删除
        funds = self.db.get_fund_codes()
        self.assertNotIn(fund_code, funds, "基金代码不应在基金列表中")
        
        # 验证持仓也已删除
        db_holdings = self.db.get_fund_holdings(fund_code)
        # 删除基金后，get_fund_holdings可能返回None或空列表
        if db_holdings is not None:
            self.assertEqual(len(db_holdings), 0, "基金删除后持仓也应被删除")


if __name__ == '__main__':
    unittest.main()