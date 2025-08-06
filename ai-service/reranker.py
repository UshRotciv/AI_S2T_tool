#!/usr/bin/env python
# -*- coding: utf-8 -*-

# RAG系統階段三優化：結果再排序
# 使用輕量級模型對混合檢索結果進行再排序，進一步優化檢索準確度

import time
import json
import numpy as np
from typing import List, Dict, Any, Optional, Union
import ollama
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 再排序配置
MODEL_NAME = "qwen2"  # 使用現有的qwen2模型作為再排序器
MAX_TOKENS = 1024  # 生成回應的最大token數
TEMPERATURE = 0.1  # 低溫度，提高確定性
TOP_K = 5  # 需要再排序的文檔數量
CONTEXT_WINDOW = 8192  # 模型上下文窗口大小

class ReRanker:
    """
    使用LLM進行檢索結果再排序的類
    """
    
    def __init__(self, model_name: str = MODEL_NAME):
        """初始化再排序器"""
        self.model_name = model_name
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CONTEXT_WINDOW // 2,
            chunk_overlap=100,
            separators=["\n\n", "\n", "。", "，", " ", ""],
            keep_separator=False,
        )
    
    def _create_reranking_prompt(self, query: str, docs: List[Dict[str, Any]]) -> str:
        """
        建立再排序prompt模板
        
        參數:
            query: 使用者原始查詢
            docs: 候選文檔列表
            
        返回:
            格式化的prompt
        """
        prompt = f"""### 任務
你是一個專業的資訊檢索排序專家。你的任務是幫我評估以下候選文檔與使用者查詢的相關性，並按照相關程度從高到低重新排序。

### 使用者查詢
{query}

### 候選文檔
"""
        
        for i, doc in enumerate(docs):
            doc_content = doc.get("text", "")
            prompt += f"[文檔{i+1}]\n{doc_content}\n\n"
        
        prompt += """
### 評估要求
1. 對每份文檔評分(0-10分)，其中：
   - 0-3分: 與查詢基本無關
   - 4-6分: 部分相關但不完全匹配
   - 7-10分: 高度相關，直接回答查詢問題
2. 考慮因素：語義匹配度、資訊完整性、專業性、權威性
3. 輸出格式：
```json
{
  "rankings": [
    {"doc_index": 文檔索引, "score": 分數, "reason": "簡短理由"},
    {"doc_index": 文檔索引, "score": 分數, "reason": "簡短理由"},
    ...
  ]
}
```
請嚴格按照上述JSON格式輸出，不要有任何額外文字，確保JSON格式正確無誤。文檔索引應使用1開始的數字對應上方文檔編號。
"""
        return prompt
    
    def _extract_json_from_response(self, response: str) -> Dict:
        """從回應中提取JSON"""
        try:
            # 嘗試直接解析整個回應
            return json.loads(response.strip())
        except json.JSONDecodeError:
            # 若失敗，尋找JSON部分
            try:
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    return json.loads(json_str)
                else:
                    return {"rankings": []}
            except (json.JSONDecodeError, ValueError):
                return {"rankings": []}
    
    def rerank(self, query: str, docs: List[Dict[str, Any]], top_k: int = TOP_K) -> List[Dict[str, Any]]:
        """
        使用LLM對文檔進行再排序
        
        參數:
            query: 使用者查詢
            docs: 候選文檔列表 
            top_k: 返回的排序後文檔數量
            
        返回:
            排序後的文檔列表
        """
        if not docs:
            print("沒有文檔需要再排序")
            return []
        
        # 限制文檔數量以避免上下文過長
        docs_to_rerank = docs[:min(len(docs), top_k*2)]
        
        start_time = time.time()
        print(f"開始對 {len(docs_to_rerank)} 個文檔進行再排序...")
        
        try:
            # 建立再排序prompt
            prompt = self._create_reranking_prompt(query, docs_to_rerank)
            
            # 調用Ollama進行再排序評估
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    "temperature": TEMPERATURE,
                    "num_predict": MAX_TOKENS,
                }
            )
            
            # 提取回應文本
            response_text = response.get("response", "")
            
            # 解析排序結果
            ranking_data = self._extract_json_from_response(response_text)
            rankings = ranking_data.get("rankings", [])
            
            if not rankings:
                print("無法從LLM回應中解析排序結果，返回原始順序")
                return docs[:top_k]
            
            # 重新排序文檔
            reranked_docs = []
            for rank in rankings:
                doc_index = rank.get("doc_index")
                if isinstance(doc_index, int) and 1 <= doc_index <= len(docs_to_rerank):
                    doc = docs_to_rerank[doc_index-1].copy()  # 複製以避免修改原始文檔
                    doc["rerank_score"] = rank.get("score", 0)
                    doc["rerank_reason"] = rank.get("reason", "")
                    reranked_docs.append(doc)
            
            # 處理未被模型排序但在原始列表中的文檔
            ranked_indices = [r.get("doc_index", 0) for r in rankings]
            for i, doc in enumerate(docs_to_rerank):
                if i+1 not in ranked_indices:
                    doc_copy = doc.copy()
                    doc_copy["rerank_score"] = 0
                    doc_copy["rerank_reason"] = "未被模型評分"
                    reranked_docs.append(doc_copy)
            
            # 確保不超過請求的top_k
            reranked_docs = reranked_docs[:top_k]
            
            rerank_time = time.time() - start_time
            print(f"再排序完成，耗時 {rerank_time:.3f} 秒，得到 {len(reranked_docs)} 個排序後文檔")
            
            return reranked_docs
            
        except Exception as e:
            print(f"再排序過程中發生錯誤: {e}")
            # 發生錯誤時返回原始排序的文檔
            return docs[:top_k]

class EnhancedRAGPipeline:
    """
    增強型RAG流程，整合混合檢索和再排序
    """
    
    def __init__(self, 
                 hybrid_search_module=None, 
                 reranker: Optional[ReRanker] = None,
                 top_k: int = TOP_K):
        """初始化增強型RAG流程"""
        self.hybrid_search = hybrid_search_module
        self.reranker = reranker if reranker else ReRanker()
        self.top_k = top_k
    
    def retrieve_and_rerank(self, query: str) -> List[Dict[str, Any]]:
        """
        執行完整的檢索與再排序流程
        
        參數:
            query: 使用者查詢
            
        返回:
            最終排序後的文檔列表
        """
        start_time = time.time()
        
        try:
            # 1. 混合檢索 (假設混合檢索模組已被導入)
            if self.hybrid_search:
                search_results = self.hybrid_search.search(query, top_k=self.top_k*2)
            else:
                raise ImportError("混合檢索模組未提供")
            
            if not search_results:
                print("混合檢索未返回結果")
                return []
            
            # 2. 再排序
            reranked_results = self.reranker.rerank(query, search_results, top_k=self.top_k)
            
            total_time = time.time() - start_time
            print(f"完整RAG檢索流程完成，總耗時 {total_time:.3f} 秒")
            
            return reranked_results
        
        except Exception as e:
            print(f"檢索流程發生錯誤: {e}")
            return []

# 測試函數
def test_reranker():
    """測試再排序功能"""
    try:
        # 測試查詢
        query = "印表機發現無人拿走的機密文件該怎麼做?"
        
        # 模擬的混合檢索結果
        mock_results = [
            {
                "id": "doc1",
                "text": "若在印表機發現無人領取的機密文件，應立即通知文件擁有者或部門主管，絕不私自翻閱。若無法確認擁有者，則應交由資安部門處理，切勿隨意丟棄或放置不管。機密文件必須妥善保管，直到確認適當處置方式。",
                "metadata": {"category": "資料安全", "confidential_level": "高"},
                "score": 0.92
            },
            {
                "id": "doc2",
                "text": "機密文件使用完畢後，必須使用碎紙機銷毀，不可直接丟入垃圾桶。文件若需要暫時保存，應放置於上鎖的櫃子或保險箱內，確保無人能隨意取得。",
                "metadata": {"category": "資料安全", "confidential_level": "中"},
                "score": 0.75
            },
            {
                "id": "doc3",
                "text": "印表機使用指南：1. 確認紙張充足 2. 選擇正確紙張尺寸 3. 檢查墨水存量 4. 若出現卡紙，請按照面板指示處理",
                "metadata": {"category": "設備使用", "confidential_level": "低"},
                "score": 0.68
            },
            {
                "id": "doc4", 
                "text": "發現他人遺忘於印表機的機密文件時，應立即聯繫文件所有人並歸還，或交由資安部門處理。切勿私自閱讀、複製或丟棄該文件，以免造成資訊外洩風險。",
                "metadata": {"category": "資料安全", "confidential_level": "高"},
                "score": 0.87
            }
        ]
        
        # 初始化再排序器
        reranker = ReRanker()
        
        # 執行再排序
        print(f"\n測試查詢: {query}")
        reranked_docs = reranker.rerank(query, mock_results, top_k=3)
        
        print(f"再排序結果 (共 {len(reranked_docs)} 項):")
        for i, doc in enumerate(reranked_docs):
            print(f"[{i+1}] ID: {doc['id']}")
            print(f"    再排序分數: {doc.get('rerank_score', 'N/A')}")
            print(f"    原始分數: {doc.get('score', 'N/A')}")
            print(f"    理由: {doc.get('rerank_reason', 'N/A')}")
            print(f"    文本: {doc['text'][:100]}..." if len(doc['text']) > 100 else f"    文本: {doc['text']}")
            print("")
            
    except Exception as e:
        print(f"測試失敗: {e}")

if __name__ == "__main__":
    test_reranker()
