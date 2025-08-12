# ai-service/doctor_env.py
import sys, os, pkgutil, platform, subprocess, importlib

def run(cmd):
    try:
        print(">", " ".join(cmd))
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        print(out)
    except Exception as e:
        print("[!] run error:", e)

print("== Python 基本資訊 ==")
print("version :", sys.version)
print("exe     :", sys.executable)
print("platform:", platform.platform())
print("cwd     :", os.getcwd())
print()

print("== 尋找是否有本地遮蔽套件的檔案/資料夾 ==")
for name in ["chromadb", "chromadb.py"]:
    for root, dirs, files in os.walk(".", topdown=True):
        # 只掃兩層避免太慢
        depth = root.count(os.sep)
        if depth > 3:
            dirs[:] = []
            continue
        if name in dirs or name in files:
            print("[!] 可能遮蔽套件：", os.path.join(root, name))
print()

print("== 試著匯入 chromadb ==")
try:
    chromadb = importlib.import_module("chromadb")
    print("chromadb OK, version:", getattr(chromadb, "__version__", "unknown"))
except Exception as e:
    print("[X] import chromadb 失敗：", repr(e))

print()
print("== pip 套件狀態（精簡） ==")
for p in ["chromadb", "fastapi", "pydantic", "uvicorn", "sentence-transformers", "numpy"]:
    try:
        m = importlib.import_module(p.replace("-", "_"))
        print(f"{p:<22} OK   (from {getattr(m, '__file__', '?')})")
    except Exception as e:
        print(f"{p:<22} FAIL ({e})")

print()
print("== which pip / pip list ==")
run([sys.executable, "-m", "pip", "--version"])
run([sys.executable, "-m", "pip", "show", "chromadb"])
