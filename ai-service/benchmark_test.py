#!/usr/bin/env python
# -*- coding: utf-8 -*-

import chromadb
import ollama
import json
import os
import time
from typing import List, Dict, Any

# 標準測試集定義 - 包含代表性問題與期望答案
TEST_CASES = [
    {
        "question": "印表機發現無人拿走的機密文件該怎麼做？",
        "expected_keywords": ["銷毀", "碎紙機", "機密", "文件", "回報", "主管", "安全", "規定"],
        "category": "辦公室安全"
    },
    {
        "question": "如何安全處理機密資料？",
        "expected_keywords": ["加密", "保護", "分類", "儲存", "安全", "授權", "銷毀"],
        "category": "資料保護"
    },
    {
        "question": "發現有人使用未授權軟體怎麼辦？",
        "expected_keywords": ["回報", "IT部門", "資安", "未授權", "軟體", "風險", "通報"],
        "category": "資訊安全"
    },
    {
        "question": "電腦中毒該如何應對？",
        "expected_keywords": ["隔離", "網路", "IT支援", "通報", "掃毒", "惡意軟體", "重置"],
        "category": "資訊安全"
    },
    {
        "question": "收到可疑郵件該怎麼做？",
        "expected_keywords": ["不開啟", "不點擊", "回報", "釣魚", "垃圾郵件", "可疑", "附件"],
        "category": "郵件安全"
    }
]

def connect_chroma():
    """連接 ChromaDB 向量資料庫"""
    print("連接 ChromaDB...")
    chroma_client = chromadb.Client()
    collection = chroma_client.get_or_create_collection("security_scenarios")
    return collection

def query_ollama_model(prompt: str, context: str = None) -> str:
    """向 Ollama 模型發送查詢，並獲取回應"""
    system_message = "你是資安專家AI助手，請根據提供的內容回答問題。"
    
    if context:
        # 有提供上下文情況下的提示詞
        messages = [
            {
                "role": "system",
                "content": f"{system_message}\n\n參考內容:\n{context}"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    else:
        # 無上下文情況下的提示詞
        messages = [
            {
                "role": "system",
                "content": system_message
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    
    try:
        response = ollama.chat(
            model="llama3",
            messages=messages
        )
        return response['message']['content']
    except Exception as e:
        print(f"查詢 Ollama 時出錯: {str(e)}")
        return f"錯誤: {str(e)}"

def retrieve_from_chroma(collection, query: str, n_results: int = 3):
    """從 ChromaDB 檢索相關文檔"""
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results
    except Exception as e:
        print(f"從 ChromaDB 檢索時出錯: {str(e)}")
        return None

def evaluate_response(response: str, expected_keywords: List[str]) -> Dict[str, Any]:
    """評估 LLM 回應與預期關鍵字的匹配程度"""
    response_lower = response.lower()
    keywords_found = []
    keywords_missed = []
    
    for keyword in expected_keywords:
        if keyword.lower() in response_lower:
            keywords_found.append(keyword)
        else:
            keywords_missed.append(keyword)
    
    coverage = len(keywords_found) / len(expected_keywords) if expected_keywords else 0
    
    return {
        "keywords_found": keywords_found,
        "keywords_missed": keywords_missed,
        "coverage": coverage,
        "coverage_percentage": f"{coverage * 100:.2f}%"
    }

def run_benchmark():
    """執行基準測試並記錄結果"""
    print("開始執行 RAG 系統基準測試...")
    
    try:
        collection = connect_chroma()
    except Exception as e:
        print(f"連接 ChromaDB 失敗: {str(e)}")
        return
    
    results = []
    total_coverage = 0
    
    for i, test_case in enumerate(TEST_CASES):
        print(f"\n測試案例 {i+1}/{len(TEST_CASES)}: {test_case['question']}")
        
        # 計時開始
        start_time = time.time()
        
        # 從向量資料庫檢索
        retrieved = retrieve_from_chroma(collection, test_case["question"])
        
        if not retrieved:
            print("檢索失敗，跳過此測試案例")
            continue
        
        # 準備上下文 (最多取前3個結果)
        contexts = []
        for doc_idx in range(min(len(retrieved["documents"][0]), 3)):
            contexts.append(retrieved["documents"][0][doc_idx])
        context = "\n\n---\n\n".join(contexts)
        
        # 查詢 LLM
        response = query_ollama_model(test_case["question"], context)
        
        # 計時結束
        elapsed_time = time.time() - start_time
        
        # 評估回應
        evaluation = evaluate_response(response, test_case["expected_keywords"])
        total_coverage += evaluation["coverage"]
        
        # 記錄結果
        result = {
            "question": test_case["question"],
            "category": test_case.get("category", "未分類"),
            "response": response,
            "evaluation": evaluation,
            "response_time": f"{elapsed_time:.2f} 秒"
        }
        results.append(result)
        
        # 輸出詳細評估
        print(f"關鍵字覆蓋率: {evaluation['coverage_percentage']}")
        print(f"找到關鍵字: {', '.join(evaluation['keywords_found'])}")
        print(f"未找到關鍵字: {', '.join(evaluation['keywords_missed'])}")
        print(f"回應時間: {elapsed_time:.2f} 秒")
    
    # 計算總體評估
    avg_coverage = total_coverage / len(TEST_CASES) if TEST_CASES else 0
    print(f"\n總體評估:")
    print(f"平均關鍵字覆蓋率: {avg_coverage * 100:.2f}%")
    
    # 保存結果到 JSON 文件
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    result_file = f"benchmark_results_{timestamp}.json"
    
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "average_coverage": avg_coverage,
            "test_cases": len(TEST_CASES),
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n測試結果已保存至 {result_file}")

if __name__ == "__main__":
    run_benchmark()
