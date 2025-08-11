#!/usr/bin/env python3
"""
RAG 檢索診斷腳本
用於深入分析向量檢索和 LLM Re-ranking 過程
"""

import requests
import json
import chromadb
from chromadb.utils import embedding_functions
import os

# 設定
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, 'chroma_db')
API_BASE = "http://localhost:8001"

def test_vector_retrieval():
    """測試向量檢索階段"""
    print("=== 向量檢索階段測試 ===")
    
    # 連接資料庫
    client = chromadb.PersistentClient(path=DB_PATH)
    sentence_transformer_ef = embedding_functions.OllamaEmbeddingFunction(
        model_name="mxbai-embed-large",
        url="http://localhost:11434",
    )
    
    try:
        collection = client.get_collection("scenarios", embedding_function=sentence_transformer_ef)
        print(f"✅ 成功連接到 scenarios 集合")
        
        # 測試查詢
        test_queries = [
            "免費測試軟體的風險",
            "印表機發現無人拿走的機密文件",
            "免費軟體",
            "測試軟體",
            "軟體風險"
        ]
        
        for query in test_queries:
            print(f"\n--- 查詢: '{query}' ---")
            results = collection.query(
                query_texts=[query],
                n_results=5,
                include=["documents", "metadatas", "distances"]
            )
            
            if results['ids'] and results['ids'][0]:
                print(f"找到 {len(results['ids'][0])} 個結果:")
                for i, doc_id in enumerate(results['ids'][0]):
                    metadata = results['metadatas'][0][i] if results.get('metadatas') and results['metadatas'][0] else {}
                    distance = results['distances'][0][i] if results.get('distances') and results['distances'][0] else None
                    title = metadata.get('title', '未知標題')
                    category = metadata.get('category', '未知類別')
                    
                    print(f"  {i+1}. ID: {doc_id}")
                    print(f"     標題: {title}")
                    print(f"     類別: {category}")
                    print(f"     距離: {distance:.4f}")
                    print(f"     內容預覽: {results['documents'][0][i][:100]}...")
            else:
                print("❌ 未找到任何結果")
                
    except Exception as e:
        print(f"❌ 資料庫連接失敗: {e}")

def test_api_with_debug():
    """測試 API 並顯示詳細過程"""
    print("\n=== API 測試階段 ===")
    
    test_queries = [
        "免費測試軟體的風險",
        "印表機發現無人拿走的機密文件"
    ]
    
    for query in test_queries:
        print(f"\n--- API 測試: '{query}' ---")
        
        # 先測試 debug 端點
        try:
            debug_response = requests.get(f"{API_BASE}/api/debug/sample", 
                                        params={"q": query, "k": 5})
            if debug_response.status_code == 200:
                debug_data = debug_response.json()
                print(f"Debug 端點找到 {len(debug_data.get('results', []))} 個結果")
                for i, result in enumerate(debug_data.get('results', [])):
                    print(f"  {i+1}. {result.get('title', 'N/A')} (距離: {result.get('distance', 'N/A'):.4f})")
            else:
                print(f"❌ Debug 端點失敗: {debug_response.status_code}")
        except Exception as e:
            print(f"❌ Debug 端點錯誤: {e}")
        
        # 再測試正式 API
        try:
            api_response = requests.post(f"{API_BASE}/api/ask", 
                                       json={"question": query})
            if api_response.status_code == 200:
                api_data = api_response.json()
                answer = api_data.get('answer', '')
                sources = api_data.get('sources', [])
                print(f"API 回答長度: {len(answer)} 字符")
                print(f"API 來源數量: {len(sources)}")
                print(f"回答預覽: {answer[:100]}...")
                
                if sources:
                    print("來源詳情:")
                    for i, source in enumerate(sources):
                        print(f"  {i+1}. {source.get('metadata', {}).get('title', 'N/A')}")
                else:
                    print("❌ 無來源返回 - 可能被 LLM Re-ranking 過濾掉了")
            else:
                print(f"❌ API 失敗: {api_response.status_code}")
        except Exception as e:
            print(f"❌ API 錯誤: {e}")

def check_database_stats():
    """檢查資料庫統計資訊"""
    print("\n=== 資料庫統計 ===")
    
    try:
        client = chromadb.PersistentClient(path=DB_PATH)
        collection = client.get_collection("scenarios")
        
        # 獲取所有文件
        all_results = collection.get(include=["documents", "metadatas"])
        total_count = len(all_results['ids']) if all_results.get('ids') else 0
        
        print(f"總文件數: {total_count}")
        
        # 統計類別分布
        if all_results.get('metadatas'):
            categories = {}
            for metadata in all_results['metadatas']:
                category = metadata.get('category', '未知')
                categories[category] = categories.get(category, 0) + 1
            
            print("類別分布:")
            for category, count in categories.items():
                print(f"  {category}: {count} 個")
                
        # 查找包含特定關鍵字的文件
        keywords = ["免費", "軟體", "測試", "風險", "印表機", "機密"]
        print("\n關鍵字分布:")
        for keyword in keywords:
            count = 0
            if all_results.get('documents'):
                for doc in all_results['documents']:
                    if keyword in doc:
                        count += 1
            print(f"  包含 '{keyword}': {count} 個文件")
            
    except Exception as e:
        print(f"❌ 統計失敗: {e}")

if __name__ == "__main__":
    print("🔍 RAG 系統診斷開始...")
    
    check_database_stats()
    test_vector_retrieval() 
    test_api_with_debug()
    
    print("\n🔍 診斷完成！")
