# AI服務與RAG系統技術規格文檔

## 技術棧概覽

### 核心框架
- **FastAPI**: 0.104.1 - 現代化Python Web框架
- **ChromaDB**: 0.4.15 - 向量數據庫
- **Sentence Transformers**: 2.2.2 - 文本嵌入模型
- **Ollama**: 本地LLM服務
- **Uvicorn**: 0.24.0 - ASGI服務器

### AI/ML庫
- **transformers**: 4.35.0 - Hugging Face模型庫
- **torch**: 2.1.0 - PyTorch深度學習框架
- **numpy**: 1.24.3 - 數值計算
- **scikit-learn**: 1.3.0 - 機器學習工具

## 服務架構

### 主服務配置 (`ai-service/main.py`)

**FastAPI應用初始化**:
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import chromadb
from sentence_transformers import SentenceTransformer
import requests
import json

app = FastAPI(
    title="ADC資安情境庫 AI服務",
    description="RAG驅動的智能問答系統",
    version="2.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**全局配置**:
```python
# 服務配置
CONFIG = {
    "embedding_model": "all-MiniLM-L6-v2",
    "ollama_url": "http://localhost:11434",
    "ollama_model": "llama3.1:8b",
    "chroma_db_path": "./chroma_db",
    "max_context_length": 4000,
    "similarity_threshold": 0.7,
    "max_results": 5
}

# 初始化組件
embedding_model = SentenceTransformer(CONFIG["embedding_model"])
chroma_client = chromadb.PersistentClient(path=CONFIG["chroma_db_path"])
collection = chroma_client.get_or_create_collection(
    name="cybersecurity_scenarios",
    metadata={"hnsw:space": "cosine"}
)
```

## RAG系統核心組件

### 1. 文檔嵌入與索引

**文檔處理流程**:
```python
def process_document(scenario_data):
    """處理單個情境文檔"""
    # 構建完整文檔內容
    full_content = f"""
    標題: {scenario_data['title']}
    分類: {scenario_data['category']}
    情境問題: {scenario_data['question']}
    標準答案: {scenario_data['answer']}
    學習重點: {', '.join(scenario_data.get('keyPoints', []))}
    難度: {scenario_data.get('difficulty', '中級')}
    標籤: {', '.join(scenario_data.get('tags', []))}
    """
    
    # 生成嵌入向量
    embedding = embedding_model.encode(full_content)
    
    # 準備元數據
    metadata = {
        "id": str(scenario_data['id']),
        "title": scenario_data['title'],
        "category": scenario_data['category'],
        "difficulty": scenario_data.get('difficulty', '中級'),
        "tags": json.dumps(scenario_data.get('tags', []), ensure_ascii=False)
    }
    
    return {
        "id": f"scenario_{scenario_data['id']}",
        "embedding": embedding.tolist(),
        "document": full_content,
        "metadata": metadata
    }
```

**批量索引建立**:
```python
def build_index_from_scenarios(scenarios_file="scenarios.json"):
    """從情境文件建立向量索引"""
    with open(scenarios_file, 'r', encoding='utf-8') as f:
        scenarios = json.load(f)
    
    documents = []
    embeddings = []
    metadatas = []
    ids = []
    
    for scenario in scenarios:
        processed = process_document(scenario)
        documents.append(processed["document"])
        embeddings.append(processed["embedding"])
        metadatas.append(processed["metadata"])
        ids.append(processed["id"])
    
    # 批量插入ChromaDB
    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"成功索引 {len(scenarios)} 個情境文檔")
```

### 2. 語義搜索引擎

**相似度搜索**:
```python
async def semantic_search(query: str, n_results: int = 5):
    """執行語義搜索"""
    try:
        # 生成查詢嵌入
        query_embedding = embedding_model.encode(query)
        
        # 執行向量搜索
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        # 處理搜索結果
        search_results = []
        for i, (doc, metadata, distance) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0], 
            results["distances"][0]
        )):
            similarity_score = 1 - distance  # 轉換為相似度分數
            
            if similarity_score >= CONFIG["similarity_threshold"]:
                search_results.append({
                    "rank": i + 1,
                    "document": doc,
                    "metadata": metadata,
                    "similarity_score": round(similarity_score, 4),
                    "relevance": "高" if similarity_score > 0.8 else "中"
                })
        
        return search_results
        
    except Exception as e:
        raise HTTPException(status_code=500, f"搜索失敗: {str(e)}")
```

**混合搜索策略**:
```python
def hybrid_search(query: str, filters: dict = None):
    """混合搜索：語義搜索 + 關鍵詞匹配"""
    
    # 1. 語義搜索
    semantic_results = semantic_search(query)
    
    # 2. 關鍵詞搜索
    keyword_results = keyword_search(query, filters)
    
    # 3. 結果融合與重排序
    combined_results = merge_and_rerank(semantic_results, keyword_results)
    
    return combined_results

def keyword_search(query: str, filters: dict = None):
    """基於關鍵詞的搜索"""
    where_clause = {}
    
    if filters:
        if "category" in filters:
            where_clause["category"] = filters["category"]
        if "difficulty" in filters:
            where_clause["difficulty"] = filters["difficulty"]
    
    results = collection.query(
        query_texts=[query],
        n_results=10,
        where=where_clause if where_clause else None,
        include=["documents", "metadatas", "distances"]
    )
    
    return results
```

### 3. LLM整合與對話管理

**Ollama API整合**:
```python
async def call_ollama(prompt: str, model: str = None):
    """調用Ollama LLM服務"""
    model = model or CONFIG["ollama_model"]
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 2000,
            "stop": ["Human:", "用戶:"]
        }
    }
    
    try:
        response = requests.post(
            f"{CONFIG['ollama_url']}/api/generate",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "").strip()
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, f"LLM服務不可用: {str(e)}")
```

**RAG提示詞模板**:
```python
def build_rag_prompt(query: str, context_docs: list):
    """構建RAG提示詞"""
    
    # 構建上下文
    context = "\n\n".join([
        f"【情境 {i+1}】\n{doc['document']}" 
        for i, doc in enumerate(context_docs[:3])
    ])
    
    prompt = f"""你是ADC資安情境庫的專業AI助手，專門回答資訊安全相關問題。

請基於以下資安情境知識來回答用戶問題，確保回答準確、專業且實用。

=== 相關資安情境 ===
{context}

=== 用戶問題 ===
{query}

=== 回答要求 ===
1. 基於提供的情境知識進行回答
2. 回答要專業、準確、易懂
3. 如果問題超出提供的知識範圍，請誠實說明
4. 提供實用的安全建議和最佳實踐
5. 使用繁體中文回答

請回答:"""

    return prompt
```

### 4. 對話API端點

**主要聊天端點**:
```python
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """主要聊天API端點"""
    try:
        query = request.message.strip()
        conversation_id = request.conversation_id or "default"
        
        # 1. 執行語義搜索
        search_results = await semantic_search(query, n_results=5)
        
        if not search_results:
            return ChatResponse(
                response="抱歉，我在知識庫中找不到相關的資安情境。請嘗試重新描述您的問題。",
                sources=[],
                confidence=0.0
            )
        
        # 2. 構建RAG提示詞
        rag_prompt = build_rag_prompt(query, search_results)
        
        # 3. 調用LLM生成回答
        llm_response = await call_ollama(rag_prompt)
        
        # 4. 計算置信度
        avg_similarity = sum(r["similarity_score"] for r in search_results) / len(search_results)
        confidence = min(avg_similarity * 1.2, 1.0)  # 調整置信度
        
        # 5. 準備來源信息
        sources = [
            {
                "title": r["metadata"]["title"],
                "category": r["metadata"]["category"],
                "similarity": r["similarity_score"],
                "relevance": r["relevance"]
            }
            for r in search_results[:3]
        ]
        
        return ChatResponse(
            response=llm_response,
            sources=sources,
            confidence=round(confidence, 3)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, f"處理聊天請求失敗: {str(e)}")
```

**數據模型定義**:
```python
from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    context: Optional[dict] = None

class Source(BaseModel):
    title: str
    category: str
    similarity: float
    relevance: str

class ChatResponse(BaseModel):
    response: str
    sources: List[Source]
    confidence: float
    processing_time: Optional[float] = None
```

## 高級RAG功能

### 1. 查詢擴展與改寫

**同義詞擴展**:
```python
def expand_query(query: str):
    """查詢擴展：添加同義詞和相關詞彙"""
    
    # 資安領域同義詞映射
    synonyms_map = {
        "密碼": ["口令", "通行碼", "認證碼"],
        "駭客": ["黑客", "攻擊者", "惡意用戶"],
        "病毒": ["惡意軟體", "木馬", "蠕蟲"],
        "防火牆": ["網路防護", "安全閘道"],
        "加密": ["編碼", "密碼學", "加密技術"]
    }
    
    expanded_terms = [query]
    
    for term, synonyms in synonyms_map.items():
        if term in query:
            expanded_terms.extend(synonyms)
    
    return " ".join(expanded_terms)
```

**查詢意圖識別**:
```python
def classify_query_intent(query: str):
    """識別查詢意圖"""
    
    intent_patterns = {
        "definition": ["什麼是", "定義", "解釋"],
        "howto": ["如何", "怎麼", "方法"],
        "prevention": ["預防", "避免", "防護"],
        "incident": ["發生", "遇到", "出現問題"],
        "best_practice": ["最佳實踐", "建議", "應該"]
    }
    
    for intent, patterns in intent_patterns.items():
        if any(pattern in query for pattern in patterns):
            return intent
    
    return "general"
```

### 2. 結果重排序與過濾

**智能重排序**:
```python
def rerank_results(results: list, query: str, user_context: dict = None):
    """基於多個因素重新排序搜索結果"""
    
    def calculate_relevance_score(result):
        base_score = result["similarity_score"]
        
        # 分類權重調整
        category_weights = {"A": 1.2, "B": 1.1, "C": 1.0, "D": 0.9}
        category_boost = category_weights.get(result["metadata"]["category"], 1.0)
        
        # 難度匹配
        difficulty_boost = 1.0
        if user_context and "preferred_difficulty" in user_context:
            if result["metadata"]["difficulty"] == user_context["preferred_difficulty"]:
                difficulty_boost = 1.15
        
        # 最終分數
        final_score = base_score * category_boost * difficulty_boost
        
        return final_score
    
    # 重新計算分數並排序
    for result in results:
        result["final_score"] = calculate_relevance_score(result)
    
    return sorted(results, key=lambda x: x["final_score"], reverse=True)
```

### 3. 對話上下文管理

**會話狀態管理**:
```python
class ConversationManager:
    def __init__(self):
        self.conversations = {}
    
    def get_conversation(self, conversation_id: str):
        """獲取對話歷史"""
        return self.conversations.get(conversation_id, {
            "messages": [],
            "context": {},
            "created_at": datetime.now()
        })
    
    def add_message(self, conversation_id: str, message: dict):
        """添加消息到對話歷史"""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = {
                "messages": [],
                "context": {},
                "created_at": datetime.now()
            }
        
        self.conversations[conversation_id]["messages"].append({
            **message,
            "timestamp": datetime.now()
        })
        
        # 保持最近20條消息
        if len(self.conversations[conversation_id]["messages"]) > 20:
            self.conversations[conversation_id]["messages"] = \
                self.conversations[conversation_id]["messages"][-20:]
    
    def get_context_for_query(self, conversation_id: str):
        """獲取查詢上下文"""
        conv = self.get_conversation(conversation_id)
        recent_messages = conv["messages"][-5:]  # 最近5條消息
        
        context = {
            "recent_topics": [],
            "user_preferences": conv.get("context", {}),
            "conversation_length": len(conv["messages"])
        }
        
        return context

# 全局對話管理器
conversation_manager = ConversationManager()
```

## 性能優化與監控

### 1. 緩存策略

**查詢結果緩存**:
```python
from functools import lru_cache
import hashlib

class QueryCache:
    def __init__(self, max_size=1000, ttl=3600):
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl
    
    def get_cache_key(self, query: str, filters: dict = None):
        """生成緩存鍵"""
        content = f"{query}_{json.dumps(filters, sort_keys=True) if filters else ''}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, query: str, filters: dict = None):
        """獲取緩存結果"""
        key = self.get_cache_key(query, filters)
        
        if key in self.cache:
            result, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return result
            else:
                del self.cache[key]
        
        return None
    
    def set(self, query: str, result, filters: dict = None):
        """設置緩存"""
        if len(self.cache) >= self.max_size:
            # 清理最舊的緩存項
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        key = self.get_cache_key(query, filters)
        self.cache[key] = (result, time.time())

query_cache = QueryCache()
```

### 2. 性能監控

**API性能監控**:
```python
import time
from functools import wraps

def monitor_performance(func):
    """性能監控裝飾器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            
            # 記錄成功調用
            processing_time = time.time() - start_time
            logger.info(f"{func.__name__} 執行成功，耗時: {processing_time:.3f}秒")
            
            if hasattr(result, 'processing_time'):
                result.processing_time = processing_time
            
            return result
            
        except Exception as e:
            # 記錄錯誤
            processing_time = time.time() - start_time
            logger.error(f"{func.__name__} 執行失敗，耗時: {processing_time:.3f}秒，錯誤: {str(e)}")
            raise
    
    return wrapper

# 應用到主要端點
@app.post("/chat")
@monitor_performance
async def chat_endpoint(request: ChatRequest):
    # ... 實現代碼
    pass
```

## 部署配置

### requirements.txt
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
chromadb==0.4.15
sentence-transformers==2.2.2
transformers==4.35.0
torch==2.1.0
numpy==1.24.3
scikit-learn==1.3.0
requests==2.31.0
python-multipart==0.0.6
pydantic==2.4.2
```

### 啟動配置
```python
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )
```

---

**文檔版本**: 1.0  
**最後更新**: 2025-08-13  
**技術負責**: AI/ML開發團隊
