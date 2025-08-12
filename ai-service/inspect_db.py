#!/usr/bin/env python3
"""
資料庫內容檢查器 - 檢查 RAG 資料庫的實際內容與結構
"""
import chromadb
from collections import Counter

def inspect_database():
    print("=== RAG 資料庫內容檢查 ===")
    
    try:
        # 連接資料庫
        client = chromadb.PersistentClient(path='chroma_db')
        collection = client.get_collection('scenarios')
        
        # 基本統計
        total_count = collection.count()
        print(f"總文檔數: {total_count}")
        
        if total_count == 0:
            print("❌ 資料庫為空！需要執行 ingest.py")
            return
        
        # 取得所有 metadata 檢查 category 分佈
        all_results = collection.get(include=['metadatas'])
        categories = [m.get('category', 'None') for m in all_results['metadatas']]
        category_counts = Counter(categories)
        
        print(f"\n=== Category 分佈 ===")
        for cat, count in category_counts.most_common():
            print(f"  {cat}: {count} 筆")
        
        # 檢查是否有 scenario_card
        scenario_cards = [m for m in all_results['metadatas'] if m.get('category') == 'scenario_card']
        print(f"\n=== scenario_card 檢查 ===")
        print(f"scenario_card 數量: {len(scenario_cards)}")
        
        if len(scenario_cards) == 0:
            print("❌ 沒有 scenario_card！這就是為什麼第一層檢索失敗")
            print("檢查 ingest.py 中的 category 設定")
        else:
            print("✓ 有 scenario_card 資料")
            print("前3個 scenario_card:")
            for i, sc in enumerate(scenario_cards[:3]):
                print(f"  {i+1}. title: {sc.get('title', '無')}")
        
        # 檢查最近更新時間（如果有的話）
        print(f"\n=== 資料新鮮度檢查 ===")
        sample_metadata = all_results['metadatas'][:5]
        for i, m in enumerate(sample_metadata):
            title = m.get('title', '無標題')
            print(f"  {i+1}. {title}")
            if 'timestamp' in m:
                print(f"     更新時間: {m['timestamp']}")
            else:
                print(f"     無時間戳記")
        
        # 測試向量檢索
        print(f"\n=== 向量檢索測試 ===")
        test_query = "作品集"
        try:
            results = collection.query(
                query_texts=[test_query],
                n_results=3,
                include=["documents", "metadatas", "distances"]
            )
            print(f"查詢 '{test_query}' 結果:")
            if results['ids'][0]:
                for i, (doc_id, dist) in enumerate(zip(results['ids'][0], results['distances'][0])):
                    metadata = results['metadatas'][0][i]
                    title = metadata.get('title', '無標題')
                    category = metadata.get('category', '無類別')
                    print(f"  {i+1}. [{category}] {title} (距離: {dist:.3f})")
            else:
                print("  ❌ 無檢索結果")
        except Exception as e:
            print(f"  ❌ 向量檢索失敗: {e}")
            
    except Exception as e:
        print(f"❌ 資料庫檢查失敗: {e}")

if __name__ == "__main__":
    inspect_database()
