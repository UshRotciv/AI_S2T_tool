#!/usr/bin/env python3
"""
驗證資料庫中是否有卡片的完整內容
"""
import chromadb
from chromadb.utils import embedding_functions

def verify_card_content():
    print("=== 驗證卡片內容是否存在 ===")
    
    try:
        # 連接資料庫
        client = chromadb.PersistentClient(path='chroma_db')
        ef = embedding_functions.OllamaEmbeddingFunction(
            model_name='mxbai-embed-large', 
            url='http://localhost:11434'
        )
        collection = client.get_collection('scenarios', embedding_function=ef)
        
        # 根據用戶提供的卡片內容，搜尋關鍵片段
        card_keywords = [
            "會議白板的拍照處理",
            "會議結束後，為了方便記錄",
            "用自己的手機拍下白板上的會議內容",
            "上傳到自己的Teams聊天室",
            "此作法存在風險，但可在特定規範下進行",
            "根據主管授權，因公需求可有限度地使用手機拍照記錄",
            "必須遵守SOP",
            "檔案必須透過公司認可的軟體",
            "Teams、公司Email",
            "傳輸完成後，必須「立即」從個人手機裝置中刪除該照片",
            "遵守「BYOD」（個人設備借辦公）的暫行規範",
            "照片等資料上傳至公司系統後，應立即從個人裝置刪除",
            "禁止使用私人的通訊軟體或雲端服務傳輸公務資料"
        ]
        
        print("搜尋卡片中的關鍵內容...")
        found_content = []
        
        for i, keyword in enumerate(card_keywords, 1):
            print(f"\n{i}. 搜尋: '{keyword}'")
            
            try:
                results = collection.query(
                    query_texts=[keyword],
                    n_results=3,
                    include=["documents", "metadatas", "distances"]
                )
                
                if results['ids'][0]:
                    best_match = results['documents'][0][0]
                    best_distance = results['distances'][0][0]
                    best_meta = results['metadatas'][0][0]
                    
                    print(f"   最佳匹配 (距離: {best_distance:.3f}):")
                    print(f"   標題: {best_meta.get('title', '無標題')}")
                    print(f"   類別: {best_meta.get('category', '無類別')}")
                    
                    # 檢查是否包含關鍵詞
                    if keyword in best_match:
                        print(f"   ✅ 完全匹配")
                        found_content.append(keyword)
                    elif any(word in best_match for word in keyword.split()[:3]):
                        print(f"   🔶 部分匹配")
                        found_content.append(f"部分:{keyword}")
                    else:
                        print(f"   ❌ 無匹配")
                    
                    print(f"   內容片段: {best_match[:150]}...")
                else:
                    print(f"   ❌ 無結果")
                    
            except Exception as e:
                print(f"   ❌ 搜尋失敗: {e}")
        
        # 總結
        print(f"\n=== 總結 ===")
        print(f"搜尋關鍵內容: {len(card_keywords)} 項")
        print(f"找到匹配內容: {len(found_content)} 項")
        print(f"匹配率: {len(found_content)/len(card_keywords)*100:.1f}%")
        
        if len(found_content) < len(card_keywords) * 0.5:
            print("❌ 資料庫中缺少大量卡片內容")
        elif len(found_content) < len(card_keywords) * 0.8:
            print("🔶 資料庫中部分缺少卡片內容")
        else:
            print("✅ 資料庫中包含大部分卡片內容")
        
        print("\n找到的匹配內容:")
        for content in found_content:
            print(f"  - {content}")
            
    except Exception as e:
        print(f"❌ 驗證失敗: {e}")

if __name__ == "__main__":
    verify_card_content()
