#!/usr/bin/env python3
"""
ChromaDB 數據修復工具
修復 JSON 解析錯誤和數據格式問題
"""

import os
import sys
import json
import traceback
from pathlib import Path

# 添加 ai-service 到路徑
sys.path.append(str(Path(__file__).parent / "ai-service"))

def backup_database():
    """備份現有數據庫"""
    try:
        import shutil
        from datetime import datetime
        
        DB_PATH = "./ai-service/chroma_db"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"./ai-service/chroma_db_backup_{timestamp}"
        
        if os.path.exists(DB_PATH):
            shutil.copytree(DB_PATH, backup_path)
            print(f"✅ 數據庫已備份到: {backup_path}")
            return backup_path
        else:
            print("❌ 原數據庫不存在，無需備份")
            return None
            
    except Exception as e:
        print(f"❌ 備份失敗: {e}")
        return None

def clean_and_rebuild_database():
    """清理並重建數據庫"""
    try:
        print("🔧 開始清理並重建數據庫...")
        
        # 備份現有數據庫
        backup_path = backup_database()
        
        # 刪除現有數據庫
        DB_PATH = "./ai-service/chroma_db"
        if os.path.exists(DB_PATH):
            import shutil
            shutil.rmtree(DB_PATH)
            print("✅ 舊數據庫已刪除")
        
        # 重新運行數據載入
        print("🔄 重新載入數據...")
        os.chdir("./ai-service")
        
        # 運行 ingest.py 重新建立數據庫
        import subprocess
        result = subprocess.run([sys.executable, "ingest.py"], 
                              capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ 數據庫重建成功")
            print("📊 重建輸出:")
            print(result.stdout)
            return True
        else:
            print("❌ 數據庫重建失敗")
            print("錯誤輸出:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 重建過程失敗: {e}")
        traceback.print_exc()
        return False

def test_repaired_database():
    """測試修復後的數據庫"""
    try:
        print("\n🧪 測試修復後的數據庫...")
        
        import chromadb
        from chromadb.config import Settings
        
        DB_PATH = "./chroma_db"  # 在 ai-service 目錄下
        
        # 初始化客戶端
        client = chromadb.PersistentClient(
            path=DB_PATH,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 獲取集合
        collection = client.get_collection("scenarios")
        count = collection.count()
        print(f"📊 修復後集合文檔數量: {count}")
        
        # 測試查詢
        test_queries = ["機密文件", "印表機", "作品集"]
        
        for query in test_queries:
            print(f"\n🔍 測試查詢: '{query}'")
            
            try:
                result = collection.query(
                    query_texts=[query],
                    n_results=3,
                    include=["documents", "metadatas", "distances"]
                )
                
                result_count = len(result['ids'][0]) if result.get('ids') and result['ids'][0] else 0
                print(f"✅ 查詢成功，找到 {result_count} 個結果")
                
                # 檢查結果格式
                if result_count > 0:
                    first_doc = result['documents'][0][0]
                    first_meta = result['metadatas'][0][0]
                    first_dist = result['distances'][0][0]
                    
                    print(f"  第一個結果:")
                    print(f"    距離: {first_dist:.4f}")
                    print(f"    標題: {first_meta.get('title', '未知')}")
                    print(f"    類別: {first_meta.get('category', '未知')}")
                    print(f"    內容預覽: {first_doc[:100]}...")
                
            except Exception as e:
                print(f"❌ 查詢失敗: {e}")
                return False
        
        print("\n✅ 所有測試查詢都成功！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("=" * 60)
    print("🔧 ChromaDB 數據修復工具")
    print("=" * 60)
    
    print("這個工具將:")
    print("1. 備份現有數據庫")
    print("2. 清理並重建數據庫")
    print("3. 測試修復後的數據庫")
    print()
    
    # 確認操作
    response = input("是否繼續修復？(y/N): ").strip().lower()
    if response != 'y':
        print("❌ 操作已取消")
        return
    
    # 執行修復
    success = clean_and_rebuild_database()
    if not success:
        print("❌ 修復失敗，請檢查錯誤信息")
        return
    
    # 測試修復結果
    os.chdir("..")  # 回到根目錄
    test_success = test_repaired_database()
    
    if test_success:
        print("\n" + "=" * 60)
        print("🎉 數據庫修復成功！")
        print("✅ 所有查詢測試都通過")
        print("🚀 現在可以重新啟動 AI Service")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 修復後測試失敗")
        print("請檢查錯誤信息並手動排查")
        print("=" * 60)

if __name__ == "__main__":
    main()
