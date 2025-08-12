import shutil
import os
import stat
from fastapi import FastAPI, Depends
import ingest
import threading
import time
import re

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

# 查詢擴展詞組庫 - 針對短查詢提供更具體的相關查詢
QUERY_EXPANSIONS = {
    "作品集": [
        "準備作品集的資安注意事項",
        "對外公開作品集的規範", 
        "未採用提案是否可放進作品集",
        "作品集避免洩露公司機密",
        "個人作品集與智慧財產權",
        "員工作品集公開限制",
        "設計提案作品集規範"
    ],
    "印表機": [
        "印表機機密文件處理",
        "印表機列印機密資料",
        "印表機安全使用規範",
        "機密文件印表機操作"
    ],
    "測試軟體": [
        "免費測試軟體風險",
        "測試軟體安全性",
        "軟體測試安全規範",
        "免費軟體使用風險"
    ]
}

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

# 查詢擴展函式 - 針對短查詢生成更具體的相關查詢
def expand_query(original_query):
    """
    查詢擴展函式 - 針對短查詢生成更具體的相關查詢
    """
    # 檢查是否有預定義的擴展
    for key, values in QUERY_EXPANSIONS.items():
        if key in original_query:
            print(f"為查詢 '{original_query}' 找到擴展詞組，添加 {len(values)} 個相關查詢")
            return [original_query] + values
    
    # 檢查是否為極短查詢（少於4個中文字符）
    if len(re.sub(r'[^\u4e00-\u9fff]', '', original_query)) < 4:
        print(f"查詢 '{original_query}' 太短，但未找到預定義擴展詞組")
    
    # 如果沒有預定義擴展，返回原查詢
    return [original_query]

# 分層檢索策略
def layered_search(collection, query, n_results=7, timeout_sec=3.0):
    """
    分層檢索策略（修復版）
    第一層：Part A-D 情境卡優先（實際存在的類別）
    第二層：排除 rule_document
    第三層：全庫檢索
    """
    try:
        # 第一層：優先檢索 Part A-D 情境卡（實際存在的類別）
        print(f"第一層檢索: Part A-D 情境卡")
        scenario_categories = [
            "Part A: 辦公室基礎好習慣 (Basic Office Habits)",
            "Part B: 數位檔案的溝通與傳遞 (Digital File Communication & Transfer)",
            "Part C: 機敏資料與高風險工具 (Sensitive Data & High-Risk Tools)",
            "Part D: 智慧財產與你的權責 (Intellectual Property & Your Responsibilities)"
        ]
        layer1_results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"category": {"$in": scenario_categories}},
            include=["documents", "metadatas", "distances"]
        )
        if len(layer1_results['ids'][0]) > 0:
            print(f"第一層找到 {len(layer1_results['ids'][0])} 個情境卡")
            return layer1_results, "scenario_parts"
    except Exception as e:
        print(f"第一層檢索失敗: {e}")
    
    try:
        # 第二層：排除 rule_document，檢索其他類型
        print(f"第二層檢索: 排除 rule_document")
        layer2_results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"category": {"$ne": "rule_document"}},
            include=["documents", "metadatas", "distances"]
        )
        if len(layer2_results['ids'][0]) > 0:
            print(f"第二層找到 {len(layer2_results['ids'][0])} 個文件 (排除 rule_document)")
            return layer2_results, "filtered"
    except Exception as e:
        print(f"第二層檢索失敗: {e}")
    
    try:
        # 第三層：全庫檢索
        print(f"第三層檢索: 全庫檢索")
        layer3_results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        if len(layer3_results['ids'][0]) > 0:
            print(f"第三層找到 {len(layer3_results['ids'][0])} 個文件 (全庫)")
            return layer3_results, "full"
    except Exception as e:
        print(f"第三層檢索失敗: {e}")
    
    print(f"所有層級檢索都無結果")
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
            # 對於元問題，直接查詢元文檔
            results = collection.query(
                query_texts=[question],
                n_results=5,
                where={"category": "meta"},
                include=["documents", "metadatas", "distances"]
            )
            print(f"元問題查詢結果: 找到 {len(results['ids'][0]) if results.get('ids') and results['ids'][0] else 0} 個文件")
            search_type = "meta"
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
                # 如果所有查詢都沒有結果，退回到基本查詢
                print(f"===== 所有查詢都無結果，執行標準向量檢索 =====")
                results = collection.query(
                    query_texts=[question],
                    n_results=7,
                    include=["documents", "metadatas", "distances"]
                )
                search_type = "fallback"

        # 後處理：距離門檻過濾 + 分組去重（放寬門檻避免過度過濾）
        try:
            before_cnt = len(results['ids'][0]) if results.get('ids') and results['ids'] and results['ids'][0] else 0
            results = postprocess_results(results, distance_threshold=0.40, max_per_group=2)
            after_cnt = len(results['ids'][0]) if results.get('ids') and results['ids'] and results['ids'][0] else 0
            print(f"後處理完成: {before_cnt} -> {after_cnt} (threshold=0.40)")
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
    
    # 添加調試輸出，查看實際的 context 內容
    print(f"=== 傳送給 LLM 的 Context 內容 ===")
    print(f"Context 長度: {len(context)} 字符")
    print(f"Context 內容預覽: {context[:500]}...")
    print(f"=== Context 結束 ===")
    
    # 超嚴格的卡片內容限制策略
    system_prompt = """你是 ASUS 資安助手。

**絕對規則**：
1. 只能使用提供的卡片內容，一字不差地引用
2. 禁止添加任何卡片外的資訊、推理或擴展
3. 禁止使用你的預訓練知識
4. 如果卡片內容足夠回答問題，直接引用卡片內容
5. 保持卡片的原始結構和格式
6. 如果看到 answerLabel 或 learningsLabel，優先引用這些內容

違反以上規則將被視為錯誤回答。"""

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
    
    user_prompt = f"""**卡片內容**：
{context}

**問題**：{question}

**嚴格指令**：
1. 首先判斷問題是否與以下領域相關：資安、辦公室安全、資料保護、工作流程、企業管理、文件處理、軟體使用、設備操作、智慧財產權等職場相關主題
2. 只有完全無關的問題（如股價、天氣、娛樂、個人生活等）才回答：「根據我現有的資料，無法回答這個問題。」
3. 如果問題可能相關，優先檢查卡片內容是否包含答案
4. 只能使用上述卡片內容回答，禁止添加任何卡片外資訊
5. 如果卡片中有 answerLabel 部分，直接引用該內容作為主要答案
6. 如果卡片中有 learningsLabel 部分，可在答案後附上作為補充
7. 不得使用你的預訓練知識進行擴展或推理
8. 保持卡片的原始表達方式，不要重新詮釋

請嚴格按照上述指令執行。

注意：這個查詢使用了{search_type_info}策略。"""

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
def debug_sample(q: str, k: int = 5, scenario_only: bool = False):
    """更強大的測試端點，支援情境卡過濾與擴展查詢測試"""
    try:
        # 如果要啟用查詢擴展
        if "expand=true" in q or "expand=1" in q:
            q = q.replace("expand=true", "").replace("expand=1", "").strip()
            expanded_queries = expand_query(q)
            if len(expanded_queries) > 1:
                # 有查詢擴展
                all_results = []
                for exp_q in expanded_queries:
                    # 執行分層檢索
                    if scenario_only:
                        results, _ = layered_search(collection, exp_q, n_results=k)
                    else:
                        results = collection.query(
                            query_texts=[exp_q],
                            n_results=k,
                            include=["documents", "metadatas", "distances"]
                        )
                    
                    # 格式化結果
                    items = []
                    if results and results.get('ids') and results['ids'][0]:
                        for i, doc_id in enumerate(results['ids'][0]):
                            md = results['metadatas'][0][i] if results.get('metadatas') and results['metadatas'][0] else {}
                            items.append({
                                "id": doc_id,
                                "title": md.get('title'),
                                "category": md.get('category'),
                                "question": md.get('question'),
                                "distance": results['distances'][0][i] if results.get('distances') and results['distances'][0] else None
                            })
                    all_results.append({
                        "query": exp_q,
                        "results": items
                    })
                return {"original_query": q, "expanded": True, "queries": all_results}
            
        # 如果是一般查詢（不擴展）
        where_filter = {"category": "scenario_card"} if scenario_only else None
        
        results = collection.query(
            query_texts=[q],
            n_results=k,
            where=where_filter,
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
        return {"query": q, "scenario_only": scenario_only, "results": items}
    except Exception as e:
        return {"query": q, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)