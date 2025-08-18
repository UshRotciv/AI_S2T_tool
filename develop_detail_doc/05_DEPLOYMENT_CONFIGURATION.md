# 部署與配置文檔

## 系統部署架構

### 服務端口配置
- **前端服務**: http://localhost:3002 (React開發服務器)
- **後端API**: http://localhost:3001 (Node.js Express)
- **AI服務**: http://localhost:8000 (Python FastAPI)
- **Ollama服務**: http://localhost:11434 (LLM服務)

### Docker Compose配置

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  # 前端服務
  client:
    build:
      context: ./client
      dockerfile: Dockerfile
    ports:
      - "3002:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:3001
      - REACT_APP_AI_SERVICE_URL=http://localhost:8000
    volumes:
      - ./client:/app
      - /app/node_modules
    depends_on:
      - app-server
      - ai-service

  # 後端API服務
  app-server:
    build:
      context: ./app-server
      dockerfile: Dockerfile
    ports:
      - "3001:3001"
    environment:
      - NODE_ENV=production
      - PORT=3001
      - DB_PATH=/app/data/database.db
    volumes:
      - ./app-server:/app
      - app_data:/app/data
    depends_on:
      - ai-service

  # AI服務
  ai-service:
    build:
      context: ./ai-service
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - PYTHONPATH=/app
      - CHROMA_DB_PATH=/app/data/chroma_db
      - OLLAMA_URL=http://host.docker.internal:11434
    volumes:
      - ./ai-service:/app
      - ai_data:/app/data
    depends_on:
      - ollama

  # Ollama LLM服務
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_MODELS=/root/.ollama/models

volumes:
  app_data:
  ai_data:
  ollama_data:
```

## 一鍵啟動腳本

### Windows批處理腳本 (start-all.bat)

```batch
@echo off
echo ========================================
echo   ADC資安情境庫 - 系統啟動腳本
echo ========================================

echo.
echo [1/4] 檢查系統環境...
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo 錯誤: 未找到 Node.js，請先安裝 Node.js 18+
    pause
    exit /b 1
)

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo 錯誤: 未找到 Python，請先安裝 Python 3.9+
    pause
    exit /b 1
)

echo Node.js 和 Python 環境檢查通過

echo.
echo [2/4] 啟動 Ollama 服務...
start "Ollama Service" cmd /c "ollama serve"
timeout /t 5 /nobreak >nul

echo.
echo [3/4] 啟動後端服務...
start "App Server" cmd /c "cd app-server && npm install && npm start"
timeout /t 10 /nobreak >nul

echo.
echo [4/4] 啟動AI服務...
start "AI Service" cmd /c "cd ai-service && python -m pip install -r requirements.txt && python main.py"
timeout /t 15 /nobreak >nul

echo.
echo [5/5] 啟動前端服務...
start "Frontend" cmd /c "cd client && npm install && npm start"

echo.
echo ========================================
echo   所有服務啟動完成！
echo ========================================
echo.
echo 服務地址:
echo   前端界面: http://localhost:3002
echo   後端API:  http://localhost:3001
echo   AI服務:   http://localhost:8000
echo   Ollama:   http://localhost:11434
echo.
echo 請等待所有服務完全啟動後再訪問前端界面
echo 按任意鍵退出...
pause >nul
```

### Linux/macOS啟動腳本 (start-all.sh)

```bash
#!/bin/bash

echo "========================================"
echo "  ADC資安情境庫 - 系統啟動腳本"
echo "========================================"

# 檢查依賴
check_dependency() {
    if ! command -v $1 &> /dev/null; then
        echo "錯誤: 未找到 $1，請先安裝"
        exit 1
    fi
}

echo
echo "[1/5] 檢查系統環境..."
check_dependency "node"
check_dependency "python3"
check_dependency "ollama"
echo "環境檢查通過"

echo
echo "[2/5] 啟動 Ollama 服務..."
ollama serve &
OLLAMA_PID=$!
sleep 5

echo
echo "[3/5] 啟動後端服務..."
cd app-server
npm install
npm start &
APP_SERVER_PID=$!
cd ..
sleep 10

echo
echo "[4/5] 啟動AI服務..."
cd ai-service
python3 -m pip install -r requirements.txt
python3 main.py &
AI_SERVICE_PID=$!
cd ..
sleep 15

echo
echo "[5/5] 啟動前端服務..."
cd client
npm install
npm start &
CLIENT_PID=$!
cd ..

echo
echo "========================================"
echo "  所有服務啟動完成！"
echo "========================================"
echo
echo "服務地址:"
echo "  前端界面: http://localhost:3002"
echo "  後端API:  http://localhost:3001"
echo "  AI服務:   http://localhost:8000"
echo "  Ollama:   http://localhost:11434"
echo
echo "進程ID:"
echo "  Ollama: $OLLAMA_PID"
echo "  App Server: $APP_SERVER_PID"
echo "  AI Service: $AI_SERVICE_PID"
echo "  Client: $CLIENT_PID"
echo
echo "按 Ctrl+C 停止所有服務"

# 等待中斷信號
trap 'kill $OLLAMA_PID $APP_SERVER_PID $AI_SERVICE_PID $CLIENT_PID; exit' INT
wait
```

## 環境配置

### 前端環境變量 (.env)

```bash
# client/.env
REACT_APP_API_URL=http://localhost:3001
REACT_APP_AI_SERVICE_URL=http://localhost:8000
REACT_APP_VERSION=2.0.0
REACT_APP_TITLE=ADC資安情境庫
GENERATE_SOURCEMAP=false
```

### 後端環境變量 (.env)

```bash
# app-server/.env
NODE_ENV=production
PORT=3001
DB_PATH=./database.db
CORS_ORIGIN=http://localhost:3002
LOG_LEVEL=info
MAX_REQUEST_SIZE=50mb
```

### AI服務環境變量 (.env)

```bash
# ai-service/.env
PYTHONPATH=/app
CHROMA_DB_PATH=./chroma_db
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
EMBEDDING_MODEL=all-MiniLM-L6-v2
MAX_CONTEXT_LENGTH=4000
SIMILARITY_THRESHOLD=0.7
LOG_LEVEL=INFO
```

## 系統初始化

### 數據庫初始化腳本

**app-server/scripts/init-database.js**:
```javascript
const sqlite3 = require('sqlite3').verbose();
const fs = require('fs');
const path = require('path');

function initializeDatabase() {
    const dbPath = './database.db';
    const db = new sqlite3.Database(dbPath);
    
    console.log('初始化數據庫...');
    
    // 創建表結構
    db.serialize(() => {
        // 情境表
        db.run(`
            CREATE TABLE IF NOT EXISTS scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                key_points TEXT DEFAULT '[]',
                difficulty TEXT DEFAULT '中級',
                tags TEXT DEFAULT '[]',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        `);
        
        // 分類表
        db.run(`
            CREATE TABLE IF NOT EXISTS categories (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                color TEXT DEFAULT '#757575',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        `);
        
        // 插入默認分類
        const categories = [
            ['A', '基礎安全', '基本的資訊安全概念', '#2196F3'],
            ['B', '網路安全', '網路相關的安全議題', '#4CAF50'],
            ['C', '系統安全', '作業系統與應用程式安全', '#FF9800'],
            ['D', '進階防護', '高級安全技術與策略', '#9C27B0']
        ];
        
        const stmt = db.prepare(`
            INSERT OR REPLACE INTO categories (id, name, description, color)
            VALUES (?, ?, ?, ?)
        `);
        
        categories.forEach(category => {
            stmt.run(category);
        });
        
        stmt.finalize();
        
        // 導入情境數據
        if (fs.existsSync('./scenarios.json')) {
            const scenarios = JSON.parse(fs.readFileSync('./scenarios.json', 'utf8'));
            
            const scenarioStmt = db.prepare(`
                INSERT OR REPLACE INTO scenarios 
                (id, title, category, question, answer, key_points, difficulty, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            `);
            
            scenarios.forEach(scenario => {
                scenarioStmt.run([
                    scenario.id,
                    scenario.title,
                    scenario.category,
                    scenario.question,
                    scenario.answer,
                    JSON.stringify(scenario.keyPoints || []),
                    scenario.difficulty || '中級',
                    JSON.stringify(scenario.tags || [])
                ]);
            });
            
            scenarioStmt.finalize();
            console.log(`導入 ${scenarios.length} 個情境數據`);
        }
    });
    
    db.close((err) => {
        if (err) {
            console.error('數據庫關閉錯誤:', err);
        } else {
            console.log('數據庫初始化完成');
        }
    });
}

if (require.main === module) {
    initializeDatabase();
}

module.exports = { initializeDatabase };
```

### AI服務初始化腳本

**ai-service/init_service.py**:
```python
#!/usr/bin/env python3
"""AI服務初始化腳本"""

import os
import json
import requests
import chromadb
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_ollama_service():
    """檢查Ollama服務是否運行"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            logger.info("Ollama服務運行正常")
            return True
    except requests.exceptions.RequestException:
        logger.error("Ollama服務未運行，請先啟動Ollama")
        return False

def download_ollama_model(model_name="llama3.1:8b"):
    """下載Ollama模型"""
    logger.info(f"檢查模型 {model_name}...")
    
    try:
        # 檢查模型是否已存在
        response = requests.get("http://localhost:11434/api/tags")
        models = response.json().get("models", [])
        
        if any(model["name"] == model_name for model in models):
            logger.info(f"模型 {model_name} 已存在")
            return True
        
        # 下載模型
        logger.info(f"開始下載模型 {model_name}，這可能需要幾分鐘...")
        response = requests.post(
            "http://localhost:11434/api/pull",
            json={"name": model_name},
            stream=True,
            timeout=1800  # 30分鐘超時
        )
        
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                if "status" in data:
                    print(f"\r{data['status']}", end="", flush=True)
        
        print()  # 換行
        logger.info(f"模型 {model_name} 下載完成")
        return True
        
    except Exception as e:
        logger.error(f"下載模型失敗: {e}")
        return False

def initialize_embedding_model():
    """初始化嵌入模型"""
    logger.info("初始化嵌入模型...")
    try:
        model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("嵌入模型初始化完成")
        return model
    except Exception as e:
        logger.error(f"嵌入模型初始化失敗: {e}")
        return None

def initialize_chromadb():
    """初始化ChromaDB"""
    logger.info("初始化ChromaDB...")
    try:
        client = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_or_create_collection(
            name="cybersecurity_scenarios",
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("ChromaDB初始化完成")
        return client, collection
    except Exception as e:
        logger.error(f"ChromaDB初始化失敗: {e}")
        return None, None

def ingest_initial_data():
    """攝取初始數據"""
    logger.info("開始數據攝取...")
    
    # 檢查是否存在情境數據文件
    scenarios_file = "../app-server/scenarios.json"
    if not os.path.exists(scenarios_file):
        logger.warning("未找到情境數據文件，跳過數據攝取")
        return
    
    # 執行數據攝取
    try:
        from ingest import main as ingest_main
        ingest_main()
        logger.info("數據攝取完成")
    except Exception as e:
        logger.error(f"數據攝取失敗: {e}")

def main():
    """主初始化流程"""
    logger.info("開始AI服務初始化...")
    
    # 1. 檢查Ollama服務
    if not check_ollama_service():
        logger.error("初始化失敗: Ollama服務未運行")
        return False
    
    # 2. 下載LLM模型
    if not download_ollama_model():
        logger.error("初始化失敗: 模型下載失敗")
        return False
    
    # 3. 初始化嵌入模型
    embedding_model = initialize_embedding_model()
    if embedding_model is None:
        logger.error("初始化失敗: 嵌入模型初始化失敗")
        return False
    
    # 4. 初始化ChromaDB
    client, collection = initialize_chromadb()
    if client is None:
        logger.error("初始化失敗: ChromaDB初始化失敗")
        return False
    
    # 5. 攝取初始數據
    ingest_initial_data()
    
    logger.info("AI服務初始化完成！")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
```

## 健康檢查與監控

### 健康檢查端點

**各服務健康檢查**:
```python
# AI服務健康檢查
@app.get("/health")
async def health_check():
    """健康檢查端點"""
    try:
        # 檢查ChromaDB
        collection.count()
        
        # 檢查Ollama
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        ollama_status = response.status_code == 200
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "chromadb": "healthy",
                "ollama": "healthy" if ollama_status else "unhealthy",
                "embedding_model": "healthy"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
```

### 系統監控腳本

**monitor_system.py**:
```python
#!/usr/bin/env python3
"""系統監控腳本"""

import requests
import time
import json
from datetime import datetime

SERVICES = {
    "frontend": "http://localhost:3002",
    "backend": "http://localhost:3001/api/scenarios",
    "ai_service": "http://localhost:8000/health",
    "ollama": "http://localhost:11434/api/tags"
}

def check_service(name, url):
    """檢查單個服務狀態"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return {"status": "healthy", "response_time": response.elapsed.total_seconds()}
        else:
            return {"status": "unhealthy", "status_code": response.status_code}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": str(e)}

def monitor_loop():
    """監控循環"""
    while True:
        timestamp = datetime.now().isoformat()
        results = {"timestamp": timestamp, "services": {}}
        
        for service_name, url in SERVICES.items():
            results["services"][service_name] = check_service(service_name, url)
        
        # 輸出結果
        print(json.dumps(results, indent=2, ensure_ascii=False))
        
        # 檢查是否有服務異常
        unhealthy_services = [
            name for name, status in results["services"].items()
            if status["status"] != "healthy"
        ]
        
        if unhealthy_services:
            print(f"警告: 以下服務異常: {', '.join(unhealthy_services)}")
        
        time.sleep(30)  # 30秒檢查一次

if __name__ == "__main__":
    print("開始系統監控...")
    monitor_loop()
```

## 故障排除指南

### 常見問題與解決方案

1. **端口衝突**
   ```bash
   # 檢查端口占用
   netstat -ano | findstr :3001
   netstat -ano | findstr :3002
   netstat -ano | findstr :8000
   
   # 終止占用進程
   taskkill /PID <PID> /F
   ```

2. **Ollama模型下載失敗**
   ```bash
   # 手動下載模型
   ollama pull llama3.1:8b
   
   # 檢查模型列表
   ollama list
   ```

3. **ChromaDB權限問題**
   ```bash
   # 修復權限
   chmod -R 755 ./chroma_db
   chown -R $USER:$USER ./chroma_db
   ```

4. **Node.js依賴問題**
   ```bash
   # 清理並重新安裝
   rm -rf node_modules package-lock.json
   npm install
   ```

---

**文檔版本**: 1.0  
**最後更新**: 2025-08-13  
**維護團隊**: DevOps團隊
