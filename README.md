# 基金估值与K线监控系统

一个基于Flask的Web应用，提供基金实时估值监控和股票K线图查询功能。

## 📁 项目结构

```
基金估值K线监控系统/
├── api/                    # API核心模块
│   ├── __init__.py
│   ├── FundValuationAPI.py # 基金估值API
│   └── KLineAPI.py         # K线图API
├── config/                 # 配置文件
│   └── test_config.json
├── data/                   # 数据文件
│   ├── zs_fund_online.json # 基金持仓数据
│   ├── zs_online.json      # 股票指数配置
│   └── *.htm               # HTML原始数据
├── docs/                   # 文档
│   ├── 基金估值快速开始.md
│   ├── 基金实时估值功能说明.md
│   ├── Web界面使用说明.md
│   └── 修改说明.txt
├── logs/                   # 日志文件
│   └── FundValuationAPI.log
├── scripts/                # 脚本工具
│   ├── txt2str.py          # 文件转换工具
│   ├── zs_fund_online.py   # 基金数据脚本
│   ├── zs_online.py        # 股票数据脚本
│   └── 启动服务器.bat      # Windows启动脚本
├── templates/              # 前端模板
│   ├── monitor.html        # 监控主页面
│   └── admin.html          # 管理页面
├── tests/                  # 测试文件
│   └── test_fund_config.py
├── utils/                  # 工具模块
│   ├── __init__.py
│   └── Logger.py           # 日志工具
├── web_server.py           # Web服务器主入口
├── 启动服务器.bat          # 快速启动脚本
└── README.md               # 项目说明文档
```

## 🚀 快速开始

### 1. 环境要求
- Python 3.7+
- Flask
- requests
- chardet

### 2. 安装依赖
```bash
pip install flask requests chardet
```

### 3. 启动服务
**方式一：使用启动脚本（推荐）**
```bash
双击 启动服务器.bat
```

**方式二：命令行启动**
```bash
python web_server.py
```

### 4. 访问系统
启动后自动打开浏览器访问：http://localhost:5000

## ✨ 主要功能

### 1️⃣ 基金实时估值监控
- 🔄 基于前十大重仓股实时行情计算基金估值
- 📊 显示基金净值、估值、涨跌幅等关键指标
- 💰 支持用户持仓金额录入，自动计算单日盈亏
- ⚡ 5分钟自动刷新，保持数据实时性
- 🎯 持仓占比自动验证（超过100%警告）

### 2️⃣ 基金管理
- ➕ 添加基金（预览-确认机制）
  - 输入基金代码后先预览前十重仓股
  - 确认无误后再正式添加到监控列表
- 🔍 查看基金持仓详情
- ❌ 移除基金
- 📝 编辑持仓金额和持仓股票

### 3️⃣ K线图查询
- 📈 支持股票/指数K线图查询
- 🎨 多种时间周期（日K、周K、月K等）
- 🔧 自定义图表参数（MA均线、是否复权等）

### 4️⃣ 持仓管理
- 📊 查看和编辑基金前十重仓股
- 🔄 联网更新持仓数据
- ⚠️ 持仓比例验证和警告提示

## 📖 详细文档

- [基金估值快速开始](docs/基金估值快速开始.md)
- [基金实时估值功能说明](docs/基金实时估值功能说明.md)
- [Web界面使用说明](docs/Web界面使用说明.md)
- [修改说明](docs/修改说明.txt)

## 🔧 配置说明

### 基金配置文件：`data/zs_fund_online.json`
```json
{
  "fund_list": ["001593", "015752"],
  "user_positions": {
    "001593": 10000,
    "015752": 5000
  },
  "001593": {
    "holdings": [...],
    "update_time": "2026-02-08 10:00:00"
  }
}
```

### 股票指数配置：`data/zs_online.json`
```json
{
  "指数列表": [
    {"名称": "上证指数", "代码": "1.000001"},
    {"名称": "深证成指", "代码": "0.399001"}
  ]
}
```

## 📝 API说明

### 基金相关API
- `GET /api/fund/list` - 获取基金监控列表
- `GET /api/fund/preview/<fund_code>` - 预览基金持仓
- `GET /api/fund/holdings/<fund_code>` - 获取基金持仓
- `POST /api/fund/add` - 添加基金
- `DELETE /api/fund/remove/<fund_code>` - 移除基金
- `POST /api/fund/update_holdings` - 更新基金持仓
- `POST /api/fund/update_position` - 更新持仓金额

### 估值相关API
- `GET /api/valuation/batch` - 批量计算基金估值
- `GET /api/valuation/<fund_code>` - 单个基金估值

### K线相关API
- `POST /api/kline/url` - 生成K线图URL

## 🎯 核心特性

### 1. 预览-确认添加机制
添加基金时先展示前十重仓股信息，用户确认后再正式添加，避免错误添加。

### 2. 并发性能优化
使用ThreadPoolExecutor并发获取股票行情，5线程并发处理，性能提升5倍。

### 3. 数据缓存策略
- 优先使用本地缓存的持仓数据
- 支持手动刷新强制联网更新
- 自动记录更新时间

### 4. 数据验证
- 基金代码格式验证（6位数字）
- 持仓比例总和验证（超过100%警告）
- 联网验证基金是否存在

### 5. 系统健壮性增强
- **统一错误处理**：自定义异常类（APIError、DatabaseError等）和全局异常处理器
- **API速率限制**：智能限流保护外部API，防止请求过载
- **全面测试覆盖**：25个单元测试覆盖核心功能，确保代码质量

## 🔒 数据来源

- **基金数据**：天天基金网 (fundgz.1234567.com.cn)
- **持仓数据**：东方财富网 (fundf10.eastmoney.com)
- **股票行情**：东方财富网 (push2.eastmoney.com)
- **K线图**：东方财富网 (webquoteklinepic.eastmoney.com)

## 📌 注意事项

1. 基金估值仅基于前十大重仓股计算，可能与实际净值有偏差
2. 数据更新有延迟，仅供参考，不构成投资建议
3. 持仓数据来源于基金定期报告，可能不是最新持仓
4. 单日盈亏计算基于估值变化，非实际交易盈亏

## 📄 许可证

本项目仅供学习交流使用。

## 👨‍💻 开发者

基于项目需求开发，持续优化中。

---

**最后更新**: 2026-02-10
