import shutil
import os
import stat
from fastapi import FastAPI, Depends
import ingest
import threading

# --- Path Setup ---
# 建立絕對路徑，確保無論從哪裡執行，路徑都正確
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, 'chroma_db')

# --- Robust Database Auto-Rebuild on Startup (Commented Out) ---

def handle_remove_readonly(func, path, exc_info):
    """
    Error handler for shutil.rmtree.

    If the error is due to an access error (read only file) it attempts to 
    change the file permissions and then retries the move.
    If the error is for another reason it re-raises the error.
    """
    exc_type, exc_value, _ = exc_info
    if exc_type is PermissionError and '[WinError 5]' in str(exc_value):
        print(f"Permission error at {path}. Attempting to change permissions and retry.")
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception as e:
            print(f"Failed to remove {path} even after chmod: {e}")
    else:
        raise

# The following logic is commented out to prevent automatic database deletion on startup.
# The database should be built manually and explicitly by running ingest.py.
# print("Checking database integrity...")
# if os.path.exists(DB_PATH):
#     print(f"Existing database found at '{DB_PATH}'. Removing to ensure model consistency.")
#     shutil.rmtree(DB_PATH, onerror=handle_remove_readonly)
#     print("Old database removed. Re-ingesting data...")
#     try:
#         ingest.main() # Assuming ingest.py has a main() function
#         print("Database re-ingestion complete.")
#     except Exception as e:
#         print(f"An error occurred during re-ingestion: {e}")
# else:
#     print("No existing database found. Ingesting data for the first time...")
#     try:
#         ingest.main()
#         print("Initial data ingestion complete.")
#     except Exception as e:
#         print(f"An error occurred during initial ingestion: {e}")

from pydantic import BaseModel
import ollama
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 3. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 資料庫連接與集合設定
# 使用絕對路徑進行連接
client = chromadb.PersistentClient(path=DB_PATH)

# 確保使用與ingest.py一致的嵌入函數設定
sentence_transformer_ef = embedding_functions.OllamaEmbeddingFunction(
    model_name="mxbai-embed-large",
    url="http://localhost:11434",
)

# 獲取或創建集合，使用一致的嵌入函數
try:
    # 1. get_collection 也綁定 embedding_function
    collection = client.get_collection(
        "scenarios",
        embedding_function=sentence_transformer_ef
    )
    print("成功連接到現有的scenarios集合")
except:
    print("集合不存在，請先執行ingest.py建立資料庫")
    collection = client.create_collection(
        "scenarios",
        embedding_function=sentence_transformer_ef,
        metadata={"hnsw:space": "cosine"}
    )

# 對話歷史記錄存儲
conversation_history = {}
history_lock = threading.Lock()

# 定期清理過期對話歷史的函數（實際應用中可加入排程任務）
def cleanup_expired_conversations():
    current_time = datetime.now()
    expired_sessions = []
    for session_id, session_data in conversation_history.items():
        # 假設 30 分鐘未活動的會話將被清理
        last_active = session_data.get('last_active', datetime.min)
        if (current_time - last_active).total_seconds() > 1800:  # 30分鐘 = 1800秒
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del conversation_history[session_id]
    
    return len(expired_sessions)

class Message(BaseModel):
    role: str  # 'user' 或 'assistant'
    content: str

class AskRequest(BaseModel):
    question: str
    session_id: Optional[str] = None  # 對話 ID，可選

# 2. 對話歷史操作加鎖
def get_or_create_session(session_id: Optional[str] = None) -> str:
    if not session_id:
        session_id = str(uuid.uuid4())
    with history_lock:
        # 如果會話不存在，則初始化
        conversation_history.setdefault(session_id, {'messages': [], 'last_active': datetime.now()})
        # 更新最後活動時間
        conversation_history[session_id]['last_active'] = datetime.now()
    return session_id

# 5. 空結果檢查輔助函式
def empty_results(r):
    return (not r) or (not r.get('documents')) or (not r['documents']) or (not r['documents'][0])

@app.post("/api/ask")
def ask(request: AskRequest):
    question = request.question
    session_id = get_or_create_session(request.session_id)

    # 檢查是否是關於 AI 本身的問題（元問題）
    meta_keywords = ["你是誰", "你是", "你知道什麼", "你知道甚麼", "你能做什麼", "你會什麼", "自我介紹"]
    is_meta_question = any(keyword in question for keyword in meta_keywords)
    
    try:
        if is_meta_question:
            # 對於元問題，直接查詢元文檔
            results = collection.query(
                query_texts=[question],
                n_results=5,
                where={"category": "meta"},
                include=["documents", "metadatas", "distances"]
            )
            print(f"元問題查詢結果: {results}")
        else:
            # 對於所有其他問題，執行標準的向量檢索
            print(f"執行標準向量檢索，查詢: '{question}'")
            # 優先排除非情境文件（如 rule_document），提高情境卡片命中率
            results = collection.query(
                query_texts=[question],
                n_results=7,
                where={"category": {"$ne": "rule_document"}},
                include=["documents", "metadatas", "distances"]
            )
            count_primary = len(results['ids'][0]) if results.get('ids') and results['ids'][0] else 0
            print(f"一般問題（排除 rule_document）查詢結果數量: {count_primary}")
            # 若無結果，回退到不過濾檢索
            if count_primary == 0:
                results = collection.query(
                    query_texts=[question],
                    n_results=7,
                    include=["documents", "metadatas", "distances"]
                )
                print(f"一般問題（回退不過濾）查詢結果數量: {len(results['ids'][0]) if results.get('ids') and results['ids'][0] else 0}")

            # LLM Re-ranking 進行相關性過濾
            if results['ids'] and results['ids'][0]:
                relevant_indices = []
                re_ranking_debug_info = []
                relevance_check_prompt_template = """You are an assistant for a cybersecurity training program. Your task is to determine if a document from your knowledge base is relevant to the user's question. The knowledge base only contains information about cybersecurity scenarios and policies.

User's Question: '{question}'

Document Content:
---
{document}
---

Based on the content, is this document relevant to answering the user's question? The document is considered relevant ONLY IF it directly addresses the user's question within the scope of cybersecurity. Answer with a single word: 'yes' or 'no'."""
                
                for i, doc in enumerate(results['documents'][0]):
                    prompt = relevance_check_prompt_template.format(question=question, document=doc)
                    try:
                        relevance_res = ollama.chat(
                            model='qwen2',
                            messages=[{'role': 'user', 'content': prompt}],
                            stream=False,
                            options={'temperature': 0.0} # 確定性檢查
                        )
                        answer = relevance_res['message']['content'].strip().lower()
                        print(f"Relevance check for doc {i} ('{results['ids'][0][i]}'): Answer is '{answer}'.")
                        if answer.startswith('yes'):
                            relevant_indices.append(i)
                    except Exception as e:
                        print(f"Error during relevance check for doc {i}: {e}")

                # 基於相關性檢查過濾結果
                print(f"Found {len(relevant_indices)} relevant documents out of {len(results['documents'][0])}.")
                if relevant_indices:
                    results['ids'][0] = [results['ids'][0][i] for i in relevant_indices]
                    results['documents'][0] = [results['documents'][0][i] for i in relevant_indices]
                    results['metadatas'][0] = [results['metadatas'][0][i] for i in relevant_indices]
                    results['distances'][0] = [results['distances'][0][i] for i in relevant_indices]
                else:
                    # 如果沒有任何文件被認為是相關的，則清空結果
                    results['ids'][0], results['documents'][0], results['metadatas'][0], results['distances'][0] = [], [], [], []

        # 5. 檢查最終結果是否為空
        if empty_results(results):
            print("No relevant documents found after re-ranking. Returning empty answer.")
            # 在返回前，仍然記錄這次無效的查詢
            with history_lock:
                conversation_history[session_id]['messages'].append({'role': 'user', 'content': question})
                conversation_history[session_id]['messages'].append({'role': 'assistant', 'content': '很抱歉，我無法從現有的資料中找到與您問題相關的答案。'})
            return {"answer":"很抱歉，我無法從現有的資料中找到與您問題相關的答案。","sources":[],"session_id":session_id}

        # 詳細調試資訊輸出
        if results['ids'] and len(results['ids'][0]) > 0:
            print("\n=== 查詢結果詳情 ===")
            for i, (doc_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
                metadata = results['metadatas'][0][i] if i < len(results['metadatas'][0]) else {}
                title = metadata.get('title', '未知標題')
                category = metadata.get('category', '未知類別')
                question_meta = metadata.get('question', '未知問題')
                
                print(f"\n結果 {i+1}:")
                print(f"  標題: {title}")
                print(f"  類別: {category}")
                print(f"  問題: {question_meta}")
                print(f"  距離: {distance:.4f}")
                print(f"  內容預覽: {results['documents'][0][i][:200]}...")
                
                # 特別檢查是否包含印表機相關內容
                content = results['documents'][0][i].lower()
                if '印表機' in content or '機密' in content or 'confidential' in content:
                    print(f"  ✓ 包含印表機/機密相關內容")
                if '非禮勿視' in content or '碎紙機' in content or '通知' in content:
                    print(f"  ✓ 包含關鍵處理步驟")
            print("\n=== 查詢結果結束 ===")
        else:
            print("  未找到任何結果")
    except Exception as e:
        print(f"查詢過程中發生錯誤: {str(e)}")
        return {"answer": "系統處理您的問題時遇到了技術問題，請稍後再試。", "sources": [], "session_id": session_id}

    # Check if there are any relevant documents
    if not results['documents'] or not results['documents'][0]:
        return {"answer": "很抱歉，我無法從現有的資料中找到與您問題相關的答案。", "sources": [], "session_id": session_id}

    # Construct the prompt for the chat model
    context = "\n".join([f"- {doc}" for doc in results['documents'][0]])
    
    # 強化系統提示，嚴格限制僅使用卡片內容
    system_prompt = """你是 ASUS 的資安助手，專門回答資安相關問題。

【重要】你必須嚴格遵守以下規則：

1. 絕對禁止使用任何不在「情境資料」中的內容回答
2. 絕對禁止發揮、推測或補充任何資料中沒有的訊息
3. 如果情境資料中有「答案」欄位，必須直接使用該答案內容，不得修改或重新表達
4. 如果情境資料中有「學習要點」，可以在答案後附上這些要點
5. 如果找不到相關資料，必須回答：「根據我現有的資料，無法回答這個問題」
6. 使用繁體中文回答

【特別注意】對於印表機機密文件等問題，必須找到包含「非禮勿視」、「碎紙機」、「通知管理師」等關鍵詞的具體處理步驟。

記住：你的任務是忠實傳達卡片內容，不是創造或重新表達內容。"""
    
    # 強化用戶提示格式，明確指示卡片結構
    user_prompt = f"""以下是資安卡片內容，包含標題、問題和答案：

{context}

現在用戶問題：{question}

請直接使用上述卡片中的「答案」內容回答。如果找不到匹配的卡片，請說「根據我現有的資料，無法回答這個問題」。"""

    # 獲取當前對話的歷史記錄（最多保留最近5輪）
    with history_lock:
        history = conversation_history[session_id]['messages'][-5:] if conversation_history[session_id]['messages'] else []
    
    # 構建完整的消息列表，包含系統提示、對話歷史和當前問題
    messages = [
        {
            'role': 'system',
            'content': system_prompt + "\n請注意之前的對話歷史，保持回答的連貫性。",
        }
    ]
    
    # 添加歷史對話
    for msg in history:
        messages.append({
            'role': msg['role'],
            'content': msg['content']
        })
    
    # 添加當前問題
    messages.append({
        'role': 'user',
        'content': user_prompt,
    })
    
    # 增加特定指示來強化卡片內容的使用
    messages.append({
        'role': 'system',
        'content': f"""在回答前，請先仔細檢查提供的卡片內容。

特別注意：
1. 尋找包含「答案：」的部分，這是你必須使用的標準答案
2. 如果問題關於印表機機密文件，尋找包含「非禮勿視」、「碎紙機」、「通知」等關鍵詞的內容
3. 直接引用卡片中的答案，不要重寫或改寫

用戶問題是：{question}"""
    })
    
    chat_response = ollama.chat(
        model='qwen2',
        messages=messages,
        options={
            'temperature': 0.1,  # 進一步降低溫度以提高確定性
            'num_predict': 300,   # 適度增加長度限制以確保完整回答
            'top_p': 0.8,        # 控制生成文本的多樣性
            'top_k': 30          # 限制候選詞彙數量
        }
    )

    # Extract the answer and the source documents（統一物件結構，包含 id/metadata/distance/document）
    answer = chat_response['message']['content']
    sources = []
    if results.get('ids') and results['ids'][0]:
        for i, doc_id in enumerate(results['ids'][0]):
            src = {
                "id": doc_id,
                "document": results['documents'][0][i] if results.get('documents') and results['documents'][0] and i < len(results['documents'][0]) else "",
                "metadata": results['metadatas'][0][i] if results.get('metadatas') and results['metadatas'][0] and i < len(results['metadatas'][0]) else {},
                "distance": results['distances'][0][i] if results.get('distances') and results['distances'][0] and i < len(results['distances'][0]) else None,
            }
            sources.append(src)
    
    # 將當前問答添加到歷史記錄
    with history_lock:
        conversation_history[session_id]['messages'].append({'role': 'user', 'content': question})
        conversation_history[session_id]['messages'].append({'role': 'assistant', 'content': answer})
    
    # 只保留最近10條消息（5輪對話）
    with history_lock:
        if len(conversation_history[session_id]['messages']) > 10:
            conversation_history[session_id]['messages'] = conversation_history[session_id]['messages'][-10:]

    return {"answer": answer, "sources": sources, "session_id": session_id}

@app.get("/api/conversation/{session_id}")
def get_conversation(session_id: str):
    """獲取指定會話的歷史記錄"""
    if session_id not in conversation_history:
        return {"error": "會話不存在"}
    
    return {"messages": conversation_history[session_id]['messages']}

@app.delete("/api/conversation/{session_id}")
def delete_conversation(session_id: str):
    """刪除指定的會話記錄"""
    if session_id in conversation_history:
        del conversation_history[session_id]
        return {"status": "success"}
    return {"error": "會話不存在"}

@app.get("/api/status")
def get_status():
    """獲取服務狀態"""
    # 執行清理過期會話
    expired_count = cleanup_expired_conversations()
    
    return {
        "status": "running",
        "active_conversations": len(conversation_history),
        "cleaned_conversations": expired_count
    }

# 簡易除錯端點：回傳查詢的 Top-K 檢索摘要
@app.get("/api/debug/sample")
def debug_sample(q: str, k: int = 5):
    try:
        results = collection.query(
            query_texts=[q],
            n_results=max(1, min(k, 10)),
            include=["documents", "metadatas", "distances"]
        )
        items = []
        if results.get('ids') and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                md = results['metadatas'][0][i] if results.get('metadatas') and results['metadatas'][0] else {}
                items.append({
                    "id": doc_id,
                    "title": md.get('title'),
                    "category": md.get('category'),
                    "question": md.get('question'),
                    "distance": results['distances'][0][i] if results.get('distances') and results['distances'][0] else None
                })
        return {"query": q, "results": items}
    except Exception as e:
        return {"query": q, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)