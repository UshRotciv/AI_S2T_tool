import shutil
import os
import stat
from fastapi import FastAPI, Depends
import ingest
import threading
import time
import re
import sqlite3

# --- Path Setup ---
# 建立絕對路徑，確保無論從哪裡執行，路徑都正確
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, 'chroma_db')

# --- Database Logging Setup ---
LOG_DB_PATH = os.path.join(SCRIPT_DIR, 'logs.db')

def init_log_db():
    """初始化日誌資料庫並建立 qa_log 資料表"""
    try:
        conn = sqlite3.connect(LOG_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qa_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ 日誌資料庫初始化成功")
    except Exception as e:
        print(f"❌ 日誌資料庫初始化失敗: {e}")

def log_qa(session_id: str, question: str, answer: str):
    """記錄問答對到資料庫"""
    try:
        conn = sqlite3.connect(LOG_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO qa_log (session_id, question, answer) VALUES (?, ?, ?)",
            (session_id, question, answer)
        )
        conn.commit()
        conn.close()
        print(f"📝 問答已記錄 (session: {session_id})")
    except Exception as e:
        print(f"❌ 問答記錄失敗: {e}")

# 幻想內容檢測和修正函式
def filter_hallucinated_content(response_text):
    """
    檢測和過濾回答中的幻想內容，特別是不當的雲端服務提及。
    採用分類和循環替換邏輯，避免重複替換導致的語意錯誤。
    """
    if not response_text or not response_text.strip():
        return response_text

    text = response_text
    modified = False

    # 定義更智能的替換規則
    hallucination_rules = {
        'corporate_services': {
            'keywords': ['AWS', 'Google Cloud', 'Azure'],
            'replacement': '公司指定的雲端服務'
        },
        'corporate_storage': {
            'keywords': ['Amazon S3', 'S3'],
            'replacement': '公司指定的雲端儲存'
        },
        'personal_storage': {
            'keywords': ['Google Drive', 'Dropbox', 'iCloud'],
            'replacements': ['OneDrive', '公司核可的個人雲端硬碟']  # 使用列表進行循環替換
        }
    }

    # 處理個人儲存服務，使用循環替換避免重複
    personal_storage_rules = hallucination_rules['personal_storage']
    personal_keywords = personal_storage_rules['keywords']
    personal_replacements = personal_storage_rules['replacements']
    replacement_index = 0

    # 為了避免在替換時互相影響，先找出所有要替換的詞
    # 按照從長到短的順序排序關鍵字，避免 'Amazon S3' 被 'S3' 規則先匹配
    all_keywords = sorted(
        personal_keywords + 
        hallucination_rules['corporate_services']['keywords'] + 
        hallucination_rules['corporate_storage']['keywords'],
        key=len,
        reverse=True
    )

    for keyword in all_keywords:
        if keyword in text:
            # 決定使用哪個替換詞
            if keyword in personal_keywords:
                replacement = personal_replacements[replacement_index % len(personal_replacements)]
                replacement_index += 1
            elif keyword in hallucination_rules['corporate_services']['keywords']:
                replacement = hallucination_rules['corporate_services']['replacement']
            else: # corporate_storage
                replacement = hallucination_rules['corporate_storage']['replacement']
            
            # 執行替換
            if keyword in text:
                text = text.replace(keyword, replacement)
                modified = True
                print(f"⚠️ 檢測到幻想內容 '{keyword}'，已替換為 '{replacement}'")

    if modified:
        print("✅ 已過濾幻想內容，確保回答符合公司政策")

    return text

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

@app.on_event("startup")
async def startup_event():
    init_log_db()

# 3. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 資料庫連接與集合設定
# 使用絕對路徑進行連接，關閉匿名遙測
client = chromadb.PersistentClient(
    path=DB_PATH,
    settings=chromadb.Settings(anonymized_telemetry=False)
)

# 嵌入函數設定 - 支援環境變數切換
EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "sentence-transformers")  # 預設使用 sentence-transformers
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

if EMBEDDING_BACKEND.lower() == "ollama":
    # 使用 Ollama 嵌入
    embedding_function = embedding_functions.OllamaEmbeddingFunction(
        model_name=EMBEDDING_MODEL,
        url="http://localhost:11434",
    )
    print(f"使用 Ollama 嵌入模型: {EMBEDDING_MODEL}")
else:
    # 使用 sentence-transformers 嵌入 (預設，更穩定)
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    print(f"使用 SentenceTransformer 嵌入模型: {EMBEDDING_MODEL}")

# 智能查詢擴展詞組庫 - 提升檢索覆蓋範圍和準確性
QUERY_EXPANSIONS = {
    # 文件處理相關
    "作品集": [
        "準備作品集的資安注意事項", "對外公開作品集的規範", "未採用提案是否可放進作品集",
        "作品集避免洩露公司機密", "個人作品集與智慧財產權", "員工作品集公開限制"
    ],
    "印表機": [
        "印表機機密文件處理", "印表機列印機密資料", "印表機安全使用規範",
        "機密文件印表機操作", "列印機密資料注意事項", "印表機資安風險"
    ],
    "機密": [
        "機密文件處理規範", "機密資料保護措施", "機密等級分類",
        "機密文件銷毀程序", "機密資訊洩露防範", "機密檔案管理"
    ],
    
    # 軟體使用相關
    "測試軟體": [
        "免費測試軟體風險", "測試軟體安全性", "軟體測試安全規範",
        "免費軟體使用風險", "軟體下載安全注意事項"
    ],
    "軟體": [
        "軟體安裝規範", "軟體使用授權", "軟體安全更新",
        "軟體下載來源驗證", "軟體使用政策"
    ],
    "下載": [
        "軟體下載安全規範", "檔案下載風險評估", "下載來源驗證",
        "安全下載指引", "下載檔案掃毒"
    ],
    
    # 辦公設備相關
    "USB": [
        "USB使用規範", "USB安全政策", "外接儲存裝置管理",
        "USB病毒防護", "可攜式儲存媒體安全"
    ],
    "隨身碟": [
        "隨身碟使用規範", "隨身碟安全管理", "外接儲存裝置政策",
        "隨身碟資料加密", "可攜式媒體安全"
    ],
    
    # 網路安全相關
    "密碼": [
        "密碼設定規範", "密碼安全政策", "密碼管理最佳實務",
        "強密碼建立指引", "密碼更新頻率"
    ],
    "釣魚": [
        "釣魚郵件識別", "釣魚攻擊防範", "社交工程防護",
        "可疑郵件處理", "釣魚網站辨識"
    ],
    "郵件": [
        "電子郵件安全", "郵件附件安全", "郵件加密規範",
        "可疑郵件處理", "郵件安全政策"
    ],
    
    # 工作流程相關
    "遠端": [
        "遠端工作安全", "居家辦公資安", "遠端連線安全",
        "遠端存取規範", "在家工作安全指引"
    ],
    "備份": [
        "資料備份規範", "備份安全管理", "備份資料保護",
        "備份策略規劃", "資料復原程序"
    ],
    "權限": [
        "存取權限管理", "使用者權限控制", "權限分級制度",
        "權限審核程序", "最小權限原則"
    ],
    
    # 智慧財產權相關
    "智財": [
        "智慧財產權保護", "智財管理規範", "智財洩露防範",
        "智財使用授權", "智財安全政策"
    ],
    "專利": [
        "專利保護措施", "專利資訊管理", "專利洩露防範",
        "專利申請安全", "專利機密保護"
    ],
    
    # 一般資安概念
    "資安": [
        "資訊安全政策", "資安管理制度", "資安風險評估",
        "資安事件處理", "資安教育訓練", "資安最佳實務"
    ],
    "安全": [
        "辦公室安全規範", "資訊安全措施", "安全管理制度",
        "安全政策執行", "安全風險控制"
    ]
}

# 獲取或創建集合，使用一致的嵌入函數
# 使用 scenarios 集合名稱
COLLECTION_NAME = "scenarios"

try:
    # 1. get_collection 也綁定 embedding_function
    collection = client.get_collection(
        COLLECTION_NAME,
        embedding_function=embedding_function
    )
    print(f"成功連接到現有的{COLLECTION_NAME}集合")
except:
    print(f"集合{COLLECTION_NAME}不存在，請先執行ingest.py建立資料庫")
    collection = client.create_collection(
        COLLECTION_NAME,
        embedding_function=embedding_function,
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

# 5. 空結果檢查輔助函式（修正邏輯）
def empty_results(r):
    if not r:
        return True
    if not r.get('documents'):
        return True
    if not r['documents']:
        return True
    if not r['documents'][0]:
        return True
    if len(r['documents'][0]) == 0:
        return True
    return False

# 檢索結果後處理：距離門檻過濾 + 去重（依 parent_id 或 title 分組）
def postprocess_results(results: Dict[str, Any], distance_threshold: float = 0.45, max_per_group: int = 2) -> Dict[str, Any]:
    """
    對檢索結果進行低風險後處理：
    1) 過濾距離過大的候選（cosine 距離門檻）
    2) 依 parent_id 或 title 分組，保留每組距離最小的前 N 筆

    備註：若傳入結構不完整，將原樣返回以避免影響主流程。
    """
    try:
        if not results or not results.get('ids') or not results['ids'] or not results['ids'][0]:
            return results

        ids = results['ids'][0]
        docs = results['documents'][0] if results.get('documents') and results['documents'] else []
        mds = results['metadatas'][0] if results.get('metadatas') and results['metadatas'] else []
        dists = results['distances'][0] if results.get('distances') and results['distances'] else []

        # 將元素打包為統一清單，方便篩選與分組
        items = []
        for i, doc_id in enumerate(ids):
            item = {
                'id': doc_id,
                'document': docs[i] if i < len(docs) else "",
                'metadata': mds[i] if i < len(mds) else {},
                'distance': dists[i] if i < len(dists) else None,
                'index': i,
            }
            items.append(item)

        before_count = len(items)

        # 1) 距離門檻過濾
        filtered = []
        for it in items:
            dist = it.get('distance')
            # 沒有距離資訊的保留（保守作法），有距離則需低於門檻
            if dist is None or dist < distance_threshold:
                filtered.append(it)
        after_threshold = len(filtered)
        print(f"後處理-距離門檻: {before_count} -> {after_threshold} (threshold={distance_threshold})")

        if not filtered:
            # 全被過濾，避免影響流程，回傳原始結果
            print("後處理結果為空，回退使用原始結果")
            return results

        # 2) 依 parent_id 或 title 分組去重（避免 ungrouped 吃光結果）
        from collections import defaultdict
        groups = defaultdict(list)
        for it in filtered:
            md = it.get('metadata') or {}
            base_key = md.get('parent_id') or md.get('title')
            # 沒有 parent_id/title 時，每個 id 自成一組
            key = base_key if base_key else f"__ungrouped__{it['id']}"
            groups[key].append(it)

        # 每組取距離最小的前 N 筆
        selected = []
        for key, arr in groups.items():
            arr_sorted = sorted(arr, key=lambda x: (float('inf') if x.get('distance') is None else x['distance']))
            keep = arr_sorted[:max_per_group]
            selected.extend(keep)
        after_group = len(selected)
        print(f"後處理-分組去重: {after_threshold} -> {after_group} (max_per_group={max_per_group}, groups={len(groups)})")

        # 重新構建 results 結構
        new_ids = []
        new_docs = []
        new_mds = []
        new_dists = []
        for it in selected:
            new_ids.append(it['id'])
            new_docs.append(it.get('document', ""))
            new_mds.append(it.get('metadata', {}))
            new_dists.append(it.get('distance'))

        new_results = {
            'ids': [new_ids],
            'documents': [new_docs],
            'metadatas': [new_mds],
            'distances': [new_dists],
        }

        return new_results
    except Exception as e:
        print(f"後處理發生錯誤，使用原始結果: {e}")
        return results

# 智能查詢擴展函式 - 提升檢索效果和覆蓋範圍
def expand_query(original_query):
    """
    智能查詢擴展函式 - 根據查詢內容和長度智能擴展
    """
    expanded_queries = [original_query]  # 始終包含原查詢
    
    # 1. 精確匹配擴展
    for key, values in QUERY_EXPANSIONS.items():
        if key in original_query:
            print(f"✓ 為查詢 '{original_query}' 找到精確匹配擴展: '{key}' -> {len(values)} 個相關查詢")
            expanded_queries.extend(values[:5])  # 限制擴展數量避免過多
            break  # 找到一個匹配就停止，避免過度擴展
    
    # 2. 部分匹配擴展（針對複合查詢）
    if len(expanded_queries) == 1:  # 如果沒有精確匹配
        for key, values in QUERY_EXPANSIONS.items():
            if any(char in original_query for char in key) and len(key) > 1:
                print(f"✓ 為查詢 '{original_query}' 找到部分匹配擴展: '{key}' -> 添加 2 個相關查詢")
                expanded_queries.extend(values[:2])  # 部分匹配只添加少量
                break
    
    # 3. 短查詢智能擴展
    chinese_chars = len(re.sub(r'[^\u4e00-\u9fff]', '', original_query))
    if chinese_chars < 4 and len(expanded_queries) == 1:
        # 對於極短查詢，嘗試語義相關的擴展
        short_query_expansions = {
            "列印": ["印表機", "機密"],
            "下載": ["軟體", "測試軟體"],
            "郵件": ["釣魚", "安全"],
            "密碼": ["安全", "資安"],
            "備份": ["資料", "安全"],
            "遠端": ["工作", "安全"]
        }
        
        for short_key, related_keys in short_query_expansions.items():
            if short_key in original_query:
                for related_key in related_keys:
                    if related_key in QUERY_EXPANSIONS:
                        expanded_queries.extend(QUERY_EXPANSIONS[related_key][:3])
                        print(f"✓ 短查詢 '{original_query}' 通過 '{short_key}' -> '{related_key}' 擴展")
                        break
                break
    
    # 4. 去重並限制總數
    seen = set()
    unique_queries = []
    for query in expanded_queries:
        if query not in seen:
            seen.add(query)
            unique_queries.append(query)
    
    # 限制最大查詢數量，避免檢索時間過長
    final_queries = unique_queries[:8]
    
    if len(final_queries) > 1:
        print(f"📝 查詢擴展完成: '{original_query}' -> {len(final_queries)} 個查詢")
    else:
        print(f"📝 查詢未擴展: '{original_query}' (無匹配的擴展詞組)")
    
    return final_queries

# 分層檢索策略 - 強化 JSON 錯誤處理版本
def layered_search(collection, query, n_results=7, timeout_sec=3.0):
    """
    分層檢索策略（JSON 錯誤修復版）
    第一層：Part A-D 情境卡優先（實際存在的類別）
    第二層：排除 rule_document
    第三層：全庫檢索
    增強 JSON 解析錯誤處理
    """
    
    def safe_chromadb_query(collection, query_params, layer_name):
        """安全的 ChromaDB 查詢包裝器，處理 JSON 解析錯誤"""
        try:
            print(f"{layer_name}檢索: 開始查詢")
            result = collection.query(**query_params)
            
            # 驗證結果結構
            if not isinstance(result, dict):
                print(f"{layer_name}檢索失敗: 結果不是字典格式")
                return None
                
            required_keys = ['ids', 'documents', 'metadatas', 'distances']
            for key in required_keys:
                if key not in result:
                    print(f"{layer_name}檢索失敗: 缺少必要鍵 '{key}'")
                    return None
            
            # 檢查結果是否為空
            if not result.get('ids') or not result['ids'][0]:
                print(f"{layer_name}檢索: 無結果")
                return None
                
            result_count = len(result['ids'][0])
            print(f"{layer_name}檢索成功: 找到 {result_count} 個結果")
            return result
            
        except json.JSONDecodeError as je:
            print(f"{layer_name}檢索失敗: JSON 解析錯誤 - {je}")
            print(f"錯誤位置: line {je.lineno}, column {je.colno}")
            return None
        except Exception as e:
            error_msg = str(e)
            if "Extra data" in error_msg:
                print(f"{layer_name}檢索失敗: ChromaDB JSON 格式錯誤 - {error_msg}")
                print("建議重建資料庫以修復數據格式問題")
            else:
                print(f"{layer_name}檢索失敗: {error_msg}")
            return None
    
    # 第一層：優先檢索 Part A-D 情境卡
    scenario_categories = [
        "Part A: 辦公室基礎好習慣 (Basic Office Habits)",
        "Part B: 數位檔案的溝通與傳遞 (Digital File Communication & Transfer)", 
        "Part C: 機敏資料與高風險工具 (Sensitive Data & High-Risk Tools)",
        "Part D: 智慧財產與你的權責 (Intellectual Property & Your Responsibilities)"
    ]
    
    layer1_params = {
        "query_texts": [query],
        "n_results": n_results,
        "where": {"category": {"$in": scenario_categories}},
        "include": ["documents", "metadatas", "distances"]
    }
    
    layer1_results = safe_chromadb_query(collection, layer1_params, "第一層")
    if layer1_results:
        return layer1_results, "scenario_parts"
    
    # 第二層：排除 rule_document
    layer2_params = {
        "query_texts": [query],
        "n_results": n_results,
        "where": {"category": {"$ne": "rule_document"}},
        "include": ["documents", "metadatas", "distances"]
    }
    
    layer2_results = safe_chromadb_query(collection, layer2_params, "第二層")
    if layer2_results:
        return layer2_results, "filtered"
    
    # 第三層：全庫檢索
    layer3_params = {
        "query_texts": [query],
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"]
    }
    
    layer3_results = safe_chromadb_query(collection, layer3_params, "第三層")
    if layer3_results:
        return layer3_results, "full"
    
    print("所有層級檢索都無結果")
    return None, "none"

@app.post("/api/ask")
def ask(request: AskRequest):
    question = request.question
    session_id = get_or_create_session(request.session_id)

    # 檢查是否是關於 AI 本身的問題（元問題）
    meta_keywords = ["你是誰", "你是", "你知道什麼", "你知道甚麼", "你能做什麼", "你會什麼", "自我介紹"]
    is_meta_question = any(keyword in question for keyword in meta_keywords)
    
    try:
        if is_meta_question:
            # 對於元問題，使用安全包裝器查詢元文檔
            def safe_meta_query(collection, query_params, layer_name):
                """安全的元問題查詢包裝器"""
                try:
                    print(f"{layer_name}檢索: 開始查詢")
                    result = collection.query(**query_params)
                    
                    # 驗證結果結構
                    if not isinstance(result, dict):
                        print(f"{layer_name}檢索失敗: 結果不是字典格式")
                        return None
                        
                    required_keys = ['ids', 'documents', 'metadatas', 'distances']
                    for key in required_keys:
                        if key not in result:
                            print(f"{layer_name}檢索失敗: 缺少必要鍵 '{key}'")
                            return None
                    
                    # 檢查結果是否為空
                    if not result.get('ids') or not result['ids'][0]:
                        print(f"{layer_name}檢索: 無結果")
                        return None
                        
                    result_count = len(result['ids'][0])
                    print(f"{layer_name}檢索成功: 找到 {result_count} 個結果")
                    return result
                    
                except json.JSONDecodeError as je:
                    print(f"{layer_name}檢索失敗: JSON 解析錯誤 - {je}")
                    print(f"錯誤位置: line {je.lineno}, column {je.colno}")
                    return None
                except Exception as e:
                    error_msg = str(e)
                    if "Extra data" in error_msg:
                        print(f"{layer_name}檢索失敗: ChromaDB JSON 格式錯誤 - {error_msg}")
                        print("建議重建資料庫以修復數據格式問題")
                    else:
                        print(f"{layer_name}檢索失敗: {error_msg}")
                    return None
            
            meta_params = {
                "query_texts": [question],
                "n_results": 5,
                "where": {"category": "meta"},
                "include": ["documents", "metadatas", "distances"]
            }
            
            results = safe_meta_query(collection, meta_params, "元問題")
            if results:
                print(f"元問題查詢結果: 找到 {len(results['ids'][0])} 個文件")
                search_type = "meta"
            else:
                print("元問題查詢失敗，改用一般檢索策略")
                results = None
                search_type = "fallback"
        else:
            # 步驟 1: 對一般問題應用查詢擴展 + 分層檢索策略
            print(f"===== 進階檢索策略 =====")
            print(f"原始查詢: '{question}'")
            
            # 執行查詢擴展
            expanded_queries = expand_query(question)
            
            # 如果有多個查詢，依次嘗試
            all_results = []
            best_result = None
            best_score = float('inf')
            best_search_type = "none"
            
            for i, query in enumerate(expanded_queries):
                print(f"測試查詢 {i+1}/{len(expanded_queries)}: '{query}'")
                
                # 對每個查詢應用分層檢索
                result, search_type = layered_search(collection, query, n_results=10)
                
                if result and result.get('distances') and result['distances'][0]:
                    min_distance = min(result['distances'][0])
                    result_count = len(result['ids'][0])
                    print(f"  '{query}': {result_count} 結果, 最佳距離: {min_distance:.4f}, 層級: {search_type}")
                    
                    all_results.append((query, result, min_distance, search_type))
                    
                    # 如果是情境卡結果，優先使用
                    if search_type == "scenario_card" and (best_search_type != "scenario_card" or min_distance < best_score):
                        best_score = min_distance
                        best_result = result
                        best_search_type = search_type
                    # 否則根據距離選擇最佳結果
                    elif search_type != "scenario_card" and best_search_type != "scenario_card" and min_distance < best_score:
                        best_score = min_distance
                        best_result = result
                        best_search_type = search_type
                else:
                    print(f"  '{query}': 無結果")
            
            # 選擇最佳結果
            if best_result:
                results = best_result
                print(f"===== 選擇最佳結果 =====")
                print(f"最佳距離: {best_score:.4f}, 層級: {best_search_type}")
                search_type = best_search_type
            else:
                # 如果所有查詢都沒有結果，退回到基本查詢（使用安全包裝器）
                print(f"===== 所有查詢都無結果，執行標準向量檢索 =====")
                
                # 重用安全查詢包裝器
                def safe_fallback_query(collection, query_params, layer_name):
                    """安全的 fallback 查詢包裝器"""
                    try:
                        print(f"{layer_name}檢索: 開始查詢")
                        result = collection.query(**query_params)
                        
                        # 驗證結果結構
                        if not isinstance(result, dict):
                            print(f"{layer_name}檢索失敗: 結果不是字典格式")
                            return None
                            
                        required_keys = ['ids', 'documents', 'metadatas', 'distances']
                        for key in required_keys:
                            if key not in result:
                                print(f"{layer_name}檢索失敗: 缺少必要鍵 '{key}'")
                                return None
                        
                        # 檢查結果是否為空
                        if not result.get('ids') or not result['ids'][0]:
                            print(f"{layer_name}檢索: 無結果")
                            return None
                            
                        result_count = len(result['ids'][0])
                        print(f"{layer_name}檢索成功: 找到 {result_count} 個結果")
                        return result
                        
                    except json.JSONDecodeError as je:
                        print(f"{layer_name}檢索失敗: JSON 解析錯誤 - {je}")
                        print(f"錯誤位置: line {je.lineno}, column {je.colno}")
                        return None
                    except Exception as e:
                        error_msg = str(e)
                        if "Extra data" in error_msg:
                            print(f"{layer_name}檢索失敗: ChromaDB JSON 格式錯誤 - {error_msg}")
                            print("建議重建資料庫以修復數據格式問題")
                        else:
                            print(f"{layer_name}檢索失敗: {error_msg}")
                        return None
                
                fallback_params = {
                    "query_texts": [question],
                    "n_results": 7,
                    "include": ["documents", "metadatas", "distances"]
                }
                
                results = safe_fallback_query(collection, fallback_params, "標準向量檢索")
                search_type = "fallback"

        # 智能後處理：動態距離門檻 + 分組去重
        try:
            before_cnt = len(results['ids'][0]) if results.get('ids') and results['ids'] and results['ids'][0] else 0
            
            # 根據檢索類型動態調整距離門檻
            if search_type == "scenario_card":
                threshold = 0.35  # 情境卡片要求更高相似度
            elif search_type == "meta":
                threshold = 0.45  # 元問題可以放寬
            else:
                threshold = 0.40  # 一般查詢使用中等門檻
            
            results = postprocess_results(results, distance_threshold=threshold, max_per_group=3)
            after_cnt = len(results['ids'][0]) if results.get('ids') and results['ids'] and results['ids'][0] else 0
            print(f"智能後處理完成: {before_cnt} -> {after_cnt} (threshold={threshold}, type={search_type})")
        except Exception as e:
            print(f"後處理套用失敗（將忽略後處理）: {e}")

        # 可選：弱結果時進行再排序（fallback），失敗則自動回退
        try:
            trigger_rerank = False
            min_dist = None
            if results.get('distances') and results['distances'] and results['distances'][0]:
                # 過濾 None 後計算最小值
                valid_dists = [d for d in results['distances'][0] if d is not None]
                if valid_dists:
                    min_dist = min(valid_dists)
            cand_count = len(results['ids'][0]) if results.get('ids') and results['ids'] and results['ids'][0] else 0
            # 動態觸發條件：避免過度啟動 rerank
            if cand_count == 0:
                trigger_rerank = False
            elif min_dist is not None and min_dist < 0.28:
                trigger_rerank = False  # 已經很像，不必 rerank
            else:
                # 候選偏少且不夠像 -> rerank
                if cand_count < 5 and (min_dist is None or min_dist > 0.36):
                    trigger_rerank = True
            
            if trigger_rerank:
                print(f"啟用再排序 fallback：cand_count={cand_count}, min_dist={min_dist}")
                # 構建候選文檔
                ids = results['ids'][0]
                docs = results['documents'][0] if results.get('documents') and results['documents'] else []
                mds = results['metadatas'][0] if results.get('metadatas') and results['metadatas'] else []
                dists = results['distances'][0] if results.get('distances') and results['distances'] else []

                candidates = []
                for i, doc_id in enumerate(ids):
                    candidates.append({
                        'id': doc_id,
                        'text': docs[i] if i < len(docs) else "",
                        'metadata': mds[i] if i < len(mds) else {},
                        'distance': dists[i] if i < len(dists) else None,
                    })

                # 調用輕量 reranker（僅在需要時）
                try:
                    from reranker import ReRanker
                    rr = ReRanker(model_name='qwen2')
                    top_k = min(5, len(candidates))
                    reranked = rr.rerank(question, candidates, top_k=top_k)
                    if reranked:
                        # 以 rerank 結果重建 results
                        new_ids, new_docs, new_mds, new_dists = [], [], [], []
                        for item in reranked:
                            new_ids.append(item.get('id'))
                            new_docs.append(item.get('text', ""))
                            new_mds.append(item.get('metadata', {}))
                            new_dists.append(item.get('distance'))
                        results = {
                            'ids': [new_ids],
                            'documents': [new_docs],
                            'metadatas': [new_mds],
                            'distances': [new_dists],
                        }
                        print(f"再排序完成，保留 {len(new_ids)} 筆候選作為最終輸入")
                    else:
                        print("再排序未返回有效結果，沿用原始順序")
                except Exception as re:
                    print(f"再排序過程失敗或模型不可用，沿用原始結果: {re}")
        except Exception as e:
            print(f"評估是否需要再排序時發生錯誤：{e}")

        # 檢查結果是否為空
        if empty_results(results):
            print("查詢結果確實為空")
            return {"answer":"很抱歉，我無法從現有的資料中找到與您問題相關的答案。","sources":[],"session_id":session_id}

        # 詳細調試資訊輸出
        if results.get('ids') and results['ids'] and len(results['ids'][0]) > 0:
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
        # 加強錯誤資訊輸出，避免靜默失敗
        try:
            import traceback
            tb = traceback.format_exc()
        except Exception:
            tb = str(e)
        print(f"查詢過程中發生錯誤: {str(e)}\n{tb}")
        # 將錯誤細節一併回傳，方便前後端快速定位問題（前端可視需要隱藏詳細錯誤）
        return {
            "answer": "系統處理您的問題時遇到了技術問題，請稍後再試。",
            "error": str(e),
            "trace": tb,
            "sources": [],
            "session_id": session_id
        }

    # Check if there are any relevant documents
    if not results['documents'] or not results['documents'][0]:
        return {"answer": "很抱歉，我無法從現有的資料中找到與您問題相關的答案。", "sources": [], "session_id": session_id}

    # Construct the prompt for the chat model
    context = "\n".join([f"- {doc}" for doc in results['documents'][0]])
    
    # 添加調試輸出，查看實際的 context 內容
    print(f"=== 傳送給 LLM 的 Context 內容 ===")
    print(f"Context 長度: {len(context)} 字符")
    print(f"Context 內容預覽: {context[:500]}...")
    print(f"=== Context 結束 ===")
    
    # 優化的智能助手提示策略
    system_prompt = """你是 ASUS 資安助手，專門協助員工處理資訊安全、辦公室安全和工作流程相關問題。

**核心原則**：
1. **準確性優先**：以提供的卡片內容為主要依據，確保資訊正確性
2. **智能整合**：可以整合多個卡片內容，提供完整且有邏輯的回答
3. **實用導向**：結合卡片內容與合理推理，提供實用的建議和解決方案
4. **專業表達**：使用專業但易懂的語言，避免過於技術性的術語

**回答策略**：
- 優先使用卡片中的 answerLabel 和 learningsLabel 內容
- 可以重新組織和整理卡片內容，使回答更清晰易懂
- 當卡片內容不完整時，可以提供合理的補充說明
- 對於複雜問題，可以分步驟或分類別進行回答
- 適當使用格式化（如條列、編號）提升可讀性

**品質標準**：
- 回答要完整、準確、實用
- 語調要專業但親切
- 結構要清晰有條理
- 重點要突出明確"""

    # 查詢類型標記
    search_type_info = ""
    if search_type == "scenario_card":
        search_type_info = "情境卡片優先"
    elif search_type == "filtered":
        search_type_info = "過濾非規則文檔"
    elif search_type == "full":
        search_type_info = "全庫檢索"
    elif search_type == "meta":
        search_type_info = "元問題查詢"
    
    user_prompt = f"""**參考資料**：
{context}

**用戶問題**：{question}

**回答指引**：
1. **相關性判斷**：判斷問題是否與資安、辦公安全、工作流程等職場主題相關
2. **資料整合**：分析參考資料，找出與問題最相關的內容
3. **智能回答**：
   - 優先使用參考資料中的核心內容（answerLabel、learningsLabel）
   - 可以重新組織內容結構，使回答更清晰
   - 對於複雜問題，可以分點或分步驟回答
   - 適當補充實用的操作建議
4. **品質控制**：
   - 確保回答完整且實用
   - 使用專業但易懂的語言
   - 重點內容可以加粗或使用條列格式
   - 如果參考資料不足，誠實說明並提供可能的建議

**檢索策略**：{search_type_info}

請基於以上指引，提供一個專業、實用且易懂的回答。"""

    # 智能上下文管理：根據問題類型調整歷史記錄數量
    with history_lock:
        all_history = conversation_history[session_id]['messages'] if conversation_history[session_id]['messages'] else []
        
        # 根據問題類型決定上下文長度
        if is_meta_question:
            # 元問題不需要太多歷史
            history = all_history[-2:] if all_history else []
        elif any(keyword in question.lower() for keyword in ["繼續", "接著", "然後", "還有", "另外"]):
            # 連續性問題需要更多上下文
            history = all_history[-8:] if all_history else []
        else:
            # 一般問題保持適中的上下文
            history = all_history[-5:] if all_history else []
    
    # 構建完整的消息列表，包含系統提示、對話歷史和當前問題
    context_hint = ""
    if history:
        context_hint = f"\n\n**對話上下文**：用戶之前詢問了 {len(history)//2} 個相關問題，請保持回答的連貫性和一致性。"
    
    messages = [
        {
            'role': 'system',
            'content': system_prompt + context_hint,
        }
    ]
    
    # 添加歷史對話（優化格式）
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
    
    try:
        # 首先檢查 Ollama 服務是否可用
        try:
            available_models = ollama.list()
            print(f"可用模型: {[model['name'] for model in available_models.get('models', [])]}")
        except Exception as model_check_error:
            print(f"Ollama 服務連接失敗: {model_check_error}")
            raise Exception(f"Ollama 服務不可用: {model_check_error}")
        
        # 檢查 qwen2 模型是否可用
        model_names = [model['name'] for model in available_models.get('models', [])]
        if 'qwen2:latest' not in model_names and 'qwen2' not in model_names:
            print(f"qwen2 模型不可用，嘗試使用其他可用模型: {model_names}")
            # 嘗試使用第一個可用模型
            if model_names:
                selected_model = model_names[0]
                print(f"使用模型: {selected_model}")
            else:
                raise Exception("沒有可用的 Ollama 模型")
        else:
            selected_model = 'qwen2'
        
        print(f"開始調用 Ollama 模型: {selected_model}")
        print(f"消息數量: {len(messages)}")
        print(f"上下文長度: {len(context) if 'context' in locals() else 'N/A'}")
        
        chat_response = ollama.chat(
            model=selected_model,
            messages=messages,
            options={
                'temperature': 0.1,  # 進一步降低溫度以提高確定性
                'num_predict': 300,   # 適度增加長度限制以確保完整回答
                'top_p': 0.8,        # 控制生成文本的多樣性
                'top_k': 30          # 限制候選詞彙數量
            }
        )
        
        print(f"Ollama 調用成功，回應類型: {type(chat_response)}")
        print(f"回應鍵: {list(chat_response.keys()) if isinstance(chat_response, dict) else 'N/A'}")
        
        # Extract the answer and the source documents（統一物件結構，包含 id/metadata/distance/document）
        if isinstance(chat_response, dict) and 'message' in chat_response:
            raw_answer = chat_response['message']['content']
            print(f"原始答案長度: {len(raw_answer)}")
            
            # 步驟1：過濾幻想內容，特別是不當的雲端服務
            answer = filter_hallucinated_content(raw_answer)
            print(f"過濾後答案長度: {len(answer)}")
        else:
            print(f"意外的回應格式: {chat_response}")
            answer = "AI 服務回應格式異常，請稍後再試。"
            
    except Exception as e:
        print(f"Ollama 調用失敗: {e}")
        import traceback
        print(f"詳細錯誤追蹤: {traceback.format_exc()}")
        answer = f"很抱歉，AI 服務暫時無法處理您的問題。錯誤詳情: {str(e)}"
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
    
    # 記錄問答日誌
    log_qa(session_id, question, answer)
    
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
    """A simple endpoint to check if the service is up and running."""
    return {"status": "ok"}

@app.get("/api/health")
def get_health():
    """獲取詳細服務狀態"""
    # 執行清理過期會話
    expired_count = cleanup_expired_conversations()
    
    # 檢查資料庫狀態
    db_info = {}
    try:
        collections = client.list_collections()
        db_info = {
            "collections_count": len(collections),
            "collections": []
        }
        total_docs = 0
        for collection in collections:
            count = collection.count()
            total_docs += count
            db_info["collections"].append({
                "name": collection.name,
                "document_count": count
            })
        db_info["total_documents"] = total_docs
        db_info["status"] = "connected"
    except Exception as e:
        db_info = {
            "status": "error",
            "error": str(e)
        }
    
    return {
        "status": "running",
        "active_conversations": len(conversation_history),
        "cleaned_conversations": expired_count,
        "database": db_info
    }

# --- 同步端點：支援增量向量更新 ---
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import hashlib
import json

class SyncRequest(BaseModel):
    operation: str  # "upsert" 或 "delete"
    data: Optional[List[Dict[str, Any]]] = None  # upsert 時的資料
    ids: Optional[List[str]] = None  # delete 時的 ID 列表

def generate_content_hash(content: str) -> str:
    """生成內容雜湊值"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def format_scenario_for_vector(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """將 scenario 資料格式化為向量儲存格式"""
    content = f"{scenario.get('title', '')}\n\n{scenario.get('body', '')}"
    
    return {
        'id': scenario['id'],
        'content': content,
        'metadata': {
            'source': 'scenario',
            'title': scenario.get('title', ''),
            'group_id': scenario.get('group_id', ''),
            'updated_at': scenario.get('updated_at', ''),
            'content_hash': generate_content_hash(content)
        }
    }

@app.post("/api/sync")
async def sync_vectors(request: SyncRequest):
    """
    同步向量資料庫
    支援 upsert (新增/更新) 和 delete (刪除) 操作
    """
    try:
        # 初始化 ChromaDB 連線
        import chromadb
        from chromadb.config import Settings
        
        client = chromadb.PersistentClient(
            path=DB_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        
        COLLECTION_NAME = "asus_security_docs"
        
        try:
            collection = client.get_collection(COLLECTION_NAME)
        except Exception:
            # 如果集合不存在，建立新集合
            collection = client.create_collection(
                name=COLLECTION_NAME,
                metadata={"description": "ASUS Security Documents and Scenarios"}
            )
        
        if request.operation == "upsert":
            if not request.data:
                return {"success": False, "message": "No data provided for upsert operation"}
            
            # 處理 upsert 操作
            documents = []
            metadatas = []
            ids = []
            
            for item in request.data:
                formatted = format_scenario_for_vector(item)
                documents.append(formatted['content'])
                metadatas.append(formatted['metadata'])
                ids.append(formatted['id'])
            
            # 執行 upsert
            collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            return {
                "success": True,
                "operation": "upsert",
                "processed_count": len(request.data),
                "message": f"Successfully upserted {len(request.data)} documents"
            }
            
        elif request.operation == "delete":
            if not request.ids:
                return {"success": False, "message": "No IDs provided for delete operation"}
            
            # 處理 delete 操作
            try:
                collection.delete(ids=request.ids)
                
                return {
                    "success": True,
                    "operation": "delete",
                    "processed_count": len(request.ids),
                    "message": f"Successfully deleted {len(request.ids)} documents"
                }
            except Exception as e:
                # 如果某些 ID 不存在，仍然回傳成功
                return {
                    "success": True,
                    "operation": "delete",
                    "processed_count": len(request.ids),
                    "message": f"Delete operation completed (some IDs may not exist): {str(e)}"
                }
        
        else:
            return {"success": False, "message": f"Unknown operation: {request.operation}"}
            
    except Exception as e:
        print(f"❌ Sync operation failed: {str(e)}")
        return {
            "success": False,
            "message": f"Sync operation failed: {str(e)}"
        }

@app.get("/api/sync/status")
async def sync_status():
    """
    檢查同步服務狀態
    """
    try:
        import chromadb
        from chromadb.config import Settings
        
        client = chromadb.PersistentClient(
            path=DB_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        
        COLLECTION_NAME = "asus_security_docs"
        
        try:
            collection = client.get_collection(COLLECTION_NAME)
            count = collection.count()
            
            return {
                "status": "healthy",
                "database_path": DB_PATH,
                "collection_name": COLLECTION_NAME,
                "document_count": count,
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "status": "collection_not_found",
                "database_path": DB_PATH,
                "collection_name": COLLECTION_NAME,
                "error": str(e),
                "timestamp": time.time()
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)