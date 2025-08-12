#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速測試 API 修復效果
"""

import requests
import json
import time

def quick_test():
    """快速測試 API 修復效果"""
    print("=== 快速測試 API 修復效果 ===")
    
    # 測試 AI Service 直接調用
    print("\n1. 測試 AI Service 直接調用...")
    try:
        response = requests.get("http://localhost:8001/api/health", timeout=5)
        print(f"AI Service 健康檢查: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"資料庫狀態: {health_data.get('database', {}).get('status', 'unknown')}")
    except Exception as e:
        print(f"AI Service 不可用: {e}")
        return
    
    # 測試問答功能
    print("\n2. 測試問答功能...")
    test_question = {"question": "印表機機密文件怎麼處理？"}
    
    try:
        response = requests.post(
            "http://localhost:8001/api/ask", 
            json=test_question, 
            timeout=30
        )
        print(f"AI Service 問答狀態: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer', '')
            
            if "系統處理您的問題時遇到了技術問題" in answer:
                print("❌ AI Service 仍返回錯誤訊息")
                if 'error' in data:
                    print(f"錯誤詳情: {data['error']}")
            elif "很抱歉，AI 服務暫時無法處理您的問題" in answer:
                print("❌ Ollama 調用失敗")
                print(f"答案: {answer}")
            else:
                print("✅ AI Service 返回正常答案！")
                print(f"答案預覽: {answer[:100]}...")
                
        else:
            print(f"❌ 請求失敗: {response.text}")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
    
    # 測試 App Server 代理
    print("\n3. 測試 App Server 代理...")
    try:
        response = requests.post(
            "http://localhost:3001/api/ask", 
            json=test_question, 
            timeout=30
        )
        print(f"App Server 代理狀態: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer', '')
            
            if "系統處理您的問題時遇到了技術問題" in answer:
                print("❌ 前端仍會收到錯誤訊息")
            else:
                print("✅ 前端將收到正常答案！")
                print(f"前端顯示: {answer[:100]}...")
        else:
            print(f"❌ App Server 代理失敗: {response.text}")
            
    except Exception as e:
        print(f"❌ App Server 測試失敗: {e}")

if __name__ == "__main__":
    quick_test()
