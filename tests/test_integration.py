# -*- coding: utf-8 -*-
"""
集成测试：验证自动获取功能与web_server的集成
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json


def test_config_with_missing_descriptions():
    """测试配置文件中存在缺失描述的情况"""
    print("=" * 60)
    print("集成测试: 配置文件中存在缺失描述")
    print("=" * 60)
    
    config_file = 'data/zs_fund_online_ui.json'
    
    # 加载配置
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    zs_all = config.get('zs_all', {})
    zs_descriptions = config.get('zs_descriptions', {})
    
    print(f"板块数量: {len(zs_all)}")
    print(f"描述数量: {len(zs_descriptions)}")
    
    # 检查是否所有板块都有描述
    missing = []
    for code in zs_all:
        if code not in zs_descriptions or not zs_descriptions.get(code):
            missing.append(code)
    
    if missing:
        print(f"[INFO] 发现 {len(missing)} 个板块缺少描述:")
        for code in missing[:3]:
            info = zs_all[code]
            name = info[0] if isinstance(info, list) else str(info)
            print(f"  - {code}: {name}")
        if len(missing) > 3:
            print(f"  ... 还有 {len(missing) - 3} 个")
    else:
        print("[OK] 所有板块都有描述")
    
    print()
    return len(missing) == 0


def test_auto_fetch_on_startup():
    """测试启动时的自动获取逻辑"""
    print("=" * 60)
    print("集成测试: 启动时自动获取逻辑")
    print("=" * 60)
    
    from scripts.txt2str import file2json
    from utils.IndexDescription import auto_fetch_missing_descriptions
    
    config_file = 'data/zs_fund_online_ui.json'
    
    # 加载配置
    config = file2json(config_file)
    zs_all = config.get('zs_all', {})
    existing_desc = config.get('zs_descriptions', {})
    
    # 模拟缺失一个描述
    test_code = list(zs_all.keys())[0] if zs_all else None
    if test_code and test_code in existing_desc:
        # 临时删除这个描述用于测试
        saved_desc = existing_desc[test_code]
        del existing_desc[test_code]
        
        # 保存修改后的配置
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"[INFO] 临时删除 {test_code} 的描述用于测试")
        
        # 重新加载并触发自动获取
        config = file2json(config_file)
        zs_all = config.get('zs_all', {})
        
        print("[INFO] 触发自动获取...")
        new_desc = auto_fetch_missing_descriptions(config_file, zs_all)
        
        # 验证描述是否被恢复
        if test_code in new_desc and new_desc[test_code]:
            print(f"[OK] 描述已自动恢复: {new_desc[test_code][:50]}...")
        else:
            print(f"[FAIL] 描述未能恢复")
        
        # 恢复原始描述
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        config['zs_descriptions'][test_code] = saved_desc
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print("[INFO] 已恢复原始配置")
    
    print()


def test_new_index_scenario():
    """测试添加新板块的场景"""
    print("=" * 60)
    print("集成测试: 添加新板块场景")
    print("=" * 60)
    
    from scripts.txt2str import file2json
    from utils.IndexDescription import auto_fetch_missing_descriptions
    
    config_file = 'data/zs_fund_online_ui.json'
    
    # 加载配置
    config = file2json(config_file)
    zs_all = config.get('zs_all', {})
    zs_descriptions = config.get('zs_descriptions', {})
    
    # 模拟添加新板块
    new_code = "9.TEST999"
    new_info = ["测试新板块", "000001"]
    
    # 检查是否已存在
    if new_code not in zs_all:
        # 添加新板块（不添加描述）
        zs_all[new_code] = new_info
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"[INFO] 添加测试板块: {new_code}")
        
        # 触发自动获取
        new_desc = auto_fetch_missing_descriptions(config_file, zs_all)
        
        # 验证描述是否已获取
        if new_code in new_desc and new_desc[new_code]:
            print(f"[OK] 新板块描述已获取: {new_desc[new_code][:50]}...")
        else:
            print(f"[INFO] 新板块描述未获取（可能联网失败）")
        
        # 清理测试数据
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if new_code in config.get('zs_all', {}):
            del config['zs_all'][new_code]
        if new_code in config.get('zs_descriptions', {}):
            del config['zs_descriptions'][new_code]
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print("[INFO] 已清理测试数据")
    else:
        print(f"[INFO] 测试板块已存在，跳过测试")
    
    print()


def main():
    """运行集成测试"""
    print("\n" + "=" * 60)
    print("板块描述自动获取功能 - 集成测试")
    print("=" * 60 + "\n")
    
    try:
        test_config_with_missing_descriptions()
        test_auto_fetch_on_startup()
        test_new_index_scenario()
        
        print("=" * 60)
        print("[OK] 集成测试完成!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
