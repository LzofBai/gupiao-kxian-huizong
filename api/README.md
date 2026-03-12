# API 模块说明

## 📦 模块功能

API层负责与外部数据源交互，获取基金和股票的实时数据。

## 📁 文件结构

```
api/
├── __init__.py                 # 模块初始化
├── FundValuationAPI.py         # 基金估值核心API
├── StockKlineAPI.py            # 股票K线数据API
└── README.md                   # 本文档
```

## 🔧 核心组件

### 1. FundValuationAPI.py

**功能**：基金估值计算的核心类

**主要方法**：
- `get_fund_basic_info(fund_code)` - 获取基金基本信息
- `get_fund_top_holdings(fund_code)` - 获取基金前十大重仓股
- `get_stock_realtime_quote(stock_code)` - 获取股票实时行情
- `calculate_fund_valuation(fund_code)` - 计算单个基金估值
- `batch_calculate_valuations(fund_codes)` - 批量计算基金估值

**数据源**：
- 天天基金网：基金基本信息
- 东方财富：股票实时行情（主）
- 新浪财经：股票行情（备用，周末可用）

**特性**：
- ✅ 智能数据源切换（周末自动使用新浪API）
- ✅ 连接池管理 + 重试机制
- ✅ 数据库持久化（持仓信息）
- ✅ 并发请求优化（ThreadPoolExecutor）
- ✅ 性能监控埋点

### 2. StockKlineAPI.py

**功能**：获取股票K线数据用于图表展示

**主要方法**：
- `get_stock_kline(stock_code, period)` - 获取指定周期K线数据
- `get_batch_klines(stock_codes)` - 批量获取K线数据

**数据源**：
- 东方财富K线接口

**支持周期**：
- 日K、周K、月K
- 1分钟、5分钟、15分钟、30分钟、60分钟

## 🔌 使用示例

```python
from api.FundValuationAPI import FundValuationAPI

# 初始化API
api = FundValuationAPI(db_path='data/funds.db')

# 计算基金估值
result = api.calculate_fund_valuation('025209')
print(f"估值涨跌幅: {result['估值涨跌幅']}%")

# 批量计算
results = api.batch_calculate_valuations(['025209', '015916'])
```

## ⚙️ 配置说明

### 请求参数优化

**周末模式**（新浪API）：
- 并发线程数：5
- 请求延迟：0.1-0.3秒

**工作日模式**（东方财富API）：
- 并发线程数：3
- 请求延迟：0.3-0.8秒
- 重试次数：3次（指数退避）

## 📊 性能指标

- 单个基金估值：**~0.6秒**（周末，10只股票）
- 批量估值：**~0.5秒/基金**（并发处理）
- API成功率：**>99%**（双数据源保障）

## 🔄 依赖关系

```
FundValuationAPI
  ├── database.FundDatabase  # 持仓数据存储
  ├── utils.Logger           # 日志记录
  └── requests               # HTTP请求
```

## 📝 日志输出

日志文件：`logs/FundValuationAPI.log`

包含以下信息：
- API请求耗时
- 数据源切换记录
- 错误和重试日志
- 性能监控数据
