---
name: eastmoney-kline
version: 1.0.0
description: 快速获取股票、指数、基金的K线图数据，支持多种技术指标和周期类型，获取基金实时估值等
displayName: "东方财富K线获取器"
author: "Internal Team"
license: "MIT"

category: data-acquisition
subcategory: financial-data
type: command
difficulty: beginner

keywords:
  - stock
  - kline
  - chart
  - eastmoney
  - financial-data
  - technical-indicator

minClaudeVersion: "1.0.0"

platforms:
  - windows
  - macos
  - linux

languages:
  - python

filesystem:
  read:
    - "${PROJECT_ROOT}/**/*"
  write:
    - "${PROJECT_ROOT}/**/*.png"
    - "${PROJECT_ROOT}/**/*.html"

network:
  allowedHosts:
    - "webquoteklinepic.eastmoney.com"
    - "quote.eastmoney.com"

tools:
  allowed:
    - read_file
    - write_file
    - run_in_terminal

input:
  arguments:
    - name: stock_code
      type: string
      description: 证券代码(格式: 市场代码.证券代码)
      required: true
    - name: period
      type: string
      description: K线周期
      required: false
      default: "D"
      enum: ["D", "W", "M", "m", "m5", "m15", "m30", "m60"]
    - name: indicator
      type: string
      description: 技术指标
      required: false
      default: "MACD"
      enum: ["MACD", "KDJ", "RSI", "BOLL", "MA", "VOL", "OBV", "WR", "CCI", "DMI"]
    - name: save_path
      type: string
      description: 保存路径
      required: false
  context:
    requiresProject: false
    requiresGit: false

output:
  format: markdown

behavior:
  timeout: 60
  cache:
    enabled: true
    ttlSeconds: 300
  interactive:
    showProgress: true

dependencies:
  pip:
    - requests>=2.25.0
---

# 东方财富K线获取器

快速获取股票、指数、基金的K线图数据，支持多种技术指标和周期类型。

## When to Use

当用户需要获取或分析股票、指数K线数据时使用此技能：

- "帮我获取沪深300的日K线图"
- "下载创业板指的周线MACD图"
- "批量下载科技板块的K线数据"
- "生成指数监控页面"
- "对比多个指数的走势"

## 核心功能

- 📊 **获取K线图**: 支持股票、指数、基金、期货的K线数据
- 🔄 **多周期支持**: 日线、周线、月线、分钟线
- 📈 **技术指标**: MACD、KDJ、RSI、BOLL、MA、VOL、OBV、WR、CCI、DMI
- 📦 **批量下载**: 支持多股票、多周期、多指标批量处理
- 🌐 **HTML集成**: 生成可嵌入网页的图表标签

## 前置准备

### 1. 确保依赖模块存在

技能依赖 `KLineAPI.py` 模块，该模块位于：
```
I:\Ai\项目尝试\3、股票信息K线汇总\KLineAPI.py
```

### 2. 安装必要依赖

```bash
pip install requests
```

### 3. 导入模块

```python
from KLineAPI import KLineAPI, get_kline_url, download_kline
```

## 使用方式

### 快速使用（推荐）

对于简单场景，直接使用便捷函数：

```python
# 1. 生成K线图URL
url = get_kline_url('1.000300', period='D', indicator='MACD')
print(url)

# 2. 下载K线图到本地
success = download_kline(
    stock_code='1.000300',
    save_path='./hs300.png',
    period='D',
    indicator='MACD'
)
```

### 完整功能（高级）

对于批量处理和自定义需求，使用完整类：

```python
# 初始化API
api = KLineAPI()

# 生成URL
url = api.generate_url(
    stock_code='1.000300',  # 沪深300
    period='D',              # 日线
    indicator='MACD'         # MACD指标
)

# 下载单张图
api.download_kline(
    stock_code='1.000300',
    save_path='./charts/hs300_day_macd.png',
    period='D',
    indicator='MACD'
)

# 批量下载
stocks = {
    '1.000300': '沪深300',
    '0.399006': '创业板指',
    '1.000016': '上证50'
}

results = api.batch_download(
    stocks=stocks,
    save_dir='./charts',
    periods=['D', 'W', 'M'],
    indicators=['MACD', 'KDJ', 'RSI']
)
```

## 证券代码格式

**格式规则**: `市场代码.证券代码`

| 市场代码 | 市场名称 | 示例 |
|---------|---------|------|
| `1` | 上海证券交易所 | `1.000300`(沪深300) |
| `0` | 深圳证券交易所 | `0.399006`(创业板指) |
| `2` | 中证指数 | `2.931186`(中证科技) |
| `90` | 东方财富板块 | `90.BK0701`(中证500) |
| `100` | 国际指数 | `100.NDX`(纳斯达克) |
| `102` | 期货市场 | `102.CL00Y`(NYMEX原油) |
| `124` | 港股指数 | `124.HSTECH`(恒生科技) |

**如何查找代码**：访问 https://quote.eastmoney.com/ 搜索证券，在URL中查看完整代码。

## 常用参数

### 周期类型 (period)

| 参数值 | 说明 |
|-------|------|
| `D` | 日线 |
| `W` | 周线 |
| `M` | 月线 |
| `m` | 1分钟 |
| `m5` | 5分钟 |
| `m15` | 15分钟 |
| `m30` | 30分钟 |
| `m60` | 60分钟 |

### 技术指标 (indicator)

支持的指标：`MACD`、`KDJ`、`RSI`、`BOLL`、`MA`、`VOL`、`OBV`、`WR`、`CCI`、`DMI`

## 实战场景

### 场景1: 快速查看单个指数

用户：**"帮我看看沪深300的日线MACD走势"**

```python
from KLineAPI import download_kline

# 下载到当前目录
download_kline('1.000300', './hs300_macd.png', period='D', indicator='MACD')
print("K线图已保存到: ./hs300_macd.png")
```

### 场景2: 批量下载行业板块

用户：**"下载半导体、新能源、医疗这几个行业的日线和周线"**

```python
from KLineAPI import KLineAPI

api = KLineAPI()

# 行业板块代码
sectors = {
    '90.BK1036': '半导体',
    '90.BK0900': '新能源车',
    '90.BK0727': '医疗服务'
}

# 批量下载日线和周线
results = api.batch_download(
    stocks=sectors,
    save_dir='./industry_charts',
    periods=['D', 'W'],
    indicators=['MACD']
)

print(f"下载完成: 成功{results['成功']}张, 失败{results['失败']}张")
```

### 场景3: 生成监控页面

用户：**"生成一个页面，展示主要指数的K线图"**

```python
from KLineAPI import KLineAPI

api = KLineAPI()

indices = {
    '1.000300': '沪深300',
    '0.399006': '创业板指',
    '1.000016': '上证50'
}

# 生成HTML
html = '<html><head><meta charset="UTF-8"><title>指数监控</title></head><body><table>'

for code, name in indices.items():
    html += f'<tr><th colspan="3">{name}</th></tr><tr>'
    
    for period in ['D', 'W', 'M']:
        img_tag = api.generate_html_img_tag(code, name, period, 'MACD')
        html += f'<td>{img_tag}</td>'
    
    html += '</tr>'

html += '</table></body></html>'

# 保存
with open('monitor.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("监控页面已生成: monitor.html")
```

### 场景4: 定时更新龙头股

用户：**"每天收盘后自动下载龙头股的K线"**

```python
from KLineAPI import KLineAPI
import schedule
import time

api = KLineAPI()

leaders = {
    '90.BK1036': '半导体',
    '90.BK0727': '医疗',
    '90.BK0900': '新能源'
}

def daily_update():
    date_str = time.strftime("%Y%m%d")
    print(f"开始下载 {date_str}")
    
    api.batch_download(
        stocks=leaders,
        save_dir=f'./daily/{date_str}',
        periods=['D'],
        indicators=['MACD', 'KDJ']
    )
    print("下载完成")

# 每天15:30执行
schedule.every().day.at("15:30").do(daily_update)

print("定时任务已启动，每天15:30自动下载...")
while True:
    schedule.run_pending()
    time.sleep(60)
```

## 辅助工具方法

```python
api = KLineAPI()

# 获取行情页面URL
quote_url = api.get_quote_url('1.000300')
# 返回: https://quote.eastmoney.com/zz/1.000300.html

# 解析股票代码
full_code = api.parse_stock_code('上海', '000300')
# 返回: 1.000300

# 查询可用指标
indicators = api.get_available_indicators()
# 返回: ['MACD', 'KDJ', 'RSI', ...]

# 查询可用周期
periods = api.get_available_periods()
# 返回: {'日线': 'D', '周线': 'W', ...}

# 查询市场代码
markets = api.get_market_codes()
# 返回: {'上海': '1', '深圳': '0', ...}
```

## 错误处理

### 常见问题

| 问题 | 原因 | 解决方案 |
|-----|------|---------|
| 下载失败 | 网络连接问题 | 检查网络，重试 |
| 证券代码错误 | 格式不正确 | 使用 `市场代码.证券代码` 格式 |
| 超时 | 请求时间过长 | 增加 timeout 参数 |
| 路径不存在 | 保存目录未创建 | API会自动创建目录 |

### 错误捕获示例

```python
try:
    success = api.download_kline('1.000300', './chart.png')
    if success:
        print("下载成功")
    else:
        print("下载失败")
except Exception as e:
    print(f"发生异常: {e}")
```

## 性能优化

### 1. 使用批量下载
```python
# ✅ 推荐
api.batch_download(stocks, './charts', periods=['D', 'W'])

# ❌ 不推荐
for code in stocks:
    for period in ['D', 'W']:
        api.download_kline(code, f'./{code}_{period}.png', period)
```

### 2. 并发下载（高级）
```python
from concurrent.futures import ThreadPoolExecutor
from KLineAPI import download_kline

stocks = ['1.000300', '0.399006', '1.000016']

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [
        executor.submit(download_kline, code, f'./charts/{code}.png')
        for code in stocks
    ]
    for future in futures:
        future.result()
```

## 工作流程

当用户请求获取K线数据时，按以下流程操作：

1. **理解需求**
   - 确认证券类型（股票/指数/板块）
   - 确认周期（日/周/月/分钟）
   - 确认指标（MACD/KDJ/RSI等）

2. **构建代码**
   - 简单需求：使用便捷函数 `get_kline_url()` 或 `download_kline()`
   - 批量需求：使用 `KLineAPI.batch_download()`
   - HTML需求：使用 `generate_html_img_tag()`

3. **处理代码**
   - 如果用户只提供简单名称，帮助查找正确的证券代码
   - 使用正确的市场代码前缀（1/0/90/100等）

4. **执行与反馈**
   - 运行代码下载数据
   - 告知用户保存位置
   - 如有错误，提供解决方案

## 注意事项

1. **合规使用**: 遵守东方财富网使用条款，避免过度频繁请求
2. **添加延迟**: 批量下载时建议添加适当延迟
3. **仅供学习**: 下载的数据仅供个人学习研究使用
4. **数据准确性**: 以官方网站数据为准

## 相关资源

- **模块位置**: `I:\Ai\项目尝试\3、股票信息K线汇总\KLineAPI.py`
- **配置文件**: `zs_online.json`
- **示例程序**: `zs_online.py`
- **东方财富官网**: https://quote.eastmoney.com/

## API接口说明

### 基础URL
```
http://webquoteklinepic.eastmoney.com/GetPic.aspx
```

### 核心参数

| 参数 | 说明 | 示例值 |
|-----|------|-------|
| nid | 证券代码 | `1.000300` |
| type | K线周期 | `D`/`W`/`M` |
| unitWidth | 单位宽度 | `-5`(自适应) |
| formula | 技术指标 | `MACD`/`KDJ` |
| AT | 显示成交量 | `1`(显示) |
| imageType | 图片类型 | `KXL`(K线图) |

---

**最后更新**: 2026-02-08
