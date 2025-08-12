#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
進階檢索診斷工具 - 測試查詢擴展與分層檢索策略
專門用於診斷「作品集」等短查詢的精準度問題
"""

import os
import chromadb
from chromadb.utils import embedding_functions

# 路徑設定
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, 'chroma_db')

def init_collection():
    """初始化 ChromaDB 連接"""
    client = chromadb.PersistentClient(path=DB_PATH)
    
    sentence_transformer_ef = embedding_functions.OllamaEmbeddingFunction(
        model_name="mxbai-embed-large",
        url="http://localhost:11434",
    )
    
    try:
        collection = client.get_collection(
            "scenarios",
            embedding_function=sentence_transformer_ef
        )
        print("成功連接到 scenarios 集合")
        return collection
    except Exception as e:
        print(f"連接集合失敗: {e}")
        return None

def expand_query(original_query):
    """
    查詢擴展函式 - 針對短查詢生成更具體的相關查詢
    """
    expansions = {
        "作品集": [
            "準備作品集的資安注意事項",
            "對外公開作品集的規範", 
            "未採用提案是否可放進作品集",
            "作品集避免洩露公司機密",
            "個人作品集與智慧財產權",
            "員工作品集公開限制",
            "設計提案作品集規範"
        ],
        "印表機": [
            "印表機機密文件處理",
            "印表機列印機密資料",
            "印表機安全使用規範",
            "機密文件印表機操作"
        ],
        "測試軟體": [
            "免費測試軟體風險",
            "測試軟體安全性",
            "軟體測試安全規範",
            "免費軟體使用風險"
        ]
    }
    
    # 檢查是否有預定義的擴展
    for key, values in expansions.items():
        if key in original_query:
            print(f"為查詢 '{original_query}' 找到擴展詞組:")
            for i, expansion in enumerate(values, 1):
                print(f"   {i}. {expansion}")
            return [original_query] + values
    
    # 如果沒有預定義擴展，返回原查詢
    print(f"查詢 '{original_query}' 未找到擴展詞組，使用原查詢")
    return [original_query]

def layered_search(collection, query, max_results=10):
    """
    分層檢索策略
    第一層：scenario 情境卡優先
    第二層：排除 rule_document
    第三層：全庫檢索
    """
    print(f"\n{'='*60}")
    print(f"開始分層檢索: '{query}'")
    print(f"{'='*60}")
    
    results_summary = {
        "query": query,
        "layers": []
    }
    
    # 第一層：scenario 情境卡優先
    print(f"\n第一層檢索: scenario 情境卡優先")
    try:
        layer1_results = collection.query(
            query_texts=[query],
            n_results=max_results,
            where={"category": "scenario_card"},
            include=["documents", "metadatas", "distances"]
        )
        
        layer1_count = len(layer1_results['ids'][0]) if layer1_results.get('ids') and layer1_results['ids'][0] else 0
        print(f"   找到 {layer1_count} 個 scenario 情境卡")
        
        if layer1_count > 0:
            print_search_results(layer1_results, "第一層 (scenario)")
            results_summary["layers"].append({
                "layer": 1,
                "description": "scenario 情境卡",
                "count": layer1_count,
                "results": format_results_for_summary(layer1_results)
            })
            return layer1_results, results_summary
            
    except Exception as e:
        print(f"   第一層檢索失敗: {e}")
    
    # 第二層：排除 rule_document
    print(f"\n第二層檢索: 排除 rule_document")
    try:
        layer2_results = collection.query(
            query_texts=[query],
            n_results=max_results,
            where={"category": {"$ne": "rule_document"}},
            include=["documents", "metadatas", "distances"]
        )
        
        layer2_count = len(layer2_results['ids'][0]) if layer2_results.get('ids') and layer2_results['ids'][0] else 0
        print(f"   找到 {layer2_count} 個文件 (排除 rule_document)")
        
        if layer2_count > 0:
            print_search_results(layer2_results, "第二層 (排除 rule_document)")
            results_summary["layers"].append({
                "layer": 2,
                "description": "排除 rule_document",
                "count": layer2_count,
                "results": format_results_for_summary(layer2_results)
            })
            return layer2_results, results_summary
            
    except Exception as e:
        print(f"   第二層檢索失敗: {e}")
    
    # 第三層：全庫檢索
    print(f"\n第三層檢索: 全庫檢索")
    try:
        layer3_results = collection.query(
            query_texts=[query],
            n_results=max_results,
            include=["documents", "metadatas", "distances"]
        )
        
        layer3_count = len(layer3_results['ids'][0]) if layer3_results.get('ids') and layer3_results['ids'][0] else 0
        print(f"   找到 {layer3_count} 個文件 (全庫)")
        
        if layer3_count > 0:
            print_search_results(layer3_results, "第三層 (全庫)")
            results_summary["layers"].append({
                "layer": 3,
                "description": "全庫檢索",
                "count": layer3_count,
                "results": format_results_for_summary(layer3_results)
            })
            return layer3_results, results_summary
            
    except Exception as e:
        print(f"   第三層檢索失敗: {e}")
    
    print(f"   所有層級檢索都無結果")
    return None, results_summary

def print_search_results(results, layer_name):
    """印出檢索結果的詳細資訊"""
    if not results or not results.get('ids') or not results['ids'][0]:
        print(f"   {layer_name}: 無結果")
        return
    
    print(f"\n{layer_name} 詳細結果:")
    for i, doc_id in enumerate(results['ids'][0]):
        metadata = results['metadatas'][0][i] if results.get('metadatas') and results['metadatas'][0] else {}
        distance = results['distances'][0][i] if results.get('distances') and results['distances'][0] else None
        document = results['documents'][0][i] if results.get('documents') and results['documents'][0] else ""
        
        title = metadata.get('title', '未知標題')
        category = metadata.get('category', '未知類別')
        question = metadata.get('question', '未知問題')
        
        print(f"\n   結果 {i+1}:")
        print(f"     標題: {title}")
        print(f"     類別: {category}")
        print(f"     問題: {question}")
        print(f"     距離: {distance:.4f}" if distance is not None else "     距離: 未知")
        print(f"     內容預覽: {document[:150]}...")
        
        # 檢查關鍵詞
        content_lower = document.lower()
        keywords_found = []
        if '作品集' in content_lower:
            keywords_found.append('作品集')
        if '智慧財產' in content_lower or '智慧財產權' in content_lower:
            keywords_found.append('智慧財產權')
        if '未採用' in content_lower:
            keywords_found.append('未採用')
        if '公開' in content_lower:
            keywords_found.append('公開')
        if '提案' in content_lower:
            keywords_found.append('提案')
        
        if keywords_found:
            print(f"     關鍵詞命中: {', '.join(keywords_found)}")

def format_results_for_summary(results):
    """格式化結果用於摘要"""
    if not results or not results.get('ids') or not results['ids'][0]:
        return []
    
    formatted = []
    for i, doc_id in enumerate(results['ids'][0]):
        metadata = results['metadatas'][0][i] if results.get('metadatas') and results['metadatas'][0] else {}
        distance = results['distances'][0][i] if results.get('distances') and results['distances'][0] else None
        
        formatted.append({
            "id": doc_id,
            "title": metadata.get('title', '未知標題'),
            "category": metadata.get('category', '未知類別'),
            "distance": distance
        })
    
    return formatted

def comprehensive_search_test(collection, original_query):
    """
    綜合搜尋測試 - 結合查詢擴展與分層檢索
    """
    print(f"\n{'='*80}")
    print(f"開始綜合搜尋測試")
    print(f"原始查詢: '{original_query}'")
    print(f"{'='*80}")
    
    # 步驟1: 查詢擴展
    expanded_queries = expand_query(original_query)
    
    # 步驟2: 對每個擴展查詢進行分層檢索
    all_results = []
    best_result = None
    best_score = float('inf')
    
    for i, query in enumerate(expanded_queries):
        print(f"\n測試查詢 {i+1}/{len(expanded_queries)}: '{query}'")
        
        result, summary = layered_search(collection, query, max_results=5)
        
        if result and result.get('distances') and result['distances'][0]:
            min_distance = min(result['distances'][0])
            if min_distance < best_score:
                best_score = min_distance
                best_result = (query, result, summary)
        
        all_results.append((query, result, summary))
    
    # 步驟3: 分析結果
    print(f"\n{'='*80}")
    print(f"綜合分析結果")
    print(f"{'='*80}")
    
    if best_result:
        best_query, best_search_result, best_summary = best_result
        print(f"最佳查詢: '{best_query}'")
        print(f"最佳距離: {best_score:.4f}")
        
        # 檢查最佳結果是否包含 scenario 情境卡
        scenario_count = 0
        if best_search_result.get('metadatas') and best_search_result['metadatas'][0]:
            for metadata in best_search_result['metadatas'][0]:
                if metadata.get('category') == 'scenario_card':
                    scenario_count += 1
        
        print(f"scenario 情境卡命中數: {scenario_count}")
        
        if scenario_count > 0:
            print(f"成功！找到相關的 scenario 情境卡")
        else:
            print(f"警告：未找到 scenario 情境卡，可能需要調整策略")
    else:
        print(f"所有查詢都無結果")
    
    return all_results

def postprocess_results_test(results, distance_threshold=0.40, max_per_group=2):
    """測試後處理效果（與 main.py 同步）"""
    if not results or not results.get('ids') or not results['ids'] or not results['ids'][0]:
        return results, 0, 0
    
    before_count = len(results['ids'][0])
    
    ids = results['ids'][0]
    docs = results['documents'][0] if results.get('documents') and results['documents'] else []
    mds = results['metadatas'][0] if results.get('metadatas') and results['metadatas'] else []
    dists = results['distances'][0] if results.get('distances') and results['distances'] else []
    
    items = []
    for i, doc_id in enumerate(ids):
        items.append({
            'id': doc_id,
            'document': docs[i] if i < len(docs) else "",
            'metadata': mds[i] if i < len(mds) else {},
            'distance': dists[i] if i < len(dists) else None,
        })
    
    # 1) 距離門檻過濾
    filtered = [it for it in items if (it['distance'] is None or it['distance'] < distance_threshold)]
    
    # 2) 分組去重（避免 ungrouped 問題）
    from collections import defaultdict
    groups = defaultdict(list)
    for it in filtered:
        md = it.get('metadata') or {}
        base_key = md.get('parent_id') or md.get('title')
        key = base_key if base_key else f"__ungrouped__{it['id']}"
        groups[key].append(it)
    
    selected = []
    for key, arr in groups.items():
        arr_sorted = sorted(arr, key=lambda x: (float('inf') if x.get('distance') is None else x['distance']))
        selected.extend(arr_sorted[:max_per_group])
    
    after_count = len(selected)
    
    new_results = {
        'ids': [[it['id'] for it in selected]],
        'documents': [[it.get('document', "") for it in selected]],
        'metadatas': [[it.get('metadata', {}) for it in selected]],
        'distances': [[it.get('distance') for it in selected]],
    }
    
    return new_results, before_count, after_count

def main():
    """主函式 - 加入後處理效果測試"""
    collection = init_collection()
    if not collection:
        return
    
    # 測試查詢列表
    test_queries = [
        "作品集",
        "印表機 機密 文件", 
        "USB 隨身碟",
        "密碼管理",
        "電子郵件 附件"
    ]
    
    print("=== 進階檢索診斷開始（含後處理測試）===")
    print(f"測試查詢數量: {len(test_queries)}")
    print(f"後處理參數: threshold=0.40, max_per_group=2")
    print("-" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n【測試 {i}/{len(test_queries)}】查詢: {query}")
        
        # 原始檢索測試
        comprehensive_search_test(collection, query)
        
        # 後處理效果測試
        print("\n--- 後處理效果測試 ---")
        try:
            results = collection.query(
                query_texts=[query],
                n_results=10,
                include=["documents", "metadatas", "distances"]
            )
            
            processed_results, before, after = postprocess_results_test(results)
            
            # 距離統計
            if results.get('distances') and results['distances'] and results['distances'][0]:
                dists = [d for d in results['distances'][0] if d is not None]
                if dists:
                    min_dist = min(dists)
                    mean_dist = sum(dists) / len(dists)
                    print(f"原始結果: {before} 筆, min_dist={min_dist:.3f}, mean_dist={mean_dist:.3f}")
                    
                    # 評估是否會觸發 rerank
                    would_rerank = False
                    if after == 0:
                        would_rerank = False
                    elif min_dist < 0.28:
                        would_rerank = False
                    elif after < 5 and min_dist > 0.36:
                        would_rerank = True
                    
                    print(f"後處理後: {after} 筆, 會觸發 rerank: {would_rerank}")
        except Exception as e:
            print(f"後處理測試失敗: {e}")
        
        print("-" * 60)
    
    print("\n=== 診斷完成 ===")
    print("觀察重點:")
    print("1. 後處理前後數量變化是否合理")
    print("2. rerank 觸發頻率是否適中")
    print("3. 距離分佈是否符合預期")

if __name__ == "__main__":
    main()
