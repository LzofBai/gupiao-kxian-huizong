# -*- coding: utf-8 -*-
"""
数据迁移脚本：JSON → SQLite
将现有JSON配置文件中的基金数据迁移到SQLite数据库
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.FundDatabase import FundDatabase
from utils.Logger import Logger

log = Logger('logs/migration.log', level='info').logger


def migrate_json_to_sqlite(json_file: str = 'data/zs_fund_online.json', 
                           db_file: str = 'data/funds.db',
                           backup: bool = True):
    """
    执行数据迁移
    
    Args:
        json_file: 源JSON文件路径
        db_file: 目标数据库文件路径
        backup: 是否备份原JSON文件
    """
    print("=" * 60)
    print("📊 基金数据迁移工具 - JSON → SQLite")
    print("=" * 60)
    
    # 1. 检查JSON文件
    if not os.path.exists(json_file):
        print(f"❌ JSON文件不存在: {json_file}")
        return False
    
    print(f"\n✓ 找到JSON文件: {json_file}")
    
    # 2. 备份JSON文件
    if backup:
        backup_file = f"{json_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            import shutil
            shutil.copy2(json_file, backup_file)
            print(f"✓ 已备份JSON文件: {backup_file}")
        except Exception as e:
            print(f"⚠️  JSON备份失败: {e}")
    
    # 3. 读取JSON数据
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        print(f"✓ 读取JSON数据成功")
    except Exception as e:
        print(f"❌ 读取JSON失败: {e}")
        return False
    
    # 4. 统计JSON数据
    fund_list = json_data.get('fund_list', [])
    fund_holdings = json_data.get('fund_holdings', {})
    user_positions = json_data.get('user_positions', {})
    
    print(f"\n📈 JSON数据统计:")
    print(f"   - 基金总数: {len(fund_list)}")
    print(f"   - 持仓数据: {len(fund_holdings)} 个基金")
    print(f"   - 用户持仓: {len(user_positions)} 个基金")
    
    # 计算持仓记录总数
    total_holdings = sum(len(h.get('holdings', [])) for h in fund_holdings.values())
    print(f"   - 持仓记录: {total_holdings} 条")
    
    # 5. 初始化数据库
    print(f"\n📦 初始化SQLite数据库...")
    db = FundDatabase(db_file)
    
    # 检查数据库是否已有数据
    existing_count = db.get_fund_count()
    if existing_count > 0:
        print(f"\n⚠️  数据库中已存在 {existing_count} 个基金")
        response = input("是否继续导入？现有数据将被覆盖 (y/n): ")
        if response.lower() != 'y':
            print("❌ 取消导入")
            return False
    
    # 6. 执行迁移
    print(f"\n🔄 开始迁移数据...")
    fund_count, holding_count = db.import_from_json(json_data)
    
    print(f"\n✅ 迁移完成!")
    print(f"   - 成功导入基金: {fund_count} 个")
    print(f"   - 成功导入持仓记录: {holding_count} 条")
    
    # 7. 验证数据
    print(f"\n🔍 验证数据...")
    db_fund_count = db.get_fund_count()
    db_holdings = db.get_all_holdings()
    db_holding_count = sum(len(h) for h in db_holdings.values())
    
    print(f"   - 数据库基金数: {db_fund_count}")
    print(f"   - 数据库持仓记录数: {db_holding_count}")
    
    if db_fund_count == len(fund_list) and db_holding_count == total_holdings:
        print(f"✅ 数据验证通过")
    else:
        print(f"⚠️  数据可能不完整，请检查日志")
    
    # 8. 创建UI配置文件（只保留UI相关配置）
    ui_config_file = json_file.replace('.json', '_ui.json')
    ui_config = {
        'zs_all': json_data.get('zs_all', {}),
        'type_all': json_data.get('type_all', ['D', 'W', 'M']),
        'last_migration': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    try:
        with open(ui_config_file, 'w', encoding='utf-8') as f:
            json.dump(ui_config, f, ensure_ascii=False, indent=2)
        print(f"\n✓ UI配置文件已创建: {ui_config_file}")
    except Exception as e:
        print(f"⚠️  UI配置文件创建失败: {e}")
    
    # 9. 数据库优化
    print(f"\n🔧 优化数据库...")
    db.vacuum()
    
    print("\n" + "=" * 60)
    print("✅ 迁移成功！数据库已就绪")
    print("=" * 60)
    print(f"\n💡 提示:")
    print(f"   - 数据库文件: {db_file}")
    print(f"   - UI配置文件: {ui_config_file}")
    print(f"   - 原JSON文件已备份")
    print(f"   - 可以删除原JSON文件: {json_file}")
    
    return True


def rollback_migration(json_file: str = 'data/zs_fund_online.json',
                       db_file: str = 'data/funds.db'):
    """
    回滚迁移：从数据库导出到JSON
    
    Args:
        json_file: 目标JSON文件路径
        db_file: 源数据库文件路径
    """
    print("=" * 60)
    print("🔄 回滚迁移 - SQLite → JSON")
    print("=" * 60)
    
    if not os.path.exists(db_file):
        print(f"❌ 数据库文件不存在: {db_file}")
        return False
    
    # 读取UI配置
    ui_config_file = json_file.replace('.json', '_ui.json')
    ui_config = {}
    if os.path.exists(ui_config_file):
        with open(ui_config_file, 'r', encoding='utf-8') as f:
            ui_config = json.load(f)
    
    # 从数据库导出
    db = FundDatabase(db_file)
    json_data = db.export_to_json()
    
    # 合并UI配置
    json_data.update({
        'zs_all': ui_config.get('zs_all', {}),
        'type_all': ui_config.get('type_all', ['D', 'W', 'M'])
    })
    
    # 保存JSON
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 回滚完成: {json_file}")
    return True


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='基金数据迁移工具')
    parser.add_argument('--action', choices=['migrate', 'rollback'], default='migrate',
                       help='操作类型：migrate(迁移到SQLite) 或 rollback(回滚到JSON)')
    parser.add_argument('--json', default='data/zs_fund_online.json',
                       help='JSON文件路径')
    parser.add_argument('--db', default='data/funds.db',
                       help='数据库文件路径')
    parser.add_argument('--no-backup', action='store_true',
                       help='不备份原JSON文件')
    
    args = parser.parse_args()
    
    if args.action == 'migrate':
        migrate_json_to_sqlite(args.json, args.db, not args.no_backup)
    else:
        rollback_migration(args.json, args.db)
