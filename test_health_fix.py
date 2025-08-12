#!/usr/bin/env python3
"""
測試修復後的健康檢查端點
"""

import requests
import json

def test_health_endpoint():
    """測試 AI Service 健康檢查端點"""
    try:
        print("=== 測試修復後的健康檢查端點 ===")
        
        # 測試健康檢查端點
        response = requests.get("http://localhost:8001/api/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 健康檢查端點正常")
            print(f"📊 服務狀態: {data.get('status')}")
            print(f"💬 活躍對話: {data.get('active_conversations')}")
            print(f"🧹 清理對話: {data.get('cleaned_conversations')}")
            
            # 檢查資料庫資訊
            db_info = data.get('database', {})
            if db_info:
                print(f"🗄️ 資料庫狀態: {db_info.get('status')}")
                if db_info.get('status') == 'connected':
                    print(f"📚 集合數量: {db_info.get('collections_count')}")
                    print(f"📄 總文檔數: {db_info.get('total_documents')}")
                    print("📋 集合詳情:")
                    for collection in db_info.get('collections', []):
                        print(f"  - {collection['name']}: {collection['document_count']} 個文檔")
                    return True
                else:
                    print(f"❌ 資料庫錯誤: {db_info.get('error')}")
                    return False
            else:
                print("❌ 沒有資料庫資訊")
                return False
        else:
            print(f"❌ 健康檢查失敗: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到 AI Service (localhost:8001)")
        return False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_ask_endpoint():
    """測試 /ask 端點是否存在"""
    try:
        print("\n=== 測試 /ask 端點 ===")
        
        test_data = {
            "question": "測試問題",
            "session_id": "test_session"
        }
        
        response = requests.post(
            "http://localhost:8001/api/ask", 
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ /ask 端點正常回應")
            return True
        elif response.status_code == 404:
            print("❌ /ask 端點返回 404 Not Found")
            return False
        else:
            print(f"⚠️ /ask 端點返回狀態碼: {response.status_code}")
            print(f"回應內容: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到 AI Service")
        return False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

if __name__ == "__main__":
    health_ok = test_health_endpoint()
    ask_ok = test_ask_endpoint()
    
    print(f"\n=== 測試結果總結 ===")
    print(f"健康檢查端點: {'✅ 通過' if health_ok else '❌ 失敗'}")
    print(f"/ask 端點: {'✅ 通過' if ask_ok else '❌ 失敗'}")
