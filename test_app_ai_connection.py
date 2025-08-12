#!/usr/bin/env python3
"""
App Server 與 AI Service 連接測試工具
診斷前後端整合問題
"""

import requests
import json
import time

def test_ai_service_direct():
    """直接測試 AI Service"""
    print("🔍 測試 AI Service 直接連接...")
    
    try:
        url = "http://localhost:8001/api/ask"
        data = {"question": "什麼是機密文件？"}
        
        print(f"請求 URL: {url}")
        print(f"請求數據: {data}")
        
        response = requests.post(url, json=data, timeout=30)
        
        print(f"響應狀態碼: {response.status_code}")
        print(f"響應標頭: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ AI Service 直接連接成功")
            print(f"回應內容: {result.get('answer', '無回應')[:100]}...")
            return True
        else:
            print(f"❌ AI Service 返回錯誤狀態碼: {response.status_code}")
            print(f"錯誤內容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ AI Service 直接連接失敗: {e}")
        return False

def test_app_server_proxy():
    """測試 App Server 代理功能"""
    print("\n🔍 測試 App Server 代理連接...")
    
    try:
        url = "http://localhost:3001/api/ask"
        data = {"question": "什麼是機密文件？"}
        
        print(f"請求 URL: {url}")
        print(f"請求數據: {data}")
        
        response = requests.post(url, json=data, timeout=30)
        
        print(f"響應狀態碼: {response.status_code}")
        print(f"響應標頭: {dict(response.headers)}")
        print(f"響應內容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ App Server 代理連接成功")
                print(f"回應內容: {result.get('data', {}).get('answer', '無回應')[:100]}...")
                return True
            else:
                print(f"❌ App Server 返回業務錯誤: {result}")
                return False
        else:
            print(f"❌ App Server 返回錯誤狀態碼: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ App Server 代理連接失敗: {e}")
        return False

def test_services_health():
    """測試服務健康狀態"""
    print("\n🔍 測試服務健康狀態...")
    
    # 測試 AI Service 健康檢查
    try:
        response = requests.get("http://localhost:8001/api/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ AI Service 健康檢查通過")
            print(f"資料庫狀態: {health_data.get('database_status', '未知')}")
            print(f"集合數量: {health_data.get('collections', '未知')}")
        else:
            print(f"❌ AI Service 健康檢查失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ AI Service 健康檢查異常: {e}")
    
    # 測試 App Server 健康狀態
    try:
        response = requests.get("http://localhost:3001/api/scenarios", timeout=10)
        if response.status_code == 200:
            print(f"✅ App Server 基本功能正常")
        else:
            print(f"❌ App Server 基本功能異常: {response.status_code}")
    except Exception as e:
        print(f"❌ App Server 連接失敗: {e}")

def main():
    """主測試函數"""
    print("=" * 60)
    print("🔧 App Server 與 AI Service 連接診斷工具")
    print("=" * 60)
    
    # 等待服務啟動
    print("⏳ 等待服務完全啟動...")
    time.sleep(2)
    
    # 測試服務健康狀態
    test_services_health()
    
    # 測試 AI Service 直接連接
    ai_direct_ok = test_ai_service_direct()
    
    # 測試 App Server 代理
    app_proxy_ok = test_app_server_proxy()
    
    # 總結結果
    print("\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    print(f"AI Service 直接連接: {'✅ 通過' if ai_direct_ok else '❌ 失敗'}")
    print(f"App Server 代理連接: {'✅ 通過' if app_proxy_ok else '❌ 失敗'}")
    
    if ai_direct_ok and not app_proxy_ok:
        print("\n🔍 診斷結論:")
        print("AI Service 工作正常，但 App Server 代理有問題")
        print("建議檢查 App Server 的錯誤處理和請求轉發邏輯")
    elif not ai_direct_ok:
        print("\n🔍 診斷結論:")
        print("AI Service 本身有問題，需要先修復 AI Service")
    elif ai_direct_ok and app_proxy_ok:
        print("\n🎉 所有測試通過！系統正常工作")
    else:
        print("\n❌ 所有服務都有問題，需要全面檢查")

if __name__ == "__main__":
    main()
