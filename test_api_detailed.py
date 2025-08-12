#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
詳細 API 串接測試腳本
"""

import requests
import json
import time

def test_api_integration():
    """測試 API 串接並顯示詳細錯誤資訊"""
    print("=== 測試 App Server 代理 AI Service ===")
    
    try:
        # 測試問題
        test_question = {"question": "印表機機密文件怎麼處理？"}
        
        # 通過 App Server 發送請求
        print(f"發送請求到 App Server: {test_question}")
        response = requests.post(
            "http://localhost:3001/api/ask", 
            json=test_question, 
            timeout=60
        )
        
        print(f"回應狀態碼: {response.status_code}")
        print(f"回應標頭: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("=== 回應內容 ===")
                print(json.dumps(data, ensure_ascii=False, indent=2))
                
                # 檢查是否包含錯誤詳情
                if 'error' in data:
                    print("\n=== 錯誤詳情 ===")
                    print(f"錯誤訊息: {data.get('error', 'N/A')}")
                    if 'trace' in data:
                        print(f"錯誤追蹤:")
                        print(data['trace'])
                        
                # 檢查答案內容
                if 'answer' in data:
                    answer = data['answer']
                    if "系統處理您的問題時遇到了技術問題" in answer:
                        print("\n⚠️ AI Service 返回錯誤訊息，需要進一步診斷")
                    else:
                        print("\n✅ AI Service 返回正常答案")
                        
            except json.JSONDecodeError as e:
                print(f"❌ JSON 解析失敗: {e}")
                print(f"原始回應: {response.text}")
        else:
            print(f"❌ 請求失敗: {response.text}")
            
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")

if __name__ == "__main__":
    test_api_integration()
