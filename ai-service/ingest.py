import chromadb
import json
import ollama
import uuid
import re
import textwrap
import os
from typing import List, Dict, Any

def chunk_text(text: str, max_chunk_size: int = 300) -> List[str]:
    """將文本分成有語義的段落，確保每個段落不超過最大尺寸
    
    Args:
        text: 要分段的文本
        max_chunk_size: 每段最大字符數
        
    Returns:
        分段後的文本列表
    """
    # 首先按段落分割
    paragraphs = re.split(r'\n+', text.strip())
    
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        # 如果段落本身超過最大尺寸，進一步分割
        if len(paragraph) > max_chunk_size:
            # 使用textwrap分割長段落，確保不會截斷中文句子
            sub_chunks = textwrap.wrap(paragraph, width=max_chunk_size, 
                                       break_on_hyphens=False, 
                                       replace_whitespace=False)
            for sub in sub_chunks:
                chunks.append(sub)
        else:
            # 如果加上當前段落後超過限制，先保存當前塊，再開始新塊
            if len(current_chunk) + len(paragraph) > max_chunk_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = paragraph
            # 否則，將段落加入當前塊
            elif not current_chunk:  # 如果當前塊為空
                current_chunk = paragraph
            else:  # 如果當前塊非空且加上段落後不超過限制
                current_chunk += "\n" + paragraph
    
    # 添加最後一個塊（如果非空）
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


def main():
    # 檢查資料庫版本
    db_version_file = "db_version.txt"
    current_version = "1.0"
    try:
        if os.path.exists(db_version_file):
            with open(db_version_file, 'r') as f:
                current_version = f.read().strip()
            print(f"目前資料庫版本: {current_version}")
    except Exception as e:
        print(f"讀取資料庫版本時發生錯誤: {e}")
    
    # 更新版本與記錄優化信息
    new_version = "2.0"
    optimization_notes = [
        "1. 實施結構化內容模板",
        "2. 實施語義分段（chunking）",
        "3. 整合同義問法"
    ]
    
    # Initialize ChromaDB client
    chroma_client = chromadb.Client()
    
    # Remove existing collection if it exists
    try:
        chroma_client.delete_collection("security_scenarios")
        print("刪除現有的向量資料庫")
    except:
        pass
        
    # 更新資料庫版本資訊
    print(f"更新資料庫版本: {current_version} -> {new_version}")
    print("本次優化項目:")
    for note in optimization_notes:
        print(f" - {note}")
        
    try:
        with open(db_version_file, 'w') as f:
            f.write(new_version)
    except Exception as e:
        print(f"寫入資料庫版本時發生錯誤: {e}")

    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path="./chroma_db")

    # 先清空舊有集合以避免id衝突問題
    try:
        client.delete_collection("scenarios")
        print("舊有集合已清空，準備重新導入資料")
    except Exception as e:
        print("集合不存在或清空失敗，建立新集合")

    # 創建新集合
    collection = client.create_collection("scenarios")

    # --- Load all data sources ---
    all_documents = []

    # 1. Load scenarios from scenarios.json
    with open('../app-server/scenarios.json', 'r', encoding='utf-8') as f:
        scenarios_data = json.load(f)
        for scenario in scenarios_data['data']:
            # 使用scenario id而非title作為文檔id，避免衝突
            doc_id = scenario.get('id', str(uuid.uuid4()))
            
            # 處理學習重點文本
            learnings_text = ", ".join(scenario.get('learnings', []))
            
            # 獲取主要內容
            metadata_value = {}
            metadata_value["category"] = scenario.get('category', 'general')
            metadata_value["title"] = scenario["title"]
            metadata_value["question"] = scenario["question"]
            
            # 如果有同義問法，加入元數據
            if 'synonymous_questions' in scenario and scenario['synonymous_questions']:
                metadata_value["has_synonyms"] = True
                metadata_value["synonym_count"] = len(scenario['synonymous_questions'])
            
            # 取得同義問法（如果有）
            synonymous_questions = scenario.get('synonymous_questions', [])
            
            # 檢查答案是否需要分段
            answer = scenario.get('answer', '未知')
            if len(answer) > 300:  # 如果答案超過300字符，進行分段
                # 將答案段落化
                answer_chunks = chunk_text(answer)
                
                # 為每個段落創建一個獨立的文檔，但保持完整的上下文
                for i, answer_chunk in enumerate(answer_chunks):
                    chunk_id = f"{doc_id}-chunk-{i}"
                    
                    # 創建結構化內容，包含完整上下文和同義問法
                    synonyms_text = "\n".join([f"相似問法：{q}" for q in synonymous_questions]) if synonymous_questions else ""
                    
                    content = (
                        f"類別：{metadata_value['category']}\n"
                        f"標題：{metadata_value['title']}\n"
                        f"問題：{metadata_value['question']}\n"
                        f"{synonyms_text}\n" if synonyms_text else ""
                        f"答案 (第 {i+1}/{len(answer_chunks)} 部分)：{answer_chunk}\n"
                        f"學習重點：{learnings_text}"
                    )
                    
                    all_documents.append({
                        'id': chunk_id,
                        'content': content,
                        'metadata': {
                            'category': metadata_value['category'],
                            'title': metadata_value['title'],
                            'question': metadata_value['question'],
                            'is_chunk': True,
                            'chunk_number': i + 1,
                            'total_chunks': len(answer_chunks),
                            'parent_id': doc_id,
                            'has_synonyms': metadata_value.get('has_synonyms', False),
                            'synonym_count': metadata_value.get('synonym_count', 0)
                        }
                    })
            else:  # 答案不需要分段
                # 創建結構化內容，包含同義問法
                synonyms_text = "\n".join([f"相似問法：{q}" for q in synonymous_questions]) if synonymous_questions else ""
                
                content = (
                    f"類別：{metadata_value['category']}\n"
                    f"標題：{metadata_value['title']}\n"
                    f"問題：{metadata_value['question']}\n"
                    f"{synonyms_text}\n" if synonyms_text else ""
                    f"答案：{answer}\n"
                    f"學習重點：{learnings_text}"
                )
                
                all_documents.append({
                    'id': doc_id,
                    'content': content,
                    'metadata': {
                        'category': metadata_value['category'],
                        'title': metadata_value['title'],
                        'question': metadata_value['question'],
                        'is_chunk': False,
                        'has_synonyms': metadata_value.get('has_synonyms', False),
                        'synonym_count': metadata_value.get('synonym_count', 0)
                    }
                })
                print(f"準備導入完整情境: {metadata_value['title']}")

    # 2. Load meta information from meta_info.json
    with open('meta_info.json', 'r', encoding='utf-8') as f:
        meta_data = json.load(f)
        for item in meta_data:
            doc_id = item.get('id', f"meta-{str(uuid.uuid4())}")
            
            # 處理學習重點文本
            learnings_text = ", ".join(item.get('learnings', []))
            
            # 獲取主要內容
            metadata_value = {}
            metadata_value["category"] = "meta"
            metadata_value["title"] = item["title"]
            metadata_value["question"] = item["question"]
            
            # 如果有同義問法，加入元數據
            if 'synonymous_questions' in item and item['synonymous_questions']:
                metadata_value["has_synonyms"] = True
                metadata_value["synonym_count"] = len(item['synonymous_questions'])
            
            # 取得同義問法（如果有）
            synonymous_questions = item.get('synonymous_questions', [])
            
            # 不再對答案進行分段，保持完整問答對
            answer = item.get('answer', '未知')
            
            # 創建結構化內容，包含同義問法
            synonyms_text = "\n".join([f"相似問法：{q}" for q in synonymous_questions]) if synonymous_questions else ""
            
            content = (
                f"標題：{metadata_value['title']}\n"
                f"問題：{metadata_value['question']}\n"
                f"{synonyms_text}\n" if synonyms_text else ""
                f"答案：{answer}"
            )
            
            all_documents.append({
                'id': doc_id,
                'content': content,
                'metadata': {
                    'category': metadata_value['category'],
                    'title': metadata_value['title'],
                    'question': metadata_value['question'],
                    'is_chunk': False,
                    'has_synonyms': metadata_value.get('has_synonyms', False),
                    'synonym_count': metadata_value.get('synonym_count', 0)
                }
            })
            print(f"準備導入完整元資訊: {metadata_value['title']}")

    # --- Process and ingest all documents ---
    print(f"總共有 {len(all_documents)} 筆文檔需要導入")
    
    for doc in all_documents:
        try:
            # Generate embedding using Ollama
            response = ollama.embeddings(model='mxbai-embed-large', prompt=doc['content'])
            embedding = response["embedding"]
            
            # Add to ChromaDB collection
            collection.add(
                ids=[doc['id']],
                embeddings=[embedding],
                documents=[doc['content']],
                metadatas=[doc['metadata']]
            )
            print(f"成功導入文檔: {doc['metadata'].get('title', doc['id'])}")
        except Exception as e:
            print(f"導入文檔失敗 {doc['id']}: {str(e)}")

    print("所有資料導入完成！")

if __name__ == "__main__":
    main()
