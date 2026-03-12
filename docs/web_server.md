# Web Server 模块说明

## 📦 模块功能

Web服务器模块是应用的核心入口，使用Flask框架提供REST API和页面服务。

## 📁 文件结构

```
项目根目录/
├── web_server.py                   # Web服务器主文件
├── templates/                      # HTML模板
├── api/                            # API模块
├── database/                       # 数据库模块
└── utils/                          # 工具模块
```

## 🚀 启动服务

### 方式1：直接启动

```bash
python web_server.py
```

### 方式2：使用批处理（Windows）

```bash
启动服务器.bat
```

### 启动信息

```
============================================================
📊 基金估值与K线监控系统
============================================================
🌐 访问地址: http://localhost:5000
🗃️ 数据库: data/funds.db
📋 UI配置: data/zs_fund_online_ui.json
⏰ 启动时间: 2026-02-09 12:00:00

按 Ctrl+C 停止服务
============================================================
```

## 🔌 API 接口

### 1. 页面路由

#### GET /

**功能**：主页面，显示基金估值和K线图

**返回**：HTML页面（monitor.html）

**模板变量**：
- `fund_list`：基金代码列表
- `user_positions`：用户持仓金额字典

---

#### GET /admin

**功能**：管理页面，基金添加/删除

**返回**：HTML页面（admin.html）

**模板变量**：
- `fund_list`：基金代码列表

---

### 2. 基金管理 API

#### POST /api/fund/add

**功能**：添加新基金到监控列表

**请求体**：
```json
{
  "fund_code": "025209"
}
```

**响应**：
```json
{
  "success": true,
  "message": "基金添加成功",
  "fund_code": "025209",
  "holdings_count": 10
}
```

**错误响应**：
```json
{
  "success": false,
  "error": "基金代码格式错误"
}
```

---

#### POST /api/fund/remove

**功能**：从监控列表删除基金

**请求体**：
```json
{
  "fund_code": "025209"
}
```

**响应**：
```json
{
  "success": true,
  "message": "基金删除成功"
}
```

---

#### GET /api/funds

**功能**：获取所有监控的基金列表

**响应**：
```json
{
  "success": true,
  "data": [
    {
      "fund_code": "025209",
      "fund_name": "永赢先锋半导体智选混合发起C",
      "user_position": 0.0
    }
  ]
}
```

---

### 3. 估值计算 API

#### GET /api/fund/valuation/<fund_code>

**功能**：计算单个基金的实时估值

**参数**：
- `fund_code`：基金代码（路径参数）

**响应**：
```json
{
  "success": true,
  "data": {
    "基金代码": "025209",
    "基金名称": "永赢先锋半导体智选混合发起C",
    "单位净值": 1.6270,
    "估值涨跌幅": 1.52,
    "持仓比例合计": 79.32,
    "股票明细": [
      {
        "股票代码": "001309",
        "股票名称": "德明利",
        "持仓比例": 11.44,
        "最新价": 45.20,
        "涨跌幅": 2.5
      }
    ]
  },
  "elapsed_time": 0.61
}
```

---

#### POST /api/fund/valuation/batch

**功能**：批量计算多个基金的估值

**请求体**：
```json
{
  "fund_codes": ["025209", "015916"]
}
```

**响应**：
```json
{
  "success": true,
  "data": [
    {
      "基金代码": "025209",
      "估值涨跌幅": 1.52,
      ...
    }
  ],
  "total_position": 0.0,
  "elapsed_time": 1.25,
  "avg_time_per_fund": 0.63
}
```

---

#### GET /api/fund/valuations

**功能**：获取所有基金的估值（不需要请求体）

**响应**：同批量计算API

---

### 4. 持仓管理 API

#### GET /api/fund/holdings/<fund_code>

**功能**：获取基金的前十大重仓股

**响应**：
```json
{
  "success": true,
  "data": {
    "fund_code": "025209",
    "holdings": [
      {
        "股票代码": "001309",
        "股票名称": "德明利",
        "持仓比例": 11.44
      }
    ],
    "total_ratio": 79.32
  }
}
```

---

#### POST /api/fund/position/update

**功能**：更新用户持仓金额

**请求体**：
```json
{
  "fund_code": "025209",
  "position": 10000.0
}
```

**响应**：
```json
{
  "success": true,
  "message": "持仓金额更新成功"
}
```

---

### 5. K线数据 API

#### GET /api/kline/<stock_code>/<period>

**功能**：获取股票K线数据

**参数**：
- `stock_code`：股票代码
- `period`：周期（day/week/month/min1/min5等）

**响应**：
```json
{
  "success": true,
  "data": {
    "dates": ["2026-02-01", "2026-02-02"],
    "kline": [
      [开盘, 收盘, 最低, 最高],
      [100.0, 102.0, 99.5, 103.0]
    ],
    "volumes": [1000000, 1200000],
    "ma5": [101.0, 101.5],
    "ma10": [100.5, 101.0]
  }
}
```

---

### 6. 配置管理 API

#### GET /api/config

**功能**：获取UI配置

**响应**：
```json
{
  "success": true,
  "data": {
    "kline_settings": {},
    "display_options": {}
  }
}
```

---

#### POST /api/config/save

**功能**：保存UI配置

**请求体**：
```json
{
  "kline_settings": {},
  "display_options": {}
}
```

---

## 🔐 错误处理

所有API遵循统一的错误响应格式：

```json
{
  "success": false,
  "error": "错误描述信息"
}
```

常见错误码：

| HTTP状态码 | 说明 |
|-----------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 📊 性能监控

所有API响应包含性能数据：

```json
{
  "success": true,
  "data": {...},
  "elapsed_time": 0.61,           // 总耗时（秒）
  "avg_time_per_fund": 0.31       // 平均耗时（批量时）
}
```

日志输出：
```
2026-02-09 12:00:00 - INFO - [性能] API层总耗时 [025209]: 0.61秒
2026-02-09 12:00:01 - INFO - [性能] 批量计算总耗时: 1.25秒, 平均每个: 0.63秒
```

## ⚙️ 配置说明

### 服务器配置

```python
# web_server.py

# 数据库路径
DB_FILE = 'data/funds.db'

# UI配置路径
UI_CONFIG_FILE = 'data/zs_fund_online_ui.json'

# 服务器启动配置
app.run(
    debug=True,          # 调试模式
    host='0.0.0.0',      # 监听所有IP
    port=5000            # 端口号
)
```

### 调试模式

**开发环境**（debug=True）：
- ✅ 代码修改自动重载
- ✅ 详细错误信息
- ✅ 开发工具条
- ⚠️ 性能较低

**生产环境**（debug=False）：
- ✅ 更高性能
- ✅ 错误页面简化
- ⚠️ 需手动重启

## 🔄 依赖关系

```
web_server.py
  ├── Flask                        # Web框架
  ├── api.FundValuationAPI         # 估值API
  ├── api.StockKlineAPI            # K线API
  ├── database.FundDatabase        # 数据库
  └── utils.Logger                 # 日志
```

## 📝 日志系统

日志文件：`logs/web_server.log`

**日志级别**：
- `INFO`：正常请求记录
- `WARNING`：异常但不影响运行
- `ERROR`：错误信息

**日志格式**：
```
2026-02-09 12:00:00 - logs/web_server.log - INFO - [性能] API层总耗时: 0.61秒
```

## 🔧 开发扩展

### 添加新API

```python
@app.route('/api/custom/endpoint', methods=['GET'])
def custom_api():
    """自定义API"""
    try:
        # 业务逻辑
        result = do_something()
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        log.error(f"API错误: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

### 添加中间件

```python
@app.before_request
def before_request():
    """请求前处理"""
    log.info(f"请求: {request.method} {request.path}")

@app.after_request
def after_request(response):
    """请求后处理"""
    log.info(f"响应: {response.status_code}")
    return response
```

## 🚀 部署建议

### 开发环境

```bash
python web_server.py
```

### 生产环境

使用 Gunicorn 或 uWSGI：

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动服务
gunicorn -w 4 -b 0.0.0.0:5000 web_server:app
```

参数说明：
- `-w 4`：4个工作进程
- `-b 0.0.0.0:5000`：监听地址和端口
- `web_server:app`：模块名:应用名

## 🔒 安全建议

1. **生产环境关闭调试模式**：`debug=False`
2. **使用环境变量存储敏感配置**
3. **添加请求限流**：防止API滥用
4. **启用HTTPS**：使用SSL证书
5. **输入验证**：严格验证用户输入

## 📊 监控指标

系统关键指标：

- **API响应时间**：<1秒
- **估值计算时间**：<0.6秒/基金
- **并发请求数**：建议<100
- **内存使用**：<500MB
- **CPU使用率**：<30%

## ⚠️ 注意事项

1. **端口占用**：确保5000端口未被占用
2. **数据库锁**：避免频繁的并发写操作
3. **日志文件**：定期清理旧日志
4. **API限流**：考虑添加请求频率限制
5. **错误处理**：所有API都应有try-except
