# -*- coding: utf-8 -*-
"""
ingest.py (v3) — 穩定增量版
- 支援資料源：SQLite / JSON（SCENARIOS_SOURCE）
- 支援嵌入後端：sentence-transformers / Ollama（EMBEDDING_BACKEND）
- 預設增量：依 scenario_id 先刪後 upsert；RESET_COLLECTION=true 才全量重建
- 統一 chunk 與 id 命名：doc_{scenario_id}_{chunk_index}
- metadata 扁平化（list 轉字串+count），便於 where 與相容性
- 關閉 Chroma 遙測：CHROMA_TELEMETRY_ENABLED=false
"""
import os, re, json, time, sqlite3, hashlib
from datetime import datetime
from typing import List, Dict, Any, Iterable

import chromadb
from chromadb.utils import embedding_functions

# ---- 環境 ----
os.environ.setdefault("CHROMA_TELEMETRY_ENABLED", "false")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

CHROMA_DIR      = os.getenv("CHROMA_DIR", os.path.join(SCRIPT_DIR, "chroma_db"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "scenarios")

SCENARIOS_SOURCE = os.getenv("SCENARIOS_SOURCE", "sqlite").lower()  # sqlite|json
SCENARIOS_JSON   = os.path.join(ROOT_DIR, "app-server", "scenarios.json")
SQLITE_DB_PATH   = os.getenv("SQLITE_DB_PATH", os.path.join(ROOT_DIR, "app-server", "sqlite", "db.sqlite"))

EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "sentence").lower()  # sentence|ollama
SENTENCE_MODEL    = os.getenv("SENTENCE_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
OLLAMA_MODEL      = os.getenv("OLLAMA_MODEL", "mxbai-embed-large")
OLLAMA_URL        = os.getenv("OLLAMA_URL", "http://localhost:11434")

RESET_COLLECTION = os.getenv("RESET_COLLECTION", "false").lower() == "true"
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "200"))
MAX_CH_LEN = int(os.getenv("MAX_CH_LEN", "500"))
OVERLAP    = int(os.getenv("OVERLAP", "80"))

# ========================
# 基礎設定
# ========================
# ========================
# 小工具
# ========================
def stable_uuid(text: str) -> str:
    """根據文字產生穩定 UUID（避免重覆導致 id 衝突）"""
    return str(uuid.UUID(hashlib.md5(text.encode("utf-8")).hexdigest()))

def content_hash(text: str) -> str:
    return hashlib.sha1(text.strip().encode("utf-8")).hexdigest()

def detect_lang(text: str) -> str:
    """非常簡單的語言偵測（夠用即可）"""
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"
    return "en"

def extract_keywords(title: str, question: str, answer: str) -> List[str]:
    """關鍵詞抽取：保留你原本邏輯並做些微限定"""
    combined_text = f"{title} {question} {answer}"
    chinese_words = re.findall(r'[\u4e00-\u9fff]{2,4}', combined_text)
    english_words = re.findall(r'[A-Za-z]{3,}', combined_text)
    important_terms = ['Teams', 'Email', 'AI', 'BYOD', '機密', '資安', '密碼', '檔案', '印表機', '白板', '拍照', '會議']
    kw = [t for t in important_terms if t in combined_text]
    kw = list(dict.fromkeys(kw + chinese_words[:5] + english_words[:3]))  # 去重保序
    return kw[:10]

def sentence_split(text: str) -> List[str]:
    """中文/中英混合的簡易句子切分"""
    t = re.sub(r"[ \t]+", " ", (text or "").strip())
    t = re.sub(r"\n{2,}", "\n", t)
    parts = re.split(r"(?<=[\u3002\uff01\uff1f!?])|\n", t)
    return [p.strip() for p in parts if p and p.strip()]

def smart_chunk(text: str, max_len: int = MAX_CH_LEN, overlap: int = OVERLAP) -> List[str]:
    """先句子切，再做長度合併與重疊"""
    sents = sentence_split(text)
    chunks, buf = [], ""
    for s in sents:
        if not buf: buf = s; continue
        if len(buf) + 1 + len(s) <= max_len: buf = f"{buf} {s}"
        else: chunks.append(buf.strip()); buf = s
    if buf: chunks.append(buf.strip())
    if overlap > 0 and len(chunks) > 1:
        overlapped = []
        for i, ch in enumerate(chunks):
            if i == 0: overlapped.append(ch); continue
            prev = overlapped[-1]; tail = prev[-overlap:] if len(prev) > overlap else prev
            merged = (tail + " " + ch).strip()[:max_len]
            overlapped.append(merged)
        chunks = overlapped
    return chunks

def chunks_iter(lst: List[Any], n: int) -> Iterable[List[Any]]:
    for i in range(0, len(lst), n): yield lst[i:i+n]

def now_iso() -> str: 
    return datetime.utcnow().isoformat() + "Z"

def build_faq_content(category: str, title: str, question: str, answer: str,
                      synonyms: List[str], learnings: List[str],
                      put_synonyms_in_body: bool = False) -> str:
    """FAQ/情境卡正文：精簡 + 可選擇是否把同義問法放到正文"""
    lines = [
        f"類別：{category}",
        f"標題：{title}",
        f"問題：{question}",
        f"答案：{answer}"
    ]
    if learnings:
        lines.append("學習重點：" + "、".join(learnings))
    if put_synonyms_in_body and synonyms:
        lines.append("相似問法：" + "；".join(synonyms))
    return "\n".join(lines)

def load_rule_ref_documents(base_dir: str) -> List[Dict[str, Any]]:
    """從 rule_ref 讀取文件，chunk 化並帶 parent_id/編號"""
    rule_ref_path = os.path.join(base_dir, "..", "rule_ref")
    docs: List[Dict[str, Any]] = []

    if not os.path.exists(rule_ref_path):
        print(f"警告: 'rule_ref' 目錄不存在於 {rule_ref_path}")
        return docs

    print(f"正在從 {rule_ref_path} 載入 rule_ref 文檔...")
    for root, _, files in os.walk(rule_ref_path):
        for fn in files:
            if not fn.lower().endswith((".txt", ".md")):
                continue
            fpath = os.path.join(root, fn)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    raw = f.read()
            except Exception as e:
                print(f"讀取失敗 {fpath}: {e}")
                continue

            # 嘗試抓「**題目 n: ...**」格式
            qa_pairs = re.findall(r"\*\*題目 \d+: (.*?)\*\*(.*?)(?=\*\*題目 \d+:|\Z)", raw, re.DOTALL)
            if qa_pairs:
                parent_id = f"rule-{os.path.splitext(fn)[0]}"
                for i, (q, a) in enumerate(qa_pairs, start=1):
                    title = q.strip()
                    ans = "\n".join([line.strip() for line in a.splitlines() if line.strip()])
                    body = f"標題：{title}\n問題：{title}\n答案：{ans}\n來源：{fn}"
                    docs.append({
                        "id": f"{parent_id}-qa-{i}",
                        "content": body,
                        "metadata": {
                            "category": "rule_document",
                            "title": title,
                            "question": title,
                            "parent_id": parent_id,
                            "doc_type": "rule_ref_qa",
                            "source": fn,
                            "source_path": fpath,
                            "is_chunk": False,
                            "lang": detect_lang(body),
                        }
                    })
                print(f"  - 解析到 {len(qa_pairs)} 個 QA：{fn}")
            else:
                # 一般長文 -> 聰明切片
                chunks = smart_chunk(raw, MAX_CH_LEN, OVERLAP)
                parent_id = f"rule-{os.path.splitext(fn)[0]}"
                title = os.path.splitext(fn)[0].replace("_", " ")
                for i, ch in enumerate(chunks, start=1):
                    body = f"標題：{title}\n來源：{fn}\n內容片段 {i}/{len(chunks)}：\n{ch}"
                    docs.append({
                        "id": f"{parent_id}-chunk-{i}",
                        "content": body,
                        "metadata": {
                            "category": "rule_document",
                            "title": title,
                            "parent_id": parent_id,
                            "doc_type": "rule_ref_chunk",
                            "source": fn,
                            "source_path": fpath,
                            "is_chunk": True,
                            "chunk_number": i,
                            "total_chunks": len(chunks),
                            "lang": detect_lang(body),
                        }
                    })
                print(f"  - 切為 {len(chunks)} 片段：{fn}")

    return docs

# ========================
# 主流程
# ========================
def get_collection(client, embedding_fn):
    """取得或建立 collection，支援增量更新"""
    try:
        collection = client.get_collection(COLLECTION_NAME, embedding_function=embedding_fn)
        print(f"[*] 使用現有集合：{COLLECTION_NAME}")
        return collection
    except Exception:
        print(f"[*] 建立新集合：{COLLECTION_NAME}")
        return client.create_collection(
            COLLECTION_NAME,
            embedding_function=embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

def delete_scenario_docs(collection, scenario_id: str):
    """刪除特定 scenario 的所有文檔"""
    try:
        # 查詢該 scenario 的所有文檔
        results = collection.get(where={"scenario_id": scenario_id})
        if results["ids"]:
            collection.delete(ids=results["ids"])
            print(f"  ✓ 已刪除 scenario {scenario_id} 的 {len(results['ids'])} 個文檔")
        return len(results["ids"])
    except Exception as e:
        print(f"  ✗ 刪除 scenario {scenario_id} 失敗：{e}")
        return 0

def upsert_docs_batch(collection, docs: List[Dict], max_retries: int = 3):
    """批次 upsert 文檔，帶重試機制"""
    total_ok = 0
    for batch in chunks_iter(docs, BATCH_SIZE):
        for attempt in range(max_retries):
            try:
                ids = [d["id"] for d in batch]
                documents = [d["content"] for d in batch]
                metadatas = [d["metadata"] for d in batch]
                
                collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
                total_ok += len(batch)
                print(f"  ✓ upsert {len(batch)} 筆（累計 {total_ok}）")
                break
            except Exception as e:
                print(f"  ✗ upsert 失敗：{e}（第 {attempt+1} 次）")
                if attempt < max_retries - 1:
                    time.sleep(3)
    return total_ok

def main():
    print(f"[*] ingest.py v3 - 最佳 RAG 架構")
    print(f"[*] 資料源：{SCENARIOS_SOURCE.upper()}")
    print(f"[*] Embedding：{EMBEDDING_BACKEND.upper()}")
    print(f"[*] 重建模式：{'ON' if RESET_COLLECTION else 'OFF（增量）'}")

    # 建立 Chroma 客戶端與 embedding function
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    embedding_fn = build_embedding_fn()

    # 處理 collection
    if RESET_COLLECTION:
        try:
            client.delete_collection(COLLECTION_NAME)
            print("[*] 已刪除舊集合（全量重建模式）")
        except Exception:
            pass
    
    collection = get_collection(client, embedding_fn)

    # ========================
    # 載入與處理資料
    # ========================
    all_docs: List[Dict[str, Any]] = []

    # 1) 載入 scenarios
    print("[*] 載入 scenarios...")
    scenarios = load_scenarios()
    print(f"[*] 載入 {len(scenarios)} 個 scenarios")

    # 2) 轉換為統一文檔格式（含 chunk 化）
    scenario_docs = build_docs_from_scenarios(scenarios)
    all_docs.extend(scenario_docs)
    print(f"[*] 產生 {len(scenario_docs)} 個 scenario 文檔")

    # 3) 載入 rule_ref 文檔
    rule_ref_dir = os.path.join(SCRIPT_DIR, "rule_ref")
    rule_docs = load_rule_ref_documents(rule_ref_dir)
    all_docs.extend(rule_docs)
    print(f"[*] 產生 {len(rule_docs)} 個 rule_ref 文檔")

    print(f"[*] 總計文檔數：{len(all_docs)}")

    # ========================
    # 增量更新處理
    # ========================
    if not RESET_COLLECTION:
        # 增量模式：按 scenario_id 分組處理
        scenario_groups = {}
        for doc in scenario_docs:
            sid = doc["metadata"].get("scenario_id")
            if sid:
                if sid not in scenario_groups:
                    scenario_groups[sid] = []
                scenario_groups[sid].append(doc)
        
        print(f"[*] 增量更新 {len(scenario_groups)} 個 scenarios...")
        for scenario_id, docs in scenario_groups.items():
            delete_scenario_docs(collection, scenario_id)
            upsert_docs_batch(collection, docs)
        
        # rule_ref 文檔直接 upsert（假設不常變動）
        if rule_docs:
            print(f"[*] 更新 rule_ref 文檔...")
            upsert_docs_batch(collection, rule_docs)
    else:
        # 全量模式：直接批次 upsert 所有文檔
        print(f"[*] 全量導入所有文檔...")
        upsert_docs_batch(collection, all_docs)

    # ========================
    # 統計與驗證
    # ========================
    try:
        total_count = collection.count()
        print(f"[✓] 導入完成！資料庫總文檔數：{total_count}")
        
        # 簡單驗證
        sample = collection.peek(limit=3)
        if sample["ids"]:
            print(f"[✓] 樣本文檔：{sample['ids'][:3]}")
    except Exception as e:
        print(f"[!] 統計失敗：{e}")

    print("[✓] ingest.py 執行完成！")

# ---- 缺失的函數 ----
def build_embedding_fn():
    """根據環境變數建立 embedding function"""
    if EMBEDDING_BACKEND == "ollama":
        try:
            print(f"[*] 使用 Ollama embedding: {OLLAMA_MODEL} @ {OLLAMA_URL}")
            return embedding_functions.OllamaEmbeddingFunction(
                model_name=OLLAMA_MODEL, url=OLLAMA_URL
            )
        except Exception as e:
            print(f"[!] Ollama 初始化失敗: {e}，回退到 sentence-transformers")
    
    print(f"[*] 使用 SentenceTransformer embedding: {SENTENCE_MODEL}")
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=SENTENCE_MODEL
    )

def load_scenarios() -> List[Dict[str, Any]]:
    """根據環境變數載入 scenarios"""
    if SCENARIOS_SOURCE == "sqlite":
        return load_scenarios_from_sqlite(SQLITE_DB_PATH)
    else:
        return load_scenarios_from_json(SCENARIOS_JSON)

def load_scenarios_from_json(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    data = raw["data"] if isinstance(raw, dict) and "data" in raw else raw
    out = []
    for s in data or []:
        out.append({
            "id": s.get("id") or s.get("uuid"),
            "title": s.get("title") or "未命名",
            "question": s.get("question", ""),
            "answer": s.get("answer", ""),
            "body": s.get("body") or s.get("answer") or "",
            "category": s.get("category", "general"),
            "synonymous_questions": s.get("synonymous_questions", []),
            "learnings": s.get("learnings", []),
            "group_id": s.get("group_id")
        })
    return out

def load_scenarios_from_sqlite(db_path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(db_path):
        print(f"[!] 找不到 SQLite：{db_path}；回退讀 JSON：{SCENARIOS_JSON}")
        return load_scenarios_from_json(SCENARIOS_JSON)
    
    try:
        conn = sqlite3.connect(db_path); conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # 先檢查資料表結構
        cur.execute("PRAGMA table_info(scenarios)")
        columns = [row[1] for row in cur.fetchall()]
        print(f"[*] SQLite 欄位：{columns}")
        
        # 根據實際欄位構建查詢
        base_fields = ["id", "title", "question", "answer", "category"]
        optional_fields = ["synonymous_questions", "learnings", "group_id", "updated_at"]
        
        select_fields = []
        for field in base_fields + optional_fields:
            if field in columns:
                select_fields.append(field)
        
        query = f"SELECT {', '.join(select_fields)} FROM scenarios ORDER BY id"
        cur.execute(query)
        rows = cur.fetchall(); conn.close()
        
        out = []
        for r in rows:
            # 安全地處理 JSON 欄位
            synonyms = []
            learnings = []
            
            if "synonymous_questions" in columns and r["synonymous_questions"]:
                try:
                    synonyms = json.loads(r["synonymous_questions"])
                except:
                    synonyms = []
            
            if "learnings" in columns and r["learnings"]:
                try:
                    learnings = json.loads(r["learnings"])
                except:
                    learnings = []
            
            out.append({
                "id": r["id"], 
                "title": r["title"] if "title" in columns else "未命名",
                "question": r["question"] if "question" in columns else "",
                "answer": r["answer"] if "answer" in columns else "",
                "body": r["answer"] if "answer" in columns else "",
                "category": r["category"] if "category" in columns else "general",
                "synonymous_questions": synonyms,
                "learnings": learnings,
                "group_id": r["group_id"] if "group_id" in columns else None
            })
        
        print(f"[*] 從 SQLite 載入 {len(out)} 個 scenarios")
        return out
        
    except Exception as e:
        print(f"[!] SQLite 讀取失敗：{e}；回退讀 JSON")
        return load_scenarios_from_json(SCENARIOS_JSON)

def build_docs_from_scenarios(scenarios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """將 scenarios 轉為統一 chunk 格式的文檔"""
    docs = []
    for sc in scenarios:
        scenario_id = str(sc.get("id", ""))
        if not scenario_id: continue
        
        title = sc.get("title", "未命名")
        question = sc.get("question", "")
        answer = sc.get("answer", "")
        body = sc.get("body", "") or answer
        category = sc.get("category", "general")
        synonyms = sc.get("synonymous_questions", []) or []
        learnings = sc.get("learnings", []) or []
        
        # 建立完整內容用於 chunk 化
        full_content = f"標題：{title}\n問題：{question}\n答案：{answer}"
        if learnings:
            full_content += "\n學習要點：" + "、".join(learnings)
        if synonyms:
            full_content += "\n同義問法：" + "、".join(synonyms)
        
        # 統一 chunk 化處理
        chunks = smart_chunk(full_content, MAX_CH_LEN, OVERLAP)
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"doc_{scenario_id}_{i:04d}"
            
            # 扁平化 metadata
            metadata = {
                "scenario_id": scenario_id,
                "doc_type": "scenario",
                "category": category,
                "title": title,
                "question": question,
                "answer": answer,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "is_chunk": len(chunks) > 1,
                "synonyms": "、".join(synonyms),
                "synonyms_count": len(synonyms),
                "learnings": "、".join(learnings),
                "learnings_count": len(learnings),
                "lang": detect_lang(chunk),
                "source": SCENARIOS_SOURCE,
                "created_at": now_iso(),
                "content_hash": content_hash(chunk)
            }
            
            docs.append({
                "id": chunk_id,
                "content": chunk,
                "metadata": metadata
            })
    
    return docs

if __name__ == "__main__":
    main()
