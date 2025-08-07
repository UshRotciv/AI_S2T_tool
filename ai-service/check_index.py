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
            # 嘗試查詢包含印表機的文檔
            results = collection.query(
                query_texts=["印表機 機密文件"],
                n_results=min(5, count),
                include=["documents", "metadatas", "distances"]
            )
            
            print(f"\n查詢結果:")
            if results['ids'] and len(results['ids'][0]) > 0:
                for i, (doc_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
                    metadata = results['metadatas'][0][i] if i < len(results['metadatas'][0]) else {}
                    title = metadata.get('title', '未知標題')
                    category = metadata.get('category', '未知類別')
                    
                    print(f"  結果 {i+1}:")
                    print(f"    ID: {doc_id}")
                    print(f"    標題: {title}")
                    print(f"    類別: {category}")
                    print(f"    距離: {distance:.4f}")
                    
                    # 顯示文檔內容的前200個字符
                    content = results['documents'][0][i]
                    print(f"    內容預覽: {content[:200]}...")
                    
                    # 檢查是否包含關鍵詞
                    if '印表機' in content and '機密' in content:
                        print(f"    ✓ 包含印表機和機密關鍵詞")
            else:
                print("  未找到相關文檔")
                
                # 嘗試列出所有文檔的標題
                print("\n列出所有文檔標題:")
                all_results = collection.get(include=["metadatas"])
                if all_results['ids']:
                    for i, doc_id in enumerate(all_results['ids'][:10]):  # 只顯示前10個
                        metadata = all_results['metadatas'][i] if i < len(all_results['metadatas']) else {}
                        title = metadata.get('title', '未知標題')
                        category = metadata.get('category', '未知類別')
                        print(f"    {i+1}. [{category}] {title}")
                    if len(all_results['ids']) > 10:
                        print(f"    ... 還有 {len(all_results['ids']) - 10} 個文檔")
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
