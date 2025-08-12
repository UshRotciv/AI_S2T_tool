#!/usr/bin/env python3
"""
最小化 ChromaDB 測試
專門測試資料寫入問題
"""

import chromadb
import os

def test_minimal_insert():
    """最小化插入測試"""
    print("🧪 最小化 ChromaDB 插入測試")
    
    try:
        # 1. 連接資料庫
        print("1. 連接 ChromaDB...")
        client = chromadb.PersistentClient(path="./chroma_db")
        print("   ✅ 連接成功")
        
        # 2. 刪除舊集合（如果存在）
        print("2. 清理舊集合...")
        try:
            client.delete_collection("test_minimal")
            print("   ✅ 刪除舊集合")
        except:
            print("   ✅ 無舊集合需刪除")
        
        # 3. 建立新集合
        print("3. 建立新集合...")
        collection = client.create_collection("test_minimal")
        print("   ✅ 集合建立成功")
        
        # 4. 插入最簡單的資料
        print("4. 插入測試資料...")
        collection.add(
            documents=["這是一個測試文件"],
            ids=["test_001"]
        )
        print("   ✅ 資料插入成功")
        
        # 5. 立即驗證
        print("5. 驗證資料...")
        count = collection.count()
        print(f"   文件數量: {count}")
        
        if count > 0:
            print("   ✅ 資料寫入成功！")
            
            # 6. 測試查詢
            print("6. 測試查詢...")
            results = collection.query(
                query_texts=["測試"],
                n_results=1
            )
            
            if results['ids'] and len(results['ids'][0]) > 0:
                print("   ✅ 查詢成功！")
                print(f"   查詢結果: {results['ids'][0][0]}")
                return True
            else:
                print("   ❌ 查詢失敗")
                return False
        else:
            print("   ❌ 資料寫入失敗")
            return False
            
    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_metadata():
    """測試帶 metadata 的插入"""
    print("\n🧪 測試帶 metadata 的插入")
    
    try:
        client = chromadb.PersistentClient(path="./chroma_db")
        
        # 刪除舊集合
        try:
            client.delete_collection("test_metadata")
        except:
            pass
        
        # 建立新集合
        collection = client.create_collection("test_metadata")
        
        # 插入帶 metadata 的資料
        collection.add(
            documents=["這是一個帶 metadata 的測試文件"],
            metadatas=[{"category": "test", "title": "測試標題"}],
            ids=["meta_001"]
        )
        
        count = collection.count()
        print(f"   文件數量: {count}")
        
        if count > 0:
            print("   ✅ 帶 metadata 的資料寫入成功！")
            return True
        else:
            print("   ❌ 帶 metadata 的資料寫入失敗")
            return False
            
    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
        return False

def main():
    """主測試流程"""
    print("🔧 ChromaDB 最小化測試")
    print("=" * 40)
    
    # 測試1: 最簡單的插入
    success1 = test_minimal_insert()
    
    # 測試2: 帶 metadata 的插入
    success2 = test_with_metadata()
    
    print("\n" + "=" * 40)
    print("📊 測試結果總結")
    
    if success1:
        print("✅ 基本插入功能正常")
    else:
        print("❌ 基本插入功能異常")
    
    if success2:
        print("✅ metadata 插入功能正常")
    else:
        print("❌ metadata 插入功能異常")
    
    if success1 and success2:
        print("💡 ChromaDB 功能正常，問題可能在 ingest.py 的邏輯")
    else:
        print("💡 ChromaDB 基本功能有問題，需要檢查環境")

if __name__ == "__main__":
    main()
