# -*- coding: utf-8 -*-
"""
板块描述自动获取功能测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.txt2str import file2json
from utils.IndexDescription import (
    auto_fetch_missing_descriptions,
    get_index_description_from_eastmoney,
    fetch_index_info_from_eastmoney,
    generate_default_description,
    get_predefined_description,
    extract_pure_code
)
import json


def test_extract_pure_code():
    """测试代码提取函数"""
    print("=" * 60)
    print("测试1: 代码提取")
    print("=" * 60)
    
    test_cases = [
        ("1.000001", "000001"),
        ("90.BK0701", "BK0701"),
        ("0.399330", "399330"),
        ("2.931071", "931071"),
        ("ABC", "ABC"),
    ]
    
    for input_code, expected in test_cases:
        result = extract_pure_code(input_code)
        assert result == expected, f"提取失败: {input_code} -> {result}, 期望 {expected}"
        print(f"[OK] {input_code} -> {result}")
    
    print()


def test_predefined_descriptions():
    """测试预定义描述"""
    print("=" * 60)
    print("测试2: 预定义描述")
    print("=" * 60)
    
    test_codes = ["1.000698", "1.000001", "90.BK1036", "100.NDX"]
    
    for code in test_codes:
        desc = get_predefined_description(code)
        if desc:
            print(f"[OK] {code}: {desc[:50]}...")
        else:
            print(f"[INFO] {code}: 无预定义描述")
    
    print()


def test_default_generation():
    """测试默认描述生成"""
    print("=" * 60)
    print("测试3: 默认描述生成")
    print("=" * 60)
    
    test_cases = [
        ("1.999999", "测试板块"),
        ("2.888888", "新能源ETF"),
        ("0.123456", "芯片指数"),
    ]
    
    for code, name in test_cases:
        desc = generate_default_description(code, name)
        assert name in desc, f"默认描述应包含板块名称"
        print(f"[OK] {name}({code}): {desc}")
    
    print()


def test_online_fetch():
    """测试联网获取（可选，需要网络）"""
    print("=" * 60)
    print("测试4: 联网获取（可选）")
    print("=" * 60)
    
    # 测试几个常见板块
    test_cases = [
        ("1.000001", "上证指数"),
        ("1.000698", "科创100"),
    ]
    
    for code, name in test_cases:
        try:
            desc = get_index_description_from_eastmoney(code, name)
            if desc:
                print(f"[OK] {name}({code}): {desc[:60]}...")
            else:
                print(f"[INFO] {name}({code}): 无法从搜索API获取")
                
            # 尝试详细信息API
            info = fetch_index_info_from_eastmoney(code, name)
            if info:
                print(f"[OK] {name}({code}) 详细信息: {info}")
        except Exception as e:
            print(f"[WARN] {name}({code}) 获取失败: {e}")
    
    print()


def test_auto_fetch():
    """测试自动获取功能"""
    print("=" * 60)
    print("测试5: 自动获取功能")
    print("=" * 60)
    
    config_file = 'data/zs_fund_online_ui.json'
    
    # 加载现有配置
    config = file2json(config_file)
    zs_all = config.get('zs_all', {})
    existing_desc = config.get('zs_descriptions', {})
    
    print(f"当前板块数量: {len(zs_all)}")
    print(f"当前描述数量: {len(existing_desc)}")
    
    # 检查缺失数量
    missing = [code for code in zs_all if code not in existing_desc or not existing_desc.get(code)]
    print(f"缺失描述数量: {len(missing)}")
    
    if missing:
        print("缺失的板块:")
        for code in missing[:5]:  # 只显示前5个
            info = zs_all[code]
            name = info[0] if isinstance(info, list) else str(info)
            print(f"  - {name}({code})")
        if len(missing) > 5:
            print(f"  ... 还有 {len(missing) - 5} 个")
    
    print()


def test_mock_new_index():
    """测试新增板块场景"""
    print("=" * 60)
    print("测试6: 新增板块场景模拟")
    print("=" * 60)
    
    config_file = 'data/zs_fund_online_ui.json'
    
    # 加载现有配置
    config = file2json(config_file)
    zs_all = config.get('zs_all', {})
    existing_desc = config.get('zs_descriptions', {})
    
    # 模拟新增一个板块（使用测试代码，不存在的）
    test_code = "9.TEST01"
    test_info = ["测试新板块", "000001"]
    
    # 临时添加到配置
    zs_all_copy = zs_all.copy()
    zs_all_copy[test_code] = test_info
    
    # 检查是否能检测到新板块
    missing = [code for code in zs_all_copy if code not in existing_desc or not existing_desc.get(code)]
    
    if test_code in missing:
        print(f"[OK] 正确检测到新板块: {test_code}")
        
        # 测试自动获取（只获取这个新板块）
        single_zs = {test_code: test_info}
        new_desc = auto_fetch_missing_descriptions(config_file, single_zs)
        
        if test_code in new_desc and new_desc[test_code]:
            print(f"[OK] 新板块描述获取成功: {new_desc[test_code][:60]}...")
        else:
            print(f"[INFO] 新板块描述未获取到")
    else:
        print(f"[WARN] 未能检测到新板块")
    
    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("板块描述自动获取功能测试")
    print("=" * 60 + "\n")
    
    try:
        test_extract_pure_code()
        test_predefined_descriptions()
        test_default_generation()
        
        # 可选测试（需要网络）
        try:
            test_online_fetch()
        except Exception as e:
            print(f"[WARN] 联网测试跳过: {e}\n")
        
        test_auto_fetch()
        test_mock_new_index()
        
        print("=" * 60)
        print("[OK] 所有基础测试通过!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n[ERROR] 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
