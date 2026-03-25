# funds.db 数据库说明文档

## 基本信息
所有基金信息、笔记等均保存在该文件下，为Sql数据库文件。
| 项目 | 说明 |
|------|------|
| 文件名称 | `funds.db` |
| 数据库类型 | SQLite3 |
| 用途 | 存储基金监控系统的核心数据 |
| 关联模块 | `database/FundDatabase.py` |

## 数据库结构

### 1. funds（基金表）

存储用户监控的基金列表及持仓金额信息。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| fund_code | TEXT | PRIMARY KEY | 基金代码（唯一标识） |
| fund_name | TEXT | - | 基金名称 |
| user_position | REAL | DEFAULT 0 | 用户持仓金额（元） |
| added_time | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 添加时间 |
| updated_time | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 最后更新时间 |

### 2. fund_holdings（持仓表）

存储各基金的重仓股票信息。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 自增主键 |
| fund_code | TEXT | NOT NULL | 基金代码（外键） |
| stock_code | TEXT | NOT NULL | 股票代码 |
| stock_name | TEXT | - | 股票名称 |
| position_ratio | REAL | NOT NULL | 持仓比例（%） |
| update_time | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

**约束说明：**
- 外键约束：`fund_code` 关联 `funds.fund_code`，删除基金时级联删除持仓记录
- 唯一约束：`(fund_code, stock_code)` 组合唯一

### 3. daily_notes（每日笔记表）

存储用户的每日投资笔记（富文本格式）。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | TEXT | PRIMARY KEY | 笔记唯一ID |
| note_date | TEXT | NOT NULL | 日期（YYYY-MM-DD格式） |
| content | TEXT | - | 笔记内容（富文本HTML） |
| create_time | INTEGER | - | 创建时间戳（毫秒） |
| update_time | INTEGER | - | 更新时间戳（毫秒） |

## 索引列表

| 索引名称 | 所属表 | 字段 | 说明 |
|----------|--------|------|------|
| idx_holdings_fund | fund_holdings | fund_code | 加速按基金查询持仓 |
| idx_holdings_stock | fund_holdings | stock_code | 加速按股票查询持仓 |
| idx_notes_date | daily_notes | note_date | 加速按日期查询笔记 |
| idx_notes_update_time | daily_notes | update_time DESC | 加速按时间排序笔记 |

## 数据关系图

```
┌─────────────────┐         ┌─────────────────────┐
│     funds       │         │   fund_holdings     │
├─────────────────┤         ├─────────────────────┤
│ PK fund_code    │◄────────┤ FK fund_code        │
│    fund_name    │   1:N   │    stock_code       │
│    user_position│         │    stock_name       │
│    added_time   │         │    position_ratio   │
│    updated_time │         │    update_time      │
└─────────────────┘         └─────────────────────┘

┌─────────────────────┐
│    daily_notes      │
├─────────────────────┤
│ PK id               │
│    note_date        │
│    content          │
│    create_time      │
│    update_time      │
└─────────────────────┘
```

## 使用说明

### 数据导入导出

数据库支持通过 `FundDatabase` 类进行 JSON 格式的数据导入导出：

```python
from database.FundDatabase import FundDatabase

# 初始化数据库
db = FundDatabase('data/funds.db')

# 导出为JSON（备份）
data = db.export_to_json()

# 从JSON导入
db.import_from_json(json_data)
```

### 备份建议

建议定期备份数据库文件：

```python
# 使用内置备份方法
db.backup('backup/funds_backup.db')

# 或直接复制文件
import shutil
shutil.copy2('data/funds.db', 'backup/funds_backup.db')
```

### 数据库维护

```python
# 优化数据库（释放空间）
db.vacuum()
```

## 注意事项

1. **文件位置**：数据库文件应存放在 `data/` 目录下
2. **并发访问**：SQLite 支持多进程读取，但写入时会锁定数据库
3. **数据完整性**：外键约束已启用，删除基金会自动删除关联的持仓记录
4. **编码格式**：所有文本字段使用 UTF-8 编码

## 更新记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0 | - | 初始版本，包含 funds 和 fund_holdings 表 |
| 1.1 | - | 新增 daily_notes 每日笔记表 |
