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
        elif is_category_query:
            # 對於類別查詢，使用向量查詢
            response = ollama.embeddings(model='mxbai-embed-large', prompt=question)
            embedding = response["embedding"]
            
            # 使用向量搜索，確保與資料庫格式相容
            results = collection.query(
                query_embeddings=[embedding],
                n_results=3
            )
        else:
            # 一般問題使用向量搜索
            response = ollama.embeddings(model='mxbai-embed-large', prompt=question)
            embedding = response["embedding"]

            # Query ChromaDB for relevant scenarios
            results = collection.query(
                query_embeddings=[embedding],
                n_results=3  # Fetch top 3 most relevant scenarios
            )
    except Exception as e:
        print(f"查詢過程中發生錯誤: {str(e)}")
        return {"answer": "系統處理您的問題時遇到了技術問題，請稍後再試。", "sources": [], "session_id": session_id}

    # Check if there are any relevant documents
    if not results['documents'] or not results['documents'][0]:
        return {"answer": "很抱歉，我無法從現有的資料中找到與您問題相關的答案。", "sources": []}

    # Construct the prompt for the chat model
    context = "\n".join([f"- {doc}" for doc in results['documents'][0]])
    
    # 系統提示 - 根據 AI Improved Plan 調整
    system_prompt = """請根據所提供的資料，用不超過五句話簡潔地回答問題。
請只使用提供的「情境資料」來回答問題。如果資訊不足，請直接回答「根據我現有的資料，無法回答這個問題」，不要使用你自己的知識。
答案應當保持客觀、準確，並直接引用提供的資料來源。
請用繁體中文回答。"""
    
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
    
    # Generate the answer using the chat model - 調整生成參數
    chat_response = ollama.chat(
        model='qwen2',
        messages=messages,
        options={
            'temperature': 0.2,  # 降低溫度以提高確定性
            'num_predict': 200   # 限制回答長度
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