#!/usr/bin/env python3
"""
深度診斷：為什麼無法回答卡片中的問題
"""
import chromadb
from chromadb.utils import embedding_functions
import sys

def deep_diagnose():
    print("=== 深度診斷：會議白板拍照問題 ===")
    
    try:
        # 連接資料庫
        client = chromadb.PersistentClient(path='chroma_db')
        ef = embedding_functions.OllamaEmbeddingFunction(
            model_name='mxbai-embed-large', 
            url='http://localhost:11434'
        )
        collection = client.get_collection('scenarios', embedding_function=ef)
        
        # 1. 檢查是否有包含「白板」、「拍照」、「Teams」的內容
        print("\n1. 搜尋關鍵詞...")
        keywords = ["白板", "拍照", "Teams", "會議", "手機"]
        
        for keyword in keywords:
            try:
                results = collection.query(
                    query_texts=[keyword],
                    n_results=3,
                    include=["documents", "metadatas", "distances"]
                )
                
                if results['ids'][0]:
                    print(f"\n關鍵詞 '{keyword}' 找到 {len(results['ids'][0])} 個結果:")
                    for i, (doc, meta, dist) in enumerate(zip(
                        results['documents'][0][:2], 
                        results['metadatas'][0][:2], 
                        results['distances'][0][:2]
                    )):
                        title = meta.get('title', '無標題')
                        category = meta.get('category', '無類別')
                        print(f"  {i+1}. [{category}] {title} (距離: {dist:.3f})")
                        if keyword in doc:
                            print(f"     ✅ 文檔包含關鍵詞")
                        else:
                            print(f"     ❌ 文檔不包含關鍵詞")
                else:
                    print(f"關鍵詞 '{keyword}': 無結果")
            except Exception as e:
                print(f"搜尋 '{keyword}' 失敗: {e}")
        
        # 2. 檢查 Part C 類別的所有文檔
        print("\n2. 檢查 Part C 類別文檔...")
        try:
            part_c_results = collection.query(
                query_texts=["會議白板拍照"],
                n_results=10,
                where={"category": "Part C: 機敏資料與高風險工具 (Sensitive Data & High-Risk Tools)"},
                include=["documents", "metadatas", "distances"]
            )
            
            if part_c_results['ids'][0]:
                print(f"Part C 類別找到 {len(part_c_results['ids'][0])} 個結果:")
                for i, (doc, meta, dist) in enumerate(zip(
                    part_c_results['documents'][0], 
                    part_c_results['metadatas'][0], 
                    part_c_results['distances'][0]
                )):
                    title = meta.get('title', '無標題')
                    print(f"  {i+1}. {title} (距離: {dist:.3f})")
                    # 檢查是否包含相關內容
                    if any(word in doc for word in ["白板", "拍照", "Teams", "會議"]):
                        print(f"     ✅ 包含相關內容")
                        print(f"     內容片段: {doc[:100]}...")
                    else:
                        print(f"     ❌ 不包含相關內容")
            else:
                print("Part C 類別: 無結果")
        except Exception as e:
            print(f"檢查 Part C 失敗: {e}")
        
        # 3. 檢查完整的查詢流程
        print("\n3. 模擬完整查詢流程...")
        test_query = "會議結束後，為了方便記錄，我用自己的手機拍下白板上的會議內容，並上傳到自己的Teams聊天室。這樣做是否合規？"
        
        try:
            full_results = collection.query(
                query_texts=[test_query],
                n_results=5,
                include=["documents", "metadatas", "distances"]
            )
            
            if full_results['ids'][0]:
                print(f"完整查詢找到 {len(full_results['ids'][0])} 個結果:")
                for i, (doc, meta, dist) in enumerate(zip(
                    full_results['documents'][0], 
                    full_results['metadatas'][0], 
                    full_results['distances'][0]
                )):
                    title = meta.get('title', '無標題')
                    category = meta.get('category', '無類別')
                    print(f"  {i+1}. [{category}] {title} (距離: {dist:.3f})")
                    
                    # 檢查相關性
                    relevance_score = 0
                    keywords_found = []
                    for word in ["白板", "拍照", "Teams", "會議", "手機", "記錄"]:
                        if word in doc:
                            relevance_score += 1
                            keywords_found.append(word)
                    
                    print(f"     相關性: {relevance_score}/6, 找到關鍵詞: {keywords_found}")
                    if relevance_score >= 2:
                        print(f"     ✅ 高相關性")
                    else:
                        print(f"     ❌ 低相關性")
            else:
                print("完整查詢: 無結果")
        except Exception as e:
            print(f"完整查詢失敗: {e}")
        
        print("\n=== 診斷完成 ===")
        
    except Exception as e:
        print(f"❌ 診斷失敗: {e}")

if __name__ == "__main__":
    deep_diagnose()
