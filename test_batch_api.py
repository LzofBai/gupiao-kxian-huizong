#!/usr/bin/env python3
"""
测试批量股票行情API和估值计算优化
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.FundValuationAPI import FundValuationAPI

def test_batch_api():
    """测试批量股票行情API"""
    print("=== 测试批量股票行情API ===")
    
    api = FundValuationAPI()
    
    # 测试股票列表（常用股票）
    test_stocks = ['600519', '000858', '000333', '300750', '002415']
    print(f"测试 {len(test_stocks)} 只股票: {test_stocks}")
    
    # 单线程逐个获取（旧方法模拟）
    print("\n1. 单线程逐个获取（模拟旧方法）:")
    start = time.time()
    single_results = {}
    for stock in test_stocks:
        quote = api.get_stock_realtime_quote(stock, retry_count=1, delay=0)
        if quote:
            single_results[stock] = quote
    single_time = time.time() - start
    print(f"   耗时: {single_time:.3f}秒，成功: {len(single_results)}/{len(test_stocks)}")
    
    # 批量获取（新方法）
    print("\n2. 批量获取（新方法）:")
    start = time.time()
    batch_results = api.get_batch_stock_quotes(test_stocks)
    batch_time = time.time() - start
    print(f"   耗时: {batch_time:.3f}秒，成功: {len(batch_results)}/{len(test_stocks)}")
    
    # 数据一致性检查
    print("\n3. 数据一致性检查:")
    all_good = True
    for stock in test_stocks:
        if stock in single_results and stock in batch_results:
            single = single_results[stock]
            batch = batch_results[stock]
            
            # 比较关键字段
            fields_to_compare = ['股票代码', '最新价', '涨跌幅']
            for field in fields_to_compare:
                s_val = single.get(field)
                b_val = batch.get(field)
                
                if isinstance(s_val, float) and isinstance(b_val, float):
                    if abs(s_val - b_val) > 0.01:  # 允许微小差异
                        print(f"   {stock} {field} 不一致: 单={s_val:.3f}, 批={b_val:.3f}")
                        all_good = False
                elif s_val != b_val:
                    print(f"   {stock} {field} 不一致: 单={s_val}, 批={b_val}")
                    all_good = False
    
    if all_good:
        print("   [OK] 数据一致")
    
    # 性能对比
    print("\n4. 性能对比:")
    if batch_time > 0 and single_time > 0:
        improvement = (single_time - batch_time) / single_time * 100
        print(f"   批量接口比单线程快 {improvement:.1f}%")
        if improvement > 0:
            print("   [OK] 性能提升")
        else:
            print("   [WARN] 批量接口没有更快，可能因为网络或API限制")
    
    return len(batch_results) > 0

def test_fund_valuation():
    """测试基金估值计算（使用批量接口）"""
    print("\n=== 测试基金估值计算 ===")
    
    api = FundValuationAPI()
    
    # 测试基金（使用数据库中的基金）
    test_funds = ['025209', '001593']
    
    for fund_code in test_funds:
        print(f"\n测试基金 {fund_code}:")
        
        try:
            start = time.time()
            result = api.calculate_fund_valuation(fund_code)
            elapsed = time.time() - start
            
            if result:
                print(f"  成功: {result.get('基金名称', fund_code)}")
                print(f"  估算涨跌幅: {result.get('估算涨跌幅', 'N/A')}%")
                print(f"  持仓股票数: {result.get('重仓股数量', 0)}")
                print(f"  总耗时: {elapsed:.2f}秒")
                
                # 检查是否使用了缓存
                if elapsed < 0.5:
                    print("  [CACHE] 可能使用了缓存（5分钟TTL）")
            else:
                print(f"  失败: 无法计算估值")
                return False
                
        except Exception as e:
            print(f"  异常: {e}")
            return False
    
    return True

def main():
    print("[TEST] 开始批量API优化测试")
    print("=" * 60)
    
    test1 = test_batch_api()
    test2 = test_fund_valuation()
    
    print("\n" + "=" * 60)
    print("[RESULT] 测试结果:")
    print(f"  批量API测试: {'通过' if test1 else '失败'}")
    print(f"  基金估值测试: {'通过' if test2 else '失败'}")
    
    if test1 and test2:
        print("\n[SUCCESS] 批量API优化测试通过！")
        return 0
    else:
        print("\n[FAIL] 测试失败")
        return 1

if __name__ == '__main__':
    sys.exit(main())