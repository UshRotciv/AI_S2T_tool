#!/usr/bin/env python3
"""
Python 環境與 ChromaDB 依賴診斷腳本
"""
import sys
import os
import subprocess

print("="*30)
print("Python 環境診斷報告")
print("="*30)

# 1. Python 解譯器資訊
print(f"\n--- 1. Python 解譯器 ---")
python_executable = sys.executable
print(f"路徑: {python_executable}")
print(f"版本: {sys.version.split()[0]}")

# 2. 虛擬環境檢查
print(f"\n--- 2. 虛擬環境 (venv) 檢查 ---")
is_venv = hasattr(sys, 'prefix') and sys.prefix != sys.base_prefix
if is_venv:
    print(f"狀態: ✓ 已啟用虛擬環境")
    print(f"venv 路徑: {sys.prefix}")
else:
    print(f"狀態: ✗ 未啟用虛擬環境")
    # 檢查當前目錄是否存在 venv
    if os.path.isdir(os.path.join(os.getcwd(), 'venv')):
        print("提示: 在當前目錄下發現 'venv' 資料夾，但未啟用。")
        print("      請執行 '.\\venv\\Scripts\\activate' 來啟用它。")

# 3. sys.path 檢查
print(f"\n--- 3. 模組搜尋路徑 (sys.path) ---")
for i, path in enumerate(sys.path):
    print(f"  {i+1}. {path}")

# 4. ChromaDB 導入測試
print(f"\n--- 4. ChromaDB 導入測試 ---")
try:
    import chromadb
    print(f"狀態: ✓ 成功導入 chromadb 模組")
    print(f"chromadb 版本: {chromadb.__version__}")
    print(f"chromadb 路徑: {chromadb.__file__}")
except ImportError as e:
    print(f"狀態: ✗ 導入 chromadb 失敗: {e}")
except Exception as e:
    print(f"狀態: ✗ 導入時發生未知錯誤: {e}")

# 5. 已安裝套件列表 (pip list)
print(f"\n--- 5. 使用當前解譯器執行的 pip list ---")
try:
    result = subprocess.run(
        [python_executable, "-m", "pip", "list"],
        capture_output=True, text=True, check=True, encoding='utf-8'
    )
    print(result.stdout)
    if 'chromadb' not in result.stdout.lower():
        print("提示: 在 pip list 中未找到 'chromadb'。")
except FileNotFoundError:
    print("錯誤: 無法執行 'pip'。請確保 pip 已安裝並在 PATH 中。")
except subprocess.CalledProcessError as e:
    print(f"執行 pip list 失敗:\n{e.stderr}")
except Exception as e:
    print(f"執行 pip list 時發生未知錯誤: {e}")

print("\n" + "="*30)
print("診斷完成")
print("="*30)
