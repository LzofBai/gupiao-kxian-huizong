# -*- coding: utf-8 -*-
"""
基金数据库管理模块
使用SQLite存储基金核心数据：基金列表、持仓信息、用户持仓金额
"""

import sqlite3
import json
from typing import Optional, List, Dict, Tuple
from datetime import datetime
from contextlib import contextmanager
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.Logger import Logger

# 初始化日志
log = Logger('logs/FundDatabase.log', level='info').logger


class FundDatabase:
    """基金数据库管理类"""
    
    def __init__(self, db_path: str = 'data/funds.db'):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        
        # 确保data目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 初始化数据库结构
        self._init_database()
        
        log.info(f"数据库初始化完成: {db_path}")
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 返回字典格式
        # 启用外键约束
        conn.execute('PRAGMA foreign_keys = ON')
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            log.error(f"数据库操作失败: {e}")
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """初始化数据库结构"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. 基金表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS funds (
                    fund_code TEXT PRIMARY KEY,
                    fund_name TEXT,
                    user_position REAL DEFAULT 0,
                    added_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 2. 持仓表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fund_holdings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fund_code TEXT NOT NULL,
                    stock_code TEXT NOT NULL,
                    stock_name TEXT,
                    position_ratio REAL NOT NULL,
                    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (fund_code) REFERENCES funds(fund_code) ON DELETE CASCADE,
                    UNIQUE(fund_code, stock_code)
                )
            ''')
            
            # 3. 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_holdings_fund 
                ON fund_holdings(fund_code)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_holdings_stock 
                ON fund_holdings(stock_code)
            ''')
            
            log.info("数据库表结构创建完成")
    
    # ==================== 基金管理 ====================
    
    def add_fund(self, fund_code: str, fund_name: str = '', user_position: float = 0) -> bool:
        """
        添加基金到监控列表
        
        Args:
            fund_code: 基金代码
            fund_name: 基金名称
            user_position: 用户持仓金额
            
        Returns:
            bool: 是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO funds (fund_code, fund_name, user_position)
                    VALUES (?, ?, ?)
                ''', (fund_code, fund_name, user_position))
                
                log.info(f"添加基金成功: {fund_code} - {fund_name}")
                return True
        except sqlite3.IntegrityError:
            log.warning(f"基金已存在: {fund_code}")
            return False
        except Exception as e:
            log.error(f"添加基金失败 [{fund_code}]: {e}")
            return False
    
    def remove_fund(self, fund_code: str) -> bool:
        """
        移除基金（级联删除持仓信息）
        
        Args:
            fund_code: 基金代码
            
        Returns:
            bool: 是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM funds WHERE fund_code = ?', (fund_code,))
                
                if cursor.rowcount > 0:
                    log.info(f"移除基金成功: {fund_code}")
                    return True
                else:
                    log.warning(f"基金不存在: {fund_code}")
                    return False
        except Exception as e:
            log.error(f"移除基金失败 [{fund_code}]: {e}")
            return False
    
    def get_all_funds(self) -> List[Dict]:
        """
        获取所有基金列表
        
        Returns:
            List[Dict]: 基金列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT fund_code, fund_name, user_position, added_time
                    FROM funds
                    ORDER BY added_time DESC
                ''')
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            log.error(f"获取基金列表失败: {e}")
            return []
    
    def get_fund_codes(self) -> List[str]:
        """
        获取所有基金代码
        
        Returns:
            List[str]: 基金代码列表
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT fund_code FROM funds ORDER BY added_time DESC')
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            log.error(f"获取基金代码列表失败: {e}")
            return []
    
    def fund_exists(self, fund_code: str) -> bool:
        """
        检查基金是否存在
        
        Args:
            fund_code: 基金代码
            
        Returns:
            bool: 是否存在
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1 FROM funds WHERE fund_code = ?', (fund_code,))
                return cursor.fetchone() is not None
        except Exception as e:
            log.error(f"检查基金存在性失败 [{fund_code}]: {e}")
            return False
    
    def update_user_position(self, fund_code: str, amount: float) -> bool:
        """
        更新用户持仓金额
        
        Args:
            fund_code: 基金代码
            amount: 持仓金额
            
        Returns:
            bool: 是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE funds 
                    SET user_position = ?, updated_time = CURRENT_TIMESTAMP
                    WHERE fund_code = ?
                ''', (amount, fund_code))
                
                if cursor.rowcount > 0:
                    log.info(f"更新持仓金额成功: {fund_code} = {amount}")
                    return True
                else:
                    log.warning(f"基金不存在: {fund_code}")
                    return False
        except Exception as e:
            log.error(f"更新持仓金额失败 [{fund_code}]: {e}")
            return False
    
    def get_user_positions(self) -> Dict[str, float]:
        """
        获取所有用户持仓金额
        
        Returns:
            Dict[str, float]: {基金代码: 持仓金额}
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT fund_code, user_position FROM funds')
                result = {}
                for row in cursor.fetchall():
                    fund_code = row[0]
                    position = row[1]
                    # 确保转换为浮点数，处理字符串或None的情况
                    if position is None or position == '':
                        position = 0.0
                    else:
                        try:
                            position = float(position)
                        except (ValueError, TypeError):
                            position = 0.0
                    result[fund_code] = position
                return result
        except Exception as e:
            log.error(f"获取用户持仓失败: {e}")
            return {}
    
    # ==================== 持仓管理 ====================
    
    def save_fund_holdings(self, fund_code: str, holdings: List[Dict]) -> bool:
        """
        保存基金持仓信息（覆盖模式）
        
        Args:
            fund_code: 基金代码
            holdings: 持仓列表 [{'股票代码', '股票名称', '持仓比例'}, ...]
            
        Returns:
            bool: 是否成功
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. 删除旧数据
                cursor.execute('DELETE FROM fund_holdings WHERE fund_code = ?', (fund_code,))
                
                # 2. 插入新数据
                for holding in holdings:
                    cursor.execute('''
                        INSERT INTO fund_holdings (fund_code, stock_code, stock_name, position_ratio)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        fund_code,
                        holding.get('股票代码', ''),
                        holding.get('股票名称', ''),
                        holding.get('持仓比例', 0)
                    ))
                
                log.info(f"保存持仓信息成功: {fund_code}, 共 {len(holdings)} 只股票")
                return True
        except Exception as e:
            log.error(f"保存持仓信息失败 [{fund_code}]: {e}")
            return False
    
    def get_fund_holdings(self, fund_code: str) -> Optional[List[Dict]]:
        """
        获取基金持仓信息
        
        Args:
            fund_code: 基金代码
            
        Returns:
            List[Dict]: 持仓列表，不存在返回None
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT stock_code, stock_name, position_ratio, update_time
                    FROM fund_holdings
                    WHERE fund_code = ?
                    ORDER BY position_ratio DESC
                ''', (fund_code,))
                
                rows = cursor.fetchall()
                if not rows:
                    return None
                
                return [{
                    '股票代码': row[0],
                    '股票名称': row[1],
                    '持仓比例': row[2]
                } for row in rows]
        except Exception as e:
            log.error(f"获取持仓信息失败 [{fund_code}]: {e}")
            return None
    
    def get_all_holdings(self) -> Dict[str, List[Dict]]:
        """
        获取所有基金的持仓信息
        
        Returns:
            Dict: {基金代码: 持仓列表}
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT fund_code, stock_code, stock_name, position_ratio
                    FROM fund_holdings
                    ORDER BY fund_code, position_ratio DESC
                ''')
                
                result = {}
                for row in cursor.fetchall():
                    fund_code = row[0]
                    if fund_code not in result:
                        result[fund_code] = []
                    
                    result[fund_code].append({
                        '股票代码': row[1],
                        '股票名称': row[2],
                        '持仓比例': row[3]
                    })
                
                return result
        except Exception as e:
            log.error(f"获取所有持仓信息失败: {e}")
            return {}
    
    def get_funds_with_holdings(self) -> dict[str, dict]:
        """
        批量获取所有基金及其持仓信息（JOIN查询优化版）
        
        Returns:
            dict: {
                基金代码: {
                    'fund_code': str,
                    'fund_name': str,
                    'user_position': float,
                    'added_time': str,
                    'updated_time': str,
                    'holdings': [
                        {'股票代码': str, '股票名称': str, '持仓比例': float},
                        ...
                    ]
                },
                ...
            }
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        f.fund_code,
                        f.fund_name,
                        f.user_position,
                        f.added_time,
                        f.updated_time,
                        h.stock_code,
                        h.stock_name,
                        h.position_ratio
                    FROM funds f
                    LEFT JOIN fund_holdings h ON f.fund_code = h.fund_code
                    ORDER BY f.fund_code, h.position_ratio DESC
                ''')
                
                result = {}
                for row in cursor.fetchall():
                    fund_code = row['fund_code']
                    
                    # 如果基金尚未添加到结果中，初始化基金信息
                    if fund_code not in result:
                        result[fund_code] = {
                            'fund_code': fund_code,
                            'fund_name': row['fund_name'],
                            'user_position': row['user_position'],
                            'added_time': row['added_time'],
                            'updated_time': row['updated_time'],
                            'holdings': []
                        }
                    
                    # 如果有持仓数据，添加到持仓列表
                    if row['stock_code']:  # LEFT JOIN可能返回NULL
                        result[fund_code]['holdings'].append({
                            '股票代码': row['stock_code'],
                            '股票名称': row['stock_name'],
                            '持仓比例': row['position_ratio']
                        })
                
                return result
        except Exception as e:
            log.error(f"批量获取基金及持仓信息失败: {e}")
            return {}
    
    # ==================== 统计查询 ====================
    
    def get_fund_count(self) -> int:
        """获取基金总数"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM funds')
                return cursor.fetchone()[0]
        except Exception as e:
            log.error(f"获取基金总数失败: {e}")
            return 0
    
    def get_total_position(self) -> float:
        """获取总持仓金额"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT SUM(user_position) FROM funds')
                result = cursor.fetchone()[0]
                return result if result else 0.0
        except Exception as e:
            log.error(f"获取总持仓金额失败: {e}")
            return 0.0
    
    # ==================== 数据迁移 ====================
    
    def import_from_json(self, json_data: Dict) -> Tuple[int, int]:
        """
        从JSON数据导入到数据库
        
        Args:
            json_data: JSON配置数据
            
        Returns:
            Tuple[int, int]: (成功导入的基金数, 成功导入的持仓记录数)
        """
        fund_count = 0
        holding_count = 0
        
        try:
            # 1. 导入基金列表
            fund_list = json_data.get('fund_list', [])
            user_positions = json_data.get('user_positions', {})
            
            for fund_code in fund_list:
                position = user_positions.get(fund_code, 0)
                if self.add_fund(fund_code, '', position):
                    fund_count += 1
            
            # 2. 导入持仓信息
            fund_holdings = json_data.get('fund_holdings', {})
            for fund_code, data in fund_holdings.items():
                holdings = data.get('holdings', [])
                if holdings and self.save_fund_holdings(fund_code, holdings):
                    holding_count += len(holdings)
            
            log.info(f"JSON导入完成: 基金 {fund_count} 个, 持仓记录 {holding_count} 条")
            return fund_count, holding_count
            
        except Exception as e:
            log.error(f"JSON导入失败: {e}")
            return fund_count, holding_count
    
    def export_to_json(self) -> Dict:
        """
        导出数据库数据为JSON格式（用于备份）
        
        Returns:
            Dict: JSON格式的数据
        """
        try:
            # 1. 导出基金列表
            fund_codes = self.get_fund_codes()
            
            # 2. 导出用户持仓
            user_positions = self.get_user_positions()
            
            # 3. 导出持仓信息
            all_holdings = self.get_all_holdings()
            fund_holdings = {}
            for fund_code, holdings in all_holdings.items():
                fund_holdings[fund_code] = {'holdings': holdings}
            
            return {
                'fund_list': fund_codes,
                'user_positions': user_positions,
                'fund_holdings': fund_holdings
            }
        except Exception as e:
            log.error(f"导出JSON失败: {e}")
            return {}
    
    def get_statistics(self) -> Dict:
        """
        获取数据库统计信息
        
        Returns:
            Dict: 统计信息
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 基金总数
                cursor.execute("SELECT COUNT(*) FROM funds")
                total_funds = cursor.fetchone()[0]
                
                # 持仓记录总数
                cursor.execute("SELECT COUNT(*) FROM fund_holdings")
                total_holdings = cursor.fetchone()[0]
                
                # 总持仓金额
                cursor.execute("SELECT SUM(user_position) FROM funds")
                result = cursor.fetchone()
                total_position = result[0] if result[0] else 0.0
                
                return {
                    'total_funds': total_funds,
                    'total_holdings': total_holdings,
                    'total_position': float(total_position)
                }
        except Exception as e:
            log.error(f"获取统计信息失败: {e}")
            return {
                'total_funds': 0,
                'total_holdings': 0,
                'total_position': 0.0
            }
    
    # ==================== 数据库维护 ====================
    
    def vacuum(self):
        """优化数据库（释放空间）"""
        try:
            with self._get_connection() as conn:
                conn.execute('VACUUM')
                log.info("数据库优化完成")
        except Exception as e:
            log.error(f"数据库优化失败: {e}")
    
    def backup(self, backup_path: str) -> bool:
        """
        备份数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            import shutil
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy2(self.db_path, backup_path)
            log.info(f"数据库备份成功: {backup_path}")
            return True
        except Exception as e:
            log.error(f"数据库备份失败: {e}")
            return False


if __name__ == '__main__':
    # 测试代码
    db = FundDatabase('data/funds_test.db')
    
    # 添加测试基金
    db.add_fund('025209', '永赢先锋半导体智选混合发起C', 10000)
    db.add_fund('015916', '天弘中证芯片产业指数C', 5000)
    
    # 保存持仓
    holdings = [
        {'股票代码': '600519', '股票名称': '贵州茅台', '持仓比例': 10.5},
        {'股票代码': '000858', '股票名称': '五粮液', '持仓比例': 8.3}
    ]
    db.save_fund_holdings('025209', holdings)
    
    # 查询测试
    print("基金列表:", db.get_all_funds())
    print("持仓信息:", db.get_fund_holdings('025209'))
    print("基金总数:", db.get_fund_count())
