#!/usr/bin/env python
# -*- coding: utf-8 -*-

# RAG系統階段三優化：混合檢索實現
# 結合BM25關鍵詞搜索與向量檢索的優點，提升檢索準確率與魯棒性

import json
import time
import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
import chromadb
from chromadb.utils import embedding_functions

# BM25參數
BM25_K1 = 1.5  # 術語飽和參數
BM25_B = 0.75  # 文檔長度正規化參數

# 混合搜索參數
ALPHA = 0.7  # 向量搜索權重
BETA = 0.3   # BM25搜索權重

# ChromaDB配置
COLLECTION_NAME = "confidential_docs"
CHROMA_PATH = "../chroma_db"

class HybridSearch:
    def __init__(self, collection_name: str = COLLECTION_NAME, chroma_path: str = CHROMA_PATH):
        """初始化混合檢索系統"""
        self.collection_name = collection_name
        self.chroma_path = chroma_path
        self.client = None
        self.collection = None
        self.documents = []
        self.doc_mapping = {}  # 文檔ID到索引的映射
        self.vectorizer = None
        self.tfidf_matrix = None
        self.doc_lens = []  # 文檔長度列表
        self.avg_doc_len = 0  # 平均文檔長度
        
        # 初始化ChromaDB客戶端
        self._init_chroma_client()
        # 加載文檔並構建BM25索引
        self._load_documents()
        self._build_bm25_index()
        
    def _init_chroma_client(self):
        """初始化ChromaDB客戶端"""
        try:
            # 使用本地嵌入函數(可替換為不同的嵌入模型)
            embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction()
            
            # 連接ChromaDB
            self.client = chromadb.PersistentClient(path=self.chroma_path)
            
            # 獲取或創建集合
            try:
                self.collection = self.client.get_collection(
                    name=self.collection_name,
                    embedding_function=embed_fn
                )
                print(f"已連接到現有集合: {self.collection_name}")
            except Exception as e:
                print(f"集合不存在，創建新集合: {self.collection_name}")
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=embed_fn
                )
        except Exception as e:
            print(f"ChromaDB初始化失敗: {e}")
            raise
    
    def _load_documents(self):
        """從ChromaDB加載文檔"""
        try:
            # 獲取所有文檔
            results = self.collection.get()
            self.documents = []
            
            # 構建文檔列表與映射
            for i, (doc_id, doc_text, metadata) in enumerate(zip(
                results["ids"], 
                results["documents"], 
                results["metadatas"]
            )):
                self.documents.append({
                    "id": doc_id,
                    "text": doc_text,
                    "metadata": metadata
                })
                self.doc_mapping[doc_id] = i
            
            print(f"已從ChromaDB加載 {len(self.documents)} 個文檔")
        except Exception as e:
            print(f"加載文檔失敗: {e}")
            raise
    
    def _build_bm25_index(self):
        """構建BM25索引"""
        if not self.documents:
            print("沒有文檔，無法構建BM25索引")
            return
        
        try:
            # 提取文本內容
            texts = [doc["text"] for doc in self.documents]
            
            # 創建TF-IDF向量化器
            self.vectorizer = TfidfVectorizer(analyzer='word', norm=None, use_idf=True, smooth_idf=False)
            
            # 計算TF-IDF矩陣
            self.tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            # 計算文檔長度
            self.doc_lens = [len(text.split()) for text in texts]
            self.avg_doc_len = sum(self.doc_lens) / len(self.doc_lens) if self.doc_lens else 0
            
            print("BM25索引構建完成")
        except Exception as e:
            print(f"構建BM25索引失敗: {e}")
            raise
    
    def _compute_bm25_scores(self, query: str) -> np.ndarray:
        """計算BM25分數"""
        if not self.tfidf_matrix or not self.vectorizer:
            print("BM25索引未初始化")
            return np.zeros(len(self.documents))
        
        # 向量化查詢
        q_vec = self.vectorizer.transform([query])
        
        # 獲取查詢詞彙索引與權重
        q_terms_idxs = q_vec.indices
        q_terms_weights = q_vec.data
        
        # 初始化BM25分數
        scores = np.zeros(self.tfidf_matrix.shape[0])
        
        # 計算每個文檔的BM25分數
        for idx, weight in zip(q_terms_idxs, q_terms_weights):
            # 獲取每個文檔中該詞的TF-IDF值
            term_scores = self.tfidf_matrix[:, idx].toarray().flatten()
            
            # 應用BM25公式計算該詞對每個文檔的貢獻
            for doc_idx, term_score in enumerate(term_scores):
                if term_score == 0:
                    continue
                
                # 文檔長度正規化因子
                doc_len = self.doc_lens[doc_idx]
                len_norm = (1 - BM25_B) + BM25_B * (doc_len / self.avg_doc_len)
                
                # BM25公式
                numerator = term_score * (BM25_K1 + 1)
                denominator = term_score + BM25_K1 * len_norm
                bm25_score = (numerator / denominator) * weight
                
                scores[doc_idx] += bm25_score
        
        return scores
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        混合搜索，結合向量搜索與BM25
        """
        start_time = time.time()
        
        # 向量搜索
        vector_results = self.collection.query(
            query_texts=[query],
            n_results=top_k*2,  # 獲取更多結果用於混合
            include=["documents", "metadatas", "distances"]
        )
        
        vector_scores = {}
        if vector_results and vector_results["ids"] and vector_results["ids"][0]:
            # 向量搜索結果轉換成字典 {doc_id: score}
            for doc_id, distance in zip(vector_results["ids"][0], vector_results["distances"][0]):
                # 距離轉換為相似度分數(1-距離)
                vector_scores[doc_id] = 1 - min(distance, 1.0)
        
        # BM25搜索
        bm25_scores = self._compute_bm25_scores(query)
        
        # 歸一化BM25分數
        max_bm25 = np.max(bm25_scores) if bm25_scores.size > 0 and np.max(bm25_scores) > 0 else 1
        normalized_bm25 = bm25_scores / max_bm25
        
        # 混合排序
        hybrid_scores = {}
        
        # 對每個文檔計算混合分數
        for doc_id, vec_score in vector_scores.items():
            if doc_id in self.doc_mapping:
                doc_idx = self.doc_mapping[doc_id]
                bm25_score = normalized_bm25[doc_idx]
                # 加權混合
                hybrid_score = ALPHA * vec_score + BETA * bm25_score
                hybrid_scores[doc_id] = hybrid_score
        
        # 按混合分數排序
        sorted_results = sorted(
            [(doc_id, score) for doc_id, score in hybrid_scores.items()],
            key=lambda x: x[1], 
            reverse=True
        )
        
        # 僅保留前top_k個結果
        top_results = sorted_results[:top_k]
        
        # 構建最終結果
        results = []
        for doc_id, score in top_results:
            doc_idx = self.doc_mapping.get(doc_id)
            if doc_idx is not None and doc_idx < len(self.documents):
                doc = self.documents[doc_idx]
                results.append({
                    "id": doc_id,
                    "text": doc["text"],
                    "metadata": doc["metadata"],
                    "score": score,
                    "vector_score": vector_scores.get(doc_id, 0),
                    "bm25_score": normalized_bm25[doc_idx] if doc_idx < len(normalized_bm25) else 0
                })
        
        search_time = time.time() - start_time
        print(f"混合搜索完成，耗時 {search_time:.3f} 秒，找到 {len(results)} 個相關文檔")
        
        return results

# 測試函數
def test_hybrid_search():
    """測試混合檢索效果"""
    try:
        # 初始化混合搜索
        hybrid = HybridSearch()
        
        # 測試查詢
        test_queries = [
            "印表機發現無人拿走的機密文件該怎麼做?",
            "看到印表機旁有機密文件但沒人在場該怎麼處理?",
            "印表機旁發現一份文件，上面寫著ASUS Confidential"
        ]
        
        for query in test_queries:
            print(f"\n測試查詢: {query}")
            results = hybrid.search(query, top_k=3)
            
            print(f"找到 {len(results)} 個結果:")
            for i, doc in enumerate(results):
                print(f"[{i+1}] ID: {doc['id']}")
                print(f"    混合分數: {doc['score']:.4f} (向量: {doc['vector_score']:.4f}, BM25: {doc['bm25_score']:.4f})")
                print(f"    文本: {doc['text'][:100]}..." if len(doc['text']) > 100 else f"    文本: {doc['text']}")
                print(f"    元數據: {doc['metadata']}")
                print("")
    
    except Exception as e:
        print(f"測試失敗: {e}")

if __name__ == "__main__":
    test_hybrid_search()
