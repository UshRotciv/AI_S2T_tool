#!/usr/bin/env python
# -*- coding: utf-8 -*-

# RAG系統第三次整合測試腳本
# 評估混合檢索與再排序的整體效能

import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
import numpy as np
import ollama
import sys

print(f"--- 正在使用的 Python 解釋器 ---")
print(sys.executable)
print(f"---------------------------------")

# 導入自定義模塊

# 確保可以導入當前目錄的模塊
import sys
import os

# 加入當前目錄到 Python 路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from hybrid_search import HybridSearch
    from reranker import ReRanker, EnhancedRAGPipeline
    print("成功導入 HybridSearch 和 ReRanker 模塊")
except ImportError as e:
    print(f"無法導入必要模塊: {e}")
    print(f"Python 路徑: {sys.path}")
    print(f"當前目錄: {current_dir}")
    print(f"檔案列表: {os.listdir(current_dir)}")
    exit(1)

# 配置
EVALUATION_DIR = "../evaluation"
TEST_RESULTS_FILE = os.path.join(EVALUATION_DIR, "test_results_phase3.json")
MODEL_NAME = "qwen2"  # 用於回答生成的模型
MAX_TOKENS = 1024
TEMPERATURE = 0.1
BENCHMARK_QUESTIONS = [
    # 基礎問題
    {"id": "q1", "type": "基礎問題", "question": "印表機發現無人拿走的機密文件該怎麼做?"},
    # 變形問題
    {"id": "q2", "type": "變形問題", "question": "看到印表機旁有機密文件但沒人在場該怎麼處理?"},
    # 語意挑戰問題
    {"id": "q3", "type": "語意挑戰問題", "question": "印表機旁發現一份文件，上面寫著ASUS Confidential"},
    # 額外測試問題
    {"id": "q4", "type": "邊緣案例", "question": "在茶水間發現有人遺忘的含有公司標誌的文件"},
    {"id": "q5", "type": "複雜問題", "question": "如果我看到別人不小心把機密資料留在印表機，但我不確定是誰的文件，我該如何安全處理？"}
]


class EnhancedRAGTester:
    """
    增強型RAG系統測試器
    """

    def __init__(self):
        """初始化測試器"""
        self.hybrid_search = None
        self.reranker = None
        self.enhanced_pipeline = None
        self.test_results = {}
        self.init_system()

    def init_system(self):
        """初始化測試系統"""
        try:
            print("初始化混合檢索系統...")
            self.hybrid_search = HybridSearch()
            
            print("初始化再排序系統...")
            self.reranker = ReRanker(model_name=MODEL_NAME)
            
            print("初始化增強型RAG流程...")
            self.enhanced_pipeline = EnhancedRAGPipeline(
                hybrid_search_module=self.hybrid_search,
                reranker=self.reranker
            )
            
            print("系統初始化完成！")
            return True
        except Exception as e:
            print(f"系統初始化失敗: {e}")
            return False

    def _generate_answer(self, query: str, contexts: List[Dict[str, Any]]) -> str:
        """使用檢索到的上下文生成回答"""
        if not contexts:
            return "抱歉，我找不到相關資訊來回答這個問題。"
        
        # 構建提示詞
        context_text = "\n\n".join([f"文檔 {i+1}：\n{ctx.get('text', '')}" for i, ctx in enumerate(contexts[:3])])
        prompt = f"""### 系統
你是華碩的資安助手，請根據提供的資訊回答問題。只使用提供的資訊回答，不要編造內容。如果資訊不足以回答問題，請誠實說明。

### 上下文資訊
{context_text}

### 問題
{query}

### 回答
"""
        
        try:
            # 調用Ollama生成回答
            response = ollama.generate(
                model=MODEL_NAME,
                prompt=prompt,
                options={
                    "temperature": TEMPERATURE,
                    "num_predict": MAX_TOKENS,
                }
            )
            return response.get("response", "生成回答時出錯")
        except Exception as e:
            print(f"生成回答時出錯: {e}")
            return f"生成回答時出錯: {e}"

    def evaluate_question(self, question_obj: Dict[str, Any]) -> Dict[str, Any]:
        """評估單個問題"""
        question_id = question_obj["id"]
        question_type = question_obj["type"]
        question = question_obj["question"]
        
        print(f"\n評估問題 [{question_id}] ({question_type}): {question}")
        
        result = {
            "id": question_id,
            "type": question_type,
            "question": question,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "stages": {},
        }
        
        try:
            # 階段1：純向量搜索
            vector_start = time.time()
            vector_results = self.hybrid_search.collection.query(
                query_texts=[question],
                n_results=5,
                include=["documents", "metadatas", "distances"]
            )
            vector_time = time.time() - vector_start
            
            vector_docs = []
            if vector_results and vector_results["ids"] and vector_results["ids"][0]:
                for i, (doc_id, doc_text, metadata, distance) in enumerate(zip(
                    vector_results["ids"][0],
                    vector_results["documents"][0],
                    vector_results["metadatas"][0],
                    vector_results["distances"][0]
                )):
                    vector_docs.append({
                        "id": doc_id,
                        "text": doc_text,
                        "metadata": metadata,
                        "score": 1 - min(distance, 1.0),
                    })
            
            # 階段2：混合搜索
            hybrid_start = time.time()
            hybrid_docs = self.hybrid_search.search(question, top_k=5)
            hybrid_time = time.time() - hybrid_start
            
            # 階段3：再排序
            rerank_start = time.time()
            reranked_docs = self.reranker.rerank(question, hybrid_docs, top_k=3)
            rerank_time = time.time() - rerank_start
            
            # 生成回答
            answer_start = time.time()
            answer = self._generate_answer(question, reranked_docs)
            answer_time = time.time() - answer_start
            
            # 記錄結果
            result["stages"]["vector"] = {
                "time_seconds": round(vector_time, 3),
                "docs_count": len(vector_docs),
                "top_docs": vector_docs[:3]
            }
            
            result["stages"]["hybrid"] = {
                "time_seconds": round(hybrid_time, 3),
                "docs_count": len(hybrid_docs),
                "top_docs": hybrid_docs[:3]
            }
            
            result["stages"]["reranked"] = {
                "time_seconds": round(rerank_time, 3),
                "docs_count": len(reranked_docs),
                "top_docs": reranked_docs
            }
            
            result["answer"] = {
                "text": answer,
                "time_seconds": round(answer_time, 3)
            }
            
            result["total_time_seconds"] = round(
                vector_time + hybrid_time + rerank_time + answer_time, 3
            )
            
            print(f"問題 [{question_id}] 評估完成，總耗時: {result['total_time_seconds']:.3f} 秒")
            return result
        
        except Exception as e:
            error_msg = f"評估問題 [{question_id}] 時出錯: {e}"
            print(error_msg)
            result["error"] = error_msg
            return result

    def run_benchmark(self):
        """執行基準測試"""
        print(f"\n===== 開始第三階段整合測試 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====\n")
        
        results = {
            "test_info": {
                "phase": "3",
                "description": "混合檢索與再排序整合測試",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            "questions": []
        }
        
        start_time = time.time()
        
        for question in BENCHMARK_QUESTIONS:
            question_result = self.evaluate_question(question)
            results["questions"].append(question_result)
        
        total_time = time.time() - start_time
        results["test_info"]["total_time_seconds"] = round(total_time, 3)
        results["test_info"]["questions_count"] = len(BENCHMARK_QUESTIONS)
        
        self.test_results = results
        print(f"\n===== 測試完成，總耗時: {results['test_info']['total_time_seconds']:.3f} 秒 =====\n")
        
        # 保存測試結果
        self._save_test_results()
        
        return results

    def _save_test_results(self):
        """保存測試結果到文件"""
        # 確保目錄存在
        os.makedirs(EVALUATION_DIR, exist_ok=True)
        
        try:
            with open(TEST_RESULTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            print(f"測試結果已保存至: {TEST_RESULTS_FILE}")
        except Exception as e:
            print(f"保存測試結果時出錯: {e}")

    def analyze_results(self):
        """分析測試結果"""
        if not self.test_results or not self.test_results.get("questions"):
            print("沒有可分析的測試結果")
            return
        
        questions = self.test_results["questions"]
        
        print("\n===== 測試結果分析 =====\n")
        
        # 各階段平均時間
        vector_times = [q["stages"].get("vector", {}).get("time_seconds", 0) for q in questions if "stages" in q]
        hybrid_times = [q["stages"].get("hybrid", {}).get("time_seconds", 0) for q in questions if "stages" in q]
        rerank_times = [q["stages"].get("reranked", {}).get("time_seconds", 0) for q in questions if "stages" in q]
        answer_times = [q["answer"].get("time_seconds", 0) for q in questions if "answer" in q]
        
        print(f"平均向量檢索時間: {np.mean(vector_times):.3f} 秒")
        print(f"平均混合檢索時間: {np.mean(hybrid_times):.3f} 秒")
        print(f"平均再排序時間: {np.mean(rerank_times):.3f} 秒")
        print(f"平均回答生成時間: {np.mean(answer_times):.3f} 秒")
        
        # 按問題類型分析
        question_types = set([q["type"] for q in questions])
        for q_type in question_types:
            type_questions = [q for q in questions if q["type"] == q_type]
            type_times = [q.get("total_time_seconds", 0) for q in type_questions]
            print(f"\n問題類型 [{q_type}] 分析:")
            print(f"  問題數量: {len(type_questions)}")
            print(f"  平均處理時間: {np.mean(type_times):.3f} 秒")
            
        print("\n詳細測試結果請查看: " + TEST_RESULTS_FILE)


def main():
    """主函數"""
    # 創建並執行測試器
    tester = EnhancedRAGTester()
    tester.run_benchmark()
    tester.analyze_results()


if __name__ == "__main__":
    main()
