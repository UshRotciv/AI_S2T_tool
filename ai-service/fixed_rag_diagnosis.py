#!/usr/bin/env python3
"""
修正版 RAG 系統診斷工具
專門用於驗證印表機機密文件等重要問題的檢索質量
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
        
        # 獲取集合
        try:
            collection = client.get_collection(name=collection_name)
            print(f"成功獲取集合: {collection_name}")
        except Exception as e:
            print(f"獲取集合失敗: {str(e)}，嘗試創建新集合")
            sentence_transformer_ef = embedding_functions.OllamaEmbeddingFunction(
                model_name="mxbai-embed-large",
                url="http://localhost:11434/api",
            )
            collection = client.create_collection(
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
            print("\n向量檢索結果:")
            for i, (doc_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
                metadata = results['metadatas'][0][i] if i < len(results['metadatas'][0]) else {}
                title = metadata.get('title', '未知標題')
                
                # 檢查內容是否包含機密文件相關關鍵字
                content = results['documents'][0][i].lower()
                has_printer_keywords = '印表機' in content or '列印' in content or '打印' in content
                has_confidential_keywords = '機密' in content or 'confidential' in content
                has_action_keywords = '非禮勿視' in content or '碎紙機' in content or '通知' in content
                
                # 輸出結果
                print(f"結果 {i+1}: {title} (距離: {distance:.4f})")
                print(f"  ID: {doc_id}")
                if has_printer_keywords:
                    print(f"  ✓ 包含印表機/列印相關內容")
                if has_confidential_keywords:
                    print(f"  ✓ 包含機密相關內容")
                if has_action_keywords:
                    print(f"  ✓ 包含關鍵處理步驟")
                
                # 輸出內容預覽
                print(f"  內容預覽: {content[:300]}...")
                print("-" * 50)
        
        return results
    except Exception as e:
        logger.error(f"向量數據庫檢索失敗: {str(e)}")
        return {"error": str(e)}

def test_text_retrieval(query: str, collection_name: str = "scenarios", collection_path: str = "./chroma_db") -> Dict[str, Any]:
    """測試文本關鍵字檢索"""
    try:
        # 創建 ChromaDB 客戶端
        client = chromadb.PersistentClient(path=collection_path)
        
        # 獲取集合
        collection = client.get_collection(name=collection_name)
        
        # 使用文本關鍵字搜索
        results = collection.query(
            query_texts=[query],
            n_results=3,
            include=["documents", "metadatas", "distances"]
        )
        
        # 分析結果
        if results['ids'] and len(results['ids'][0]) > 0:
            print("\n文本關鍵字檢索結果:")
            for i, (doc_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
                metadata = results['metadatas'][0][i] if i < len(results['metadatas'][0]) else {}
                title = metadata.get('title', '未知標題')
                
                # 檢查內容是否包含機密文件相關關鍵字
                content = results['documents'][0][i].lower()
                has_printer_keywords = '印表機' in content or '列印' in content or '打印' in content
                has_confidential_keywords = '機密' in content or 'confidential' in content
                has_action_keywords = '非禮勿視' in content or '碎紙機' in content or '通知' in content
                
                # 輸出結果
                print(f"結果 {i+1}: {title} (距離: {distance:.4f})")
                print(f"  ID: {doc_id}")
                if has_printer_keywords:
                    print(f"  ✓ 包含印表機/列印相關內容")
                if has_confidential_keywords:
                    print(f"  ✓ 包含機密相關內容")
                if has_action_keywords:
                    print(f"  ✓ 包含關鍵處理步驟")
                
                # 輸出內容預覽
                print(f"  內容預覽: {content[:300]}...")
                print("-" * 50)
        
        return results
    except Exception as e:
        logger.error(f"文本關鍵字檢索失敗: {str(e)}")
        return {"error": str(e)}

def test_hybrid_retrieval(query: str, collection_name: str = "scenarios", collection_path: str = "./chroma_db") -> Dict[str, Any]:
    """測試混合檢索策略（向量 + 關鍵字）"""
    try:
        # 創建 ChromaDB 客戶端
        client = chromadb.PersistentClient(path=collection_path)
        
        # 獲取集合
        collection = client.get_collection(name=collection_name)
        
        # 1. 先用向量搜索
        response = ollama.embeddings(model='mxbai-embed-large', prompt=query)
        embedding = response["embedding"]
        
        vector_results = collection.query(
            query_embeddings=[embedding],
            n_results=3,
            include=["documents", "metadatas", "distances", "embeddings"]
        )
        
        # 2. 再用關鍵字搜索
        keyword_results = collection.query(
            query_texts=[query],
            n_results=3,
            include=["documents", "metadatas", "distances", "embeddings"]
        )
        
        # 3. 合併結果並去重
        combined_ids = []
        combined_docs = []
        combined_metadatas = []
        combined_distances = []
        
        # 處理向量結果
        if vector_results['ids'] and len(vector_results['ids'][0]) > 0:
            for i, doc_id in enumerate(vector_results['ids'][0]):
                if doc_id not in combined_ids:
                    combined_ids.append(doc_id)
                    combined_docs.append(vector_results['documents'][0][i])
                    combined_metadatas.append(vector_results['metadatas'][0][i])
                    combined_distances.append(vector_results['distances'][0][i])
        
        # 處理關鍵字結果
        if keyword_results['ids'] and len(keyword_results['ids'][0]) > 0:
            for i, doc_id in enumerate(keyword_results['ids'][0]):
                if doc_id not in combined_ids:
                    combined_ids.append(doc_id)
                    combined_docs.append(keyword_results['documents'][0][i])
                    combined_metadatas.append(keyword_results['metadatas'][0][i])
                    combined_distances.append(keyword_results['distances'][0][i])
        
        # 組合最終結果
        results = {
            'ids': [combined_ids],
            'documents': [combined_docs],
            'metadatas': [combined_metadatas],
            'distances': [combined_distances]
        }
        
        # 分析結果
        if results['ids'] and len(results['ids'][0]) > 0:
            print("\n混合檢索結果:")
            print(f"總計找到 {len(results['ids'][0])} 筆相關結果")
            
            for i, (doc_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
                metadata = results['metadatas'][0][i] if i < len(results['metadatas'][0]) else {}
                title = metadata.get('title', '未知標題')
                
                # 檢查內容是否包含機密文件相關關鍵字
                content = results['documents'][0][i].lower()
                has_printer_keywords = '印表機' in content or '列印' in content or '打印' in content
                has_confidential_keywords = '機密' in content or 'confidential' in content
                has_action_keywords = '非禮勿視' in content or '碎紙機' in content or '通知' in content
                
                # 輸出結果
                print(f"結果 {i+1}: {title} (距離: {distance:.4f})")
                print(f"  ID: {doc_id}")
                
                # 輸出關鍵字匹配
                keywords_match = []
                if has_printer_keywords:
                    keywords_match.append("印表機/列印")
                if has_confidential_keywords:
                    keywords_match.append("機密")
                if has_action_keywords:
                    keywords_match.append("處理步驟")
                
                if keywords_match:
                    print(f"  ✓ 匹配關鍵字: {', '.join(keywords_match)}")
                else:
                    print(f"  ✗ 未匹配關鍵關鍵字")
                
                # 輸出內容預覽
                print(f"  內容預覽: {content[:300]}...")
                print("-" * 50)
        
        return results
    except Exception as e:
        logger.error(f"混合檢索失敗: {str(e)}")
        return {"error": str(e)}

def analyze_collection(collection_name: str = "scenarios", collection_path: str = "./chroma_db") -> Dict[str, Any]:
    """分析向量數據庫集合"""
    try:
        # 創建 ChromaDB 客戶端
        client = chromadb.PersistentClient(path=collection_path)
        
        # 獲取集合
        collection = client.get_collection(name=collection_name)
        
        # 獲取集合信息
        count = collection.count()
        print(f"集合中有 {count} 個項目")
        
        # 獲取所有項目ID
        all_ids = collection.get(limit=count)["ids"]
        
        # 統計項目類型
        metadata_all = collection.get(limit=count)["metadatas"]
        
        # 計算類別分布
        categories = {}
        for meta in metadata_all:
            category = meta.get("category", "未知")
            if category in categories:
                categories[category] += 1
            else:
                categories[category] = 1
        
        print("\n類別分布:")
        for category, count in categories.items():
            print(f"- {category}: {count} 筆")
        
        # 檢查是否有機密文件相關的文檔
        print("\n檢查機密文件相關文檔:")
        found = False
        
        # 嘗試使用關鍵字搜索
        queries = ["印表機", "機密文件", "confidential", "非禮勿視"]
        for query in queries:
            results = collection.query(
                query_texts=[query],
                n_results=1,
                include=["documents", "metadatas"]
            )
            
            if results['ids'] and len(results['ids'][0]) > 0:
                title = results['metadatas'][0][0].get('title', '未知標題')
                print(f"✓ 找到關鍵字 '{query}' 相關文檔: {title}")
                found = True
        
        if not found:
            print("✗ 未找到任何機密文件相關文檔")
        
        # 如果找到項目，顯示樣本數據
        print("\n文檔樣本:")
        sample_size = min(5, len(all_ids))
        sample_ids = all_ids[:sample_size]
        
        # 獲取樣本數據
        sample_data = collection.get(ids=sample_ids, include=["documents", "metadatas"])
        
        for i, (id, doc, metadata) in enumerate(zip(sample_data["ids"], sample_data["documents"], sample_data["metadatas"])):
            title = metadata.get("title", "未知標題")
            category = metadata.get("category", "未知類別")
            is_chunk = metadata.get("is_chunk", False)
            
            print(f"樣本 {i+1}: {id}")
            print(f"  標題: {title}")
            print(f"  類別: {category}")
            print(f"  分段: {'是' if is_chunk else '否'}")
            print(f"  內容 (前200字): {doc[:200]}...")
            print("-" * 40)
        
        return {
            "count": count,
            "categories": categories,
        }
    except Exception as e:
        logger.error(f"分析向量數據庫集合失敗: {str(e)}")
        return {"error": str(e)}

def main():
    """主函數"""
    print("=" * 60)
    print("RAG系統診斷工具 v2.0")
    print("=" * 60)
    
    # 0. 分析向量數據庫集合
    print("\n步驟 0: 分析向量數據庫集合")
    try:
        collection_info = analyze_collection()
    except Exception as e:
        print(f"集合分析失敗: {str(e)}")
    
    # 1. 測試向量相似度
    print("\n步驟 1: 測試向量相似度")
    original_question = "印表機發現無人拿走的機密文件該怎麼做?"
    similar_question = "列印機發現的機密資料應該如何處理?"
    dissimilar_question = "如何設定公司電子郵件?"
    
    try:
        sim1 = test_vector_similarity(original_question, similar_question)
        print(f"相似問題的相似度: {sim1:.4f}")
        
        sim2 = test_vector_similarity(original_question, dissimilar_question)
        print(f"不相似問題的相似度: {sim2:.4f}")
        
        if sim1 > sim2:
            print("✓ 向量化表現正常：相似問題相似度較高")
        else:
            print("✗ 向量化異常：不相似問題相似度高於或等於相似問題")
    except Exception as e:
        print(f"向量相似度測試失敗: {str(e)}")
    
    # 2. 測試關鍵問題檢索
    print("\n步驟 2: 測試關鍵問題檢索")
    test_queries = [
        "印表機發現無人拿走的機密文件該怎麼做?",
        "列印機的保密資料該如何處理?",
        "如何處理印表機列印出的機密資料?",
        "印表機機密文件處理",
    ]
    
    success_count = 0
    
    for query in test_queries:
        print(f"\n測試查詢: '{query}'")
        
        # 先測試向量檢索
        try:
            vector_results = test_chroma_retrieval(query)
            if vector_results.get('documents') and len(vector_results['documents'][0]) > 0:
                # 檢查結果是否包含關鍵字
                for doc in vector_results['documents'][0]:
                    if '印表機' in doc.lower() or '列印' in doc.lower():
                        if '機密' in doc.lower() or 'confidential' in doc.lower():
                            success_count += 1
                            break
        except Exception as e:
            print(f"向量檢索測試失敗: {str(e)}")
        
        # 再測試混合檢索
        try:
            hybrid_results = test_hybrid_retrieval(query)
        except Exception as e:
            print(f"混合檢索測試失敗: {str(e)}")
    
    # 輸出檢索成功率
    print(f"\n檢索成功率: {success_count}/{len(test_queries)} ({success_count/len(test_queries)*100:.2f}%)")
    if success_count == len(test_queries):
        print("✓ 所有關鍵問題都能被正確檢索")
    elif success_count > 0:
        print("⚠ 部分關鍵問題能被檢索，但仍需改進")
    else:
        print("✗ 所有關鍵問題都無法被正確檢索，檢索系統需要大幅改進")
    
    print("\n診斷完成!")

if __name__ == "__main__":
    main()
