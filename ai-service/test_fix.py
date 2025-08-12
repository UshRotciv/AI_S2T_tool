#!/usr/bin/env python3
"""
測試修復後的分層檢索邏輯
"""
import sys
sys.path.append('.')

from main import layered_search
import chromadb
from chromadb.utils import embedding_functions

def test_fixed_search():
    print("=== 測試修復後的分層檢索 ===")
    
    try:
        # 初始化
        client = chromadb.PersistentClient(path='chroma_db')
        ef = embedding_functions.OllamaEmbeddingFunction(
            model_name='mxbai-embed-large', 
            url='http://localhost:11434'
        )
        collection = client.get_collection('scenarios', embedding_function=ef)
        
        # 測試查詢
        test_queries = ["作品集可以公開嗎", "印表機機密文件", "密碼管理"]
        
        for query in test_queries:
            print(f"\n--- 測試查詢: {query} ---")
            result, search_type = layered_search(collection, query, n_results=5)
            
            print(f"檢索類型: {search_type}")
            if result and result.get('ids') and result['ids'][0]:
                print(f"結果數量: {len(result['ids'][0])}")
                print("前3個結果:")
                for i, metadata in enumerate(result['metadatas'][0][:3]):
                    category = metadata.get('category', '無')
                    title = metadata.get('title', '無標題')
                    distance = result['distances'][0][i] if i < len(result['distances'][0]) else 'N/A'
                    print(f"  {i+1}. [{category}] {title} (距離: {distance})")
            else:
                print("❌ 無結果")
        
        print("\n=== 測試完成 ===")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

if __name__ == "__main__":
    test_fixed_search()
