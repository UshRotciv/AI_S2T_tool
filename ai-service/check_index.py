#!/usr/bin/env python3
"""
索引診斷腳本
用於檢查 ChromaDB 中的索引狀態和內容
"""
import sys
import os

# 添加當前目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import chromadb
    from chromadb.utils import embedding_functions
    print("✓ 成功導入 chromadb 模組")
except ImportError as e:
    print(f"✗ 無法導入 chromadb 模組: {e}")
    sys.exit(1)

try:
    # 連接到 ChromaDB
    client = chromadb.PersistentClient(path="./chroma_db")
    print("✓ 成功連接到 ChromaDB")
    
    # 獲取集合
    try:
        collection = client.get_collection("scenarios")
        print("✓ 成功獲取 scenarios 集合")
        
        # 獲取集合統計信息
        count = collection.count()
        print(f"  集合中文檔數量: {count}")
        
        # 檢查是否存在包含印表機相關內容的文檔
        if count > 0:
            # 執行針對性的查詢測試
            print("\n正在執行針對性的查詢測試...")
            
            test_queries = [
                "免費測試軟體的風險",
                "加密檔案的密碼傳遞",
                "印表機發現無人拿走的機密文件"
            ]

            for query in test_queries:
                print(f"\n--- 查詢: '{query}' ---")
                try:
                    results = collection.query(
                        query_texts=[query],
                        n_results=3, # 檢索3個最相關的結果
                        include=["documents", "metadatas", "distances"]
                    )
                    
                    if results.get('ids') and results['ids'][0]:
                        print("查詢成功！結果:")
                        for i, doc_id in enumerate(results['ids'][0]):
                            metadata = results['metadatas'][0][i]
                            distance = results['distances'][0][i]
                            document = results['documents'][0][i]
                            print(f"  結果 {i+1}: (ID: {doc_id}, 距離: {distance:.4f})")
                            print(f"    標題: {metadata.get('title', 'N/A')}")
                            print(f"    內容: {document[:120].replace('\n', ' ')}...")
                    else:
                        print("  未找到任何結果。")

                except Exception as e:
                    print(f"查詢失敗: {e}")

                import traceback
                print(f"\n✗ 查詢時發生嚴重錯誤:")
                print(str(e))
                print("\n詳細錯誤追蹤:")
                traceback.print_exc()
        else:
            print("  集合為空")
            
    except Exception as e:
        print(f"✗ 無法獲取 scenarios 集合: {e}")
        
        # 嘗試列出所有集合
        print("\n可用的集合:")
        collections = client.list_collections()
        for collection in collections:
            print(f"  - {collection.name}")
            
except Exception as e:
    print(f"✗ 無法連接到 ChromaDB: {e}")
    sys.exit(1)

print("\n診斷完成")
