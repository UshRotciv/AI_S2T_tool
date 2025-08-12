#!/usr/bin/env python3
"""
緊急修復腳本 - 最簡化的資料匯入
直接硬編碼測試資料，確保 AI Service 能正常工作
"""

import chromadb
from chromadb.utils import embedding_functions

def emergency_fix():
    """緊急修復 - 直接硬編碼資料"""
    print("🚨 緊急修復 - 直接硬編碼資料")
    
    try:
        # 1. 連接 ChromaDB
        client = chromadb.PersistentClient(path="./chroma_db")
        
        # 2. 刪除舊集合
        try:
            client.delete_collection("scenarios")
            print("✅ 刪除舊集合")
        except:
            print("✅ 無舊集合")
        
        # 3. 建立新集合（使用與 AI Service 完全相同的設定）
        embedding_function = embedding_functions.OllamaEmbeddingFunction(
            model_name="mxbai-embed-large",
            url="http://localhost:11434",
        )
        
        collection = client.create_collection(
            "scenarios",
            embedding_function=embedding_function,
            metadata={"hnsw:space": "cosine"}  # 與 AI Service 一致
        )
        print("✅ 建立新集合（完全匹配 AI Service 設定）")
        
        # 4. 硬編碼測試資料（確保格式正確）
        test_data = [
            {
                "id": "scenario-001",
                "document": "標題：印表機發現無人拿走的機密文件\n問題：你在印表機旁發現一份標示著「ASUS Confidential」的設計圖，但附近沒有人。這時你該怎麼做？\n答案：即使出於善意，也不應隨意接觸或移動不屬於自己權限的資料，任何含有機密資訊的輸出實體圖紙本都應妥善看顧並記得帶走。基本上發現時不主動碰觸也不可窺探文件內容，可以直接用碎紙機將其碎掉，如果是可判斷為正本則立即通知設計中心管理師或文件所有者前來處理，徹底做到「非禮勿視」。",
                "metadata": {
                    "category": "Part A: 辦公室基礎好習慣 (Basic Office Habits)",
                    "title": "印表機發現無人拿走的機密文件",
                    "question": "你在印表機旁發現一份標示著「ASUS Confidential」的設計圖，但附近沒有人。這時你該怎麼做？",
                    "doc_type": "scenario",
                    "content_type": "faq_scenario"
                }
            },
            {
                "id": "scenario-002",
                "document": "標題：密碼政策與安全管理\n問題：什麼是密碼政策？\n答案：密碼政策是組織制定的關於密碼創建、使用和管理的規範，包括密碼複雜度要求、定期更換、多因素驗證等安全措施。良好的密碼政策能有效防範未授權存取和資料外洩風險。",
                "metadata": {
                    "category": "資安基礎",
                    "title": "密碼政策與安全管理", 
                    "question": "什麼是密碼政策？",
                    "doc_type": "scenario",
                    "content_type": "faq_scenario"
                }
            },
            {
                "id": "scenario-003",
                "document": "標題：人離機鎖的重要性\n問題：你只是要去茶水間倒杯水，大概3分鐘就回來，有需要手動鎖定電腦嗎？\n答案：是的，即使只是短暫離開，也應該鎖定電腦。養成「人離機鎖」的習慣是基本的資安防護措施，能防止他人未經授權存取您的工作資料。",
                "metadata": {
                    "category": "Part A: 辦公室基礎好習慣 (Basic Office Habits)",
                    "title": "人離機鎖的重要性",
                    "question": "你只是要去茶水間倒杯水，大概3分鐘就回來，有需要手動鎖定電腦嗎？",
                    "doc_type": "scenario", 
                    "content_type": "faq_scenario"
                }
            }
        ]
        
        # 5. 批次插入
        ids = [item["id"] for item in test_data]
        documents = [item["document"] for item in test_data]
        metadatas = [item["metadata"] for item in test_data]
        
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"✅ 成功插入 {len(test_data)} 筆資料")
        
        # 6. 立即驗證
        count = collection.count()
        print(f"✅ 集合文件數: {count}")
        
        # 7. 測試查詢
        if count > 0:
            test_queries = ["密碼政策", "印表機", "機密文件"]
            for query in test_queries:
                results = collection.query(
                    query_texts=[query],
                    n_results=2,
                    include=["documents", "metadatas", "distances"]
                )
                result_count = len(results['ids'][0]) if results['ids'] else 0
                print(f"✅ 查詢 '{query}': {result_count} 個結果")
        
        return True
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚨 緊急修復腳本")
    print("=" * 40)
    
    if emergency_fix():
        print("\n🎉 緊急修復成功！")
        print("💡 現在測試 AI Service:")
        print("python -c \"import requests; r = requests.post('http://localhost:8000/api/ask', json={'question': '什麼是密碼政策？'}, timeout=30); print('回應:', r.json())\"")
    else:
        print("\n❌ 緊急修復失敗")
