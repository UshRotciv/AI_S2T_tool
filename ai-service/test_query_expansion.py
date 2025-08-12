#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試查詢擴展和分層檢索功能
這個腳本專門用來測試主要的短查詢，確認查詢擴展和分層檢索策略是否能提高精準度
"""

import requests
import json
import time
import sys
import os

# 測試配置
API_BASE = "http://localhost:8001"
TEST_QUERIES = [
    "作品集",
    "印表機",
    "測試軟體",
    "免費測試軟體風險",
    "員工作品集公開限制"
]

# 建立輸出目錄
OUTPUT_DIR = "test_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def check_service_health():
    """檢查服務是否在線"""
    try:
        response = requests.get(f"{API_BASE}/api/status")
        if response.status_code == 200:
            return True
        return False
    except Exception:
        return False
    
def wait_for_service(max_attempts=20, delay=5):
    """等待服務上線"""
    print(f"等待服務啟動 (最多嘗試 {max_attempts} 次)...")
    
    for attempt in range(1, max_attempts + 1):
        if check_service_health():
            print(f"✓ 服務已啟動 (嘗試 {attempt}/{max_attempts})")
            return True
        
        print(f"服務未啟動，等待中... ({attempt}/{max_attempts})")
        time.sleep(delay)
    
    print("❌ 服務啟動超時")
    return False

def test_debug_sample(query, scenario_only=False, expanded=False):
    """測試除錯樣本端點"""
    endpoint = f"{API_BASE}/api/debug/sample"
    
    # 添加擴展查詢標記
    if expanded:
        query = f"{query} expand=true"
    
    params = {
        "q": query,
        "k": 5,
        "scenario_only": scenario_only
    }
    
    try:
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"請求失敗: {response.status_code}"}
    except Exception as e:
        return {"error": f"請求異常: {str(e)}"}

def test_ask_endpoint(query):
    """測試標準問答 API 端點"""
    endpoint = f"{API_BASE}/api/ask"
    
    payload = {
        "question": query,
        "session_id": f"test_{int(time.time())}"
    }
    
    try:
        response = requests.post(endpoint, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"請求失敗: {response.status_code}"}
    except Exception as e:
        return {"error": f"請求異常: {str(e)}"}

def run_tests():
    """運行所有測試"""
    results = {}
    
    # 測試所有查詢
    for query in TEST_QUERIES:
        print(f"\n===== 測試查詢: '{query}' =====")
        
        # 1. 測試標準除錯端點
        print(f"1. 測試標準查詢...")
        standard_result = test_debug_sample(query)
        
        # 2. 測試情境卡過濾
        print(f"2. 測試情境卡過濾...")
        scenario_result = test_debug_sample(query, scenario_only=True)
        
        # 3. 測試查詢擴展
        print(f"3. 測試查詢擴展...")
        expanded_result = test_debug_sample(query, expanded=True)
        
        # 4. 測試標準問答 API
        print(f"4. 測試標準問答 API...")
        ask_result = test_ask_endpoint(query)
        
        # 儲存結果
        results[query] = {
            "standard": standard_result,
            "scenario_only": scenario_result,
            "expanded": expanded_result,
            "ask": ask_result
        }
        
        # 簡單分析結果
        if "error" not in standard_result:
            std_count = len(standard_result.get("results", []))
            print(f"  - 標準查詢找到 {std_count} 個結果")
        
        if "error" not in scenario_result:
            scenario_count = len(scenario_result.get("results", []))
            print(f"  - 情境卡過濾找到 {scenario_count} 個結果")
        
        if "error" not in expanded_result:
            if "queries" in expanded_result:
                print(f"  - 查詢擴展生成了 {len(expanded_result['queries'])} 個查詢")
                for idx, exp_query in enumerate(expanded_result["queries"]):
                    exp_count = len(exp_query.get("results", []))
                    print(f"    + 擴展查詢 {idx+1}: '{exp_query['query']}' 找到 {exp_count} 個結果")
        
        if "error" not in ask_result:
            sources_count = len(ask_result.get("sources", []))
            print(f"  - 問答 API 回答包含 {sources_count} 個參考資料")
            if ask_result.get("answer"):
                ans_len = len(ask_result["answer"])
                print(f"  - 答案長度: {ans_len} 字元")
        
        # 暫停一下，避免 API 過載
        time.sleep(1)
    
    # 保存完整結果
    with open(os.path.join(OUTPUT_DIR, "query_expansion_tests.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    return results

def main():
    """主函數"""
    # 檢查服務是否在線
    if not wait_for_service():
        print("服務未啟動，測試中止")
        sys.exit(1)
    
    # 運行測試
    print("\n開始運行測試...\n")
    results = run_tests()
    
    # 輸出測試概要
    print("\n===== 測試概要 =====")
    for query, result in results.items():
        print(f"\n查詢: '{query}'")
        
        # 檢查是否有錯誤
        has_error = False
        for test_type, test_result in result.items():
            if isinstance(test_result, dict) and "error" in test_result:
                print(f"  - {test_type}: ❌ {test_result['error']}")
                has_error = True
        
        if not has_error:
            # 分析問答 API 回答
            if "answer" in result["ask"] and result["ask"]["answer"] != "很抱歉，我無法從現有的資料中找到與您問題相關的答案。":
                print(f"  ✓ 問答 API 成功回答查詢")
                sources = result["ask"].get("sources", [])
                if sources:
                    print(f"  ✓ 找到 {len(sources)} 個參考資料")
                    for idx, source in enumerate(sources[:2]):  # 只顯示前兩個
                        print(f"    + 參考資料 {idx+1}: {source.get('title', '無標題')}")
                    if len(sources) > 2:
                        print(f"    + 以及其他 {len(sources)-2} 個資料...")
            else:
                print(f"  ❌ 問答 API 無法回答查詢")
    
    print("\n測試完成！詳細結果已保存到 test_results/query_expansion_tests.json")

if __name__ == "__main__":
    main()
