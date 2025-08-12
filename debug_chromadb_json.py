#!/usr/bin/env python3
"""
ChromaDB JSON 解析錯誤診斷工具
用於診斷和修復 "Extra data: line 1 column 5 (char 4)" 錯誤
"""

import os
import sys
import json
import traceback
from pathlib import Path

# 添加 ai-service 到路徑
sys.path.append(str(Path(__file__).parent / "ai-service"))

def test_chromadb_connection():
    """測試 ChromaDB 基本連接"""
    try:
        import chromadb
        from chromadb.config import Settings
        
        DB_PATH = "./ai-service/chroma_db"
        
        print("🔍 測試 ChromaDB 連接...")
        print(f"資料庫路徑: {DB_PATH}")
        
        # 初始化 ChromaDB 客戶端
        client = chromadb.PersistentClient(
            path=DB_PATH,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        print("✅ ChromaDB 客戶端初始化成功")
        
        # 獲取集合
        collection = client.get_collection("scenarios")
        print("✅ 成功獲取 scenarios 集合")
        
        # 獲取集合統計
        count = collection.count()
        print(f"📊 集合文檔數量: {count}")
        
        return client, collection
        
    except Exception as e:
        print(f"❌ ChromaDB 連接失敗: {e}")
        traceback.print_exc()
        return None, None

def test_simple_query(collection):
    """測試簡單查詢"""
    try:
        print("\n🔍 測試簡單查詢...")
        
        # 最簡單的查詢
        result = collection.query(
            query_texts=["測試"],
            n_results=1,
            include=["documents", "metadatas", "distances"]
        )
        
        print("✅ 簡單查詢成功")
        print(f"結果類型: {type(result)}")
        print(f"結果鍵: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        
        return result
        
    except Exception as e:
        print(f"❌ 簡單查詢失敗: {e}")
        traceback.print_exc()
        return None

def test_metadata_query(collection):
    """測試帶 metadata 過濾的查詢"""
    try:
        print("\n🔍 測試 metadata 查詢...")
        
        # 測試 where 條件查詢
        result = collection.query(
            query_texts=["機密"],
            n_results=3,
            where={"category": {"$ne": "rule_document"}},
            include=["documents", "metadatas", "distances"]
        )
        
        print("✅ Metadata 查詢成功")
        return result
        
    except Exception as e:
        print(f"❌ Metadata 查詢失敗: {e}")
        traceback.print_exc()
        return None

def inspect_result_structure(result):
    """詳細檢查查詢結果結構"""
    if not result:
        print("❌ 結果為空，無法檢查")
        return
    
    try:
        print("\n🔍 檢查結果結構...")
        print(f"結果類型: {type(result)}")
        
        if isinstance(result, dict):
            print(f"結果鍵: {list(result.keys())}")
            
            for key, value in result.items():
                print(f"\n鍵 '{key}':")
                print(f"  類型: {type(value)}")
                print(f"  長度: {len(value) if hasattr(value, '__len__') else 'N/A'}")
                
                if isinstance(value, list) and len(value) > 0:
                    print(f"  第一個元素類型: {type(value[0])}")
                    if isinstance(value[0], list) and len(value[0]) > 0:
                        print(f"  第一個子元素類型: {type(value[0][0])}")
                        
                        # 檢查是否有問題的 JSON 字符串
                        if isinstance(value[0][0], str):
                            sample = value[0][0]
                            print(f"  樣本內容前100字符: {repr(sample[:100])}")
                            
                            # 嘗試解析為 JSON
                            try:
                                json.loads(sample)
                                print("  ✅ JSON 格式正確")
                            except json.JSONDecodeError as je:
                                print(f"  ❌ JSON 解析錯誤: {je}")
                                print(f"  問題位置: line {je.lineno}, column {je.colno}")
        
        print("✅ 結構檢查完成")
        
    except Exception as e:
        print(f"❌ 結構檢查失敗: {e}")
        traceback.print_exc()

def test_problematic_queries():
    """測試導致錯誤的具體查詢"""
    client, collection = test_chromadb_connection()
    if not collection:
        return
    
    # 測試導致錯誤的查詢
    problematic_queries = [
        "什麼是機密文件？",
        "印表機使用注意事項",
        "作品集準備規範"
    ]
    
    for query in problematic_queries:
        print(f"\n🔍 測試問題查詢: '{query}'")
        
        try:
            # 測試第一層查詢（Part A-D）
            scenario_categories = [
                "Part A: 辦公室基礎好習慣 (Basic Office Habits)",
                "Part B: 數位檔案的溝通與傳遞 (Digital File Communication & Transfer)",
                "Part C: 機敏資料與高風險工具 (Sensitive Data & High-Risk Tools)",
                "Part D: 智慧財產與你的權責 (Intellectual Property & Your Responsibilities)"
            ]
            
            result = collection.query(
                query_texts=[query],
                n_results=7,
                where={"category": {"$in": scenario_categories}},
                include=["documents", "metadatas", "distances"]
            )
            
            print(f"✅ 第一層查詢成功，結果數量: {len(result['ids'][0]) if result.get('ids') and result['ids'][0] else 0}")
            inspect_result_structure(result)
            
        except Exception as e:
            print(f"❌ 第一層查詢失敗: {e}")
            traceback.print_exc()
            
            # 如果是 JSON 錯誤，嘗試更詳細的診斷
            if "Extra data" in str(e):
                print("🚨 發現 JSON 解析錯誤！")
                print("這可能是由於 ChromaDB 中存儲的數據格式問題")

def main():
    """主函數"""
    print("=" * 60)
    print("🔧 ChromaDB JSON 解析錯誤診斷工具")
    print("=" * 60)
    
    # 基本連接測試
    client, collection = test_chromadb_connection()
    if not collection:
        print("❌ 無法連接到 ChromaDB，診斷結束")
        return
    
    # 簡單查詢測試
    result = test_simple_query(collection)
    if result:
        inspect_result_structure(result)
    
    # Metadata 查詢測試
    result = test_metadata_query(collection)
    if result:
        inspect_result_structure(result)
    
    # 問題查詢測試
    test_problematic_queries()
    
    print("\n" + "=" * 60)
    print("🏁 診斷完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
