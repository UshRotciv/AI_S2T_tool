"""
基礎向量索引建立腳本 - 簡化版本
用於還原 RAG 系統基本功能
"""
# 環境診斷代碼 - 自動修復chromadb導入問題
import sys
print(f"Python 路徑: {sys.executable}")
print(f"Python 版本: {sys.version}")
print(f"sys.path: {sys.path}")

# 嘗試安裝缺失的套件
try:
    print("嘗試自動安裝chromadb...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "chromadb", "--quiet"])
    print("chromadb安裝成功!")
except Exception as e:
    print(f"自動安裝失敗: {e}")

# 再次嘗試導入
try:
    import chromadb
    print(f"chromadb 已成功導入!")
except ImportError as e:
    print(f"導入 chromadb 失敗: {e}")
    print("\n檢查已安裝的套件:")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "list"], capture_output=True, text=True)
        print(result.stdout)
    except:
        print("無法列出已安裝套件")
    sys.exit(1)  # 如果仍然失敗，退出程序
import json
import ollama
import uuid
import os
import time
from typing import List, Dict, Any

def rebuild_basic_index():
    """重建基礎索引，專注於保持完整問答對，不進行複雜分段"""
    print("開始重建基礎索引...")
    start_time = time.time()
    
    # 初始化 ChromaDB 客戶端
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # 刪除舊集合（如果存在）
    try:
        client.delete_collection("scenarios")
        print("刪除現有的向量資料庫")
    except:
        print("集合不存在或已刪除")
        
    # 建立新集合
    collection = client.create_collection("scenarios")
    
    # 載入 scenarios.json
    scenario_docs = []
    with open('../app-server/scenarios.json', 'r', encoding='utf-8') as f:
        scenarios_data = json.load(f)
        for scenario in scenarios_data['data']:
            # 使用 scenario id 作為文檔 id
            doc_id = scenario.get('id', str(uuid.uuid4()))
            
            # 學習重點文本
            learnings_text = ", ".join(scenario.get('learnings', []))
            
            # 取得主要內容與元數據
            category = scenario.get('category', 'general')
            title = scenario.get('title', '未知標題')
            question = scenario.get('question', '未知問題')
            answer = scenario.get('answer', '未知答案')
            
            # 將完整問答保持為單一文檔，不分段
            content = (
                f"類別：{category}\n"
                f"標題：{title}\n"
                f"問題：{question}\n"
                f"答案：{answer}\n"
                f"學習重點：{learnings_text}"
            )
            
            scenario_docs.append({
                'id': doc_id,
                'content': content,
                'metadata': {
                    'category': category,
                    'title': title,
                    'question': question,
                    'is_chunk': False
                }
            })
            print(f"準備導入情境: {title}")
    
    # 載入 meta_info.json（如果存在）
    meta_docs = []
    if os.path.exists('meta_info.json'):
        try:
            with open('meta_info.json', 'r', encoding='utf-8') as f:
                meta_data = json.load(f)
                for item in meta_data:
                    doc_id = item.get('id', f"meta-{str(uuid.uuid4())}")
                    
                    title = item.get('title', '未知標題')
                    question = item.get('question', '未知問題')
                    answer = item.get('answer', '未知答案')
                    
                    # 將完整問答保持為單一文檔，不分段
                    content = (
                        f"標題：{title}\n"
                        f"問題：{question}\n"
                        f"答案：{answer}"
                    )
                    
                    meta_docs.append({
                        'id': doc_id,
                        'content': content,
                        'metadata': {
                            'category': 'meta',
                            'title': title,
                            'question': question,
                            'is_chunk': False
                        }
                    })
                    print(f"準備導入元資訊: {title}")
        except Exception as e:
            print(f"載入元資訊時發生錯誤: {e}")
    
    # 合併所有文檔
    all_docs = scenario_docs + meta_docs
    print(f"總共有 {len(all_docs)} 筆文檔需要導入")
    
    # 文檔索引化
    success_count = 0
    error_count = 0
    
    for doc in all_docs:
        try:
            # 使用 Ollama 生成嵌入向量
            response = ollama.embeddings(model='mxbai-embed-large', prompt=doc['content'])
            embedding = response["embedding"]
            
            # 添加至 ChromaDB 集合
            collection.add(
                ids=[doc['id']],
                embeddings=[embedding],
                documents=[doc['content']],
                metadatas=[doc['metadata']]
            )
            success_count += 1
            print(f"成功導入文檔: {doc['metadata'].get('title', doc['id'])}")
        except Exception as e:
            error_count += 1
            print(f"導入文檔失敗: {doc['metadata'].get('title', doc['id'])}, 錯誤: {e}")
    
    end_time = time.time()
    print(f"索引建立完成! 耗時: {end_time - start_time:.2f} 秒")
    print(f"成功導入: {success_count}/{len(all_docs)} 筆文檔")
    print(f"失敗: {error_count}/{len(all_docs)} 筆文檔")
    
    # 驗證索引質量
    print("\n開始進行索引質量驗證...")
    validate_index_quality(collection)
    
    return collection

def validate_index_quality(collection):
    """驗證索引質量，測試基本問題是否能被正確檢索"""
    test_questions = [
        "印表機發現無人拿走的機密文件該怎麼做?",
        "人離機鎖的重要性",
        "網頁上發現ASUS產品未公開資訊"
    ]
    
    for question in test_questions:
        print(f"\n測試問題: {question}")
        try:
            # 使用 Ollama 生成嵌入向量
            response = ollama.embeddings(model='mxbai-embed-large', prompt=question)
            query_embedding = response["embedding"]
            
            # 進行向量搜索
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=3
            )
            
            # 顯示搜索結果
            if results and len(results['documents']) > 0:
                print(f"找到 {len(results['documents'][0])} 筆相關結果")
                for i, (doc, dist) in enumerate(zip(results['documents'][0], results['distances'][0])):
                    title = results['metadatas'][0][i].get('title', '未知標題')
                    print(f"結果 {i+1}: {title} (距離: {dist:.4f})")
                    # 只顯示摘要
                    content_preview = doc.split('\n', 3)[0:3]
                    for line in content_preview:
                        print(f"  {line}")
            else:
                print("未找到相關結果")
        except Exception as e:
            print(f"查詢失敗: {e}")

if __name__ == "__main__":
    rebuild_basic_index()
