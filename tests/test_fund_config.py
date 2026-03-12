# -*- coding: utf-8 -*-
"""
测试基金估值配置文件功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from api.FundValuationAPI import FundValuationAPI
import json

print("="*60)
print("测试基金估值配置文件功能")
print("="*60)

# 测试1: 首次运行，从网络获取持仓
print("\n测试1: 首次运行（将从网络获取持仓）")
api = FundValuationAPI(config_file='test_config.json')
result = api.calculate_fund_valuation('001593')

if result:
    print(f"[OK] 基金: {result['基金名称']}")
    print(f"[OK] 估值: {result['估算净值']:.4f} ({result['估算涨跌幅']:+.2f}%)")
    print(f"[OK] 重仓股: {result['重仓股数量']}只")
else:
    print("[ERROR] 估值计算失败")

# 测试2: 查看配置文件
print("\n测试2: 查看配置文件中的持仓信息")
try:
    with open('test_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
        if 'fund_holdings' in config and '001593' in config['fund_holdings']:
            holdings = config['fund_holdings']['001593']
            print(f"[OK] 配置文件中已保存持仓信息")
            print(f"[OK] 更新时间: {holdings['update_time']}")
            print(f"[OK] 持仓数量: {len(holdings['holdings'])}只")
            print("\n前3只持仓:")
            for i, stock in enumerate(holdings['holdings'][:3], 1):
                print(f"  {i}. {stock['股票名称']}({stock['股票代码']}) - {stock['持仓比例']:.2f}%")
        else:
            print("[ERROR] 配置文件中没有持仓信息")
except Exception as e:
    print(f"[ERROR] 读取配置文件失败: {e}")

# 测试3: 第二次运行，从配置文件读取
print("\n测试3: 第二次运行（将从配置文件读取持仓）")
api2 = FundValuationAPI(config_file='test_config.json')
result2 = api2.calculate_fund_valuation('001593')

if result2:
    print(f"[OK] 基金: {result2['基金名称']}")
    print(f"[OK] 估值: {result2['估算净值']:.4f} ({result2['估算涨跌幅']:+.2f}%)")
    print("[OK] 成功从配置文件读取持仓")
else:
    print("[ERROR] 估值计算失败")

print("\n"+"="*60)
print("测试完成！")
print("="*60)
print("\n配置文件说明:")
print("- 配置文件: test_config.json")
print("- 持仓信息已保存在 fund_holdings 节点")
print("- 可手动编辑持仓比例，程序会优先使用配置中的数据")
print("- 如需强制从网络更新，删除对应基金的持仓信息即可")
