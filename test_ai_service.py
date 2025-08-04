import requests
import json
import time
from typing import List, Dict
from datetime import datetime
import os
import markdown

# 定義標準問題測試集
STANDARD_QUESTIONS = [
    "你知道甚麼資安知識？",  # 元問題測試
    "什麼是釣魚郵件？",      # 基本資安概念
    "如何保護個人密碼安全？", # 實用建議
    "企業應如何預防資料外洩？", # 組織層級問題
    "資安威脅有哪些類型？",    # 分類問題
    "沒有相關資料的問題是什麼？" # 測試無相關資料情況
]

# AI服務URL設定
URL = "http://localhost:8000/api/ask"
HEADERS = {"Content-Type": "application/json"}

def test_question(question: str) -> Dict:
    """測試單一問題並返回結果"""
    payload = {"question": question}
    try:
        response = requests.post(URL, data=json.dumps(payload), headers=HEADERS)
        response.raise_for_status()  # 檢查HTTP錯誤
        return {
            "question": question,
            "status_code": response.status_code,
            "answer": response.json().get("answer", ""),
            "sources": response.json().get("sources", []),
            "error": None
        }
    except Exception as e:
        return {
            "question": question,
            "status_code": getattr(response, 'status_code', 500),
            "answer": "",
            "sources": [],
            "error": str(e)
        }

def evaluate_answer(answer: str) -> Dict:
    """簡單評估答案的品質"""
    word_count = len(answer.split())
    sentence_count = len([s for s in answer.split("。") if s.strip()])
    
    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "is_concise": sentence_count <= 5,  # 根據系統提示的要求
    }

def run_tests() -> List[Dict]:
    """執行所有標準問題測試"""
    results = []
    
    print("開始執行標準問題測試...")
    for question in STANDARD_QUESTIONS:
        print(f"\n測試問題: {question}")
        result = test_question(question)
        
        if result["error"] is None:
            evaluation = evaluate_answer(result["answer"])
            result.update({"evaluation": evaluation})
            print(f"回答: {result['answer'][:100]}..." if len(result['answer']) > 100 else f"回答: {result['answer']}")
            print(f"字數: {evaluation['word_count']}, 句數: {evaluation['sentence_count']}, 簡潔: {'是' if evaluation['is_concise'] else '否'}")
        else:
            print(f"錯誤: {result['error']}")
        
        results.append(result)
        time.sleep(1)  # 避免請求過於頻繁
    
    return results

def generate_markdown_report(results: List[Dict]) -> str:
    """生成Markdown格式的測試報告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    md_content = f"## {now} 調校測試結果\n\n"
    md_content += "### 測試環境\n\n"
    md_content += "- 系統提示: 限制回答不超過五句話，只使用提供的資料\n"
    md_content += "- 生成參數: temperature=0.2, num_predict=200\n\n"
    
    md_content += "### 測試結果摘要\n\n"
    md_content += "| 問題 | 回答長度(字數) | 回答長度(句數) | 是否簡潔 | 是否有錯誤 |\n"
    md_content += "|------|--------------|--------------|----------|------------|\n"
    
    for result in results:
        question = result["question"]
        if result["error"] is None:
            word_count = result["evaluation"]["word_count"]
            sentence_count = result["evaluation"]["sentence_count"]
            is_concise = "是" if result["evaluation"]["is_concise"] else "否"
            has_error = "否"
        else:
            word_count = "N/A"
            sentence_count = "N/A"
            is_concise = "N/A"
            has_error = "是"
            
        md_content += f"| {question} | {word_count} | {sentence_count} | {is_concise} | {has_error} |\n"
    
    md_content += "\n### 詳細測試結果\n\n"
    
    for i, result in enumerate(results, 1):
        md_content += f"#### 測試 {i}: {result['question']}\n\n"
        if result["error"] is None:
            md_content += f"**回答:** {result['answer']}\n\n"
            md_content += f"**資料來源:** {', '.join(result['sources'])}\n\n"
            md_content += f"**評估:** 字數={result['evaluation']['word_count']}, "
            md_content += f"句數={result['evaluation']['sentence_count']}, "
            md_content += f"簡潔={'是' if result['evaluation']['is_concise'] else '否'}\n\n"
        else:
            md_content += f"**錯誤:** {result['error']}\n\n"
    
    return md_content

def update_tuning_log(md_content: str) -> None:
    """更新AI_tuning_log.md檔案"""
    log_path = "AI_tuning_log.md"
    try:
        # 讀取現有內容
        existing_content = ""
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                existing_content = f.read()
        
        # 將新內容添加到原有內容之後
        with open(log_path, "w", encoding="utf-8") as f:
            if existing_content:
                f.write(existing_content + "\n\n" + md_content)
            else:
                f.write("# AI 回答品質調校日誌 (AI Answer Tuning Log)\n\n" + md_content)
        
        print(f"\n測試結果已添加到 {log_path}")
    except Exception as e:
        print(f"更新日誌時出錯: {e}")

# 執行主程式
if __name__ == "__main__":
    print("AI回答品質測試工具 v1.0")
    print("====================================")
    
    try:
        results = run_tests()
        md_report = generate_markdown_report(results)
        update_tuning_log(md_report)
        print("\n測試完成並記錄到AI_tuning_log.md")
    except KeyboardInterrupt:
        print("\n測試被使用者中斷")
    except Exception as e:
        print(f"\n測試過程中發生錯誤: {e}")
