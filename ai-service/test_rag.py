#!/usr/bin/env python
# -*- coding: utf-8 -*-

# RAG系統第二次基準測試腳本
# 用於評估同義問法擴充與元數據豐富化後的檢索效能和回答品質

import json
import time
import os
from typing import List, Dict, Any
import ollama
import requests
from datetime import datetime

# 測試集（基本問題、變形問題、語意挑戰問題）
TEST_QUERIES = [
    {
        "type": "基礎問題",
        "query": "印表機發現無人拿走的機密文件該怎麼做?",
        "expected_doc": "confidential_document_handling" # 預期應該匹配到的文檔ID或關鍵詞
    },
    {
        "type": "變形問題",
        "query": "看到印表機旁有機密文件但沒人在場該怎麼處理?",
        "expected_doc": "confidential_document_handling"
    },
    {
        "type": "語意挑戰問題",
        "query": "印表機旁發現一份文件，上面寫著ASUS Confidential",
        "expected_doc": "confidential_document_handling"
    }
]

# 評估指標
RESULT_TEMPLATE = {
    "query": "",
    "query_type": "",
    "expected_doc": "",
    "retrieved_docs": [],
    "top_doc_match": False,  # 檢索成功率指標
    "llm_answer": "",
    "accuracy_score": 0,    # 1-5分評估回答準確性
    "response_time": 0      # 總體響應時間（毫秒）
}

# 測試結果保存路徑
TEST_RESULTS_PATH = "../evaluation/test_results_phase2.json"

# API 端點 (假設RAG服務運行在本地5000端口)
API_ENDPOINT = "http://localhost:5000/query"

def run_test_query(query: str) -> Dict[str, Any]:
    """
    向RAG API發送查詢，獲取回應
    """
    start_time = time.time()
    try:
        response = requests.post(
            API_ENDPOINT,
            json={"query": query, "stream": False},
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        end_time = time.time()
        result["response_time"] = (end_time - start_time) * 1000  # 毫秒
        return result
    except Exception as e:
        print(f"API請求失敗: {e}")
        # 如果API無法使用，改用直接調用Ollama模型
        return fallback_ollama_query(query, start_time)

def fallback_ollama_query(query: str, start_time: float) -> Dict[str, Any]:
    """
    如果API無法使用，退回到直接使用Ollama的備用方案
    """
    try:
        response = ollama.chat(
            model="qwen2",
            messages=[
                {"role": "system", "content": "你是資安專家，請盡可能準確回答資訊安全問題。"},
                {"role": "user", "content": query}
            ]
        )
        end_time = time.time()
        return {
            "answer": response["message"]["content"],
            "sources": [],  # 無來源（純LLM回答）
            "response_time": (end_time - start_time) * 1000
        }
    except Exception as e:
        print(f"Ollama調用失敗: {e}")
        return {
            "answer": "測試失敗: 無法連接到API或Ollama服務",
            "sources": [],
            "response_time": 0
        }

def check_retrieval_success(retrieved_sources: List[Dict], expected_doc: str) -> bool:
    """
    檢查是否成功檢索到預期文檔
    """
    if not retrieved_sources:
        return False
    
    # 檢查前三個檢索結果中是否包含預期文檔
    # 這裡需要根據實際RAG系統的source格式調整判斷邏輯
    top_sources = retrieved_sources[:3] if len(retrieved_sources) >= 3 else retrieved_sources
    
    for source in top_sources:
        # 根據實際文檔ID或內容特徵進行匹配判斷
        source_id = source.get("id", "")
        source_text = source.get("text", "")
        if (expected_doc in source_id) or (expected_doc in source_text.lower()):
            return True
    
    return False

def evaluate_answer_accuracy(answer: str, query_type: str) -> int:
    """
    評估回答準確性（1-5分）
    未來可以改用LLM自動評分或人工評分
    """
    # 這裡先返回預設值，後續可以由人工評分或使用LLM評分
    return 0  # 0代表待評分

def save_test_results(results: List[Dict]):
    """
    保存測試結果到JSON文件
    """
    # 確保目錄存在
    os.makedirs(os.path.dirname(TEST_RESULTS_PATH), exist_ok=True)
    
    # 加上時間戳記
    output = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "phase": "第二次測試（同義問法與元數據）",
        "results": results
    }
    
    with open(TEST_RESULTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"測試結果已保存至 {TEST_RESULTS_PATH}")

def print_test_summary(results: List[Dict]):
    """
    打印測試結果摘要
    """
    retrieval_success = sum(1 for r in results if r["top_doc_match"])
    avg_response_time = sum(r["response_time"] for r in results) / len(results)
    
    print("\n========== 測試摘要 ==========")
    print(f"總測試查詢數: {len(results)}")
    print(f"檢索成功率: {retrieval_success}/{len(results)} ({retrieval_success/len(results)*100:.1f}%)")
    print(f"平均響應時間: {avg_response_time:.2f} ms")
    print("回答準確性評分待人工評估")
    print("=============================\n")

def run_all_tests():
    """
    執行所有測試查詢並評估結果
    """
    print("開始RAG系統第二次基準測試...\n")
    
    results = []
    for test_case in TEST_QUERIES:
        query = test_case["query"]
        query_type = test_case["type"]
        expected_doc = test_case["expected_doc"]
        
        print(f"測試 [{query_type}]: {query}")
        api_result = run_test_query(query)
        
        # 構建測試結果
        result = dict(RESULT_TEMPLATE)
        result["query"] = query
        result["query_type"] = query_type
        result["expected_doc"] = expected_doc
        result["llm_answer"] = api_result.get("answer", "無回答")
        result["response_time"] = api_result.get("response_time", 0)
        result["retrieved_docs"] = api_result.get("sources", [])
        result["top_doc_match"] = check_retrieval_success(
            api_result.get("sources", []), expected_doc
        )
        
        results.append(result)
        print(f"  檢索成功: {result['top_doc_match']}")
        print(f"  回答: {result['llm_answer'][:100]}..." if len(result['llm_answer']) > 100 else f"  回答: {result['llm_answer']}")
        print(f"  響應時間: {result['response_time']:.2f} ms\n")
    
    # 保存並顯示結果
    save_test_results(results)
    print_test_summary(results)

if __name__ == "__main__":
    run_all_tests()
