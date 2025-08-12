#!/usr/bin/env python3
"""
simple_ingest.py - Smoke Test 版本
- 快速驗證 ChromaDB 寫入/查詢功能
- 使用與 ingest.py 一致的 embedding function
- 支援環境變數配置
"""

import os
import json
import chromadb
from chromadb.utils import embedding_functions
from datetime import datetime

# 環境設定（與 ingest.py 一致）
os.environ.setdefault("CHROMA_TELEMETRY_ENABLED", "false")

CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "scenarios")
EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "sentence").lower()
SENTENCE_MODEL = os.getenv("SENTENCE_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mxbai-embed-large")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

def build_embedding_fn():
    """建立與 ingest.py 一致的 embedding function"""
    if EMBEDDING_BACKEND == "ollama":
        try:
            print(f"[*] 使用 Ollama embedding: {OLLAMA_MODEL} @ {OLLAMA_URL}")
            return embedding_functions.OllamaEmbeddingFunction(
                model_name=OLLAMA_MODEL, url=OLLAMA_URL
            )
        except Exception as e:
            print(f"[!] Ollama 初始化失敗: {e}，回退到 sentence-transformers")
    
    print(f"[*] 使用 SentenceTransformer embedding: {SENTENCE_MODEL}")
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=SENTENCE_MODEL
    )

def simple_ingest():
    """簡化的資料匯入測試"""
    print("🔧 Simple Ingest - Smoke Test")
    print(f"[*] Embedding 後端：{EMBEDDING_BACKEND.upper()}")
    
    try:
        # 1. 連接 ChromaDB
        print("[1] 連接 ChromaDB...")
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        
        # 2. 建立 embedding function
        print("[2] 建立 embedding function...")
        embedding_fn = build_embedding_fn()
        
        # 3. 重建集合（smoke test 用）
        print("[3] 重建測試集合...")
        try:
            client.delete_collection(COLLECTION_NAME)
            print("   ✅ 刪除舊集合")
        except:
            print("   ✅ 無舊集合")
        
        collection = client.create_collection(
            COLLECTION_NAME,
            embedding_function=embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"   ✅ 建立集合：{COLLECTION_NAME}")
        
        # 4. 寫入測試資料
        print("[4] 寫入測試資料...")
        test_docs = [
            {
                "id": "test_001",
                "content": "標題：資安測試\n問題：什麼是資訊安全？\n答案：資訊安全是保護資訊系統免受未經授權的存取、使用、披露、破壞、修改或銷毀的做法。",
                "metadata": {
                    "doc_type": "test",
                    "category": "security",
                    "title": "資安測試",
                    "source": "smoke_test",
                    "created_at": datetime.utcnow().isoformat() + "Z"
                }
            },
            {
                "id": "test_002", 
                "content": "標題：密碼安全\n問題：如何設定安全密碼？\n答案：使用至少8個字符，包含大小寫字母、數字和特殊符號，避免使用個人資訊。",
                "metadata": {
                    "doc_type": "test",
                    "category": "password",
                    "title": "密碼安全",
                    "source": "smoke_test", 
                    "created_at": datetime.utcnow().isoformat() + "Z"
                }
            }
        ]
        
        # 批次寫入
        ids = [doc["id"] for doc in test_docs]
        documents = [doc["content"] for doc in test_docs]
        metadatas = [doc["metadata"] for doc in test_docs]
        
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        print(f"   ✅ 寫入 {len(test_docs)} 筆測試資料")
        
        # 5. 驗證資料
        print("[5] 驗證資料...")
        count = collection.count()
        print(f"   ✅ 集合總數：{count}")
        
        # 6. 測試查詢
        print("[6] 測試查詢...")
        results = collection.query(
            query_texts=["資訊安全"],
            n_results=2
        )
        
        if results["ids"] and len(results["ids"][0]) > 0:
            print(f"   查詢成功，找到 {len(results['ids'][0])} 筆結果")
            for i, doc_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i]
                print(f"     - {doc_id}: 距離 {distance:.4f}")
        else:
            print("   查詢無結果")
            return False
        
        print("[✓] Smoke Test 通過！")
        return True
        
    except Exception as e:
        print(f"[✗] Smoke Test 失敗：{e}")
        import traceback
        traceback.print_exc()
        return False

def batch_ingest():
    """批次匯入所有資料"""
    print("\n 批次匯入所有資料")
    
    try:
        # 1. 連接 ChromaDB
        client = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_collection("scenarios")
        
        # 2. 讀取所有資料
        scenarios_file = "../app-server/scenarios.json"
        with open(scenarios_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        scenarios = data.get("data", []) if isinstance(data, dict) else data
        print(f"   準備匯入 {len(scenarios)} 筆資料")
        
        # 3. 批次處理
        batch_size = 10
        success_count = 0
        
        for i in range(0, len(scenarios), batch_size):
            batch = scenarios[i:i+batch_size]
            
            # 準備批次資料
            ids = []
            documents = []
            metadatas = []
            
            for j, scenario in enumerate(batch):
                doc_id = f"scenario_{scenario.get('id', f'{i+j:03d}')}"
                doc_text = f"標題: {scenario.get('title', '')}\n問題: {scenario.get('question', '')}\n答案: {scenario.get('answer', '')}"
                
                metadata = {
                    "title": str(scenario.get('title', '')),
                    "category": str(scenario.get('category', 'general')),
                    "doc_type": "scenario",
                    "created_at": datetime.utcnow().isoformat()
                }
                
                ids.append(doc_id)
                documents.append(doc_text)
                metadatas.append(metadata)
            
            # 執行批次插入
            try:
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                success_count += len(batch)
                print(f"   批次 {i//batch_size + 1}: 成功匯入 {len(batch)} 筆（累計 {success_count}）")
            except Exception as e:
                print(f"   批次 {i//batch_size + 1} 失敗: {e}")
        
        # 4. 最終驗證
        final_count = collection.count()
        print(f"\n   最終集合文件數: {final_count}")
        
        if final_count > 0:
            print("   批次匯入成功！")
            return True
        else:
            print("   批次匯入失敗")
            return False
            
    except Exception as e:
        print(f"   錯誤: {e}")
        return False

def main():
    """主測試流程"""
    print("=" * 50)
    print(" Simple Ingest - Smoke Test")
    print("=" * 50)
    
    success = simple_ingest()
    
    if success:
        print("\n" + "=" * 50)
        print(" Simple Ingest - Smoke Test")
        print("=" * 50)
        
        # 測試 2: 批次資料匯入
        success2 = batch_ingest()
        
        if success2:
            print("\n" + "=" * 50)
            print(" 所有測試成功！")
            print(" 現在可以測試 AI Service 是否能正常查詢")
        else:
            print("\n批次匯入失敗")
    else:
        print("\n單筆插入失敗，無法繼續批次匯入")

if __name__ == "__main__":
    main()
