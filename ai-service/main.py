from fastapi import FastAPI, Depends
from pydantic import BaseModel
import ollama
import chromadb
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

app = FastAPI()

# 資料庫連接
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("scenarios")

# 對話歷史記錄存儲
conversation_history = {}

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

def get_or_create_session(session_id: Optional[str] = None) -> str:
    """獲取或創建對話會話ID"""
    if not session_id:
        session_id = str(uuid.uuid4())
    
    if session_id not in conversation_history:
        conversation_history[session_id] = {
            'messages': [],
            'last_active': datetime.now()
        }
    else:
        conversation_history[session_id]['last_active'] = datetime.now()
    
    return session_id

@app.post("/api/ask")
def ask(request: AskRequest):
    question = request.question
    session_id = get_or_create_session(request.session_id)

    # 檢查是否是關於 AI 本身的問題（元問題）
    meta_keywords = ["你是誰", "你是", "你知道什麼", "你知道甚麼", "你能做什麼", "你會什麼", "自我介紹"]
    is_meta_question = any(keyword in question for keyword in meta_keywords)
    
    # 檢查是否是類別查詢
    category_keywords = ["辦公室好習慣", "基礎好習慣", "辦公室基礎好習慣", "數位檔案", "機敏資料"]
    is_category_query = any(keyword in question for keyword in category_keywords)

    try:
        if is_meta_question:
            # 對於元問題，直接查詢元文檔
            results = collection.query(
                query_texts=[question],  # 使用問題查詢相關的元文檔
                n_results=1,
                where={"category": "meta"}
            )
            print(f"元問題查詢結果: {results}")
        elif is_category_query:
            # 對於類別查詢，使用混合檢索策略
            try:
                # 1. 先用向量搜索
                response = ollama.embeddings(model='mxbai-embed-large', prompt=question)
                embedding = response["embedding"]
                
                vector_results = collection.query(
                    query_embeddings=[embedding],
                    n_results=3,
                    include=["documents", "metadatas", "distances"]
                )
                
                # 2. 再用關鍵字搜索
                keyword_results = collection.query(
                    query_texts=[question],
                    n_results=3,
                    include=["documents", "metadatas", "distances"]
                )
                
                # 3. 合併結果並去重
                combined_ids = []
                combined_docs = []
                combined_metadatas = []
                combined_distances = []
                
                # 處理向量結果
                if vector_results['ids'] and len(vector_results['ids'][0]) > 0:
                    for i, doc_id in enumerate(vector_results['ids'][0]):
                        if doc_id not in combined_ids:
                            combined_ids.append(doc_id)
                            combined_docs.append(vector_results['documents'][0][i])
                            combined_metadatas.append(vector_results['metadatas'][0][i])
                            combined_distances.append(vector_results['distances'][0][i])
                
                # 處理關鍵字結果
                if keyword_results['ids'] and len(keyword_results['ids'][0]) > 0:
                    for i, doc_id in enumerate(keyword_results['ids'][0]):
                        if doc_id not in combined_ids:
                            combined_ids.append(doc_id)
                            combined_docs.append(keyword_results['documents'][0][i])
                            combined_metadatas.append(keyword_results['metadatas'][0][i])
                            combined_distances.append(keyword_results['distances'][0][i])
                
                # 組合最終結果
                results = {
                    'ids': [combined_ids],
                    'documents': [combined_docs],
                    'metadatas': [combined_metadatas],
                    'distances': [combined_distances]
                }
                
                print(f"類別查詢結果數量 (混合檢索): {len(results['ids'][0]) if results['ids'] else 0}")
            except Exception as e:
                print(f"混合檢索失敗: {str(e)}，回退到標準向量檢索")
                response = ollama.embeddings(model='mxbai-embed-large', prompt=question)
                embedding = response["embedding"]
                
                results = collection.query(
                    query_embeddings=[embedding],
                    n_results=3,
                    include=["documents", "metadatas", "distances"]
                )
        else:
            # 一般問題使用混合檢索策略
            try:
                # 1. 先用向量搜索
                response = ollama.embeddings(model='mxbai-embed-large', prompt=question)
                embedding = response["embedding"]
                
                vector_results = collection.query(
                    query_embeddings=[embedding],
                    n_results=5,
                    include=["documents", "metadatas", "distances"]
                )
                
                # 2. 再用關鍵字搜索
                keyword_results = collection.query(
                    query_texts=[question],
                    n_results=5,
                    include=["documents", "metadatas", "distances"]
                )
                
                # 3. 合併結果並去重
                combined_ids = []
                combined_docs = []
                combined_metadatas = []
                combined_distances = []
                
                # 處理向量結果
                if vector_results['ids'] and len(vector_results['ids'][0]) > 0:
                    for i, doc_id in enumerate(vector_results['ids'][0]):
                        if doc_id not in combined_ids:
                            combined_ids.append(doc_id)
                            combined_docs.append(vector_results['documents'][0][i])
                            combined_metadatas.append(vector_results['metadatas'][0][i])
                            combined_distances.append(vector_results['distances'][0][i])
                
                # 處理關鍵字結果
                if keyword_results['ids'] and len(keyword_results['ids'][0]) > 0:
                    for i, doc_id in enumerate(keyword_results['ids'][0]):
                        if doc_id not in combined_ids:
                            combined_ids.append(doc_id)
                            combined_docs.append(keyword_results['documents'][0][i])
                            combined_metadatas.append(keyword_results['metadatas'][0][i])
                            combined_distances.append(keyword_results['distances'][0][i])
                
                # 組合最終結果
                results = {
                    'ids': [combined_ids],
                    'documents': [combined_docs],
                    'metadatas': [combined_metadatas],
                    'distances': [combined_distances]
                }
                
                print(f"一般查詢結果數量 (混合檢索): {len(results['ids'][0]) if results['ids'] else 0}")
            except Exception as e:
                print(f"混合檢索失敗: {str(e)}，回退到標準向量檢索")
                response = ollama.embeddings(model='mxbai-embed-large', prompt=question)
                embedding = response["embedding"]
                
                results = collection.query(
                    query_embeddings=[embedding],
                    n_results=5,
                    include=["documents", "metadatas", "distances"]
                )
            print(f"一般問題查詢結果數量: {len(results['ids'][0]) if results['ids'] else 0}")
            
            # 印出查詢資訊以便調試
            if results['ids'] and len(results['ids'][0]) > 0:
                for i, (doc_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
                    metadata = results['metadatas'][0][i] if i < len(results['metadatas'][0]) else {}
                    title = metadata.get('title', '未知標題')
                    print(f"  結果 {i+1}: {title} (距離: {distance:.4f})")
            else:
                print("  未找到任何結果")
                
            # 如果沒有找到結果，嘗試關鍵字直接搜索
            if not results['documents'] or not results['documents'][0]:
                print("嘗試使用文本關鍵字搜索")
                results = collection.query(
                    query_texts=[question],
                    n_results=3,
                    include=["documents", "metadatas", "distances"]
                )
    except Exception as e:
        print(f"查詢過程中發生錯誤: {str(e)}")
        return {"answer": "系統處理您的問題時遇到了技術問題，請稍後再試。", "sources": [], "session_id": session_id}

    # Check if there are any relevant documents
    if not results['documents'] or not results['documents'][0]:
        return {"answer": "很抱歉，我無法從現有的資料中找到與您問題相關的答案。", "sources": []}

    # Construct the prompt for the chat model
    context = "\n".join([f"- {doc}" for doc in results['documents'][0]])
    
    # 增強系統提示設計
    system_prompt = """你是ASUS的資安助手，專門回答資安相關問題。

請遵循以下指示：
1. 僅使用提供的「情境資料」來回答問題，不要使用自己的知識或猜測
2. 如果在資料中能找到明確答案，請準確簡潔地回答
3. 如果問題是關於印表機、機密資料、文件處理等，特別注意找出相關政策與處理方式
4. 如果資訊不足，請直接回答「根據我現有的資料，無法回答這個問題」
5. 回答應保持客觀、準確，並以3-5句話為宜
6. 請用繁體中文回答

記住：精確查找與問題最相關的資訊，不要過度延伸解讀，也不要提供資料中沒有的內容。"""
    
    # 使用者提示
    user_prompt = f"""情境資料：
{context}

問題：{question}"""

    # 獲取當前對話的歷史記錄（最多保留最近5輪）
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
    
    # 生成答案時增加思考步驟，改進參數設定
    messages.append({
        'role': 'system',
        'content': "在回答前，請先分析問題並找出與問題最相關的內容。如果問題是關於印表機、機密資料或文件處理，請特別關注相關規範與處理方式。"
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

    # Extract the answer and the source documents
    answer = chat_response['message']['content']
    sources = results['documents'][0] if results.get('documents') and results['documents'][0] else []
    
    # 更新對話歷史
    conversation_history[session_id]['messages'].append({
        'role': 'user',
        'content': question
    })
    conversation_history[session_id]['messages'].append({
        'role': 'assistant',
        'content': answer
    })
    
    # 只保留最近10條消息（5輪對話）
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