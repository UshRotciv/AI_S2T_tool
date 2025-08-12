#!/usr/bin/env python3
"""
檢查特定的會議白板內容是否在資料庫中
"""
import chromadb
from chromadb.utils import embedding_functions

def check_whiteboard_content():
    print("=== 檢查會議白板內容是否在資料庫中 ===")
    
    try:
        # 連接資料庫
        client = chromadb.PersistentClient(path='chroma_db')
        ef = embedding_functions.OllamaEmbeddingFunction(
            model_name='mxbai-embed-large', 
            url='http://localhost:11434'
        )
        collection = client.get_collection('scenarios', embedding_function=ef)
        
        # 檢查是否有 scenario-new-010
        print("1. 檢查 ID 'scenario-new-010'...")
        try:
            result = collection.get(ids=["scenario-new-010"])
            if result['ids']:
                print("✅ 找到 scenario-new-010")
                print(f"   文檔數量: {len(result['documents'])}")
                if result['documents']:
                    print(f"   內容片段: {result['documents'][0][:150]}...")
                if result['metadatas']:
                    meta = result['metadatas'][0]
                    print(f"   標題: {meta.get('title', '無')}")
                    print(f"   類別: {meta.get('category', '無')}")
            else:
                print("❌ 未找到 scenario-new-010")
        except Exception as e:
            print(f"❌ 檢查 ID 失敗: {e}")
        
        # 檢查是否有標題匹配
        print("\n2. 搜尋標題 '會議白板的拍照處理'...")
        try:
            results = collection.query(
                query_texts=["會議白板的拍照處理"],
                n_results=5,
                include=["documents", "metadatas", "distances"]
            )
            
            if results['ids'][0]:
                print(f"✅ 找到 {len(results['ids'][0])} 個結果")
                for i, (doc, meta, dist) in enumerate(zip(
                    results['documents'][0], 
                    results['metadatas'][0], 
                    results['distances'][0]
                )):
                    title = meta.get('title', '無標題')
                    print(f"   {i+1}. {title} (距離: {dist:.3f})")
                    if "會議白板" in title:
                        print("      ✅ 標題匹配")
                    if "會議白板" in doc:
                        print("      ✅ 內容匹配")
            else:
                print("❌ 搜尋標題無結果")
        except Exception as e:
            print(f"❌ 搜尋標題失敗: {e}")
        
        # 檢查完整問題
        print("\n3. 搜尋完整問題...")
        question = "會議結束後，為了方便記錄，我用自己的手機拍下白板上的會議內容，並上傳到自己的Teams聊天室。這樣做是否合規？"
        try:
            results = collection.query(
                query_texts=[question],
                n_results=5,
                include=["documents", "metadatas", "distances"]
            )
            
            if results['ids'][0]:
                print(f"✅ 找到 {len(results['ids'][0])} 個結果")
                for i, (doc, meta, dist) in enumerate(zip(
                    results['documents'][0], 
                    results['metadatas'][0], 
                    results['distances'][0]
                )):
                    title = meta.get('title', '無標題')
                    print(f"   {i+1}. {title} (距離: {dist:.3f})")
                    if "白板" in doc and "Teams" in doc:
                        print("      ✅ 內容高度相關")
                        print(f"      內容: {doc[:200]}...")
            else:
                print("❌ 搜尋完整問題無結果")
        except Exception as e:
            print(f"❌ 搜尋完整問題失敗: {e}")
        
        # 檢查資料庫總數
        print("\n4. 檢查資料庫狀態...")
        try:
            count_result = collection.count()
            print(f"資料庫總文檔數: {count_result}")
            
            # 檢查最近的文檔
            recent = collection.peek(limit=5)
            if recent['ids']:
                print("最近的文檔 ID:")
                for doc_id in recent['ids']:
                    print(f"  - {doc_id}")
        except Exception as e:
            print(f"❌ 檢查資料庫狀態失敗: {e}")
        
    except Exception as e:
        print(f"❌ 連接失敗: {e}")

if __name__ == "__main__":
    check_whiteboard_content()
