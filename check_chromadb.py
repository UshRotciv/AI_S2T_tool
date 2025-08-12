#!/usr/bin/env python3
"""
ChromaDB 狀態檢查工具
檢查資料庫連接、集合數量和文檔數量
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-service'))

def check_chromadb():
    try:
        import chromadb
        print("✅ ChromaDB 模組載入成功")
        
        # 連接到資料庫
        db_path = os.path.join('ai-service', 'chroma_db')
        client = chromadb.PersistentClient(path=db_path)
        print(f"✅ 成功連接到資料庫: {db_path}")
        
        # 列出所有集合
        collections = client.list_collections()
        print(f"📊 找到 {len(collections)} 個集合:")
        
        total_docs = 0
        for collection in collections:
            count = collection.count()
            total_docs += count
            print(f"  - {collection.name}: {count} 個文檔")
        
        print(f"📈 總文檔數量: {total_docs}")
        
        if total_docs > 0:
            print("✅ ChromaDB 資料載入正常")
            return True
        else:
            print("❌ ChromaDB 沒有資料，需要重新載入")
            return False
            
    except ImportError as e:
        print(f"❌ ChromaDB 模組載入失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ ChromaDB 檢查失敗: {e}")
        return False

if __name__ == "__main__":
    print("=== ChromaDB 狀態檢查 ===")
    success = check_chromadb()
    sys.exit(0 if success else 1)
