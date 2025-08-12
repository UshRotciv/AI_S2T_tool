#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速測試優化後的檢索功能"""

import requests
import json

def test_api(port=8001):
    """測試 API 回應"""
    url = f"http://localhost:{port}/api/ask"
    
    # 測試會議白板問題
    test_question = "會議結束後，為了方便記錄，我用自己的手機拍攝會議白板內容，並上傳到自己的Teams聊天室。這樣做是否合規？"
    
    payload = {
        "question": test_question,
        "session_id": "test_session"
    }
    
    print("=== 測試優化後的檢索功能 ===")
    print(f"問題: {test_question}")
    print("發送請求...")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ API 回應成功")
            print(f"回答長度: {len(result.get('answer', ''))} 字")
            print(f"來源數量: {len(result.get('sources', []))} 筆")
            
            print(f"\n💬 回答內容:")
            print(result.get('answer', '無回答'))
            
            if result.get('sources'):
                print(f"\n📚 來源資料:")
                for i, source in enumerate(result.get('sources', []), 1):
                    print(f"  {i}. {source.get('title', '無標題')} (距離: {source.get('distance', 'N/A')})")
                    print(f"     內容片段: {source.get('content', '')[:100]}...")
            else:
                print("\n❌ 沒有找到相關來源")
                
        else:
            print(f"❌ API 錯誤: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 請求失敗: {e}")

if __name__ == "__main__":
    test_api()
