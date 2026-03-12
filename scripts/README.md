# Scripts 模块说明

## 📦 模块功能

脚本模块包含各种维护工具和自动化脚本，用于数据迁移、备份、测试等任务。

## 📁 文件结构

```
scripts/
├── migrate_to_sqlite.py        # JSON到SQLite数据迁移工具
├── backup_database.py          # 数据库备份脚本（待实现）
├── test_api.py                 # API测试脚本（待实现）
└── README.md                   # 本文档
```

## 🔧 核心脚本

### 1. migrate_to_sqlite.py

**功能**：将JSON配置文件中的基金数据迁移到SQLite数据库

#### 使用方法

```bash
# 执行迁移（会自动备份原JSON）
python scripts/migrate_to_sqlite.py --action migrate

# 导出数据为JSON
python scripts/migrate_to_sqlite.py --action export --output backup.json

# 查看数据库统计
python scripts/migrate_to_sqlite.py --action stats
```

#### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--action` | 操作类型（migrate/export/stats） | migrate |
| `--json-file` | 源JSON文件路径 | data/zs_fund_online.json |
| `--db-file` | 目标数据库路径 | data/funds.db |
| `--output` | 导出文件路径（export时使用） | - |
| `--backup` | 是否备份原JSON | True |

#### 迁移流程

```
1. 检查源JSON文件 ✓
   └─ 验证文件存在性和格式

2. 备份原JSON文件 ✓
   └─ 创建 zs_fund_online.json.backup_YYYYMMDD_HHMMSS

3. 初始化SQLite数据库 ✓
   └─ 创建 funds 和 fund_holdings 表

4. 迁移数据 ✓
   ├─ 迁移基金列表到 funds 表
   ├─ 迁移用户持仓金额
   └─ 迁移持仓明细到 fund_holdings 表

5. 创建UI配置文件 ✓
   └─ 保留K线设置到 zs_fund_online_ui.json

6. 验证数据完整性 ✓
   └─ 对比迁移前后数据
```

#### 输出示例

```
============================================================
📊 基金数据迁移工具 - JSON → SQLite
============================================================

1️⃣ 检查源文件
   ✓ 源文件存在: data/zs_fund_online.json

2️⃣ 备份原文件
   ✓ 备份完成: data/zs_fund_online.json.backup_20260209_120000

3️⃣ 初始化数据库
   ✓ 数据库初始化完成: data/funds.db

4️⃣ 迁移数据
   ✓ 迁移 5 个基金
   ✓ 迁移 212 条持仓记录

5️⃣ 创建UI配置
   ✓ UI配置保存: data/zs_fund_online_ui.json

6️⃣ 验证数据
   ✓ 数据完整性验证通过

============================================================
✅ 迁移完成！
============================================================
```

#### 回滚方案

如果迁移出现问题，可以恢复备份：

```bash
# 找到备份文件
ls data/*.backup_*

# 恢复备份
copy data/zs_fund_online.json.backup_XXXXXXXX data/zs_fund_online.json
```

### 2. backup_database.py（规划中）

**功能**：定期备份数据库

计划功能：
```bash
# 手动备份
python scripts/backup_database.py

# 自动备份（定时任务）
python scripts/backup_database.py --schedule daily

# 清理旧备份
python scripts/backup_database.py --cleanup --keep 7
```

### 3. test_api.py（规划中）

**功能**：API接口测试

计划功能：
```bash
# 测试基金估值API
python scripts/test_api.py --test valuation

# 测试K线API
python scripts/test_api.py --test kline

# 全部测试
python scripts/test_api.py --all
```

## 🔄 数据迁移详解

### 迁移前后对比

**迁移前（JSON）**：
```json
{
  "fund_list": ["025209", "015916"],
  "user_positions": {
    "025209": 0,
    "015916": 0
  },
  "fund_holdings": {
    "025209": {
      "holdings": [
        {"股票代码": "001309", "股票名称": "德明利", "持仓比例": 11.44}
      ]
    }
  }
}
```

**迁移后（SQLite）**：

**funds 表**：
| fund_code | fund_name | user_position | created_at | updated_at |
|-----------|-----------|---------------|------------|------------|
| 025209 | | 0.0 | 2026-02-09 12:00:00 | 2026-02-09 12:00:00 |
| 015916 | | 0.0 | 2026-02-09 12:00:00 | 2026-02-09 12:00:00 |

**fund_holdings 表**：
| id | fund_code | stock_code | stock_name | holding_ratio | created_at |
|----|-----------|------------|------------|---------------|------------|
| 1 | 025209 | 001309 | 德明利 | 11.44 | 2026-02-09 12:00:00 |

### UI配置分离

迁移后，UI相关配置（K线设置、显示选项等）保存在独立的JSON文件中：

**zs_fund_online_ui.json**：
```json
{
  "kline_settings": {
    "default_period": "day",
    "show_ma": true
  },
  "display_options": {
    "auto_refresh": true,
    "refresh_interval": 60
  }
}
```

## 📊 数据完整性验证

迁移工具会自动验证：

1. **基金数量一致性**：JSON中的基金数 = 数据库中的基金数
2. **持仓记录数一致性**：JSON中的持仓记录数 = 数据库中的持仓记录数
3. **持仓金额一致性**：JSON中的user_positions = 数据库中的user_position
4. **持仓比例一致性**：随机抽样验证持仓比例是否匹配

## 🛠️ 维护脚本示例

### 定期备份脚本

```python
# backup_schedule.py
from database.FundDatabase import FundDatabase
from datetime import datetime
import os

def daily_backup():
    """每日备份"""
    db = FundDatabase()
    backup_dir = 'backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d')
    backup_file = f'{backup_dir}/funds_{timestamp}.db'
    
    if db.backup(backup_file):
        print(f"✓ 备份完成: {backup_file}")
    else:
        print("✗ 备份失败")

if __name__ == '__main__':
    daily_backup()
```

### 数据清理脚本

```python
# cleanup_old_logs.py
import os
import time
from datetime import datetime, timedelta

def cleanup_old_logs(days=30):
    """删除30天前的日志"""
    log_dir = 'logs'
    cutoff = time.time() - (days * 86400)
    
    for filename in os.listdir(log_dir):
        filepath = os.path.join(log_dir, filename)
        if os.path.isfile(filepath):
            if os.path.getmtime(filepath) < cutoff:
                os.remove(filepath)
                print(f"✓ 删除旧日志: {filename}")

if __name__ == '__main__':
    cleanup_old_logs()
```

## 📝 日志输出

迁移脚本日志：`logs/migration.log`

包含：
- 迁移过程详细记录
- 数据验证结果
- 错误和警告信息

## ⚠️ 注意事项

1. **迁移前备份**：脚本会自动备份，但建议手动再备份一次
2. **数据验证**：迁移后检查数据完整性
3. **测试环境**：建议先在测试环境验证迁移脚本
4. **磁盘空间**：确保有足够空间存储备份文件
5. **权限问题**：确保脚本有读写权限

## 🔗 依赖关系

```
migrate_to_sqlite.py
  ├── database.FundDatabase
  ├── utils.Logger
  └── json (内置)
```

## 📖 使用场景

### 场景1：首次迁移

```bash
# 1. 检查原JSON文件
cat data/zs_fund_online.json

# 2. 执行迁移
python scripts/migrate_to_sqlite.py --action migrate

# 3. 验证数据
python scripts/migrate_to_sqlite.py --action stats
```

### 场景2：导出备份

```bash
# 导出当前数据库为JSON格式
python scripts/migrate_to_sqlite.py --action export --output backup.json
```

### 场景3：灾难恢复

```bash
# 1. 从备份JSON恢复
python scripts/migrate_to_sqlite.py --action migrate --json-file backup.json

# 2. 验证恢复结果
python scripts/migrate_to_sqlite.py --action stats
```
