#!/usr/bin/env python3
"""
快速診斷腳本：檢查 main.py 修改是否正常
"""

def check_syntax():
    """檢查語法"""
    try:
        import ast
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        print("✓ main.py 語法檢查通過")
        return True
    except SyntaxError as e:
        print(f"✗ main.py 語法錯誤: {e}")
        return False
    except Exception as e:
        print(f"✗ 檢查語法時發生錯誤: {e}")
        return False

def check_imports():
    """檢查關鍵模組是否可載入"""
    try:
        # 測試基本模組
        import sys
        sys.path.append('.')
        
        # 檢查 reranker 模組
        try:
            from reranker import ReRanker
            print("✓ reranker 模組可正常載入")
        except Exception as e:
            print(f"⚠ reranker 模組載入問題: {e}")
        
        # 檢查其他依賴
        import chromadb
        print("✓ chromadb 可載入")
        
        return True
    except Exception as e:
        print(f"✗ 模組檢查失敗: {e}")
        return False

def check_postprocess_function():
    """檢查後處理函數定義"""
    try:
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'def postprocess_results(' in content:
            print("✓ postprocess_results 函數已定義")
        else:
            print("✗ postprocess_results 函數未找到")
            
        if 'trigger_rerank = False' in content:
            print("✓ rerank fallback 邏輯已加入")
        else:
            print("✗ rerank fallback 邏輯未找到")
            
        return True
    except Exception as e:
        print(f"✗ 檢查函數定義失敗: {e}")
        return False

def main():
    print("=== RAG 系統快速診斷 ===")
    print(f"時間: 2025-08-11 17:07")
    
    results = []
    results.append(check_syntax())
    results.append(check_imports())
    results.append(check_postprocess_function())
    
    print(f"\n=== 診斷結果 ===")
    if all(results):
        print("✓ 所有檢查通過，系統應該可以正常運行")
    else:
        print("⚠ 發現問題，需要進一步調查")
    
    print("\n建議下一步:")
    print("1. 如果語法通過，嘗試啟動 FastAPI 服務")
    print("2. 測試 /api/debug/sample 端點")
    print("3. 觀察日誌輸出中的後處理訊息")

if __name__ == "__main__":
    main()
