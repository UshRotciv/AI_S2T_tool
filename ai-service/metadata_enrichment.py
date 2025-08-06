#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import ollama
import time
import os
from typing import List, Dict, Any

# 元數據生成提示詞模板
METADATA_GENERATION_PROMPT = """
作為資安專家，請為以下資安問答內容生成豐富的元數據標籤。
根據內容分析，生成以下類別的標籤：

1. 主題標籤（topic_tags）：與內容主題相關的 3-5 個標籤，例如「密碼管理」、「釣魚郵件」、「社交工程」等
2. 風險等級（risk_level）：將內容涉及的資安風險評估為以下之一：低風險、中風險、高風險
3. 適用對象（target_audience）：最適合閱讀此內容的人員類型，如「一般員工」、「IT人員」、「主管」、「全體員工」等
4. 應對時機（timing）：此知識最適合在什麼時間點應用，例如「預防階段」、「事件發生中」、「事後處理」

問題：{question}
答案：{answer}

請以 JSON 格式回覆，只包含以下欄位：
{{
    "topic_tags": ["標籤1", "標籤2", "標籤3"],
    "risk_level": "風險等級",
    "target_audience": ["目標對象1", "目標對象2"],
    "timing": ["時機1", "時機2"]
}}

僅提供 JSON 內容，不要有其他解釋或前後文。
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

def generate_metadata(question: str, answer: str) -> Dict[str, Any]:
    """使用 Ollama 生成豐富的元數據"""
    try:
        # 準備提示詞
        prompt = METADATA_GENERATION_PROMPT.format(question=question, answer=answer)
        
        # 調用 Ollama 生成元數據
        response = ollama.chat(
            model="qwen2",  # 使用 qwen2 模型
            messages=[
                {"role": "system", "content": "你是資安專家，擁長為資安內容生成精確的元數據標籤。"},
                {"role": "user", "content": prompt}
            ]
        )
        
        # 解析回應內容
        content = response['message']['content']
        
        # 從回應文本中提取 JSON
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        # 解析為 JSON 對象
        metadata = json.loads(content)
        return metadata
    
    except Exception as e:
        print(f"生成元數據時出錯: {str(e)}")
        return {
            "topic_tags": [],
            "risk_level": "未知",
            "target_audience": [],
            "timing": []
        }

def save_enhanced_data(original_data: List[Dict], file_name: str, enhanced: bool = True):
    """保存增強的數據到新文件"""
    if not original_data:
        return
    
    # 為輸出文件名添加標記
    base_name, ext = os.path.splitext(file_name)
    output_file = f"{base_name}_metadata_enhanced{ext}" if enhanced else f"{base_name}_backup{ext}"
    
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
    """處理單個源文件，生成並添加元數據"""
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
        
        # 跳過已有豐富元數據的條目
        if "enriched_metadata" in item and item["enriched_metadata"]:
            print(f"跳過已有豐富元數據的條目 ({processed}/{total_items}): {item.get('title', '未知')}")
            continue
        
        # 獲取問題和答案
        question = item.get("question", "")
        answer = item.get("answer", "")
        
        if not question or not answer:
            print(f"跳過無問題或答案的條目 ({processed}/{total_items}): {item.get('title', '未知')}")
            continue
        
        # 生成豐富元數據
        print(f"為條目生成豐富元數據 ({processed}/{total_items}): {item.get('title', '未知')}")
        enriched_metadata = generate_metadata(question, answer)
        
        # 添加豐富元數據到原始數據
        if enriched_metadata:
            item["enriched_metadata"] = enriched_metadata
            enhanced_count += 1
            
            # 顯示生成的元數據
            print(f"  已生成豐富元數據:")
            for key, value in enriched_metadata.items():
                print(f"  - {key}: {value}")
        else:
            print("  無法生成豐富元數據")
        
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
    print("開始元數據豐富化工具...")
    
    for file_name in SOURCE_FILES:
        process_file(file_name)
    
    print("\n所有文件處理完成！")

if __name__ == "__main__":
    main()
