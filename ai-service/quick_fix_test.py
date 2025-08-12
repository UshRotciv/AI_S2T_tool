#!/usr/bin/env python3
"""
快速修復測試
直接插入測試資料，使用正確的 embedding function
"""

import chromadb
from chromadb.utils import embedding_functions
from datetime import datetime

def quick_fix():
    """快速修復測試"""
    print("🔧 快速修復測試 - 使用正確的 embedding function")
    
    try:
        # 1. 連接 ChromaDB
        print("1. 連接 ChromaDB...")
        client = chromadb.PersistentClient(path="./chroma_db")
        
        # 2. 刪除舊集合
        print("2. 清理舊集合...")
        try:
            client.delete_collection("scenarios")
            print("   ✅ 刪除舊集合成功")
        except:
            print("   ✅ 無舊集合需刪除")
        
        # 3. 建立新集合（使用與 AI Service 相同的 embedding function）
        print("3. 建立新集合...")
        embedding_function = embedding_functions.OllamaEmbeddingFunction(
            model_name="mxbai-embed-large",
            url="http://localhost:11434",
        )
        collection = client.create_collection(
            "scenarios",
            embedding_function=embedding_function
        )
        print("   ✅ 集合建立成功（使用 mxbai-embed-large embedding）")
        
        # 4. 插入測試資料
        print("4. 插入測試資料...")
        
        # 測試資料 - 直接硬編碼避免 JSON 解析問題
        test_scenarios = [
            {
                "id": "scenario-001",
                "title": "印表機發現無人拿走的機密文件",
                "question": "你在印表機旁發現一份標示著「ASUS Confidential」的設計圖，但附近沒有人。這時你該怎麼做？",
                "answer": "即使出於善意，也不應隨意接觸或移動不屬於自己權限的資料，任何含有機密資訊的輸出實體圖紙本都應妥善看顧並記得帶走。基本上發現時不主動碰觸也不可窺探文件內容，可以直接用碎紙機將其碎掉，如果是可判斷為正本(如身分證)則立即通知設計中心管理師或文件所有者前來處理，徹底做到「非禮勿視」。",
                "category": "Part A: 辦公室基礎好習慣 (Basic Office Habits)"
            },
            {
                "id": "scenario-002", 
                "title": "人離機鎖的重要性",
                "question": "你只是要去茶水間倒杯水，大概3分鐘就回來，有需要手動鎖定電腦嗎？",
                "answer": "是的，即使只是短暫離開，也應該鎖定電腦。養成「人離機鎖」的習慣是基本的資安防護措施。",
                "category": "Part A: 辦公室基礎好習慣 (Basic Office Habits)"
            },
            {
                "id": "scenario-003",
                "title": "密碼政策與安全",
                "question": "什麼是密碼政策？",
                "answer": "密碼政策是組織制定的關於密碼創建、使用和管理的規範，包括密碼複雜度要求、定期更換、多因素驗證等安全措施。",
                "category": "資安基礎"
            }
        ]
        
        # 批次插入
        ids = []
        documents = []
        metadatas = []
        
        for scenario in test_scenarios:
            doc_id = scenario["id"]
            doc_text = f"標題: {scenario['title']}\n問題: {scenario['question']}\n答案: {scenario['answer']}"
            
            metadata = {
                "title": scenario["title"],
                "category": scenario["category"],
                "doc_type": "scenario",
                "created_at": datetime.utcnow().isoformat()
            }
            
            ids.append(doc_id)
            documents.append(doc_text)
            metadatas.append(metadata)
        
        # 執行插入
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"   ✅ 成功插入 {len(test_scenarios)} 筆測試資料")
        
        # 5. 立即驗證
        print("5. 驗證資料...")
        count = collection.count()
        print(f"   集合文件數: {count}")
        
        if count > 0:
            print("   ✅ 資料寫入成功！")
            
            # 6. 測試查詢
            print("6. 測試查詢...")
            test_queries = ["密碼政策", "印表機", "機密文件", "電腦鎖定"]
            
            for query in test_queries:
                results = collection.query(
                    query_texts=[query],
                    n_results=2
                )
                
                result_count = len(results['ids'][0]) if results['ids'] else 0
                print(f"   查詢 '{query}': 找到 {result_count} 個結果")
                
                if result_count > 0:
                    for i, doc_id in enumerate(results['ids'][0]):
                        distance = results['distances'][0][i] if results.get('distances') else 'N/A'
                        print(f"     結果 {i+1}: {doc_id} (距離: {distance})")
            
            return True
        else:
            print("   ❌ 資料寫入失敗")
            return False
            
    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試流程"""
    print("🔧 快速修復測試")
    print("=" * 50)
    
    success = quick_fix()
    
    if success:
        print("\n🎉 修復成功！")
        print("💡 現在可以測試 AI Service 是否能正常查詢")
        print("💡 執行: python -c \"import requests; r = requests.post('http://localhost:8000/api/ask', json={'question': '什麼是密碼政策？'}, timeout=30); print('回應:', r.json())\"")
    else:
        print("\n❌ 修復失敗")

if __name__ == "__main__":
    main()
