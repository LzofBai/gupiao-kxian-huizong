# -*- coding: utf-8 -*-
"""
东方财富K线API工具类
功能：提供便捷的K线图获取、下载、URL生成等功能
作者：基于项目需求封装
日期：2026-02-08
"""

import requests
from typing import Literal, List, Dict, Optional
from datetime import datetime
import os


class KLineAPI:
    """
    东方财富K线API封装类
    提供K线图URL生成、图片下载、批量处理等功能
    """
    
    # API基础配置
    BASE_URL = "http://webquoteklinepic.eastmoney.com/GetPic.aspx"
    QUOTE_URL = "https://quote.eastmoney.com/zz"
    
    # 市场代码映射
    MARKET_CODE = {
        '上海': '1',
        '深圳': '0',
        '中证': '2',
        '东财板块': '90',
        '国际': '100',
        '期货': '102',
        '港股': '124'
    }
    
    # K线周期类型
    PERIOD_TYPE = {
        '日线': 'D',
        '周线': 'W',
        '月线': 'M',
        '分钟': 'm',
        '5分钟': 'm5',
        '15分钟': 'm15',
        '30分钟': 'm30',
        '60分钟': 'm60'
    }
    
    # 技术指标
    INDICATORS = [
        'MACD',  # 指数平滑异同移动平均线
        'KDJ',   # 随机指标
        'RSI',   # 相对强弱指标
        'BOLL',  # 布林线
        'MA',    # 移动平均线
        'VOL',   # 成交量
        'OBV',   # 能量潮
        'WR',    # 威廉指标
        'CCI',   # 顺势指标
        'DMI'    # 趋向指标
    ]
    
    def __init__(self):
        """初始化K线API工具"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def generate_url(self, 
                     stock_code: str,
                     period: Literal['D', 'W', 'M', 'm', 'm5', 'm15', 'm30', 'm60'] = 'D',
                     indicator: str = 'MACD',
                     unit_width: int = -5,
                     show_volume: bool = True,
                     image_type: str = 'KXL') -> str:
        """
        生成K线图URL
        
        Args:
            stock_code: 证券代码，格式如 '1.000300'(沪深300)
            period: K线周期，D=日线, W=周线, M=月线, m=分钟线
            indicator: 技术指标，如 MACD, KDJ, RSI等
            unit_width: 单位宽度，负数表示自适应，默认-5
            show_volume: 是否显示成交量，默认True
            image_type: 图片类型，默认KXL(K线图)
        
        Returns:
            str: 完整的K线图URL
        
        Example:
            >>> api = KLineAPI()
            >>> url = api.generate_url('1.000300', period='D', indicator='MACD')
        """
        timestamp = int(datetime.now().timestamp())
        
        params = {
            'nid': stock_code,
            'type': period,
            'unitWidth': unit_width,
            'ef': '',
            'formula': indicator,
            'AT': 1 if show_volume else 0,
            'imageType': image_type,
            'timespan': timestamp
        }
        
        # 构建URL
        param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.BASE_URL}?{param_str}"
    
    def download_kline(self,
                       stock_code: str,
                       save_path: str,
                       period: Literal['D', 'W', 'M', 'm', 'm5', 'm15', 'm30', 'm60'] = 'D',
                       indicator: str = 'MACD') -> bool:
        """
        下载K线图片到本地
        
        Args:
            stock_code: 证券代码
            save_path: 保存路径
            period: K线周期
            indicator: 技术指标
        
        Returns:
            bool: 下载是否成功
        
        Example:
            >>> api = KLineAPI()
            >>> api.download_kline('1.000300', './charts/hs300_day.png', period='D')
        """
        try:
            url = self.generate_url(stock_code, period, indicator)
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # 保存图片
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✓ 下载成功: {save_path}")
            return True
            
        except Exception as e:
            print(f"✗ 下载失败 [{stock_code}]: {e}")
            return False
    
    def batch_download(self,
                       stocks: Dict[str, str],
                       save_dir: str,
                       periods: List[str] = ['D', 'W', 'M'],
                       indicators: List[str] = ['MACD']) -> Dict[str, bool]:
        """
        批量下载多个股票的K线图
        
        Args:
            stocks: 股票字典，格式 {'代码': '名称'}
            save_dir: 保存目录
            periods: 周期列表
            indicators: 指标列表
        
        Returns:
            dict: 下载结果统计 {'成功': count, '失败': count}
        
        Example:
            >>> api = KLineAPI()
            >>> stocks = {'1.000300': '沪深300', '0.399006': '创业板指'}
            >>> api.batch_download(stocks, './charts', periods=['D', 'W'])
        """
        results = {'成功': 0, '失败': 0}
        total = len(stocks) * len(periods) * len(indicators)
        current = 0
        
        print(f"开始批量下载，共 {total} 张图片...")
        
        for code, name in stocks.items():
            for period in periods:
                for indicator in indicators:
                    current += 1
                    filename = f"{name}_{code.replace('.', '_')}_{period}_{indicator}.png"
                    save_path = os.path.join(save_dir, filename)
                    
                    print(f"[{current}/{total}] 下载: {name} - {period}线 - {indicator}", end=' ')
                    
                    if self.download_kline(code, save_path, period, indicator):
                        results['成功'] += 1
                    else:
                        results['失败'] += 1
        
        print(f"\n下载完成! 成功: {results['成功']}, 失败: {results['失败']}")
        return results
    
    def get_quote_url(self, stock_code: str) -> str:
        """
        获取股票行情页面URL
        
        Args:
            stock_code: 证券代码
        
        Returns:
            str: 行情页面URL
        """
        return f"{self.QUOTE_URL}/{stock_code}.html"
    
    def parse_stock_code(self, market: str, code: str) -> str:
        """
        根据市场和代码生成完整的股票代码
        
        Args:
            market: 市场名称，如 '上海', '深圳'
            code: 证券代码
        
        Returns:
            str: 完整代码，如 '1.000300'
        
        Example:
            >>> api = KLineAPI()
            >>> api.parse_stock_code('上海', '000300')
            '1.000300'
        """
        market_code = self.MARKET_CODE.get(market, '1')
        return f"{market_code}.{code}"
    
    def generate_html_img_tag(self,
                              stock_code: str,
                              stock_name: str,
                              period: str = 'D',
                              indicator: str = 'MACD',
                              alt_text: Optional[str] = None) -> str:
        """
        生成HTML图片标签
        
        Args:
            stock_code: 证券代码
            stock_name: 证券名称
            period: K线周期
            indicator: 技术指标
            alt_text: 图片描述文本
        
        Returns:
            str: HTML img标签
        """
        url = self.generate_url(stock_code, period, indicator)
        alt = alt_text or f"{stock_name}_{period}线_{indicator}"
        return f'<img src="{url}" alt="{alt}" />'
    
    @staticmethod
    def get_available_indicators() -> List[str]:
        """获取所有可用的技术指标列表"""
        return KLineAPI.INDICATORS.copy()
    
    @staticmethod
    def get_available_periods() -> Dict[str, str]:
        """获取所有可用的K线周期"""
        return KLineAPI.PERIOD_TYPE.copy()
    
    @staticmethod
    def get_market_codes() -> Dict[str, str]:
        """获取所有市场代码"""
        return KLineAPI.MARKET_CODE.copy()


# 便捷函数封装
def get_kline_url(stock_code: str, period: str = 'D', indicator: str = 'MACD') -> str:
    """
    快速生成K线图URL的便捷函数
    
    Args:
        stock_code: 证券代码，如 '1.000300'
        period: K线周期，D/W/M
        indicator: 技术指标，如MACD
    
    Returns:
        str: K线图URL
    """
    api = KLineAPI()
    return api.generate_url(stock_code, period, indicator)


def download_kline(stock_code: str, save_path: str, period: str = 'D', indicator: str = 'MACD') -> bool:
    """
    快速下载K线图的便捷函数
    
    Args:
        stock_code: 证券代码
        save_path: 保存路径
        period: K线周期
        indicator: 技术指标
    
    Returns:
        bool: 是否成功
    """
    api = KLineAPI()
    return api.download_kline(stock_code, save_path, period, indicator)


# 使用示例
if __name__ == '__main__':
    # 创建API实例
    api = KLineAPI()
    
    # 示例1: 生成单个K线图URL
    print("=" * 60)
    print("示例1: 生成K线图URL")
    print("=" * 60)
    url = api.generate_url('1.000300', period='D', indicator='MACD')
    print(f"沪深300日线MACD图URL:\n{url}\n")
    
    # 示例2: 下载单个K线图
    print("=" * 60)
    print("示例2: 下载单个K线图")
    print("=" * 60)
    api.download_kline('1.000300', './charts/hs300_day_macd.png', period='D', indicator='MACD')
    print()
    
    # 示例3: 批量下载多个股票的K线图
    print("=" * 60)
    print("示例3: 批量下载K线图")
    print("=" * 60)
    stocks = {
        '1.000300': '沪深300',
        '0.399006': '创业板指',
        '1.000016': '上证50'
    }
    api.batch_download(stocks, './charts', periods=['D', 'W'], indicators=['MACD'])
    print()
    
    # 示例4: 生成HTML图片标签
    print("=" * 60)
    print("示例4: 生成HTML图片标签")
    print("=" * 60)
    html_tag = api.generate_html_img_tag('1.000300', '沪深300', period='D', indicator='MACD')
    print(f"HTML标签:\n{html_tag}\n")
    
    # 示例5: 查看可用的指标和周期
    print("=" * 60)
    print("示例5: 可用的技术指标和周期")
    print("=" * 60)
    print("可用指标:", ', '.join(api.get_available_indicators()))
    print("可用周期:", api.get_available_periods())
    print("市场代码:", api.get_market_codes())
