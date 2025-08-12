#!/usr/bin/env python3
"""
API 串接測試腳本
測試 前端 → app-server → ai-service 的完整調用鏈路
"""

import requests
import json
import time

def test_service(name, url, method="GET", data=None, timeout=10):
    """測試單一服務端點"""
    print(f"\n🧪 測試 {name}: {method} {url}")
    try:
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        
        print(f"   狀態碼: {response.status_code}")
        print(f"   回應時間: {response.elapsed.total_seconds():.2f}s")
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                print(f"   回應內容: {str(json_data)[:100]}...")
                return True, json_data
            except:
                print(f"   回應內容: {response.text[:100]}...")
                return True, response.text
        else:
            print(f"   錯誤回應: {response.text[:200]}")
            return False, response.text
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ 連線失敗: 服務可能未啟動")
        return False, "連線失敗"
    except requests.exceptions.Timeout:
        print(f"   ❌ 請求超時")
        return False, "請求超時"
    except Exception as e:
        print(f"   ❌ 其他錯誤: {str(e)}")
        return False, str(e)

def main():
    """主要測試流程"""
    print("🔍 API 串接完整測試")
    print("=" * 50)
    
    # 測試各服務的健康狀態
    services = [
        ("AI Service 健康檢查", "http://localhost:8001/api/status", "GET"),
        ("App Server 健康檢查", "http://localhost:3001/api/health", "GET"),
        ("前端服務", "http://localhost:3000", "GET"),
    ]
    
    print("\n📋 步驟 1: 檢查各服務狀態")
    service_status = {}
    
    for name, url, method in services:
        success, result = test_service(name, url, method)
        service_status[name] = success
    
    # 測試 AI Service 直接調用
    print("\n📋 步驟 2: 測試 AI Service 直接調用")
    ai_test_data = {
        "question": "什麼是密碼政策？",
        "top_k": 3
    }
    
    ai_success, ai_result = test_service(
        "AI Service /api/ask", 
        "http://localhost:8001/api/ask", 
        "POST", 
        ai_test_data
    )
    
    # 測試 App Server 調用 AI Service
    print("\n📋 步驟 3: 測試 App Server 調用 AI Service")
    app_test_data = {
        "question": "什麼是密碼政策？"
    }
    
    app_success, app_result = test_service(
        "App Server /api/ask", 
        "http://localhost:3001/api/ask", 
        "POST", 
        app_test_data
    )
    
    # 測試結果總結
    print("\n" + "=" * 50)
    print("📊 測試結果總結")
    
    all_services_up = all(service_status.values())
    
    if all_services_up:
        print("✅ 所有服務都已啟動")
    else:
        print("❌ 部分服務未啟動:")
        for name, status in service_status.items():
            if not status:
                print(f"   - {name}")
    
    if ai_success:
        print("✅ AI Service 直接調用正常")
    else:
        print("❌ AI Service 直接調用失敗")
    
    if app_success:
        print("✅ App Server 調用 AI Service 正常")
    else:
        print("❌ App Server 調用 AI Service 失敗")
    
    # 診斷建議
    print("\n💡 診斷建議:")
    
    if not all_services_up:
        print("1. 請確認所有服務都已正確啟動")
        print("   - 檢查 start-all.bat 啟動的 4 個視窗")
        print("   - 確認沒有錯誤訊息")
    
    if not ai_success:
        print("2. AI Service 問題:")
        print("   - 檢查 ChromaDB 是否正常")
        print("   - 檢查 Ollama 是否正常")
        print("   - 查看 AI Service 日誌")
    
    if not app_success and ai_success:
        print("3. App Server → AI Service 串接問題:")
        print("   - 檢查 app-server 的 AI_SERVICE_URL 設定")
        print("   - 檢查網路連線和防火牆")
        print("   - 查看 app-server 日誌")
    
    if all_services_up and ai_success and app_success:
        print("✅ 所有 API 串接正常！")
        print("   前端錯誤可能是其他原因，建議檢查瀏覽器開發者工具")

if __name__ == "__main__":
    main()
