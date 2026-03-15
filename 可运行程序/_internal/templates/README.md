# Templates 模块说明

## 📦 模块功能

模板模块包含Web应用的前端页面，使用Jinja2模板引擎渲染HTML页面。

## 📁 文件结构

```
templates/
├── monitor.html                # 主页面 - 基金估值与K线监控
├── admin.html                  # 管理页面 - 基金添加/删除
└── README.md                   # 本文档
```

## 🎨 页面概览

### 1. monitor.html（主页面）

**功能**：基金实时估值监控 + 股票K线图展示

#### 页面布局

```
┌────────────────────────────────────────────────┐
│  📊 基金估值与K线监控系统                      │
├────────────────────────────────────────────────┤
│  [基金管理] [刷新] [自动刷新: ON]  [12:00:00] │
├────────────────────────────────────────────────┤
│  基金实时估值（基于前十大重仓股）              │
│  ┌──────────────────────────────────────────┐ │
│  │ 基金代码 | 涨跌幅 | 重仓股占比 | 持仓     │ │
│  │ 025209   | +1.5%  | 79.32%    | 编辑    │ │
│  │ 015916   | -0.8%  | 85.20%    | 编辑    │ │
│  └──────────────────────────────────────────┘ │
├────────────────────────────────────────────────┤
│  股票指数K线图                                  │
│  ┌──────────────────────────────────────────┐ │
│  │  [K线图1]  [K线图2]  [K线图3]            │ │
│  │  ┌────────────────────────────────────┐  │ │
│  │  │                                    │  │ │
│  │  │       K线图表（ECharts）           │  │ │
│  │  │                                    │  │ │
│  │  └────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────┘ │
└────────────────────────────────────────────────┘
```

#### 主要功能

**1. 基金实时估值表格**

显示列：
- 基金代码/名称
- 估值涨跌幅（红涨绿跌）
- 重仓股占比（<50%标红）
- 持仓金额（可编辑）
- 操作按钮（编辑、查看持仓）

特性：
- ✅ 实时计算估值
- ✅ 颜色标识（涨红跌绿）
- ✅ 低占比警示（<50%标红）
- ✅ 持仓编辑（双击或点击按钮）
- ✅ 查看重仓股明细

**2. 股票K线图**

功能：
- 多标签页展示不同股票
- ECharts图表渲染
- 支持多种周期（日K、周K、月K）
- 移动平均线（MA5、MA10、MA20、MA30）

交互：
- 缩放拖拽
- 数据提示（Tooltip）
- 图例控制

**3. 自动刷新**

- 默认60秒自动刷新
- 可手动开关
- 显示刷新时间和耗时

**4. 性能监控**

```javascript
PerformanceMonitor = {
    logFundRefreshTime(startTime, fundCount),
    logKlineLoadTime(startTime, klineCount)
}
```

显示：
- 基金刷新耗时
- K线加载耗时
- 刷新时间戳

#### 技术实现

**前端框架**：
- jQuery 3.6.0
- ECharts 5.4.0
- Bootstrap 4（样式）

**API调用**：
```javascript
// 批量获取基金估值
fetch('/api/fund/valuation/batch', {
    method: 'POST',
    body: JSON.stringify({fund_codes: [...]})
})

// 获取K线数据
fetch('/api/kline/stock_code/period')
```

**数据刷新**：
```javascript
setInterval(() => {
    if (autoRefreshEnabled) {
        loadFundData();
    }
}, 60000);  // 60秒
```

### 2. admin.html（管理页面）

**功能**：基金添加/删除、持仓预览

#### 页面布局

```
┌────────────────────────────────────────────────┐
│  ⚙️ 基金管理                                   │
├────────────────────────────────────────────────┤
│  添加基金                                       │
│  ┌──────────────────────────────────────────┐ │
│  │  基金代码: [______]  [预览]              │ │
│  │                                          │ │
│  │  预览信息：                               │ │
│  │  ┌────────────────────────────────────┐  │ │
│  │  │ 基金名称: xxx                       │  │ │
│  │  │ 前十大重仓股：                      │  │ │
│  │  │ 1. 600519 贵州茅台 10.5%            │  │ │
│  │  │ 2. 000858 五粮液 8.3%               │  │ │
│  │  │ ...                                │  │ │
│  │  │ 累计占比: 85.3%                     │  │ │
│  │  └────────────────────────────────────┘  │ │
│  │                                          │ │
│  │  [确认添加]  [取消]                      │ │
│  └──────────────────────────────────────────┘ │
├────────────────────────────────────────────────┤
│  当前监控基金                                   │
│  ┌──────────────────────────────────────────┐ │
│  │  025209 | 永赢先锋... | [删除]           │ │
│  │  015916 | 易方达...   | [删除]           │ │
│  └──────────────────────────────────────────┘ │
├────────────────────────────────────────────────┤
│  [返回主页]                                    │
└────────────────────────────────────────────────┘
```

#### 主要功能

**1. 基金添加（两步确认）**

流程：
```
输入基金代码 → 预览持仓 → 确认添加 → 更新列表
```

预览显示：
- 基金名称
- 前十大重仓股列表
- 累计持仓比例
- 数据时间

特性：
- ✅ 代码格式验证
- ✅ 重复添加检查
- ✅ 持仓数据预览
- ✅ 确认机制（防误操作）

**2. 基金删除**

流程：
```
点击删除 → 确认对话框 → 删除数据 → 更新列表
```

删除内容：
- 基金基本信息
- 持仓明细数据
- 用户持仓金额

**3. localStorage标记**

```javascript
// 添加/删除成功后标记
localStorage.setItem('fundListChanged', 'true');

// 主页检测并刷新
if (localStorage.getItem('fundListChanged') === 'true') {
    localStorage.removeItem('fundListChanged');
    location.reload();
}
```

#### 技术实现

**API调用**：
```javascript
// 获取持仓预览
fetch(`/api/fund/holdings/${fund_code}`)

// 添加基金
fetch('/api/fund/add', {
    method: 'POST',
    body: JSON.stringify({fund_code: '025209'})
})

// 删除基金
fetch('/api/fund/remove', {
    method: 'POST',
    body: JSON.stringify({fund_code: '025209'})
})
```

## 🎯 交互流程

### 基金估值查看流程

```
用户访问主页
    ↓
加载基金列表
    ↓
并发请求基金估值（批量）
    ↓
渲染表格（实时更新）
    ↓
自动刷新（60秒）
```

### 基金添加流程

```
用户输入基金代码
    ↓
点击"预览"按钮
    ↓
获取持仓数据
    ↓
显示预览信息
    ↓
用户确认
    ↓
调用添加API
    ↓
标记变更（localStorage）
    ↓
返回主页自动刷新
```

### 持仓编辑流程

```
用户点击"编辑"或双击金额
    ↓
弹出输入框
    ↓
用户输入新金额
    ↓
调用更新API
    ↓
更新本地显示
    ↓
保存到数据库
```

## 🎨 样式设计

### 颜色方案

- **涨幅正值**：`#e74c3c`（红色）
- **跌幅负值**：`#27ae60`（绿色）
- **警告标识**：`#e74c3c`（红色，持仓比例<50%）
- **主题色**：`#3498db`（蓝色）

### 响应式设计

```css
/* 大屏幕 */
@media (min-width: 1200px) {
    .fund-table { font-size: 16px; }
}

/* 中等屏幕 */
@media (min-width: 768px) and (max-width: 1199px) {
    .fund-table { font-size: 14px; }
}

/* 小屏幕 */
@media (max-width: 767px) {
    .fund-table { font-size: 12px; }
}
```

## 📊 性能优化

### 1. 批量请求

```javascript
// 不好的做法：逐个请求
funds.forEach(fund => {
    fetch(`/api/fund/valuation/${fund}`);  // N次请求
});

// 好的做法：批量请求
fetch('/api/fund/valuation/batch', {
    method: 'POST',
    body: JSON.stringify({fund_codes: funds})  // 1次请求
});
```

### 2. 缓存机制

```javascript
// K线数据缓存
const klineCache = {};
if (klineCache[stock_code]) {
    renderChart(klineCache[stock_code]);
} else {
    fetch(`/api/kline/${stock_code}`)
        .then(data => {
            klineCache[stock_code] = data;
            renderChart(data);
        });
}
```

### 3. 防抖和节流

```javascript
// 编辑持仓金额时防抖
let debounceTimer;
function updatePosition(fund_code, amount) {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        saveToServer(fund_code, amount);
    }, 500);  // 500ms后执行
}
```

## 🔗 依赖关系

```
Templates
  ├── jQuery 3.6.0
  ├── ECharts 5.4.0
  ├── Bootstrap 4 (CDN)
  └── Flask (Jinja2)
```

## ⚠️ 浏览器兼容性

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Edge 90+
- ✅ Safari 14+

## 📝 模板变量

### monitor.html

```jinja2
{{ fund_list }}         # 基金代码列表
{{ user_positions }}    # 用户持仓金额字典
```

### admin.html

```jinja2
{{ fund_list }}         # 基金代码列表
```

## 🛠️ 自定义开发

### 添加新功能示例

```javascript
// 在 monitor.html 中添加导出功能
function exportToExcel() {
    const data = getCurrentTableData();
    // 调用导出API
    fetch('/api/export', {
        method: 'POST',
        body: JSON.stringify(data)
    });
}
```

### 修改刷新间隔

```javascript
// 修改自动刷新间隔为30秒
setInterval(() => {
    if (autoRefreshEnabled) {
        loadFundData();
    }
}, 30000);  // 改为30秒
```
