#!/usr/bin/env python3
"""
簡單的 ChromaDB 測試腳本
按步驟驗證每個環節
"""

import chromadb
import json
import os

def step1_check_db():
    """步驟1: 檢查資料庫狀態"""
    print("步驟1: 檢查 ChromaDB 狀態")
    try:
        client = chromadb.PersistentClient(path="./chroma_db")
        collections = client.list_collections()
        print(f"  可用集合: {[c.name for c in collections]}")
        
        if collections:
            for collection in collections:
                count = collection.count()
                print(f"  集合 '{collection.name}' 文件數: {count}")
        
        return client
    except Exception as e:
        print(f"  錯誤: {e}")
        return None

def step2_test_simple_insert(client):
    """步驟2: 測試簡單插入"""
    print("\n步驟2: 測試簡單資料插入")
    try:
        # 嘗試獲取或建立集合
        try:
            collection = client.get_collection("test_collection")
            print("  使用現有 test_collection")
        except:
            collection = client.create_collection("test_collection")
            print("  建立新的 test_collection")
        
        # 插入測試資料
        test_data = {
            "documents": ["這是一個測試文件"],
            "metadatas": [{"category": "test"}],
            "ids": ["test_001"]
        }
        
        collection.add(**test_data)
        print("  測試資料插入成功")
        
        # 立即驗證
        count = collection.count()
        print(f"  插入後文件數: {count}")
        
        # 測試查詢
        results = collection.query(
            query_texts=["測試"],
            n_results=1
        )
        print(f"  查詢結果數: {len(results['ids'][0]) if results['ids'] else 0}")
        
        return True
    except Exception as e:
        print(f"  錯誤: {e}")
        return False

def step3_check_source_data():
    """步驟3: 檢查原始資料來源"""
    print("\n步驟3: 檢查原始資料來源")
    
    # 檢查 app-server 的 SQLite 資料
    sqlite_path = "../app-server/sqlite/db.sqlite"
    if os.path.exists(sqlite_path):
        print(f"  ✅ SQLite 資料庫存在: {sqlite_path}")
    else:
        print(f"  ❌ SQLite 資料庫不存在: {sqlite_path}")
    
    # 檢查 JSON 檔案
    json_files = [
        "../app-server/scenarios.json",
        "../app-server/groups.json"
    ]
    
    for json_file in json_files:
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"  ✅ {json_file}: {len(data)} 筆資料")
            except Exception as e:
                print(f"  ❌ {json_file}: 讀取錯誤 - {e}")
        else:
            print(f"  ❌ {json_file}: 檔案不存在")

def step4_simple_ingest():
    """步驟4: 簡單的資料匯入測試"""
    print("\n步驟4: 簡單資料匯入測試")
    
    try:
        client = chromadb.PersistentClient(path="./chroma_db")
        
        # 刪除舊的 scenarios 集合（如果存在）
        try:
            client.delete_collection("scenarios")
            print("  刪除舊的 scenarios 集合")
        except:
            pass
        
        # 建立新集合
        collection = client.create_collection("scenarios")
        print("  建立新的 scenarios 集合")
        
        # 讀取一筆測試資料
        scenarios_file = "../app-server/scenarios.json"
        if os.path.exists(scenarios_file):
            with open(scenarios_file, 'r', encoding='utf-8') as f:
                scenarios = json.load(f)
            
            if scenarios:
                # 只取第一筆資料進行測試
                first_scenario = scenarios[0]
                
                # 準備資料
                doc_text = f"標題: {first_scenario.get('title', '')}\n問題: {first_scenario.get('question', '')}\n答案: {first_scenario.get('answer', '')}"
                
                collection.add(
                    documents=[doc_text],
                    metadatas=[{
                        "title": first_scenario.get('title', ''),
                        "category": first_scenario.get('category', ''),
                        "id": first_scenario.get('id', '')
                    }],
                    ids=[f"scenario_{first_scenario.get('id', '001')}"]
                )
                
                print("  插入第一筆測試資料成功")
                
                # 驗證
                count = collection.count()
                print(f"  集合文件數: {count}")
                
                # 測試查詢
                results = collection.query(
                    query_texts=[first_scenario.get('title', '')],
                    n_results=1
                )
                print(f"  查詢結果數: {len(results['ids'][0]) if results['ids'] else 0}")
                
                return True
        
        return False
        
    except Exception as e:
        print(f"  錯誤: {e}")
        return False

def main():
    """主要測試流程"""
    print("🔧 ChromaDB 按步驟診斷與修復")
    print("=" * 50)
    
    # 步驟 1: 檢查資料庫
    client = step1_check_db()
    if not client:
        print("❌ 無法連接到 ChromaDB")
        return
    
    # 步驟 2: 測試簡單插入
    if step2_test_simple_insert(client):
        print("✅ 簡單插入測試成功")
    else:
        print("❌ 簡單插入測試失敗")
        return
    
    # 步驟 3: 檢查原始資料
    step3_check_source_data()
    
    # 步驟 4: 簡單資料匯入
    if step4_simple_ingest():
        print("✅ 簡單資料匯入成功")
        print("💡 現在可以測試 AI Service 是否能正常查詢")
    else:
        print("❌ 簡單資料匯入失敗")

if __name__ == "__main__":
    main()
