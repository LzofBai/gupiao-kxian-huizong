#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试笔记API功能
"""

import requests
import json
from datetime import datetime
import time

BASE_URL = "http://localhost:5000"

def test_notes_api():
    print("开始测试笔记API功能...")
    
    # 1. 检查笔记表
    print("\n1. 检查笔记表是否存在...")
    try:
        response = requests.get(f"{BASE_URL}/api/notes/check")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
    except Exception as e:
        print(f"检查笔记表失败: {e}")
        return
    
    # 2. 获取所有笔记
    print("\n2. 获取所有笔记...")
    try:
        response = requests.get(f"{BASE_URL}/api/notes")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"笔记数量: {len(data.get('data', []))}")
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"响应: {response.text}")
    except Exception as e:
        print(f"获取笔记失败: {e}")
    
    # 3. 创建新笔记
    print("\n3. 创建新笔记...")
    note_id = f"test_note_{int(time.time())}"
    today = datetime.now().strftime('%Y-%m-%d')
    
    note_data = {
        "id": note_id,
        "date": today,
        "content": "<p>这是测试笔记内容</p>",
        "createTime": int(time.time() * 1000)
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/notes",
            json=note_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            print("✅ 笔记创建成功")
        else:
            print("❌ 笔记创建失败")
    except Exception as e:
        print(f"创建笔记失败: {e}")
    
    # 4. 再次获取所有笔记
    print("\n4. 再次获取所有笔记...")
    try:
        response = requests.get(f"{BASE_URL}/api/notes")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"笔记数量: {len(data.get('data', []))}")
            for note in data.get('data', []):
                print(f"  - {note.get('id')}: {note.get('date')}")
        else:
            print(f"响应: {response.text}")
    except Exception as e:
        print(f"获取笔记失败: {e}")

if __name__ == "__main__":
    test_notes_api()