#!/usr/bin/env python3
"""
修復 ChromaDB 連線問題
重建資料庫並重新匯入資料
"""

import os
import shutil
import chromadb
from pathlib import Path

def backup_old_db():
    """備份舊資料庫"""
    chroma_path = Path("./chroma_db")
    if chroma_path.exists():
        backup_path = Path("./chroma_db_backup")
        if backup_path.exists():
            shutil.rmtree(backup_path)
        shutil.move(str(chroma_path), str(backup_path))
        print(f"✅ 舊資料庫已備份至: {backup_path}")
        return True
    else:
        print("ℹ️  沒有找到舊資料庫")
        return False

def create_new_db():
    """建立新的 ChromaDB 資料庫"""
    try:
        client = chromadb.PersistentClient(path="./chroma_db")
        
        # 建立 scenarios 集合
        collection = client.create_collection(
            name="scenarios",
            metadata={"description": "資安情境卡片向量資料庫"}
        )
        
        print(f"✅ 新資料庫建立成功")
        print(f"✅ scenarios 集合建立成功")
        return client, collection
        
    except Exception as e:
        print(f"❌ 建立新資料庫失敗: {e}")
        return None, None

def test_new_db():
    """測試新資料庫"""
    try:
        client = chromadb.PersistentClient(path="./chroma_db")
        collections = client.list_collections()
        collection_names = [c.name for c in collections]
        
        print(f"✅ 資料庫連線測試成功")
        print(f"✅ 可用集合: {collection_names}")
        
        if "scenarios" in collection_names:
            collection = client.get_collection("scenarios")
            count = collection.count()
            print(f"✅ scenarios 集合文件數: {count}")
            return True
        else:
            print("⚠️  scenarios 集合不存在")
            return False
            
    except Exception as e:
        print(f"❌ 資料庫測試失敗: {e}")
        return False

def main():
    """主要修復流程"""
    print("🔧 修復 ChromaDB 連線問題")
    print("=" * 40)
    
    # 1. 備份舊資料庫
    print("\n步驟 1: 備份舊資料庫")
    backup_old_db()
    
    # 2. 建立新資料庫
    print("\n步驟 2: 建立新資料庫")
    client, collection = create_new_db()
    
    if client is None:
        print("❌ 修復失敗")
        return False
    
    # 3. 測試新資料庫
    print("\n步驟 3: 測試新資料庫")
    success = test_new_db()
    
    if success:
        print("\n✅ ChromaDB 修復成功！")
        print("💡 下一步: 執行 ingest.py 重新匯入資料")
        print("   指令: python ingest.py")
    else:
        print("\n❌ 修復未完成，需要進一步診斷")
    
    return success

if __name__ == "__main__":
    main()
