#!/usr/bin/env python3
"""
基礎向量索引建立腳本 - 偵錯版本
用於診斷並修復RAG系統中的環境問題
"""
import sys
import os
import time
import subprocess
from datetime import datetime

# 設置日誌
log_file = "debug_log.txt"
with open(log_file, "a", encoding="utf-8") as f:
    f.write(f"\n===== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 開始執行環境診斷 =====\n")
    f.write(f"Python 路徑: {sys.executable}\n")
    f.write(f"Python 版本: {sys.version}\n")

# 步驟1: 確認Python環境
print("步驟1: 確認Python環境")
print(f"Python 路徑: {sys.executable}")
print(f"Python 版本: {sys.version}")

# 步驟2: 檢查已安裝的套件
print("\n步驟2: 檢查已安裝的套件")
try:
    result = subprocess.run([sys.executable, "-m", "pip", "list"], capture_output=True, text=True)
    print(result.stdout)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("\n已安裝套件:\n" + result.stdout + "\n")
except Exception as e:
    print(f"無法列出已安裝套件: {e}")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"無法列出已安裝套件: {e}\n")

# 步驟3: 嘗試安裝必要套件
print("\n步驟3: 嘗試安裝必要套件")
packages = ["chromadb", "numpy", "ollama"]

for package in packages:
    print(f"正在安裝 {package}...")
    try:
        start_time = time.time()
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package, "--user"],
            capture_output=True,
            text=True,
            timeout=60  # 設置60秒超時
        )
        end_time = time.time()
        
        if result.returncode == 0:
            print(f"{package} 安裝成功! 耗時: {end_time - start_time:.2f}秒")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{package} 安裝成功! 耗時: {end_time - start_time:.2f}秒\n")
        else:
            print(f"{package} 安裝失敗:\n{result.stderr}")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{package} 安裝失敗:\n{result.stderr}\n")
    except subprocess.TimeoutExpired:
        print(f"{package} 安裝超時! 已超過60秒")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{package} 安裝超時! 已超過60秒\n")
    except Exception as e:
        print(f"{package} 安裝出錯: {e}")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{package} 安裝出錯: {e}\n")

# 步驟4: 檢查模組是否可導入
print("\n步驟4: 檢查模組是否可導入")
modules = ["chromadb", "numpy", "ollama", "json", "uuid"]
success_count = 0

for module in modules:
    print(f"嘗試導入 {module}...")
    try:
        __import__(module)
        print(f"{module} 成功導入!")
        success_count += 1
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{module} 成功導入!\n")
    except ImportError as e:
        print(f"{module} 導入失敗: {e}")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{module} 導入失敗: {e}\n")

print(f"\n導入成功率: {success_count}/{len(modules)}")
with open(log_file, "a", encoding="utf-8") as f:
    f.write(f"\n導入成功率: {success_count}/{len(modules)}\n")

# 步驟5: 檢查系統路徑
print("\n步驟5: 檢查系統路徑")
for i, path in enumerate(sys.path):
    print(f"  {i+1}. {path}")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"  {i+1}. {path}\n")

# 步驟6: 提出解決方案
print("\n步驟6: 診斷結果與解決方案")
if success_count == len(modules):
    print("✓ 所有必要模組都已成功導入!")
    print("\n您可以繼續執行以下命令來重建索引:")
    print("  python basic_ingest.py")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("✓ 所有必要模組都已成功導入!\n")
        f.write("您可以繼續執行以下命令來重建索引:\n  python basic_ingest.py\n")
else:
    print("⚠ 部分模組導入失敗，建議嘗試以下解決方案:")
    print("  1. 啟用虛擬環境:")
    print("     .\\venv\\Scripts\\activate")
    print("  2. 重新安裝所有依賴:")
    print("     pip install -r requirements.txt")
    print("  3. 如果仍有問題，可以嘗試使用系統管理員權限:")
    print("     pip install chromadb --user")
    print("\n詳細診斷結果已保存至 debug_log.txt")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("⚠ 部分模組導入失敗，建議嘗試以下解決方案:\n")
        f.write("  1. 啟用虛擬環境:\n     .\\venv\\Scripts\\activate\n")
        f.write("  2. 重新安裝所有依賴:\n     pip install -r requirements.txt\n")
        f.write("  3. 如果仍有問題，可以嘗試使用系統管理員權限:\n     pip install chromadb --user\n")

with open(log_file, "a", encoding="utf-8") as f:
    f.write(f"\n===== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 診斷完成 =====\n")
