#!/usr/bin/env python3
"""
RAG系統診斷工具
"""
import os
import sys
import json
import ollama
import chromadb
import numpy as np
from chromadb.utils import embedding_functions
from typing import List, Dict, Any

# 配置日誌
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_scenarios(file_path: str = "../app-server/scenarios.json") -> List[Dict[str, Any]]:
    """載入場景數據"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "data" in data:
                return data["data"]
            return []
    except Exception as e:
        logger.error(f"載入場景數據失敗: {str(e)}")
        return []

def test_vector_similarity(question1: str, question2: str, model: str = "mxbai-embed-large") -> float:
    """測試兩個問題的向量相似度"""
    try:
        # 獲取問題1的嵌入
        response1 = ollama.embeddings(model=model, prompt=question1)
        embedding1 = np.array(response1["embedding"])
        
        # 獲取問題2的嵌入
        response2 = ollama.embeddings(model=model, prompt=question2)
        embedding2 = np.array(response2["embedding"])
        
        # 計算餘弦相似度
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        similarity = dot_product / (norm1 * norm2)
        
        return similarity
    except Exception as e:
        logger.error(f"計算向量相似度失敗: {str(e)}")
        return 0.0

def test_chroma_retrieval(query: str, collection_name: str = "scenarios", collection_path: str = "./chroma_db") -> Dict[str, Any]:
    """測試向量數據庫檢索"""
    try:
        # 創建 ChromaDB 客戶端
        client = chromadb.PersistentClient(path=collection_path)
        
        # 獲取向量化函數
        sentence_transformer_ef = embedding_functions.OllamaEmbeddingFunction(
            model_name="mxbai-embed-large",
            url="http://localhost:11434",
        )
        
        # 獲取集合
        collection = client.get_or_create_collection(
            name=collection_name,
            embedding_function=sentence_transformer_ef,
            metadata={"hnsw:space": "cosine"}
        )
        
        # 使用向量搜索
        response = ollama.embeddings(model='mxbai-embed-large', prompt=query)
        embedding = response["embedding"]
        
        # 進行查詢
        results = collection.query(
            query_embeddings=[embedding],
            n_results=3,
            include=["documents", "metadatas", "distances"]
        )
        
        # 分析結果
        if results['ids'] and len(results['ids'][0]) > 0:
            for i, (doc_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
                metadata = results['metadatas'][0][i] if i < len(results['metadatas'][0]) else {}
                title = metadata.get('title', '未知標題')
                logger.info(f"結果 {i+1}: {title} (距離: {distance:.4f})")
                logger.info(f"內容: {results['documents'][0][i][:200]}...")
        
        return results
    except Exception as e:
        logger.error(f"向量數據庫檢索失敗: {str(e)}")
        return {"error": str(e)}

def test_text_retrieval(query: str, collection_name: str = "scenarios", collection_path: str = "./chroma_db") -> Dict[str, Any]:
    """測試文本關鍵字檢索"""
    try:
        # 創建 ChromaDB 客戶端
        client = chromadb.PersistentClient(path=collection_path)
        
        # 獲取向量化函數
        sentence_transformer_ef = embedding_functions.OllamaEmbeddingFunction(
            model_name="mxbai-embed-large",
            url="http://localhost:11434",
        )
        
        # 獲取集合
        collection = client.get_or_create_collection(
            name=collection_name,
            embedding_function=sentence_transformer_ef,
            metadata={"hnsw:space": "cosine"}
        )
        
        # 使用文本關鍵字搜索
        results = collection.query(
            query_texts=[query],
            n_results=3,
            include=["documents", "metadatas", "distances"]
        )
        
        # 分析結果
        if results['ids'] and len(results['ids'][0]) > 0:
            for i, (doc_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
                metadata = results['metadatas'][0][i] if i < len(results['metadatas'][0]) else {}
                title = metadata.get('title', '未知標題')
                logger.info(f"關鍵字搜索結果 {i+1}: {title} (距離: {distance:.4f})")
                logger.info(f"內容: {results['documents'][0][i][:200]}...")
        
        return results
    except Exception as e:
        logger.error(f"文本關鍵字檢索失敗: {str(e)}")
        return {"error": str(e)}

def analyze_collection(collection_name: str = "scenarios", collection_path: str = "./chroma_db") -> Dict[str, Any]:
    """分析向量數據庫集合"""
    try:
        # 創建 ChromaDB 客戶端
        client = chromadb.PersistentClient(path=collection_path)
        
        # 獲取集合
        collection = client.get_collection(name=collection_name)
        
        # 獲取集合信息
        collection_info = {
            "count": collection.count(),
        }
        
        # 獲取所有項目ID
        all_ids = collection.get()["ids"]
        
        # 如果數量太多，只取前10個進行分析
        sample_ids = all_ids[:10] if len(all_ids) > 10 else all_ids
        
        # 獲取樣本數據
        sample_data = collection.get(ids=sample_ids, include=["documents", "metadatas"])
        
        collection_info["sample_data"] = sample_data
        
        return collection_info
    except Exception as e:
        logger.error(f"分析向量數據庫集合失敗: {str(e)}")
        return {"error": str(e)}

def main():
    """主函數"""
    print("=" * 50)
    print("RAG系統診斷工具")
    print("=" * 50)
    
    # 1. 測試向量相似度
    print("\n1. 測試向量相似度")
    original_question = "如何處理印表機的機密文件?"
    similar_question = "辦公室列印機的機密資料該如何處理?"
    dissimilar_question = "如何設定公司電子郵件?"
    
    try:
        sim1 = test_vector_similarity(original_question, similar_question)
        print(f"相似問題的相似度: {sim1:.4f}")
        
        sim2 = test_vector_similarity(original_question, dissimilar_question)
        print(f"不相似問題的相似度: {sim2:.4f}")
    except Exception as e:
        print(f"向量相似度測試失敗: {str(e)}")
    
    # 2. 測試向量檢索
    print("\n2. 測試向量檢索")
    test_query = "如何處理印表機的機密文件?"
    
    try:
        print(f"使用查詢: '{test_query}'")
        vector_results = test_chroma_retrieval(test_query)
        if "error" in vector_results:
            print(f"向量檢索失敗: {vector_results['error']}")
    except Exception as e:
        print(f"向量檢索測試失敗: {str(e)}")
    
    # 3. 測試文本關鍵字檢索
    print("\n3. 測試文本關鍵字檢索")
    
    try:
        print(f"使用查詢: '{test_query}'")
        text_results = test_text_retrieval(test_query)
        if "error" in text_results:
            print(f"文本檢索失敗: {text_results['error']}")
    except Exception as e:
        print(f"文本檢索測試失敗: {str(e)}")
    
    # 4. 分析向量數據庫集合
    print("\n4. 分析向量數據庫集合")
    
    try:
        collection_info = analyze_collection()
        if "error" in collection_info:
            print(f"集合分析失敗: {collection_info['error']}")
        else:
            print(f"集合中有 {collection_info['count']} 個項目")
            
            if "sample_data" in collection_info:
                sample = collection_info["sample_data"]
                print("\n樣本數據:")
                for i, (id, doc, metadata) in enumerate(zip(sample["ids"], sample["documents"], sample["metadatas"])):
                    title = metadata.get("title", "未知標題")
                    is_chunk = metadata.get("is_chunk", False)
                    print(f"項目 {i+1}: {id} - {title} (分段: {'是' if is_chunk else '否'})")
                    print(f"內容 (前200字): {doc[:200]}...")
                    print("-" * 30)
    except Exception as e:
        print(f"向量數據庫集合分析失敗: {str(e)}")
    
    print("\n診斷完成!")

if __name__ == "__main__":
    main()
