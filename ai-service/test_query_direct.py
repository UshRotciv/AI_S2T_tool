#!/usr/bin/env python3
"""
直接測試 AI Service 查詢邏輯
不通過 API，直接調用內部函數
"""

import chromadb
import ollama

def test_chromadb_query():
    """測試 ChromaDB 查詢"""
    print("🧪 測試 ChromaDB 查詢")
    
    try:
        # 1. 連接資料庫
        client = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_collection("scenarios")
        
        print(f"   集合文件數: {collection.count()}")
        
        # 2. 測試查詢
        query_text = "密碼政策"
        print(f"   查詢文字: {query_text}")
        
        results = collection.query(
            query_texts=[query_text],
            n_results=3,
            include=["documents", "metadatas", "distances"]
        )
        
        print(f"   查詢結果數: {len(results['ids'][0]) if results['ids'] else 0}")
        
        if results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                print(f"   結果 {i+1}: {doc_id}")
                print(f"     距離: {results['distances'][0][i]:.4f}")
                print(f"     內容: {results['documents'][0][i][:100]}...")
            return True, results
        else:
            print("   ❌ 查詢無結果")
            return False, None
            
    except Exception as e:
        print(f"   ❌ 查詢錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_ollama_with_context():
    """測試 Ollama 與上下文"""
    print("\n🧪 測試 Ollama 與上下文")
    
    try:
        # 1. 先獲取查詢結果
        success, results = test_chromadb_query()
        
        if not success or not results:
            print("   ❌ 無法獲取上下文，使用空上下文測試")
            context = "沒有找到相關的參考資料。"
        else:
            # 2. 構建上下文
            context_parts = []
            for i, doc in enumerate(results['documents'][0]):
                context_parts.append(f"參考資料 {i+1}: {doc}")
            context = "\n".join(context_parts)
        
        # 3. 構建 Ollama 消息
        system_prompt = """你是一個專業的資安助手。請根據提供的參考資料回答用戶的問題。
如果參考資料中有相關內容，請優先使用；如果沒有，請提供一般性的專業建議。"""
        
        user_prompt = f"""問題: 什麼是密碼政策？

參考資料:
{context}

請提供一個專業且實用的回答。"""
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]
        
        print("   正在調用 Ollama...")
        print(f"   上下文長度: {len(context)} 字元")
        
        # 4. Ollama 調用
        response = ollama.chat(
            model='qwen2',
            messages=messages,
            options={
                'temperature': 0.1,
                'num_predict': 200
            }
        )
        
        answer = response['message']['content']
        print(f"   ✅ Ollama 調用成功")
        print(f"   回答長度: {len(answer)} 字元")
        print(f"   回答內容: {answer[:200]}...")
        
        return True, answer
        
    except Exception as e:
        print(f"   ❌ Ollama 調用錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_ai_service_logic():
    """模擬 AI Service 的完整邏輯"""
    print("\n🧪 模擬 AI Service 完整邏輯")
    
    try:
        question = "什麼是密碼政策？"
        
        # 1. 查詢擴展（簡化版）
        expanded_queries = [question, "密碼", "政策", "安全"]
        print(f"   擴展查詢: {expanded_queries}")
        
        # 2. ChromaDB 查詢
        client = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_collection("scenarios")
        
        all_results = []
        for query in expanded_queries:
            try:
                results = collection.query(
                    query_texts=[query],
                    n_results=2,
                    include=["documents", "metadatas", "distances"]
                )
                if results['ids'] and results['ids'][0]:
                    all_results.extend(zip(
                        results['ids'][0],
                        results['documents'][0],
                        results['distances'][0]
                    ))
            except Exception as e:
                print(f"   查詢 '{query}' 失敗: {e}")
        
        print(f"   總查詢結果數: {len(all_results)}")
        
        # 3. 去重並排序
        unique_results = {}
        for doc_id, doc, distance in all_results:
            if doc_id not in unique_results or distance < unique_results[doc_id][1]:
                unique_results[doc_id] = (doc, distance)
        
        sorted_results = sorted(unique_results.items(), key=lambda x: x[1][1])[:3]
        print(f"   去重後結果數: {len(sorted_results)}")
        
        # 4. 構建上下文
        if sorted_results:
            context_parts = []
            for i, (doc_id, (doc, distance)) in enumerate(sorted_results):
                context_parts.append(f"參考資料 {i+1}: {doc}")
            context = "\n".join(context_parts)
        else:
            context = "沒有找到相關的參考資料。"
        
        # 5. Ollama 調用
        messages = [
            {
                'role': 'system',
                'content': '你是一個專業的資安助手。請根據提供的參考資料回答用戶的問題。'
            },
            {
                'role': 'user',
                'content': f"""問題: {question}

參考資料:
{context}

請提供一個專業且實用的回答。"""
            }
        ]
        
        print("   正在調用 Ollama...")
        response = ollama.chat(
            model='qwen2',
            messages=messages,
            options={
                'temperature': 0.1,
                'num_predict': 200
            }
        )
        
        answer = response['message']['content']
        print(f"   ✅ 完整邏輯測試成功")
        print(f"   最終回答: {answer}")
        
        return True, answer
        
    except Exception as e:
        print(f"   ❌ 完整邏輯測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def main():
    """主測試流程"""
    print("🔍 AI Service 查詢邏輯診斷")
    print("=" * 50)
    
    # 測試 1: ChromaDB 查詢
    success1, _ = test_chromadb_query()
    
    # 測試 2: Ollama 與上下文
    success2, _ = test_ollama_with_context()
    
    # 測試 3: 完整邏輯
    success3, _ = test_ai_service_logic()
    
    print("\n" + "=" * 50)
    print("📊 診斷結果總結")
    
    if success1:
        print("✅ ChromaDB 查詢正常")
    else:
        print("❌ ChromaDB 查詢異常")
    
    if success2:
        print("✅ Ollama 調用正常")
    else:
        print("❌ Ollama 調用異常")
    
    if success3:
        print("✅ 完整邏輯正常")
        print("💡 AI Service 應該能正常工作，問題可能在 API 層面")
    else:
        print("❌ 完整邏輯異常")
        print("💡 問題出現在內部邏輯")

if __name__ == "__main__":
    main()
