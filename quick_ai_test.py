#!/usr/bin/env python3
"""
快速 AI Service 診斷和測試工具
檢查 AI Service 的核心功能是否正常
"""

import requests
import json
import time

def test_ai_service_basic():
    """測試 AI Service 基本功能"""
    print("=== 測試 AI Service 基本功能 ===")
    
    try:
        # 1. 測試狀態端點
        print("1. 測試狀態端點...")
        response = requests.get("http://localhost:8001/api/status", timeout=10)
        if response.status_code == 200:
            print("✅ 狀態端點正常")
        else:
            print(f"❌ 狀態端點異常: {response.status_code}")
            return False
            
        # 2. 測試健康檢查端點
        print("2. 測試健康檢查端點...")
        response = requests.get("http://localhost:8001/api/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ 健康檢查正常")
            print(f"   服務狀態: {data.get('status')}")
            
            # 檢查資料庫資訊
            db_info = data.get('database', {})
            if db_info and db_info.get('status') == 'connected':
                print(f"✅ 資料庫已連接")
                print(f"   集合數量: {db_info.get('collections_count')}")
                print(f"   總文檔數: {db_info.get('total_documents')}")
                
                # 顯示集合詳情
                for collection in db_info.get('collections', []):
                    print(f"   - {collection['name']}: {collection['document_count']} 個文檔")
            else:
                print(f"❌ 資料庫連接異常: {db_info}")
                return False
        else:
            print(f"❌ 健康檢查異常: {response.status_code}")
            return False
            
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到 AI Service (localhost:8001)")
        return False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_ai_ask_function():
    """測試 AI 問答功能"""
    print("\n=== 測試 AI 問答功能 ===")
    
    try:
        # 測試簡單問題
        test_questions = [
            "什麼是機密文件？",
            "印表機使用注意事項",
            "作品集準備規範"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"{i}. 測試問題: {question}")
            
            test_data = {
                "question": question,
                "session_id": f"test_session_{i}"
            }
            
            response = requests.post(
                "http://localhost:8001/api/ask", 
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer', '')
                if answer and len(answer) > 10:
                    print(f"✅ 問答正常 (回應長度: {len(answer)})")
                    print(f"   回應預覽: {answer[:100]}...")
                else:
                    print(f"❌ 回應內容異常: {answer}")
                    return False
            else:
                print(f"❌ 問答請求失敗: {response.status_code}")
                print(f"   錯誤內容: {response.text}")
                return False
                
            time.sleep(1)  # 避免請求過快
            
        return True
        
    except Exception as e:
        print(f"❌ 問答測試失敗: {e}")
        return False

def test_frontend_backend_integration():
    """測試前後端整合"""
    print("\n=== 測試前後端整合 ===")
    
    try:
        # 通過 App Server 測試 AI 功能
        test_data = {
            "question": "機密文件處理規範",
            "session_id": "integration_test"
        }
        
        response = requests.post(
            "http://localhost:3001/api/ask", 
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer', '')
            if answer and len(answer) > 10:
                print("✅ 前後端整合正常")
                print(f"   回應長度: {len(answer)}")
                return True
            else:
                print(f"❌ 整合回應異常: {answer}")
                return False
        else:
            print(f"❌ 前後端整合失敗: {response.status_code}")
            print(f"   錯誤內容: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到 App Server (localhost:3001)")
        return False
    except Exception as e:
        print(f"❌ 整合測試失敗: {e}")
        return False

def main():
    """執行完整的 AI Service 診斷"""
    print("🔧 AI Service 快速診斷工具")
    print("=" * 50)
    
    # 測試順序
    tests = [
        ("AI Service 基本功能", test_ai_service_basic),
        ("AI 問答功能", test_ai_ask_function),
        ("前後端整合", test_frontend_backend_integration)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ 測試執行錯誤: {e}")
            results[test_name] = False
    
    # 結果總結
    print(f"\n{'='*50}")
    print("🎯 診斷結果總結")
    print(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📊 總體結果: {passed}/{total} 通過 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 AI Service 完全正常！RAG 功能已打通！")
        return True
    else:
        print("⚠️ 發現問題，需要進一步修復")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
