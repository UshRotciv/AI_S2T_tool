#!/usr/bin/env python3
"""
直接測試 Ollama 調用，排除其他因素
"""

import ollama
import chromadb

def test_ollama_direct():
    """直接測試 Ollama 調用"""
    print("🧪 直接測試 Ollama 調用")
    
    try:
        # 簡單的測試消息
        messages = [
            {
                'role': 'system',
                'content': '你是一個資安助手，請回答用戶的問題。'
            },
            {
                'role': 'user',
                'content': '什麼是密碼政策？'
            }
        ]
        
        print("正在調用 Ollama...")
        response = ollama.chat(
            model='qwen2',
            messages=messages,
            options={
                'temperature': 0.1,
                'num_predict': 100
            }
        )
        
        answer = response['message']['content']
        print(f"✅ Ollama 調用成功")
        print(f"回答: {answer[:200]}...")
        return True, answer
        
    except Exception as e:
        print(f"❌ Ollama 調用失敗: {e}")
        return False, str(e)

def test_chromadb_query():
    """測試 ChromaDB 查詢"""
    print("\n🧪 測試 ChromaDB 查詢")
    
    try:
        client = chromadb.PersistentClient(path="./ai-service/chroma_db")
        collection = client.get_collection("scenarios")
        
        results = collection.query(
            query_texts=["密碼政策"],
            n_results=3,
            include=["documents", "metadatas", "distances"]
        )
        
        if results['ids'] and results['ids'][0]:
            print(f"✅ ChromaDB 查詢成功，找到 {len(results['ids'][0])} 個結果")
            for i, doc_id in enumerate(results['ids'][0]):
                print(f"  結果 {i+1}: {doc_id}")
                print(f"    距離: {results['distances'][0][i]:.4f}")
                print(f"    內容: {results['documents'][0][i][:100]}...")
            return True, results
        else:
            print("⚠️ ChromaDB 查詢無結果")
            return False, "無結果"
            
    except Exception as e:
        print(f"❌ ChromaDB 查詢失敗: {e}")
        return False, str(e)

def test_combined():
    """測試組合調用（模擬 AI Service 流程）"""
    print("\n🧪 測試組合調用")
    
    try:
        # 1. ChromaDB 查詢
        client = chromadb.PersistentClient(path="./ai-service/chroma_db")
        collection = client.get_collection("scenarios")
        
        results = collection.query(
            query_texts=["密碼政策"],
            n_results=3,
            include=["documents", "metadatas", "distances"]
        )
        
        if not results['ids'] or not results['ids'][0]:
            print("⚠️ 沒有找到相關資料")
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
        
        # 4. Ollama 調用
        print("正在調用 Ollama 生成回答...")
        response = ollama.chat(
            model='qwen2',
            messages=messages,
            options={
                'temperature': 0.1,
                'num_predict': 200
            }
        )
        
        answer = response['message']['content']
        print(f"✅ 組合調用成功")
        print(f"最終回答: {answer}")
        return True, answer
        
    except Exception as e:
        print(f"❌ 組合調用失敗: {e}")
        return False, str(e)

def main():
    """主要測試流程"""
    print("🔍 AI Service 深度診斷")
    print("=" * 50)
    
    # 測試 1: 直接 Ollama 調用
    ollama_success, ollama_result = test_ollama_direct()
    
    # 測試 2: ChromaDB 查詢
    chromadb_success, chromadb_result = test_chromadb_query()
    
    # 測試 3: 組合調用
    combined_success, combined_result = test_combined()
    
    # 總結
    print("\n" + "=" * 50)
    print("📊 診斷結果總結")
    
    if ollama_success:
        print("✅ Ollama 直接調用正常")
    else:
        print("❌ Ollama 直接調用失敗")
    
    if chromadb_success:
        print("✅ ChromaDB 查詢正常")
    else:
        print("❌ ChromaDB 查詢失敗")
    
    if combined_success:
        print("✅ 組合調用正常")
        print("💡 AI Service 應該能正常工作，問題可能在其他地方")
    else:
        print("❌ 組合調用失敗")
        print("💡 問題出現在 AI Service 的內部邏輯")

if __name__ == "__main__":
    main()
