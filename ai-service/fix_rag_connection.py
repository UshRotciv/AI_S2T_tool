#!/usr/bin/env python3
"""
AI-RAG 連線問題修復腳本
快速診斷和修復 AI 服務與 RAG 資料庫的連線問題
"""

import sys
import os
import subprocess
import importlib

def print_status(message, status="INFO"):
    """列印狀態訊息"""
    symbols = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
    print(f"{symbols.get(status, 'ℹ️')} {message}")

def check_python_version():
    """檢查 Python 版本"""
    print_status(f"Python 版本: {sys.version}")
    if sys.version_info < (3, 8):
        print_status("Python 版本過舊，建議使用 3.8+", "WARNING")
        return False
    return True

def check_module(module_name):
    """檢查模組是否可以正常載入"""
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, '__version__', 'unknown')
        print_status(f"{module_name} 載入成功，版本: {version}", "SUCCESS")
        return True
    except ImportError as e:
        print_status(f"{module_name} 載入失敗: {e}", "ERROR")
        return False

def install_package(package_name, version=None):
    """安裝或重新安裝套件"""
    try:
        if version:
            cmd = [sys.executable, "-m", "pip", "install", f"{package_name}=={version}"]
        else:
            cmd = [sys.executable, "-m", "pip", "install", "--upgrade", package_name]
        
        print_status(f"正在安裝 {package_name}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print_status(f"{package_name} 安裝成功", "SUCCESS")
            return True
        else:
            print_status(f"{package_name} 安裝失敗: {result.stderr}", "ERROR")
            return False
    except Exception as e:
        print_status(f"安裝 {package_name} 時發生錯誤: {e}", "ERROR")
        return False

def test_chromadb_connection():
    """測試 ChromaDB 連線"""
    try:
        import chromadb
        
        # 測試建立客戶端
        client = chromadb.PersistentClient(path="./chroma_db")
        print_status("ChromaDB 客戶端建立成功", "SUCCESS")
        
        # 測試取得集合
        try:
            collection = client.get_collection("scenarios")
            count = collection.count()
            print_status(f"找到 scenarios 集合，包含 {count} 個文件", "SUCCESS")
            return True
        except Exception as e:
            print_status(f"scenarios 集合不存在或無法存取: {e}", "WARNING")
            print_status("可能需要重新執行 ingest.py 建立向量資料庫", "INFO")
            return False
            
    except Exception as e:
        print_status(f"ChromaDB 連線測試失敗: {e}", "ERROR")
        return False

def test_ollama_connection():
    """測試 Ollama 連線"""
    try:
        import ollama
        
        # 測試 Ollama 服務
        models = ollama.list()
        print_status("Ollama 服務連線成功", "SUCCESS")
        print_status(f"可用模型數量: {len(models.get('models', []))}", "INFO")
        return True
    except Exception as e:
        print_status(f"Ollama 連線測試失敗: {e}", "ERROR")
        return False

def main():
    """主要診斷和修復流程"""
    print("🔍 AI-RAG 連線問題診斷和修復")
    print("=" * 50)
    
    # 1. 檢查 Python 版本
    print_status("步驟 1: 檢查 Python 版本")
    if not check_python_version():
        return False
    
    # 2. 檢查關鍵模組
    print_status("步驟 2: 檢查關鍵模組")
    modules_to_check = {
        'fastapi': None,
        'chromadb': '0.4.24',
        'ollama': None,
        'uvicorn': None,
        'pydantic': None
    }
    
    failed_modules = []
    for module_name, preferred_version in modules_to_check.items():
        if not check_module(module_name):
            failed_modules.append((module_name, preferred_version))
    
    # 3. 修復失敗的模組
    if failed_modules:
        print_status("步驟 3: 修復失敗的模組")
        for module_name, version in failed_modules:
            if not install_package(module_name, version):
                print_status(f"無法修復 {module_name}，請手動處理", "ERROR")
                return False
            
            # 重新檢查
            if not check_module(module_name):
                print_status(f"{module_name} 安裝後仍無法載入", "ERROR")
                return False
    
    # 4. 測試 ChromaDB 連線
    print_status("步驟 4: 測試 ChromaDB 連線")
    chromadb_ok = test_chromadb_connection()
    
    # 5. 測試 Ollama 連線
    print_status("步驟 5: 測試 Ollama 連線")
    ollama_ok = test_ollama_connection()
    
    # 6. 總結
    print("\n" + "=" * 50)
    print("🎯 診斷結果總結")
    
    if chromadb_ok and ollama_ok:
        print_status("AI-RAG 連線修復成功！", "SUCCESS")
        print_status("建議重新啟動 AI 服務以確保變更生效", "INFO")
        return True
    else:
        print_status("仍有問題需要解決:", "WARNING")
        if not chromadb_ok:
            print_status("- ChromaDB 連線問題", "ERROR")
        if not ollama_ok:
            print_status("- Ollama 連線問題", "ERROR")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
