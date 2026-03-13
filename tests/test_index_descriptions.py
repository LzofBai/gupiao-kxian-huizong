# -*- coding: utf-8 -*-
"""
板块描述功能测试脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.txt2str import file2json
from utils.IndexDescription import (
    initialize_descriptions,
    load_descriptions_from_config,
    get_predefined_description,
    generate_default_description
)


def test_config_structure():
    """测试配置文件结构"""
    print("=" * 60)
    print("测试1: 配置文件结构验证")
    print("=" * 60)
    
    config_file = 'data/zs_fund_online_ui.json'
    ui_config = file2json(config_file)
    
    assert 'zs_all' in ui_config, "缺少 zs_all 字段"
    assert 'zs_descriptions' in ui_config, "缺少 zs_descriptions 字段"
    
    zs_all = ui_config['zs_all']
    zs_descriptions = ui_config['zs_descriptions']
    
    print(f"板块数量: {len(zs_all)}")
    print(f"描述数量: {len(zs_descriptions)}")
    
    # 验证每个板块都有描述
    for code in zs_all:
        assert code in zs_descriptions, f"板块 {code} 缺少描述"
        assert zs_descriptions[code], f"板块 {code} 描述为空"
    
    print("[OK] 所有板块都有描述")
    print()


def test_description_content():
    """测试描述内容"""
    print("=" * 60)
    print("测试2: 描述内容验证")
    print("=" * 60)
    
    config_file = 'data/zs_fund_online_ui.json'
    descriptions = load_descriptions_from_config(config_file)
    
    # 测试几个关键板块
    test_cases = [
        ('1.000698', '科创100'),
        ('1.000001', '上证指数'),
        ('90.BK1036', '半导体'),
        ('100.NDX', '纳斯达克'),
    ]
    
    for code, expected_name in test_cases:
        desc = descriptions.get(code, '')
        assert desc, f"{code} 描述为空"
        assert expected_name in desc or len(desc) > 10, f"{code} 描述内容异常"
        print(f"[OK] {expected_name}({code}): {desc[:50]}...")
    
    print()


def test_predefined_descriptions():
    """测试预定义描述"""
    print("=" * 60)
    print("测试3: 预定义描述验证")
    print("=" * 60)
    
    # 测试科创100的预定义描述
    desc = get_predefined_description('1.000698')
    assert desc, "科创100应该有预定义描述"
    assert '科创100' in desc, "描述应包含板块名称"
    assert '科创板' in desc or '硬科技' in desc, "描述应包含关键特征"
    print(f"[OK] 科创100预定义描述: {desc[:60]}...")
    
    # 测试默认描述生成
    default_desc = generate_default_description('1.999999', '测试板块')
    assert '测试板块' in default_desc, "默认描述应包含板块名称"
    print(f"[OK] 默认描述生成: {default_desc}")
    print()


def test_api_endpoints():
    """测试API端点(需要服务器运行)"""
    print("=" * 60)
    print("测试4: API端点验证 (静态代码检查)")
    print("=" * 60)
    
    # 读取 web_server.py 检查API端点
    with open('web_server.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查必要的路由
    required_routes = [
        '/api/index/descriptions',
        '/api/index/description/',
        '/api/index/descriptions/refresh',
    ]
    
    for route in required_routes:
        assert route in content, f"缺少路由: {route}"
        print(f"[OK] 路由存在: {route}")
    
    # 检查关键函数
    required_functions = [
        'get_index_descriptions',
        'get_single_index_description',
        'update_index_description',
        'refresh_index_descriptions',
        'ensure_descriptions_initialized',
    ]
    
    for func in required_functions:
        assert func in content, f"缺少函数: {func}"
        print(f"[OK] 函数存在: {func}")
    
    print()


def test_template_changes():
    """测试模板修改"""
    print("=" * 60)
    print("测试5: 模板修改验证")
    print("=" * 60)
    
    with open('templates/monitor.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查关键元素
    required_elements = [
        'index-description',
        'zs_descriptions',
        'index-description.empty',
    ]
    
    for elem in required_elements:
        assert elem in content, f"模板缺少元素: {elem}"
        print(f"[OK] 模板元素存在: {elem}")
    
    # 检查描述显示逻辑
    assert 'zs_descriptions.get' in content, "模板应使用 zs_descriptions.get 获取描述"
    print("[OK] 描述显示逻辑正确")
    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("板块描述功能测试")
    print("=" * 60 + "\n")
    
    try:
        test_config_structure()
        test_description_content()
        test_predefined_descriptions()
        test_api_endpoints()
        test_template_changes()
        
        print("=" * 60)
        print("[OK] 所有测试通过!")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
