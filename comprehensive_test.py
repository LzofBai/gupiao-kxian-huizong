#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合测试笔记功能修复效果
"""

import requests
import json
from datetime import datetime
import time

BASE_URL = "http://localhost:5000"

def comprehensive_test():
    print("开始综合测试笔记功能...")
    
    # 1. 清理测试数据
    print("\n1. 清理历史测试数据...")
    try:
        response = requests.get(f"{BASE_URL}/api/notes")
        if response.status_code == 200:
            data = response.json()
            test_notes = [note for note in data.get('data', []) if note.get('id', '').startswith('test_note_')]
            for note in test_notes:
                requests.delete(f"{BASE_URL}/api/notes/{note['id']}")
                print(f"  删除测试笔记: {note['id']}")
    except Exception as e:
        print(f"清理测试数据失败: {e}")
    
    # 2. 测试创建笔记功能
    print("\n2. 测试创建笔记功能...")
    test_cases = [
        {
            "name": "正常笔记创建",
            "data": {
                "id": f"test_create_{int(time.time())}",
                "date": datetime.now().strftime('%Y-%m-%d'),
                "content": "<p>正常测试笔记内容</p>",
                "createTime": int(time.time() * 1000)
            }
        },
        {
            "name": "带特殊字符的笔记",
            "data": {
                "id": f"test_special_{int(time.time())}",
                "date": datetime.now().strftime('%Y-%m-%d'),
                "content": "<p>测试内容包含特殊字符：!@#$%^&*()_+-=[]{}|;':\",./<>?</p>",
                "createTime": int(time.time() * 1000)
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"  测试: {test_case['name']}")
        try:
            response = requests.post(
                f"{BASE_URL}/api/notes",
                json=test_case['data'],
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"    ✅ 成功: {test_case['data']['id']}")
                else:
                    print(f"    ❌ 失败: {result.get('message', '未知错误')}")
            else:
                print(f"    ❌ HTTP错误: {response.status_code}")
        except Exception as e:
            print(f"    ❌ 异常: {e}")
    
    # 3. 测试获取笔记列表
    print("\n3. 测试获取笔记列表...")
    try:
        response = requests.get(f"{BASE_URL}/api/notes")
        if response.status_code == 200:
            data = response.json()
            notes_count = len(data.get('data', []))
            print(f"  ✅ 当前共有 {notes_count} 条笔记")
            
            # 显示最近几条笔记
            recent_notes = data.get('data', [])[:3]
            for note in recent_notes:
                print(f"    - {note.get('id')}: {note.get('date')} ({len(note.get('content', ''))} 字符)")
        else:
            print(f"  ❌ 获取失败: HTTP {response.status_code}")
    except Exception as e:
        print(f"  ❌ 异常: {e}")
    
    # 4. 测试笔记更新
    print("\n4. 测试笔记更新...")
    try:
        # 获取第一条测试笔记
        response = requests.get(f"{BASE_URL}/api/notes")
        if response.status_code == 200:
            data = response.json()
            test_notes = [note for note in data.get('data', []) if note.get('id', '').startswith('test_')]
            
            if test_notes:
                note_to_update = test_notes[0]
                updated_content = f"<p>更新后的测试内容 - {datetime.now().strftime('%H:%M:%S')}</p>"
                
                update_data = {
                    "id": note_to_update['id'],
                    "date": note_to_update['date'],
                    "content": updated_content,
                    "createTime": note_to_update['createTime'],
                    "updateTime": int(time.time() * 1000)
                }
                
                response = requests.post(
                    f"{BASE_URL}/api/notes",
                    json=update_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        print(f"  ✅ 笔记更新成功: {note_to_update['id']}")
                    else:
                        print(f"  ❌ 更新失败: {result.get('message')}")
                else:
                    print(f"  ❌ HTTP错误: {response.status_code}")
            else:
                print("  ⚠️  没有找到测试笔记进行更新")
    except Exception as e:
        print(f"  ❌ 异常: {e}")
    
    # 5. 测试边界情况
    print("\n5. 测试边界情况...")
    
    # 测试空内容笔记
    print("  测试空内容笔记...")
    try:
        empty_note_data = {
            "id": f"test_empty_{int(time.time())}",
            "date": datetime.now().strftime('%Y-%m-%d'),
            "content": "",
            "createTime": int(time.time() * 1000)
        }
        
        response = requests.post(
            f"{BASE_URL}/api/notes",
            json=empty_note_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("    ✅ 空内容笔记创建成功")
            else:
                print(f"    ❌ 创建失败: {result.get('message')}")
        else:
            print(f"    ❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"    ❌ 异常: {e}")
    
    print("\n🎉 综合测试完成！")

if __name__ == "__main__":
    comprehensive_test()