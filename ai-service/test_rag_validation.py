#!/usr/bin/env python3
import os
import requests
import json
import time

BASE_URL = "http://localhost:8001"

# Test cases
# Each tuple: (test_name, query, expected_to_find_sources, minimum_source_count)
TEST_CASES = [
    ("title_query", "Office Cybersecurity Basics", True, 1),
    ("question_label_query", "What are the best practices for creating strong passwords?", True, 1),
    ("nlp_query", "How can I protect my computer from malware?", True, 1),
    ("ood_query", "What is the stock price of Tesla?", False, 0)
]

def run_test(test_name, query, expected_to_find_sources, min_sources):
    """Runs a single test case against the /api/ask endpoint."""
    print(f"--- Running test: {test_name} ---")
    print(f"Query: {query}")

    try:
        response = requests.post(
            f"{BASE_URL}/api/ask",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"question": query, "session_id": f"test_{test_name}"})
        )
        response.raise_for_status()
        data = response.json()

        sources = data.get("sources", [])
        answer = data.get("answer", "")
        
        print(f"Answer received: {answer[:100]}...")
        print(f"Sources found: {len(sources)}")

        if expected_to_find_sources:
            if len(sources) >= min_sources:
                print(f"PASS: Found {len(sources)} sources, expected at least {min_sources}.")
                # Further check if the sources are scenarios
                scenario_sources = [s for s in sources if s.get("id", "").startswith("scenario-")]
                if len(scenario_sources) > 0:
                    print(f"PASS: Found {len(scenario_sources)} scenario-based sources.")
                    return True
                else:
                    print("FAIL: No scenario-based sources found in the results.")
                    return False
            else:
                print(f"FAIL: Found {len(sources)} sources, but expected at least {min_sources}.")
                return False
        else: # Out-of-domain
            if not sources:
                print("PASS: Correctly found no sources for out-of-domain query.")
                return True
            else:
                print(f"FAIL: Found {len(sources)} sources for an out-of-domain query.")
                return False

    except requests.exceptions.RequestException as e:
        print(f"FAIL: API request failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"FAIL: Failed to decode JSON response: {e}")
        return False
    except Exception as e:
        print(f"FAIL: An unexpected error occurred: {e}")
        return False

def main():
    """Main function to run all tests."""
    print("Starting RAG validation tests...")
    print(f"Waiting for service at {BASE_URL}...")
    time.sleep(3) # Wait for service to initialize
    
    # Check if service is up
    try:
        status_res = requests.get(f"{BASE_URL}/api/status")
        status_res.raise_for_status()
        print(f"API Status: {status_res.json().get('status')}")
    except requests.exceptions.RequestException as e:
        print(f"CRITICAL: AI service is not running at {BASE_URL}. Aborting tests. Error: {e}")
        return

    test_results = {}
    for name, query, expected, min_count in TEST_CASES:
        test_results[name] = run_test(name, query, expected, min_count)
        print("-" * 20)

    print("\n--- Test Summary ---")
    passed_count = sum(1 for result in test_results.values() if result)
    total_count = len(test_results)
    for name, result in test_results.items():
        print(f"{name}: {'PASS' if result else 'FAIL'}")
    
    print(f"\n{passed_count} / {total_count} tests passed.")
    
    if passed_count != total_count:
        exit(1)

if __name__ == "__main__":
    main()

"""
RAG系統完整性驗證腳本

此腳本會自動讀取 scenarios.json 和 meta_info.json 中的所有情境，
並逐一測試RAG系統是否能針對每個問題，正確地從向量資料庫中檢索到對應的來源文件。
這能有效驗證所有情境卡片是否都已成功導入系統。
"""

import requests
import json
import time
import os
from typing import Dict, List, Any

# 資料來源檔案
SCENARIOS_FILE = "../app-server/scenarios.json"
META_INFO_FILE = "meta_info.json"

def load_test_questions_from_sources() -> List[Dict[str, Any]]:
    """從源文件動態加載所有測試問題"""
    test_cases = []
    sources = [SCENARIOS_FILE, META_INFO_FILE]

    for file_path in sources:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 處理 scenarios.json 的特殊結構
            if "data" in data and isinstance(data["data"], list):
                items = data["data"]
            elif isinstance(data, list):
                items = data
            else:
                print(f"警告：無法解析 {file_path} 的結構")
                continue

            for item in items:
                if "question" in item and "id" in item:
                    test_cases.append({
                        "question": item["question"],
                        "expected_id": item["id"],
                        "category": item.get("title", "N/A"),
                        "source_file": file_path
                    })
        except FileNotFoundError:
            print(f"錯誤：找不到來源檔案 {file_path}")
        except Exception as e:
            print(f"錯誤：讀取或解析 {file_path} 失敗: {e}")

    if not test_cases:
        print("\n🚨 警告：沒有成功加載任何測試問題！")
        print("請確認以下檔案是否存在且格式正確：")
        print(f"- {os.path.abspath(SCENARIOS_FILE)}")
        print(f"- {os.path.abspath(META_INFO_FILE)}")

    return test_cases

def test_rag_system(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    對RAG系統進行完整性測試

    Args:
        base_url: RAG系統的API基礎URL

    Returns:
        測試結果統計
    """
    test_questions = load_test_questions_from_sources()
    
    if not test_questions:
        return {"error": "無法加載測試問題，測試中止。"}

    results = {
        "total_tests": len(test_questions),
        "passed_tests": 0,
        "failed_tests": 0,
        "test_details": []
    }

    print("=" * 60)
    print(f"RAG 系統完整性驗證開始 (共 {len(test_questions)} 個情境)")
    print("=" * 60)

    for i, test_case in enumerate(test_questions, 1):
        print(f"\n測試 {i}/{len(test_questions)}: {test_case['category']}")
        print(f"問題: {test_case['question']}")
        
        # 發送請求到RAG系統
        try:
            response = requests.post(
                f"{base_url}/api/ask",
                json={"question": test_case['question']},
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer', '')
                sources = data.get('sources', [])
                
                print(f"回答: {answer}")
                print(f"來源數量: {len(sources)}")
                
                # 驗證返回的來源是否包含預期的ID
                retrieved_ids = [source.get('metadata', {}).get('id') for source in sources]
                test_passed = test_case['expected_id'] in retrieved_ids

                print(f"預期來源ID: {test_case['expected_id']}")
                print(f"檢索到的來源ID: {retrieved_ids}")
                
                if test_passed:
                    results["passed_tests"] += 1
                    print("✓ 測試通過")
                else:
                    results["failed_tests"] += 1
                    print("✗ 測試失敗")
                
                # 記錄詳細結果
                results["test_details"].append({
                    "question": test_case['question'],
                    "category": test_case['category'],
                    "answer": answer,
                    "expected_id": test_case['expected_id'],
                    "retrieved_ids": retrieved_ids,
                    "passed": test_passed,
                    "sources_count": len(sources),
                    "source_file": test_case['source_file']
                })
                
            else:
                print(f"✗ API請求失敗: {response.status_code}")
                results["failed_tests"] += 1
                results["test_details"].append({
                    "question": test_case['question'],
                    "category": test_case['category'],
                    "error": f"API請求失敗: HTTP {response.status_code}",
                    "passed": False,
                    "source_file": test_case['source_file'],
                    "expected_id": test_case['expected_id'],
                    "retrieved_ids": []
                })   
                
        except Exception as e:
            print(f"✗ 請求異常: {str(e)}")
            results["failed_tests"] += 1
            results["test_details"].append({
                "question": test_case['question'],
                "category": test_case['category'],
                "error": str(e),
                "passed": False,
                "source_file": test_case['source_file'],
                "expected_id": test_case['expected_id'],
                "retrieved_ids": []
            })
        
        print("-" * 40)
        time.sleep(1)  # 避免請求過於頻繁
    
    # 輸出總結
    print("\n" + "=" * 60)
    print("測試結果總結")
    print("=" * 60)
    print(f"總測試數: {results['total_tests']}")
    print(f"通過測試: {results['passed_tests']}")
    print(f"失敗測試: {results['failed_tests']}")
    print(f"通過率: {results['passed_tests']/results['total_tests']*100:.1f}%")
    
    # 分析失敗的案例
    failed_cases = [detail for detail in results["test_details"] if not detail["passed"]]
    if failed_cases:
        print("\n--- 失敗案例分析 ---")
        for case in failed_cases:
            print(f"  - [失敗] {case['category']} (來自 {os.path.basename(case['source_file'])})")
            print(f"    問題: {case['question'][:50]}...")
            print(f"    預期ID: {case['expected_id']}")
            print(f"    實際檢索ID: {case.get('retrieved_ids', 'N/A')}")
    
    return results

def save_test_results(results: Dict[str, Any], filename: str = "test_results_validation.json"):
    """保存測試結果到文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n測試結果已保存到: {filename}")
    except Exception as e:
        print(f"保存測試結果失敗: {str(e)}")

def main():
    """主函數"""
    print("RAG 系統完整性驗證工具")
    print("本工具將自動驗證所有情境卡片是否都已成功載入系統。")
    
    # 執行測試
    results = test_rag_system()

    if "error" in results:
        print(f"\n測試無法執行: {results['error']}")
        return

    # 保存測試結果
    save_test_results(results)

if __name__ == "__main__":
    main()
    
    # 根據結果給出建議
    if results["passed_tests"] == results["total_tests"]:
        print("\n🎉 所有測試都通過了！RAG系統運行良好。")
    elif results["passed_tests"] >= results["total_tests"] * 0.8:
        print("\n👍 大部分測試通過，系統基本正常，但仍有改進空間。")
    elif results["passed_tests"] >= results["total_tests"] * 0.5:
        print("\n⚠️  約半數測試通過，系統需要進一步優化。")
    else:
        print("\n🚨 大部分測試失敗，系統需要重大修正！")
        
        print("\n🚨 系統導入不完整，請檢查 `ingest.py` 的日誌或資料庫內容。")

if __name__ == "__main__":
    main()
