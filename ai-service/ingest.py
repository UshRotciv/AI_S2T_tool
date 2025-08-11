import chromadb
from chromadb.utils import embedding_functions
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

def load_rule_ref_documents(script_dir: str) -> List[Dict[str, Any]]:
    """從 rule_ref 目錄加載並解析文檔"""
    rule_ref_path = os.path.join(script_dir, '..', 'rule_ref')
    documents = []
    
    if not os.path.exists(rule_ref_path):
        print(f"警告: 'rule_ref' 目錄不存在於 {rule_ref_path}")
        return documents

    print(f"正在從 {rule_ref_path} 加載文檔...")
    
    for root, _, files in os.walk(rule_ref_path):
        for file in files:
            if file.endswith(('.txt', '.md')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(f"讀取檔案: {file}")

                        # 嘗試解析遊戲問答格式
                        # 使用正則表達式匹配多個題目
                        qa_pairs = re.findall(r'\*\*題目 \d+: (.*?)\*\*(.*?)(?=\*\*題目 \d+:|\Z)', content, re.DOTALL)
                        
                        if qa_pairs:
                            for i, (question, answer_text) in enumerate(qa_pairs):
                                question = question.strip()
                                answer = answer_text.strip()
                                doc_id = f"rule-{os.path.splitext(file)[0]}-{i}"
                                
                                # 清理答案文本
                                answer_lines = [line.strip() for line in answer.split('\n') if line.strip()]
                                clean_answer = "\n".join(answer_lines)

                                doc_content = (
                                    f"標題：{question}\n"
                                    f"問題：{question}\n"
                                    f"答案：{clean_answer}\n"
                                    f"來源：{file}"
                                )
                                
                                documents.append({
                                    'id': doc_id,
                                    'content': doc_content,
                                    'metadata': {
                                        'category': 'rule_document',
                                        'title': question,
                                        'question': question,
                                        'source': file,
                                        'is_chunk': False,
                                    }
                                })
                                print(f"  - 成功解析問答: {question}")
                        else:
                            # 如果不是問答格式，則作為單一文檔處理
                            chunks = chunk_text(content)
                            for i, chunk in enumerate(chunks):
                                doc_id = f"rule-{os.path.splitext(file)[0]}-doc-chunk-{i}"
                                title = os.path.splitext(file)[0].replace('_', ' ')
                                
                                doc_content = (
                                    f"標題：{title}\n"
                                    f"來源：{file}\n"
                                    f"內容片段 {i+1}/{len(chunks)}:\n{chunk}"
                                )

                                documents.append({
                                    'id': doc_id,
                                    'content': doc_content,
                                    'metadata': {
                                        'category': 'rule_document',
                                        'title': title,
                                        'source': file,
                                        'is_chunk': True,
                                        'chunk_number': i + 1,
                                        'total_chunks': len(chunks),
                                    }
                                })
                            print(f"  - 作為一般文檔導入，共 {len(chunks)} 個片段")

                except Exception as e:
                    print(f"讀取或解析檔案 {file_path} 失敗: {e}")

    return documents

def main():
    # --- 路徑設定 ---
    # 建立絕對路徑，確保無論從哪裡執行，路徑都正確
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, 'chroma_db')
    db_version_file = os.path.join(script_dir, "db_version.txt")
    scenarios_path = os.path.join(script_dir, '..', 'app-server', 'scenarios.json')
    meta_info_path = os.path.join(script_dir, 'meta_info.json')

    # 檢查資料庫版本
    current_version = "1.0"
    try:
        if os.path.exists(db_version_file):
            with open(db_version_file, 'r') as f:
                current_version = f.read().strip()
            print(f"目前資料庫版本: {current_version}")
    except Exception as e:
        print(f"讀取資料庫版本時發生錯誤: {e}")
    
    # 更新版本與記錄優化信息
    new_version = "3.0"
    optimization_notes = [
        "1. 實施結構化內容模板",
        "2. 實施語義分段（chunking）",
        "3. 整合同義問法",
        "4. 新增 rule_ref 目錄作為知識來源"
    ]
    
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

    # Initialize ChromaDB client (使用持久化客戶端與絕對路徑)
    client = chromadb.PersistentClient(path=db_path)

    # 設定嵌入函數，確保與main.py一致
    sentence_transformer_ef = embedding_functions.OllamaEmbeddingFunction(
        model_name="mxbai-embed-large",
        url="http://localhost:11434",
    )
    
    # 先清空舊有集合以避免id衝突問題
    try:
        client.delete_collection("scenarios")
        print("舊有集合已清空，準備重新導入資料")
    except Exception as e:
        print("集合不存在或清空失敗，建立新集合")

    # 創建新集合，使用一致的嵌入函數設定
    collection = client.create_collection(
        "scenarios",
        embedding_function=sentence_transformer_ef,
        metadata={"hnsw:space": "cosine"}
    )
    print("成功創建 scenarios 集合，使用 mxbai-embed-large 嵌入模型")

    # --- Load all data sources ---
    all_documents = []

    # 1. Load scenarios from scenarios.json
    with open(scenarios_path, 'r', encoding='utf-8') as f:
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
    with open(meta_info_path, 'r', encoding='utf-8') as f:
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
            
            # 創建更明確的結構化內容，包含同義問法和學習要點
            synonyms_text = "\n".join([f"相似問法：{q}" for q in synonymous_questions]) if synonymous_questions else ""
            learnings_text = "\n".join([f"學習要點：{learning}" for learning in item.get('learnings', [])]) if item.get('learnings') else ""
            
            content = (
                f"標題：{metadata_value['title']}\n"
                f"問題：{metadata_value['question']}\n"
                f"{synonyms_text}\n" if synonyms_text else ""
                f"答案：{answer}\n"
                f"{learnings_text}" if learnings_text else ""
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

    # 3. Load documents from rule_ref directory
    rule_ref_docs = load_rule_ref_documents(script_dir)
    all_documents.extend(rule_ref_docs)

    # --- Process and ingest all documents ---
    print(f"總共有 {len(all_documents)} 筆文檔需要導入")
    
    import time

    max_retries = 5
    retry_delay = 10  # seconds

    for doc in all_documents:
        for attempt in range(max_retries):
            try:
                # The collection will automatically use the OllamaEmbeddingFunction to generate the embedding.
                print(f"(嘗試 {attempt + 1}/{max_retries}) 正在為文檔 {doc['metadata'].get('title', doc['id'])} 生成向量並導入...")
                collection.add(
                    ids=[doc['id']],
                    documents=[doc['content']],
                    metadatas=[doc['metadata']]
                )
                print(f"  ✓ 成功導入文檔: {doc['metadata'].get('title', doc['id'])}")
                break  # Success, exit retry loop
            except Exception as e:
                print(f"  ✗ 導入失敗: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"  ... {retry_delay} 秒後重試 ...")
                    time.sleep(retry_delay)
                else:
                    print(f"  ✗✗✗ 已達最大重試次數，放棄導入文檔: {doc['id']}")

    print("所有資料導入完成！")

if __name__ == "__main__":
    main()