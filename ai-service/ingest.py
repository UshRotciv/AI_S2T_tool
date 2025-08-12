# -*- coding: utf-8 -*-
"""
改良版 ingest.py
- 句子感知的中文/中英混合切分 + 長度控制 + 重疊(overlap)
- FAQ/情境卡：正文精簡，synonyms 同時寫入 metadata（也可選擇附在正文）
- rule_ref：為每個來源檔建立 parent_id，chunk 帶編號，便於後處理分組
- 內容去重（hash），避免重覆污染索引
- 批次 upsert，提高寫入穩定性與速度
"""

import os
import re
import json
import uuid
import time
import hashlib
from datetime import datetime
from typing import List, Dict, Any

import chromadb
from chromadb.utils import embedding_functions

# ========================
# 基礎設定
# ========================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "chroma_db")
DB_VERSION_FILE = os.path.join(SCRIPT_DIR, "db_version.txt")
SCENARIOS_PATH = os.path.join(SCRIPT_DIR, "..", "app-server", "scenarios.json")
META_INFO_PATH = os.path.join(SCRIPT_DIR, "meta_info.json")

EMBED_MODEL = "mxbai-embed-large"
EMBED_URL = "http://localhost:11434"
COLLECTION_NAME = "scenarios"
BATCH_SIZE = 200   # 批次 upsert 大小
MAX_CH_LEN = 500   # 每個 chunk 最大字元（大約 300~500 漂亮）
OVERLAP = 80       # chunk 重疊字元數（保護上下文）

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
    # 先規整換行
    t = re.sub(r"[ \t]+", " ", text.strip())
    t = re.sub(r"\n{2,}", "\n", t)

    # 以中文標點與英文句點/問號/驚嘆號切分，保留標點
    parts = re.split(r"(?<=[。！？!?])|\n", t)
    parts = [p.strip() for p in parts if p and p.strip()]
    return parts

def smart_chunk(text: str, max_len: int = MAX_CH_LEN, overlap: int = OVERLAP) -> List[str]:
    """先句子切，再做長度合併與重疊"""
    sents = sentence_split(text)
    chunks = []
    buf = ""

    for s in sents:
        if not buf:
            buf = s
            continue
        if len(buf) + 1 + len(s) <= max_len:
            buf = f"{buf} {s}"
        else:
            chunks.append(buf.strip())
            buf = s
    if buf:
        chunks.append(buf.strip())

    # 做 overlap（以字元為單位，簡單但好用）
    if overlap > 0 and len(chunks) > 1:
        overlapped = []
        for i, ch in enumerate(chunks):
            if i == 0:
                overlapped.append(ch)
            else:
                prev = overlapped[-1]
                tail = prev[-overlap:] if len(prev) > overlap else prev
                merged = (tail + " " + ch).strip()
                # 盡量限制在 max_len 內
                overlapped[-1] = prev  # 保留前一個
                overlapped.append(merged[:max_len])
        chunks = overlapped

    return chunks

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
def main():
    # 版本標記（可用於灰度與回溯）
    old_version = "unknown"
    if os.path.exists(DB_VERSION_FILE):
        try:
            with open(DB_VERSION_FILE, "r", encoding="utf-8") as f:
                old_version = f.read().strip()
        except Exception:
            pass

    new_version = "3.1"
    with open(DB_VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(new_version)

    print(f"DB 版本: {old_version} -> {new_version}")

    # 建立 Chroma
    client = chromadb.PersistentClient(path=DB_PATH)
    ef = embedding_functions.OllamaEmbeddingFunction(model_name=EMBED_MODEL, url=EMBED_URL)

    # 重新建立 collection（乾淨環境）
    try:
        client.delete_collection(COLLECTION_NAME)
        print("舊有集合已刪除")
    except Exception:
        print("集合不存在，將建立新集合")

    collection = client.create_collection(
        COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )
    print(f"成功建立集合：{COLLECTION_NAME}（cosine）")

    # ========================
    # 蒐集所有文件
    # ========================
    all_docs: List[Dict[str, Any]] = []

    # 1) scenarios.json（情境卡 / FAQ）
    with open(SCENARIOS_PATH, "r", encoding="utf-8") as f:
        scenarios = json.load(f)["data"]

    for sc in scenarios:
        doc_id = sc.get("id") or stable_uuid(sc.get("title", "") + sc.get("question", ""))
        category = sc.get("category", "general")
        title = sc.get("title", "未命名")
        question = sc.get("question", "")
        answer = sc.get("answer", "未知")
        synonyms = sc.get("synonymous_questions", []) or []
        learnings = sc.get("learnings", []) or []

        # 正文盡量精簡；同義問法可只放 metadata（也保留選項可進正文）
        body = build_faq_content(
            category, title, question, answer,
            synonyms, learnings,
            put_synonyms_in_body=False
        )

        md = {
            "category": category,
            "title": title,
            "question": question,
            "answer": answer,
            "learnings": "、".join(learnings),
            "content_type": "faq_scenario",
            "has_answer": bool(answer and answer != "未知"),
            "has_learnings": bool(learnings),
            "has_synonyms": bool(synonyms),
            "synonym_count": len(synonyms),
            "synonyms": synonyms,  # 保留在 metadata，查詢擴展可直接用
            "keywords": extract_keywords(title, question, answer),
            "parent_id": doc_id,  # 供後處理分組
            "doc_type": "scenario",
            "lang": detect_lang(body),
            "version": new_version,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "source": "scenarios.json",
            "source_path": SCENARIOS_PATH,
        }

        all_docs.append({"id": doc_id, "content": body, "metadata": md})
        print(f"情境卡：{title}")

    # 2) meta_info.json（系統自我介紹/元資料）
    if os.path.exists(META_INFO_PATH):
        with open(META_INFO_PATH, "r", encoding="utf-8") as f:
            meta_items = json.load(f)
    else:
        meta_items = []

    for item in meta_items:
        doc_id = item.get("id") or stable_uuid(item.get("title", "") + item.get("question", ""))
        title = item.get("title", "未命名")
        question = item.get("question", "")
        answer = item.get("answer", "未知")
        synonyms = item.get("synonymous_questions", []) or []
        learnings = item.get("learnings", []) or []

        lines = [f"標題：{title}", f"問題：{question}", f"答案：{answer}"]
        if learnings:
            lines.append("學習要點：" + "、".join(learnings))
        # 不強制把 synonyms 放正文，避免噪音
        body = "\n".join(lines)

        md = {
            "category": "meta",
            "title": title,
            "question": question,
            "has_synonyms": bool(synonyms),
            "synonym_count": len(synonyms),
            "synonyms": synonyms,
            "doc_type": "meta",
            "lang": detect_lang(body),
            "version": new_version,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "source": "meta_info.json",
            "source_path": META_INFO_PATH,
            "parent_id": doc_id,
        }
        all_docs.append({"id": doc_id, "content": body, "metadata": md})
        print(f"元資訊：{title}")

    # 3) rule_ref 目錄
    rule_docs = load_rule_ref_documents(SCRIPT_DIR)
    all_docs.extend(rule_docs)

    print(f"總計待導入文件數：{len(all_docs)}")

    # ========================
    # 去重與批次 upsert
    # ========================
    # 依內容 hash 去重（同內容不同 id 也過濾掉）
    seen = set()
    deduped: List[Dict[str, Any]] = []
    for d in all_docs:
        h = content_hash(d["content"])
        if h in seen:
            continue
        seen.add(h)
        d["metadata"]["content_hash"] = h
        deduped.append(d)

    print(f"去重後剩餘：{len(deduped)}")

    # 批次 upsert
    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    total_ok = 0
    for batch in chunks(deduped, BATCH_SIZE):
        ids = [x["id"] for x in batch]
        docs = [x["content"] for x in batch]
        mds = [x["metadata"] for x in batch]
        # upsert 比 add 更安全（若 id 已存在會覆蓋）
        for attempt in range(3):
            try:
                collection.upsert(ids=ids, documents=docs, metadatas=mds)
                total_ok += len(batch)
                print(f"  ✓ upsert {len(batch)} 筆（累計 {total_ok}）")
                break
            except Exception as e:
                print(f"  ✗ upsert 失敗：{e}（第 {attempt+1} 次）")
                time.sleep(3)

    print("所有資料導入完成！")

if __name__ == "__main__":
    main()
