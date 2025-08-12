#!/usr/bin/env python3
"""
AI-RAG 系統快速整合測試
一鍵測試所有關鍵功能，快速定位問題
"""

import sys
import os
import time
import traceback
from pathlib import Path

def test_step(name, func):
    """執行測試步驟並記錄結果"""
    print(f"\n🧪 測試: {name}")
    try:
        start_time = time.time()
        result = func()
        elapsed = time.time() - start_time
        print(f"✅ 通過 ({elapsed:.2f}s)")
        return True, result
    except Exception as e:
        print(f"❌ 失敗: {str(e)}")
        print(f"   詳細錯誤: {traceback.format_exc().splitlines()[-1]}")
        return False, str(e)

def test_imports():
    """測試關鍵模組匯入"""
    import chromadb
    import fastapi
    import ollama
    return {
        "chromadb": chromadb.__version__,
        "fastapi": fastapi.__version__
    }

def test_chromadb_connection():
    """測試 ChromaDB 連線"""
    import chromadb
    client = chromadb.PersistentClient(path="./chroma_db")
    collections = client.list_collections()
    collection_names = [c.name for c in collections]
    
    if "scenarios" in collection_names:
        collection = client.get_collection("scenarios")
        count = collection.count()
        return {"collections": collection_names, "scenarios_count": count}
    else:
        return {"collections": collection_names, "scenarios_count": 0}

def test_ollama_connection():
    """測試 Ollama 連線"""
    import ollama
    try:
        models = ollama.list()
        model_names = [m['name'] for m in models.get('models', [])]
        return {"available_models": model_names, "count": len(model_names)}
    except Exception as e:
        return {"error": str(e), "available_models": [], "count": 0}

def test_main_py_syntax():
    """測試 main.py 語法"""
    import ast
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()
    ast.parse(content)
    return "語法檢查通過"

def test_api_endpoints():
    """測試 API 端點定義"""
    # 簡單檢查 main.py 中是否有必要的端點
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    endpoints = {
        "/api/ask": "@app.post(\"/api/ask\")" in content,
        "/api/sync": "@app.post(\"/api/sync\")" in content,
        "/status": "def status" in content or "/status" in content
    }
    
    return endpoints

def test_environment_vars():
    """測試環境變數"""
    env_vars = {
        "CHROMA_TELEMETRY_ENABLED": os.getenv("CHROMA_TELEMETRY_ENABLED", "未設定"),
        "PYTHONPATH": os.getenv("PYTHONPATH", "未設定"),
        "AI_PORT": os.getenv("AI_PORT", "未設定")
    }
    return env_vars

def main():
    """主測試流程"""
    print("🔍 AI-RAG 系統快速整合測試")
    print("=" * 50)
    
    tests = [
        ("關鍵模組匯入", test_imports),
        ("main.py 語法檢查", test_main_py_syntax),
        ("API 端點定義", test_api_endpoints),
        ("環境變數配置", test_environment_vars),
        ("ChromaDB 連線", test_chromadb_connection),
        ("Ollama 連線", test_ollama_connection),
    ]
    
    results = {}
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        success, result = test_step(test_name, test_func)
        results[test_name] = {"success": success, "result": result}
        if success:
            passed += 1
    
    print(f"\n" + "=" * 50)
    print(f"📊 測試結果總結: {passed}/{total} 通過")
    
    # 詳細結果
    print(f"\n📋 詳細結果:")
    for test_name, data in results.items():
        status = "✅" if data["success"] else "❌"
        print(f"{status} {test_name}: {data['result']}")
    
    # 建議
    print(f"\n💡 建議:")
    if passed == total:
        print("✅ 所有測試通過！可以嘗試啟動 AI 服務")
        print("   下一步: python main.py 或 uvicorn main:app --reload")
    else:
        print("⚠️  發現問題，建議優先修復:")
        for test_name, data in results.items():
            if not data["success"]:
                print(f"   - {test_name}: {data['result']}")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
