# -*- coding: utf-8 -*-
"""
基金实时估值工具
功能：通过基金前十大重仓股的实时涨跌估算基金净值变化
数据来源：天天基金网、东方财富网
作者：基于项目需求开发
日期：2026-02-08
"""

import requests
import json
import re
from typing import Optional, Dict, List
from datetime import datetime
from os.path import splitext, exists
import sys
import os
import random
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.Logger import Logger
from database.FundDatabase import FundDatabase
from utils.rate_limiter import api_rate_limiter

# 初始化日志
log = Logger(f'logs/{os.path.basename(splitext(__file__)[0])}.log', level='info').logger


class FundValuationAPI:
    """
    基金估值API类
    通过爬取基金持仓数据和股票实时行情，计算基金估值
    支持持仓信息本地缓存，优先使用配置文件中的持仓数据
    """
    
    # 天天基金网API
    FUND_INFO_URL = "http://fundgz.1234567.com.cn/js/{fund_code}.js"  # 基金基本信息
    FUND_POSITION_URL = "http://fundf10.eastmoney.com/FundArchivesDatas.aspx"  # 基金持仓
    
    # 东方财富股票行情API
    STOCK_QUOTE_URL = "http://push2.eastmoney.com/api/qt/stock/get"
    BATCH_STOCK_QUOTE_URL = "http://push2.eastmoney.com/api/qt/ulist.np/get"
    
    # 新浪股票行情API（备用，周末可用）
    SINA_STOCK_URL = "http://hq.sinajs.cn/list="
    # 腾讯股票行情API（备用，支持批量）
    TENCENT_STOCK_URL = "http://qt.gtimg.cn/q="
    
    # 并发配置
    MAX_WORKERS_WEEKEND = 5
    MAX_WORKERS_WEEKDAY = 3
    # 请求延迟配置（秒）
    DELAY_WEEKEND_MIN = 0.1
    DELAY_WEEKEND_MAX = 0.3
    DELAY_WEEKDAY_MIN = 0.3
    DELAY_WEEKDAY_MAX = 0.8
    
    # 超时配置（秒）
    STOCK_QUOTE_TIMEOUT = 30  # 获取股票行情总超时时间
    
    def __init__(self, config_file: Optional[str] = None, db_path: str = 'data/funds.db'):
        """初始化
        
        Args:
            config_file: 配置文件路径（保留兼容，不再使用）
            db_path: 数据库文件路径
        """
        # 配置连接池，限制并发连接数
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'http://fundf10.eastmoney.com/',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Connection': 'keep-alive'
        })
        
        # 配置重试策略和连接池
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=3, pool_maxsize=5)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # 初始化数据库（新）
        self.db = FundDatabase(db_path)
        
        # 保留config_file兼容旧代码，但不再使用
        self.config_file = config_file
        self.config_data = {}  # 兼容性属性
        self._valuation_cache = {}  # 估值缓存，5分钟TTL
        
        # 检测是否为周末，如果是则优先使用新浪API
        from datetime import datetime
        self.is_weekend = datetime.now().weekday() >= 5  # 5=周六, 6=周日
        if self.is_weekend:
            log.info("检测到周末，优先使用新浪API获取股票行情")
    
    def _load_config(self) -> Dict:
        """
        加载配置文件（兼容性保留，不再使用）
        
        Returns:
            dict: 配置数据
        """
        try:
            if self.config_file is not None and exists(self.config_file):
                # 类型守卫：此时self.config_file不是None
                config_file = self.config_file
                with open(config_file, 'r', encoding='utf-8') as f:
                    import json
                    return json.load(f)
            return {}
        except Exception as e:
            log.error(f"加载配置文件失败: {e}")
            return {}
    
    def _save_config(self):
        """
        保存配置到文件
        """
        if not self.config_file:
            return
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
            log.info(f"配置已保存到: {self.config_file}")
        except Exception as e:
            log.error(f"保存配置文件失败: {e}")
    
    def get_fund_basic_info(self, fund_code: str) -> Optional[Dict]:
        """
        获取基金基本信息（当前净值、估值等）
        
        Args:
            fund_code: 基金代码，如 '001593'
        
        Returns:
            dict: 基金信息字典
        """
        try:
            url = self.FUND_INFO_URL.format(fund_code=fund_code)
            api_rate_limiter.wait_for_endpoint('fund_position')
            response = self.session.get(url, timeout=10)
            
            # 检查响应状态码
            if response.status_code != 200:
                log.error(f"获取基金信息失败 [{fund_code}]: HTTP {response.status_code}")
                return None
            
            # 检查响应类型
            content_type = response.headers.get('content-type', '')
            if 'text/html' in content_type:
                log.error(f"获取基金信息失败 [{fund_code}]: 服务器返回HTML而非JSON")
                return None
                
            response.encoding = 'utf-8'
            
            # 解析JSONP格式数据
            text = response.text
            json_str = re.search(r'jsonpgz\((.*?)\);?$', text)
            if json_str:
                data = json.loads(json_str.group(1))
                return {
                    '基金代码': data.get('fundcode'),
                    '基金名称': data.get('name'),
                    '净值日期': data.get('jzrq'),
                    '单位净值': float(data.get('dwjz', 0)),
                    '估值': float(data.get('gsz', 0)),
                    '估值时间': data.get('gztime'),
                    '日涨跌幅': float(data.get('gszzl', 0))
                }
            return None
            
        except Exception as e:
            log.error(f"获取基金基本信息失败 [{fund_code}]: {e}")
            return None
    
    def get_fund_top_holdings(self, fund_code: str, force_update: bool = False) -> Optional[list[dict]]:
        """
        获取基金前十大重仓股信息
        优先从配置文件读取，如果没有或强制更新则从网络获取
        
        Args:
            fund_code: 基金代码
            force_update: 是否强制从网络更新
        
        Returns:
            list: 持仓股票列表，格式 [{'股票代码': '600519', '股票名称': '贵州茅台', '持仓比例': 10.5}, ...]
        """
        print(f"[监控] 开始获取基金 {fund_code} 持仓 (强制更新: {force_update})")
        start_time = time.time()
        
        # 1. 如果不强制更新，先尝试从数据库读取
        if not force_update:
            print(f"[监控] 尝试从数据库读取基金 {fund_code} 持仓")
            db_start = time.time()
            holdings = self.db.get_fund_holdings(fund_code)
            db_time = time.time() - db_start
            
            if holdings:
                elapsed_time = time.time() - start_time
                print(f"[监控] 从数据库读取成功，共 {len(holdings)} 只股票")
                print(f"[监控] 数据库查询耗时: {db_time:.3f}秒，总耗时: {elapsed_time:.2f}秒")
                
                # 显示持仓比例摘要
                if holdings:
                    total_ratio = sum(h.get('持仓比例', 0) for h in holdings)
                    print(f"[监控] 持仓比例合计: {total_ratio:.2f}%")
                
                log.info(f"从数据库读取基金 [{fund_code}] 持仓，共 {len(holdings)} 只股票")
                return holdings
            else:
                print(f"[监控] 数据库无持仓数据，查询耗时: {db_time:.3f}秒")
        
        # 2. 从网络获取持仓信息
        print(f"[监控] 从网络获取基金 {fund_code} 持仓信息")
        holdings = self._fetch_fund_holdings_online(fund_code)
        
        # 3. 保存到数据库
        if holdings:
            print(f"[监控] 保存持仓信息到数据库")
            save_start = time.time()
            self._save_fund_holdings(fund_code, holdings)
            save_time = time.time() - save_start
            print(f"[监控] 数据库保存耗时: {save_time:.3f}秒")
        
        elapsed_time = time.time() - start_time
        if holdings:
            print(f"[监控] 基金 {fund_code} 持仓获取完成，共 {len(holdings)} 只股票，总耗时 {elapsed_time:.2f}秒")
        else:
            print(f"[监控] 基金 {fund_code} 持仓获取失败，总耗时 {elapsed_time:.2f}秒")
        
        return holdings
    
    def _fetch_fund_holdings_online(self, fund_code: str) -> Optional[List[Dict]]:
        """
        从网络获取基金前十大重仓股信息
        
        Args:
            fund_code: 基金代码
        
        Returns:
            list: 持仓股票列表
        """
        start_time = time.time()
        
        try:
            print(f"[监控] 开始从网络获取基金 {fund_code} 持仓信息")
            
            params = {
                'type': 'jjcc',  # 基金持仓
                'code': fund_code,
                'topline': '10',  # 前10大持仓
                'year': '',
                'month': '',
                'rt': str(datetime.now().timestamp())
            }
            
            print(f"[监控] 发送HTTP请求到: {self.FUND_POSITION_URL}")
            api_rate_limiter.wait_for_endpoint('fund_position')
            response = self.session.get(self.FUND_POSITION_URL, params=params, timeout=10)
            response.encoding = 'utf-8'
            text = response.text
            
            # 尝试解析JavaScript响应格式：var apidata={content:"..."}
            import re
            # 直接提取content字段的值
            content_match = re.search(r'content\s*:\s*"([^"]*)"', text, re.DOTALL)
            if content_match:
                text = content_match.group(1)
                # 处理转义字符
                text = text.replace('\\"', '"').replace("\\'", "'").replace('\\\\', '\\')
                print(f"[监控] 成功提取content字段，长度: {len(text)} 字符")
            else:
                # 尝试其他格式：content:'...'
                content_match = re.search(r"content\s*:\s*'([^']*)'", text, re.DOTALL)
                if content_match:
                    text = content_match.group(1)
                    text = text.replace('\\"', '"').replace("\\'", "'").replace('\\\\', '\\')
                    print(f"[监控] 成功提取content字段(单引号)，长度: {len(text)} 字符")
            
            # 检查响应内容
            text_sample = text[:500] if len(text) > 500 else text
            print(f"[监控] 收到响应，长度: {len(text)} 字符")
            print(f"[监控] 响应样本: {text_sample[:100]}...")
            
            # 解析HTML中的表格数据
            # 天天基金网实际HTML结构：
            # <td>1</td><td><a>001309</a></td><td class='tol'><a>德明利</a></td>...<td class='tor'>11.44%</td>
            holdings = []
            
            # 正则匹配：尝试多个模式以适应不同的HTML结构
            patterns = [
                # 模式1：原始精确模式
                r"<td>(\d+)</td><td[^>]*><a[^>]*>([\d]+)</a></td><td[^>]*><a[^>]*>([^<]+)</a></td>.*?<td[^>]*>([\d.]+)%</td>",
                # 模式2：更灵活的模式，允许标签间有更多内容
                r"<td>(\d+)</td>.*?<a[^>]*>(\d{6})</a>.*?<a[^>]*>([^<]+)</a>.*?([\d.]+)%",
                # 模式3：备用模式，用于处理不同的HTML结构
                r'(\d{6})\s*</td>.*?<a[^>]*>([^<]+)</a>.*?([\d.]+)%'
            ]
            
            matches = []
            used_pattern = None
            
            for pattern_idx, pattern in enumerate(patterns):
                current_matches = re.findall(pattern, text, re.DOTALL)
                print(f"[监控] 模式{pattern_idx+1}匹配结果: 找到 {len(current_matches)} 个匹配")
                
                if current_matches and len(current_matches) >= 5:  # 至少找到5个匹配才认为是有效的
                    matches = current_matches
                    used_pattern = pattern_idx + 1
                    print(f"[监控] 使用模式{used_pattern}，找到 {len(matches)} 个有效匹配")
                    break
            
            if not matches:
                print(f"[监控] 所有正则模式都未能匹配到足够的持仓数据")
                # 尝试备用解析方案
                return self._parse_holdings_fallback(text)
            
            if matches:
                for i, match in enumerate(matches[:10]):
                    # 根据使用的模式解析匹配结果
                    if used_pattern == 3:
                        # 模式3：只有3个捕获组 (股票代码, 股票名称, 持仓比例)
                        stock_code = match[0].strip()
                        stock_name = match[1].strip()
                        position_ratio = float(match[2].strip())
                    else:
                        # 模式1和2：4个捕获组 (序号, 股票代码, 股票名称, 持仓比例)
                        stock_code = match[1].strip()
                        stock_name = match[2].strip()
                        position_ratio = float(match[3].strip())
                    
                    print(f"[监控]  匹配 {i+1}: 代码={stock_code}, 名称={stock_name}, 比例={position_ratio}%")
                    
                    holdings.append({
                        '股票代码': stock_code,
                        '股票名称': stock_name,
                        '持仓比例': position_ratio
                    })
                
                elapsed_time = time.time() - start_time
                print(f"[监控] 基金 {fund_code} 持仓解析成功，使用模式{used_pattern}，共 {len(holdings)} 只股票，耗时 {elapsed_time:.2f}秒")
                log.info(f"从网络获取基金 [{fund_code}] 持仓成功，共 {len(holdings)} 只股票")
                return holdings
            
            print(f"[监控] 正则匹配失败，尝试备用解析方案")
            # 备用解析方案：使用正则表达式
            result = self._parse_holdings_fallback(text)
            elapsed_time = time.time() - start_time
            
            if result:
                print(f"[监控] 备用解析成功，找到 {len(result)} 只股票，耗时 {elapsed_time:.2f}秒")
            else:
                print(f"[监控] 备用解析失败，耗时 {elapsed_time:.2f}秒")
            
            return result
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"[监控] 获取基金 {fund_code} 持仓异常，耗时 {elapsed_time:.2f}秒: {e}")
            log.error(f"获取基金持仓失败 [{fund_code}]: {e}")
            return None
    
    def _parse_holdings_fallback(self, html_text: str) -> Optional[List[Dict]]:
        """备用持仓解析方案"""
        try:
            # 使用更宽松的正则匹配
            pattern = r'(\d{6})\s*</td>.*?<a[^>]*>([^<]+)</a>.*?([\d.]+)%'
            matches = re.findall(pattern, html_text, re.DOTALL)
            
            holdings = []
            for match in matches[:10]:
                holdings.append({
                    '股票代码': match[0].strip(),
                    '股票名称': match[1].strip(),
                    '持仓比例': float(match[2].strip())
                })
            
            return holdings if holdings else None
        except:
            return None
    
    def _save_fund_holdings(self, fund_code: str, holdings: list[dict]):
        """
        保存基金持仓信息（使用数据库）
        
        Args:
            fund_code: 基金代码
            holdings: 持仓列表
        """
        # 使用数据库保存
        self.db.save_fund_holdings(fund_code, holdings)
        log.info(f"已保存基金 [{fund_code}] 持仓信息到数据库")
    
    def get_stock_realtime_quote(self, stock_code: str, retry_count: int = 3, delay: float = 0.5) -> Optional[Dict]:
        """
        获取股票实时行情（带重试机制）
        
        Args:
            stock_code: 股票代码，如 '600519'
            retry_count: 重试次数，默认3次
            delay: 请求间隔（秒），默认0.5秒
        
        Returns:
            dict: 股票行情信息
        """
        # 如果是周末，直接使用新浪API
        if self.is_weekend:
            return self._get_stock_quote_sina(stock_code)
        
        import time
        
        for attempt in range(retry_count):
            try:
                # 添加延迟避免请求过快
                if attempt > 0:
                    wait_time = delay * (2 ** attempt)  # 指数退避
                    time.sleep(wait_time)
                
                # 判断市场：6开头是沪市(1)，其他是深市(0)，港股特殊处理
                if stock_code.startswith('6'):
                    market = '1'
                elif stock_code.startswith('0') or stock_code.startswith('3'):
                    market = '0'
                else:
                    # 港股等其他市场，跳过
                    log.debug(f"跳过非沺a股票 [{stock_code}]")
                    return None
                
                secid = f"{market}.{stock_code}"
                
                params = {
                    'fields': 'f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f57,f58,f60,f169,f170',
                    'secid': secid,
                    'ut': 'fa5fd1943c7b386f172d6893dbfba10b'
                }
                
                response = self.session.get(self.STOCK_QUOTE_URL, params=params, timeout=10)
                data = response.json()
                
                if data.get('data'):
                    stock_data = data['data']
                    return {
                        '股票代码': stock_code,
                        '股票名称': stock_data.get('f58'),  # 名称
                        '最新价': stock_data.get('f43', 0) / 100,  # 最新价
                        '涨跌幅': stock_data.get('f170', 0) / 100,  # 涨跌幅
                        '涨跌额': stock_data.get('f169', 0) / 100,  # 涨跌额
                        '昨收': stock_data.get('f60', 0) / 100,  # 昨收
                    }
                
                # 数据为空，等待后重试
                if attempt < retry_count - 1:
                    log.debug(f"股票 [{stock_code}] 数据为空，第 {attempt+1} 次重试")
                    continue
                
                return None
                
            except Exception as e:
                if attempt < retry_count - 1:
                    log.debug(f"股票 [{stock_code}] 请求失败，第 {attempt+1} 次重试: {e}")
                else:
                    # 东方财富失败，尝试新浪备用API
                    log.debug(f"东方财富API失败 [{stock_code}]，尝试新浪API")
                    return self._get_stock_quote_sina(stock_code)
        
        return None
    
    def _get_stock_quote_sina(self, stock_code: str) -> Optional[Dict]:
        """
        使用新浪API获取股票行情（备用数据源，周末可用）
        
        Args:
            stock_code: 股票代码
            
        Returns:
            dict: 股票行情信息
        """
        try:
            # 判断市场：6开头是沪市(sh)，0/3开头是深市(sz)
            if stock_code.startswith('6'):
                symbol = f'sh{stock_code}'
            elif stock_code.startswith('0') or stock_code.startswith('3'):
                symbol = f'sz{stock_code}'
            else:
                return None
            
            url = f"{self.SINA_STOCK_URL}{symbol}"
            api_rate_limiter.wait_for_endpoint('sina')
            response = self.session.get(url, timeout=10, headers={'Referer': 'http://finance.sina.com.cn'})
            
            # 解析新浪数据格式: var hq_str_sh600519="名称,今开,昨收,现价,..."
            text = response.text
            if '=""' in text or not text.strip():
                return None
            
            # 提取数据部分
            import re
            match = re.search(r'="([^"]+)"', text)
            if not match:
                return None
            
            data = match.group(1).split(',')
            if len(data) < 10:
                return None
            
            name = data[0]       # 股票名称
            yesterday_close = float(data[2]) if data[2] else 0  # 昨收
            current_price = float(data[3]) if data[3] else 0    # 现价
            
            # 计算涨跌幅
            if yesterday_close > 0:
                change_pct = (current_price - yesterday_close) / yesterday_close * 100
                change_amount = current_price - yesterday_close
            else:
                change_pct = 0
                change_amount = 0
            
            log.debug(f"新浪API获取成功 [{stock_code}]: {name} 现价{current_price}")
            
            return {
                '股票代码': stock_code,
                '股票名称': name,
                '最新价': current_price,
                '涨跌幅': round(change_pct, 2),
                '涨跌额': round(change_amount, 2),
                '昨收': yesterday_close,
            }
            
        except Exception as e:
            log.error(f"新浪API获取失败 [{stock_code}]: {e}")
            return None
    
    def _get_stock_quote_tencent_batch(self, stock_codes: list[str]) -> dict[str, dict]:
        """
        使用腾讯API批量获取股票行情（更快更稳定）
        
        Args:
            stock_codes: 股票代码列表
            
        Returns:
            dict: {股票代码: 行情数据字典}
        """
        if not stock_codes:
            return {}
        
        try:
            # 构建腾讯格式的股票代码列表
            tencent_codes = []
            for code in stock_codes:
                if code.startswith('6'):
                    tencent_codes.append(f"sh{code}")
                elif code.startswith('0') or code.startswith('3'):
                    tencent_codes.append(f"sz{code}")
                else:
                    continue
            
            if not tencent_codes:
                return {}
            
            # 腾讯API支持一次请求多只股票，用逗号分隔
            codes_str = ','.join(tencent_codes)
            url = f"{self.TENCENT_STOCK_URL}{codes_str}"
            
            log.info(f"使用腾讯API批量获取 {len(tencent_codes)} 只股票行情")
            api_rate_limiter.wait_for_endpoint('tencent')
            
            response = self.session.get(url, timeout=10, headers={
                'Referer': 'http://stock.qq.com',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.encoding = 'gbk'  # 腾讯返回GBK编码
            
            results = {}
            text = response.text
            
            import re
            matches = []
            for part in text.split(';'):
                if not part.strip():
                    continue
                match = re.match(r'v_((?:sh|sz)\d{6})="(.+)"', part.strip())
                if match:
                    tencent_code = match.group(1)
                    data_str = match.group(2)
                    matches.append((tencent_code, data_str))
            
            for tencent_code, data_str in matches:
                # 提取纯数字股票代码
                stock_code = tencent_code[2:]  # 去掉 sh 或 sz 前缀
                
                # 按 ~ 分割数据
                fields = data_str.split('~')
                if len(fields) < 35:
                    continue
                
                # 字段映射（根据腾讯API文档）
                # 0:未知, 1:名字, 2:代码, 3:当前价格, 4:昨收, 5:今开
                # 31:涨跌, 32:涨跌%
                try:
                    current_price = float(fields[3]) if fields[3] else 0
                    yesterday_close = float(fields[4]) if fields[4] else 0
                    change_amount = float(fields[31]) if fields[31] else 0
                    change_pct = float(fields[32]) if fields[32] else 0
                    
                    results[stock_code] = {
                        '股票代码': stock_code,
                        '股票名称': fields[1],
                        '最新价': current_price,
                        '涨跌幅': change_pct,
                        '涨跌额': change_amount,
                        '昨收': yesterday_close,
                    }
                except (ValueError, IndexError) as e:
                    log.warning(f"解析腾讯股票数据失败 [{stock_code}]: {e}")
                    continue
            
            log.info(f"腾讯API成功返回 {len(results)}/{len(tencent_codes)} 只股票行情")
            return results
            
        except Exception as e:
            log.error(f"腾讯API批量获取失败: {e}")
            return {}
    
    def get_batch_stock_quotes(self, stock_codes: list[str], timeout: float = 30.0) -> dict[str, dict]:
        """
        批量获取股票实时行情（优先使用腾讯API，更快更稳定）
        
        Args:
            stock_codes: 股票代码列表，如 ['600519', '000858']
            timeout: 超时时间（秒），默认30秒
        
        Returns:
            dict: {股票代码: 行情数据字典}
        """
        if not stock_codes:
            return {}
        
        start_time = time.time()
        
        # 首先尝试使用腾讯API（更快更稳定）
        log.info(f"尝试使用腾讯API批量获取 {len(stock_codes)} 只股票行情")
        tencent_results = self._get_stock_quote_tencent_batch(stock_codes)
        
        if len(tencent_results) >= len(stock_codes) * 0.8:  # 如果获取到80%以上数据
            elapsed_time = time.time() - start_time
            log.info(f"腾讯API获取成功，耗时 {elapsed_time:.2f}秒，返回 {len(tencent_results)} 只股票")
            return tencent_results
        
        # 腾讯API获取不完整，使用东方财富API补充
        log.info(f"腾讯API返回不完整 ({len(tencent_results)}/{len(stock_codes)})，尝试东方财富API")
        
        # 找出未获取到的股票
        missing_codes = [code for code in stock_codes if code not in tencent_results]
        
        try:
            # 构建secids参数：market.code,market.code,...
            secid_list = []
            for stock_code in missing_codes:
                if stock_code.startswith('6'):
                    market = '1'
                elif stock_code.startswith('0') or stock_code.startswith('3'):
                    market = '0'
                else:
                    continue
                secid_list.append(f"{market}.{stock_code}")
            
            if not secid_list:
                return {}
            
            secids = ','.join(secid_list)
            
            params = {
                'fields': 'f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f57,f58,f60,f169,f170',
                'secids': secids,
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b'
            }
            
            log.info(f"批量请求 {len(secid_list)} 只股票行情")
            api_rate_limiter.wait_for_endpoint('eastmoney_batch')
            
            remaining_time = timeout - (time.time() - start_time)
            if remaining_time <= 0:
                log.warning(f"获取股票行情超时（{timeout}秒），未开始请求")
                return {}
            
            response = self.session.get(self.BATCH_STOCK_QUOTE_URL, params=params, timeout=min(15, remaining_time))
            data = response.json()
            
            results = {}
            if data.get('data') and data['data'].get('diff'):
                for item in data['data']['diff']:
                    if time.time() - start_time > timeout:
                        log.warning(f"处理响应数据超时（{timeout}秒），已处理 {len(results)} 只股票")
                        break
                    
                    secid = item.get('f57')
                    if not secid:
                        continue
                    
                    parts = secid.split('.')
                    if len(parts) != 2:
                        continue
                    
                    stock_code = parts[1]
                    
                    results[stock_code] = {
                        '股票代码': stock_code,
                        '股票名称': item.get('f58'),  # 名称
                        '最新价': item.get('f43', 0) / 100 if item.get('f43') else 0,
                        '涨跌幅': item.get('f170', 0) / 100 if item.get('f170') else 0,
                        '涨跌额': item.get('f169', 0) / 100 if item.get('f169') else 0,
                        '昨收': item.get('f60', 0) / 100 if item.get('f60') else 0,
                    }
            
            elapsed_time = time.time() - start_time
            log.info(f"批量获取成功，返回 {len(results)} 只股票行情，耗时 {elapsed_time:.2f}秒")
            return results
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            log.error(f"批量获取股票行情失败（耗时 {elapsed_time:.2f}秒）: {e}")
            log.info(f"批量接口失败，回退到单线程获取")
            results = {}
            for stock_code in missing_codes:
                if time.time() - start_time > timeout:
                    log.warning(f"单线程回退获取超时（{timeout}秒），已获取 {len(results)}/{len(missing_codes)} 只股票")
                    break
                quote = self.get_stock_realtime_quote(stock_code, retry_count=1, delay=0.3)
                if quote:
                    results[stock_code] = quote
                time.sleep(random.uniform(self.DELAY_WEEKDAY_MIN, self.DELAY_WEEKDAY_MAX))
            return {**tencent_results, **results}
    
    def calculate_fund_valuation(self, fund_code: str) -> Optional[Dict]:
        """
        计算基金估值（并发优化版）
        
        Args:
            fund_code: 基金代码
        
        Returns:
            dict: 估值结果
        """
        import time
        start_time = time.time()
        
        try:
            log.info(f"开始计算基金估值 [{fund_code}]")
            
            # 检查缓存（5分钟TTL）
            cache_key = fund_code
            if cache_key in self._valuation_cache:
                cached_result, timestamp = self._valuation_cache[cache_key]
                if time.time() - timestamp < 300:  # 5分钟TTL
                    log.info(f"使用缓存估值结果 [{fund_code}]")
                    return cached_result
            
            # 1. 获取基金基本信息
            step1_start = time.time()
            fund_info = self.get_fund_basic_info(fund_code)
            if not fund_info:
                log.warning(f"无法获取基金基本信息 [{fund_code}]")
                fund_info = {'基金代码': fund_code, '单位净值': 0}
            step1_time = time.time() - step1_start
            log.info(f"[性能] 步骤1-获取基金基本信息: {step1_time:.2f}秒")
            
            # 2. 获取持仓信息
            step2_start = time.time()
            holdings = self.get_fund_top_holdings(fund_code)
            if not holdings:
                log.error(f"无法获取基金持仓信息 [{fund_code}]")
                return None
            step2_time = time.time() - step2_start
            log.info(f"[性能] 步骤2-获取持仓信息: {step2_time:.2f}秒")
            
            # 3. 批量获取持仓股票实时行情
            step3_start = time.time()
            total_ratio = 0  # 总持仓比例
            weighted_change = 0  # 加权涨跌幅
            stock_details = []
            
            # 提取所有股票代码
            stock_codes = [h['股票代码'] for h in holdings]
            log.info(f"批量获取 {len(stock_codes)} 只股票行情")
            
            batch_quotes = self.get_batch_stock_quotes(stock_codes, timeout=self.STOCK_QUOTE_TIMEOUT)
            
            failed_stocks = [code for code in stock_codes if code not in batch_quotes]
            
            if failed_stocks:
                log.warning(f"基金 [{fund_code}] 部分重仓股行情获取失败: {failed_stocks}，跳过估值计算")
                return {
                    '基金代码': fund_code,
                    '基金名称': fund_info.get('基金名称', ''),
                    '上次净值': fund_info.get('单位净值', 0),
                    '净值日期': fund_info.get('净值日期', ''),
                    '估算净值': '/',
                    '估算涨跌幅': '/',
                    '估算时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    '重仓股数量': len(holdings),
                    '持仓比例合计': sum(h['持仓比例'] for h in holdings),
                    '重仓股明细': [],
                    '获取失败的股票': failed_stocks
                }
            
            for holding in holdings:
                stock_code = holding['股票代码']
                position_ratio = holding['持仓比例']
                
                quote = batch_quotes[stock_code]
                change_pct = quote['涨跌幅']
                
                weighted_change += change_pct * position_ratio / 100
                total_ratio += position_ratio
                
                stock_details.append({
                    '股票代码': stock_code,
                    '股票名称': quote['股票名称'],
                    '持仓比例': position_ratio,
                    '最新价': quote['最新价'],
                    '涨跌幅': change_pct,
                    '贡献度': change_pct * position_ratio / 100
                })
                
                log.debug(f"  {quote['股票名称']}({stock_code}): "
                         f"涨跌{change_pct:+.2f}%, 持仓{position_ratio:.2f}%, "
                         f"贡献{change_pct * position_ratio / 100:+.4f}%")
            
            step3_time = time.time() - step3_start
            log.info(f"[性能] 步骤3-批量获取{len(stock_codes)}只股票行情: {step3_time:.2f}秒")
            log.info(f"  成功获取全部 {len(stock_codes)} 只股票行情")
            
            # 4. 计算估值
            if total_ratio > 0:
                # 估算涨跌幅（考虑持仓比例）
                estimated_change = weighted_change
                
                # 估算净值
                last_nav = fund_info.get('单位净值', 1.0)
                estimated_nav = last_nav * (1 + estimated_change / 100)
                
                result = {
                    '基金代码': fund_code,
                    '基金名称': fund_info.get('基金名称', ''),
                    '上次净值': last_nav,
                    '净值日期': fund_info.get('净值日期', ''),
                    '估算净值': round(estimated_nav, 4),
                    '估算涨跌幅': round(estimated_change, 2),
                    '估算时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    '重仓股数量': len(stock_details),
                    '持仓比例合计': round(total_ratio, 2),
                    '重仓股明细': stock_details
                }
                
                log.info(f"估值计算完成: {fund_info.get('基金名称', fund_code)} "
                        f"估值 {estimated_nav:.4f} ({estimated_change:+.2f}%)")
                
                total_time = time.time() - start_time
                log.info(f"[性能] 基金 [{fund_code}] 总耗时: {total_time:.2f}秒")
                
                # 存储到缓存
                self._valuation_cache[cache_key] = (result, time.time())
                
                return result
            
            return None
            
        except Exception as e:
            log.error(f"计算基金估值失败 [{fund_code}]: {e}")
            return None
    
    def batch_calculate_valuations(self, fund_codes: List[str]) -> Dict[str, Dict]:
        """
        批量计算多个基金的估值
        
        Args:
            fund_codes: 基金代码列表
        
        Returns:
            dict: 基金估值字典
        """
        results = {}
        total = len(fund_codes)
        
        log.info(f"开始批量计算 {total} 个基金的估值")
        
        for i, fund_code in enumerate(fund_codes, 1):
            log.info(f"[{i}/{total}] 处理基金: {fund_code}")
            
            result = self.calculate_fund_valuation(fund_code)
            if result:
                results[fund_code] = result
            else:
                log.warning(f"基金 [{fund_code}] 估值计算失败")
        
        log.info(f"批量计算完成，成功 {len(results)}/{total}")
        return results


# 便捷函数
def get_fund_valuation(fund_code: str) -> Optional[Dict]:
    """
    快速获取单个基金估值的便捷函数
    
    Args:
        fund_code: 基金代码
    
    Returns:
        dict: 估值结果
    """
    api = FundValuationAPI()
    return api.calculate_fund_valuation(fund_code)


def print_fund_valuation(valuation: Dict):
    """
    格式化打印基金估值信息
    
    Args:
        valuation: 估值结果字典
    """
    if not valuation:
        print("无估值数据")
        return
    
    print("\n" + "=" * 80)
    print(f"【{valuation['基金名称']}】({valuation['基金代码']})")
    print("=" * 80)
    print(f"上次净值: {valuation['上次净值']:.4f} ({valuation['净值日期']})")
    print(f"估算净值: {valuation['估算净值']:.4f}")
    print(f"估算涨幅: {valuation['估算涨跌幅']:+.2f}%")
    print(f"估算时间: {valuation['估算时间']}")
    print(f"重仓股数: {valuation['重仓股数量']}只 (持仓比例合计: {valuation['持仓比例合计']:.2f}%)")
    print("-" * 80)
    print(f"{'股票代码':<10} {'股票名称':<12} {'持仓%':<8} {'最新价':<10} {'涨跌%':<10} {'贡献%':<10}")
    print("-" * 80)
    
    for stock in valuation['重仓股明细']:
        print(f"{stock['股票代码']:<10} {stock['股票名称']:<12} "
              f"{stock['持仓比例']:>6.2f}% {stock['最新价']:>9.2f} "
              f"{stock['涨跌幅']:>+8.2f}% {stock['贡献度']:>+8.4f}%")
    
    print("=" * 80 + "\n")


# 使用示例
if __name__ == '__main__':
    # 创建API实例
    api = FundValuationAPI()
    
    # 示例1: 计算单个基金估值
    print("示例1: 计算单个基金估值")
    print("-" * 60)
    
    fund_code = '001593'  # 天弘创业板ETF联接C
    result = api.calculate_fund_valuation(fund_code)
    
    if result:
        print_fund_valuation(result)
    else:
        print(f"基金 {fund_code} 估值计算失败\n")
    
    # 示例2: 批量计算多个基金估值
    print("\n示例2: 批量计算多个基金估值")
    print("-" * 60)
    
    fund_list = ['001593', '001549', '004742']  # 创业板、上证50、深证100
    results = api.batch_calculate_valuations(fund_list)
    
    for fund_code, valuation in results.items():
        print(f"\n{valuation['基金名称']}: "
              f"{valuation['估算净值']:.4f} ({valuation['估算涨跌幅']:+.2f}%)")
    
    # 示例3: 使用便捷函数
    print("\n示例3: 使用便捷函数")
    print("-" * 60)
    
    valuation = get_fund_valuation('001593')
    if valuation:
        print(f"基金: {valuation['基金名称']}")
        print(f"估值: {valuation['估算净值']:.4f} ({valuation['估算涨跌幅']:+.2f}%)")
