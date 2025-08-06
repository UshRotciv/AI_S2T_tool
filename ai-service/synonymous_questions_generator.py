#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import ollama
import time
import os
from typing import List, Dict, Any

# 同義問法生成提示詞模板
SYNONYMOUS_QUESTIONS_PROMPT = """
作為資安教育專家，請為以下問題生成 5 個不同表達方式的同義問法。
這些問法應該保持原始問題的核心意思和專業性，但使用不同的措辭、語序或表達方式。

原始問題: {question}

請直接列出 5 個同義問法，每行一個，不要有編號或其他標記。確保每個問法都是一個完整的問句，並以問號結尾。
"""

# 原始問題來源文件（含完整路徑）
SOURCE_FILES = [
    "../app-server/scenarios.json",
    "meta_info.json"
]

def load_source_data(file_path: str) -> List[Dict]:
    """從源文件加載數據"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 處理 scenarios.json 的特殊結構
        if "data" in data and isinstance(data["data"], list):
            return data["data"]
        elif isinstance(data, list):
            return data
        else:
            print(f"警告：{file_path} 結構不符合預期。")
            return []
    except Exception as e:
        print(f"無法加載源文件 {file_path}: {e}")
        return []

def generate_synonymous_questions(question: str, num_questions: int = 5) -> list:
    """單題同義問法生成，回傳同義問法list[str]"""
    import concurrent.futures
    prompt = f"請為以下問題生成 {num_questions} 個不同表達方式的同義問法，每個問法請獨立換行，不要重複：\n問題：{question}"
    def call_ollama():
        return ollama.chat(
            model="qwen2",
            messages=[
                {"role": "system", "content": "你是資安教育專家，專門生成同義問法。"},
                {"role": "user", "content": prompt}
            ]
        )
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(call_ollama)
            response = future.result(timeout=60)
        print(f"[DEBUG] Ollama 回應內容: {response}")
        if not response or not isinstance(response, dict):
            print(f"[錯誤] Ollama 回傳格式異常，response = {response}")
            return []
        if "message" not in response or "content" not in response["message"]:
            print(f"[錯誤] Ollama 回傳缺少 message/content 欄位，response = {response}")
            return []
        output = response["message"]["content"]
        synonyms = [line.strip() for line in output.split("\n") if line.strip()]
        if len(synonyms) > num_questions:
            synonyms = synonyms[:num_questions]
        return synonyms
    except concurrent.futures.TimeoutError:
        print(f"[超時] 單題超過 60 秒未回應，自動跳過。問題：{question}")
        return []
    except Exception as e:
        print(f"生成同義問法失敗: {e}")
        return []


def save_enhanced_data(original_data: List[Dict], file_name: str, enhanced: bool = True):
    """保存增強的數據到新文件"""
    if not original_data:
        return
    
    # 為輸出文件名添加標記
    base_name, ext = os.path.splitext(file_name)
    output_file = f"{base_name}_enhanced{ext}" if enhanced else f"{base_name}_backup{ext}"
    
    # 檢查原始檔案結構
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            original_structure = json.load(f)
        
        # 如果原始檔案有 data 鍵，則保持相同結構
        if "data" in original_structure and isinstance(original_structure["data"], list):
            output_data = {"data": original_data}
        else:
            output_data = original_data
    except Exception:
        # 如果讀取原始檔案失敗，則直接使用原始數據
        output_data = original_data
    
    # 保存到新文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"數據已保存到 {output_file}")

def process_file(file_path: str):
    """處理單個源文件，生成並添加同義問法"""
    print(f"\n處理文件: {file_path}")
    
    # 加載原始數據
    original_data = load_source_data(file_path)
    if not original_data:
        return
    
    # 創建原始數據備份
    save_enhanced_data(original_data, file_path, enhanced=False)
    
    # 跟踪進度
    total_items = len(original_data)
    processed = 0
    enhanced_count = 0
    
    # 處理每個條目
    for item in original_data:
        processed += 1
        
        # 跳過已有同義問法的條目
        if "synonymous_questions" in item and item["synonymous_questions"]:
            print(f"跳過已有同義問法的條目 ({processed}/{total_items}): {item.get('title', '未知')}")
            continue
        
        # 獲取原始問題
        original_question = item.get("question", "")
        if not original_question:
            print(f"跳過無問題的條目 ({processed}/{total_items}): {item.get('title', '未知')}")
            continue
        
        # 生成同義問法
        print(f"為問題生成同義問法 ({processed}/{total_items}): {original_question}")
        synonymous_questions = generate_synonymous_questions(original_question)
        
        # 添加同義問法到原始數據
        if synonymous_questions:
            item["synonymous_questions"] = synonymous_questions
            enhanced_count += 1
            
            # 顯示生成的同義問法
            print(f"  已生成 {len(synonymous_questions)} 個同義問法:")
            for q in synonymous_questions:
                print(f"  - {q}")
        else:
            print("  無法生成同義問法")
        
        # 每處理 5 個條目保存一次，避免中斷時丟失數據
        if processed % 5 == 0 or processed == total_items:
            save_enhanced_data(original_data, file_path)
        
        # 稍微暫停，避免過快請求
        time.sleep(1)
    
    # 最終保存
    save_enhanced_data(original_data, file_path)
    print(f"\n完成處理 {file_path}: 總共 {total_items} 個條目，增強了 {enhanced_count} 個條目")

def main():
    """主函數"""
    print("開始同義問法擴充工具...")
    
    for file_name in SOURCE_FILES:
        process_file(file_name)
    
    print("\n所有文件處理完成！")

if __name__ == "__main__":
    main()
