#!/usr/bin/env python3
"""
RAG系統驗證測試腳本
專門測試印表機機密文件等關鍵問題的回答準確性
"""

import requests
import json
import time
from typing import Dict, List, Any

# 測試問題集合
TEST_QUESTIONS = [
    {
        "question": "你在印表機旁發現一份標示著「ASUS Confidential」的設計圖，但附近沒有人。這時你該怎麼做？",
        "expected_keywords": ["非禮勿視", "碎紙機", "通知", "設計中心管理師", "文件所有者"],
        "category": "印表機機密文件處理"
    },
    {
        "question": "印表機發現無人拿走的機密文件該怎麼做?",
        "expected_keywords": ["非禮勿視", "碎紙機", "通知", "管理師"],
        "category": "印表機機密文件處理"
    },
    {
        "question": "看到印表機旁有機密文件但沒人在場該怎麼處理?",
        "expected_keywords": ["非禮勿視", "碎紙機", "通知"],
        "category": "印表機機密文件處理"
    },
    {
        "question": "你只是要去茶水間倒杯水，大概3分鐘就回來，有需要手動鎖定電腦嗎？",
        "expected_keywords": ["需要", "人離機鎖", "15分鐘", "自動鎖定"],
        "category": "電腦鎖定習慣"
    },
    {
        "question": "居家辦公時，家人對你正在設計的產品模型感到好奇，可以拿給他們看嗎？",
        "expected_keywords": ["絕對不行", "保密協議", "非專案相關人員"],
        "category": "居家辦公保密"
    }
]

def test_rag_system(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    測試RAG系統的回答準確性
    
    Args:
        base_url: RAG系統的API基礎URL
        
    Returns:
        測試結果統計
    """
    results = {
        "total_tests": len(TEST_QUESTIONS),
        "passed_tests": 0,
        "failed_tests": 0,
        "test_details": []
    }
    
    print("=" * 60)
    print("RAG系統驗證測試開始")
    print("=" * 60)
    
    for i, test_case in enumerate(TEST_QUESTIONS, 1):
        print(f"\n測試 {i}/{len(TEST_QUESTIONS)}: {test_case['category']}")
        print(f"問題: {test_case['question']}")
        
        # 發送請求到RAG系統
        try:
            response = requests.post(
                f"{base_url}/api/ask",
                json={"question": test_case['question']},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer', '')
                sources = data.get('sources', [])
                
                print(f"回答: {answer}")
                print(f"來源數量: {len(sources)}")
                
                # 檢查關鍵詞是否存在於回答中
                found_keywords = []
                missing_keywords = []
                
                for keyword in test_case['expected_keywords']:
                    if keyword in answer:
                        found_keywords.append(keyword)
                    else:
                        missing_keywords.append(keyword)
                
                # 計算匹配率
                match_rate = len(found_keywords) / len(test_case['expected_keywords']) * 100
                
                print(f"關鍵詞匹配率: {match_rate:.1f}%")
                print(f"找到的關鍵詞: {found_keywords}")
                if missing_keywords:
                    print(f"缺少的關鍵詞: {missing_keywords}")
                
                # 判定測試是否通過（至少匹配50%的關鍵詞）
                test_passed = match_rate >= 50.0
                
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
                    "expected_keywords": test_case['expected_keywords'],
                    "found_keywords": found_keywords,
                    "missing_keywords": missing_keywords,
                    "match_rate": match_rate,
                    "passed": test_passed,
                    "sources_count": len(sources)
                })
                
            else:
                print(f"✗ API請求失敗: {response.status_code}")
                results["failed_tests"] += 1
                results["test_details"].append({
                    "question": test_case['question'],
                    "category": test_case['category'],
                    "error": f"HTTP {response.status_code}",
                    "passed": False
                })
                
        except Exception as e:
            print(f"✗ 請求異常: {str(e)}")
            results["failed_tests"] += 1
            results["test_details"].append({
                "question": test_case['question'],
                "category": test_case['category'],
                "error": str(e),
                "passed": False
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
    
    # 特別關注印表機機密文件測試
    printer_tests = [detail for detail in results["test_details"] 
                    if "印表機" in detail["category"]]
    if printer_tests:
        printer_passed = sum(1 for test in printer_tests if test["passed"])
        print(f"\n印表機機密文件測試: {printer_passed}/{len(printer_tests)} 通過")
        
        if printer_passed == 0:
            print("⚠️  警告: 印表機機密文件問題全部失敗，需要重點修正！")
        elif printer_passed < len(printer_tests):
            print("⚠️  注意: 印表機機密文件問題部分失敗，需要進一步優化")
        else:
            print("✓ 印表機機密文件問題全部通過")
    
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
    print("RAG系統驗證測試工具")
    print("專門測試關鍵問題的回答準確性")
    
    # 執行測試
    results = test_rag_system()
    
    # 保存結果
    save_test_results(results)
    
    # 根據結果給出建議
    if results["passed_tests"] == results["total_tests"]:
        print("\n🎉 所有測試都通過了！RAG系統運行良好。")
    elif results["passed_tests"] >= results["total_tests"] * 0.8:
        print("\n👍 大部分測試通過，系統基本正常，但仍有改進空間。")
    elif results["passed_tests"] >= results["total_tests"] * 0.5:
        print("\n⚠️  約半數測試通過，系統需要進一步優化。")
    else:
        print("\n🚨 大部分測試失敗，系統需要重大修正！")
        
        # 分析主要問題
        failed_categories = {}
        for detail in results["test_details"]:
            if not detail["passed"]:
                category = detail["category"]
                failed_categories[category] = failed_categories.get(category, 0) + 1
        
        print("\n失敗最多的問題類型:")
        for category, count in sorted(failed_categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {category}: {count} 次失敗")

if __name__ == "__main__":
    main()
