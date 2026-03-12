# Utils 模块说明

## 📦 模块功能

工具模块提供项目通用的辅助功能，包括日志管理、配置读取、数据处理等。

## 📁 文件结构

```
utils/
├── __init__.py                 # 模块初始化
├── Logger.py                   # 日志管理类
├── Config.py                   # 配置管理（待实现）
└── README.md                   # 本文档
```

## 🔧 核心组件

### 1. Logger.py

**功能**：统一的日志管理类

#### 使用方法

```python
from utils.Logger import Logger

# 初始化日志
log = Logger('logs/myapp.log', level='info').logger

# 记录日志
log.info("应用启动")
log.debug("调试信息")
log.warning("警告信息")
log.error("错误信息")
log.critical("严重错误")
```

#### 配置选项

**日志级别**：
- `DEBUG`：调试信息（最详细）
- `INFO`：常规信息
- `WARNING`：警告信息
- `ERROR`：错误信息
- `CRITICAL`：严重错误

**日志格式**：
```
2026-02-09 12:00:00 - logs/app.log - INFO - 应用启动成功
```

格式说明：
- 时间戳：`YYYY-MM-DD HH:MM:SS`
- 日志文件路径
- 日志级别
- 日志消息

#### 特性

- ✅ **自动创建目录**：日志目录不存在时自动创建
- ✅ **文件和控制台双输出**：同时输出到文件和终端
- ✅ **中文支持**：UTF-8编码，完美支持中文
- ✅ **线程安全**：支持多线程并发写入

#### 日志文件管理

```python
# 每个模块使用独立的日志文件
api_log = Logger('logs/FundValuationAPI.log').logger
db_log = Logger('logs/FundDatabase.log').logger
web_log = Logger('logs/web_server.log').logger
```

**日志目录结构**：
```
logs/
├── FundValuationAPI.log        # API层日志
├── FundDatabase.log            # 数据库日志
├── web_server.log              # Web服务日志
├── StockKlineAPI.log           # K线API日志
└── migration.log               # 迁移工具日志
```

### 2. Config.py（规划中）

**功能**：配置文件管理

预期功能：
- 读取YAML/JSON配置
- 环境变量管理
- 配置热更新

### 3. 其他工具函数

#### file2json（待迁移）

当前在 `web_server.py` 中，计划迁移到 utils：

```python
def file2json(file_path: str) -> dict:
    """读取JSON文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
```

#### json2file（待迁移）

```python
def json2file(data: dict, file_path: str):
    """写入JSON文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

## 📊 日志最佳实践

### 1. 日志级别使用建议

```python
# DEBUG - 详细的调试信息
log.debug(f"处理请求参数: {params}")

# INFO - 关键操作记录
log.info(f"开始计算基金估值 [{fund_code}]")

# WARNING - 不影响运行但需注意
log.warning(f"基金 [{fund_code}] 持仓数据为空")

# ERROR - 错误但不影响整体
log.error(f"获取股票 [{stock_code}] 行情失败: {e}")

# CRITICAL - 严重错误，影响系统运行
log.critical(f"数据库连接失败: {e}")
```

### 2. 性能监控日志

```python
import time

start_time = time.time()
# ... 执行操作 ...
elapsed = time.time() - start_time
log.info(f"[性能] 操作耗时: {elapsed:.2f}秒")
```

### 3. 异常捕获日志

```python
try:
    result = some_operation()
    log.info("操作成功")
except Exception as e:
    log.error(f"操作失败: {e}", exc_info=True)  # exc_info=True 输出堆栈
```

## 🔍 日志查看技巧

### Windows PowerShell

```powershell
# 查看最后50行
Get-Content logs/web_server.log -Tail 50

# 实时监控日志
Get-Content logs/web_server.log -Wait -Tail 20

# 搜索错误日志
Select-String -Path logs/*.log -Pattern "ERROR"

# 查看特定时间段
Select-String -Path logs/web_server.log -Pattern "2026-02-09 12:"
```

### Linux/Mac

```bash
# 查看最后50行
tail -n 50 logs/web_server.log

# 实时监控
tail -f logs/web_server.log

# 搜索错误
grep "ERROR" logs/*.log

# 查看性能日志
grep "\\[性能\\]" logs/FundValuationAPI.log
```

## 📈 日志分析

### 性能分析

```python
# 查找耗时操作
import re

with open('logs/FundValuationAPI.log', 'r', encoding='utf-8') as f:
    for line in f:
        if '[性能]' in line:
            match = re.search(r'(\d+\.\d+)秒', line)
            if match and float(match.group(1)) > 1.0:
                print(line)  # 输出耗时>1秒的操作
```

### 错误统计

```python
from collections import Counter

error_types = Counter()
with open('logs/web_server.log', 'r', encoding='utf-8') as f:
    for line in f:
        if 'ERROR' in line:
            # 提取错误类型
            if ':' in line:
                error_msg = line.split('ERROR')[1].split(':')[0]
                error_types[error_msg.strip()] += 1

print(error_types.most_common(5))  # 前5种错误
```

## 🔄 依赖关系

```
Logger
  └── logging (Python内置)
```

## ⚙️ 配置选项

```python
# 自定义日志格式
custom_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logger = Logger('logs/app.log', level='debug', format=custom_format)

# 只输出到文件（不输出到控制台）
logger = Logger('logs/app.log', console=False)

# 日志文件大小限制（轮转）
from logging.handlers import RotatingFileHandler
handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5           # 保留5个备份
)
```

## 📝 注意事项

1. **日志目录**：确保 `logs/` 目录存在或可创建
2. **磁盘空间**：定期清理旧日志文件
3. **敏感信息**：不要记录密码、密钥等敏感数据
4. **日志级别**：生产环境建议使用 `INFO` 级别
5. **性能影响**：大量 `DEBUG` 日志会影响性能
