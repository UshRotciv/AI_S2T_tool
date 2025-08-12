#!/usr/bin/env python3
"""
完整的 RAG 系統修復驗證測試
測試所有修復是否成功
"""

import requests
import json
import time

def test_ollama_service():
    """測試 Ollama 服務"""
    try:
        print("=== 測試 Ollama 服務 ===")
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            print("✅ Ollama 服務正常")
            return True
        else:
            print(f"❌ Ollama 服務異常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama 服務連接失敗: {e}")
        return False

def test_ai_service_health():
    """測試 AI Service 健康檢查（修復後）"""
    try:
        print("\n=== 測試 AI Service 健康檢查 ===")
        response = requests.get("http://localhost:8001/api/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ AI Service 健康檢查正常")
            print(f"📊 服務狀態: {data.get('status')}")
            
            # 檢查資料庫資訊（修復重點）
            db_info = data.get('database', {})
            if db_info and db_info.get('status') == 'connected':
                print("✅ 資料庫連接正常")
                print(f"📚 集合數量: {db_info.get('collections_count')}")
                print(f"📄 總文檔數: {db_info.get('total_documents')}")
                return True
            else:
                print(f"❌ 資料庫連接異常: {db_info}")
                return False
        else:
            print(f"❌ AI Service 健康檢查失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ AI Service 連接失敗: {e}")
        return False

def test_ai_service_ask():
    """測試 AI Service /ask 端點"""
    try:
        print("\n=== 測試 AI Service /ask 端點 ===")
        test_data = {
            "question": "什麼是機密文件？",
            "session_id": "test_session"
        }
        
        response = requests.post(
            "http://localhost:8001/api/ask", 
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ /ask 端點正常回應")
            print(f"📝 回應長度: {len(data.get('answer', ''))}")
            return True
        else:
            print(f"❌ /ask 端點異常: {response.status_code}")
            print(f"錯誤內容: {response.text}")
            return False
    except Exception as e:
        print(f"❌ /ask 端點測試失敗: {e}")
        return False

def test_app_server():
    """測試 App Server 基本功能"""
    try:
        print("\n=== 測試 App Server ===")
        response = requests.get("http://localhost:3001/api/scenarios", timeout=10)
        
        if response.status_code == 200:
            print("✅ App Server 基本功能正常")
            return True
        else:
            print(f"❌ App Server 異常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ App Server 連接失敗: {e}")
        return False

def test_frontend_backend_integration():
    """測試前後端整合（修復重點）"""
    try:
        print("\n=== 測試前後端整合 ===")
        test_data = {
            "question": "印表機使用注意事項",
            "session_id": "integration_test"
        }
        
        # 通過 App Server 代理到 AI Service
        response = requests.post(
            "http://localhost:3001/api/ask", 
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 前後端整合正常")
            print(f"📝 AI 回應: {data.get('answer', '')[:100]}...")
            return True
        else:
            print(f"❌ 前後端整合失敗: {response.status_code}")
            print(f"錯誤內容: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 前後端整合測試失敗: {e}")
        return False

def test_react_client():
    """測試 React Client"""
    try:
        print("\n=== 測試 React Client ===")
        # 嘗試兩個可能的端口
        for port in [3000, 3002]:
            try:
                response = requests.get(f"http://localhost:{port}", timeout=5)
                if response.status_code == 200:
                    print(f"✅ React Client 正常運行在端口 {port}")
                    return True
            except:
                continue
        
        print("❌ React Client 未運行")
        return False
    except Exception as e:
        print(f"❌ React Client 測試失敗: {e}")
        return False

def main():
    """執行完整測試"""
    print("🔧 RAG 系統修復驗證測試")
    print("=" * 50)
    
    tests = [
        ("Ollama 服務", test_ollama_service),
        ("AI Service 健康檢查", test_ai_service_health),
        ("AI Service /ask 端點", test_ai_service_ask),
        ("App Server", test_app_server),
        ("前後端整合", test_frontend_backend_integration),
        ("React Client", test_react_client)
    ]
    
    results = {}
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results[test_name] = result
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ 測試執行錯誤: {e}")
            results[test_name] = False
    
    # 測試結果總結
    print(f"\n{'='*50}")
    print("🎯 測試結果總結")
    print(f"{'='*50}")
    
    for test_name, result in results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
    
    print(f"\n📊 總體結果: {passed}/{total} 通過 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有測試通過！RAG 系統修復成功！")
        return True
    else:
        print("⚠️ 部分測試失敗，需要進一步檢查")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
