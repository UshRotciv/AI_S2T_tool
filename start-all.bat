@echo off

echo Starting all services for Confidential Expert AI...

REM --- 執行資料同步 ---
echo 正在同步最新scenarios.json到ChromaDB...
cd ai-service && venv\Scripts\python ingest.py
cd ..
echo 資料同步完成！

REM --- Backend Server ---
echo Starting Backend Server (app-server) on port 3004...
start "Backend" cmd /k "cd app-server && npm run dev"

REM --- Frontend React App ---
echo Starting Frontend React App (client) on port 3002...
start "Frontend" cmd /k "cd client && npm start"

REM --- Ollama Service ---
echo Starting Ollama Service...
start "Ollama" cmd /k "ollama serve"

REM --- AI Service ---
echo Starting AI Service (ai-service) on port 8000...
start "AI Service" cmd /k "cd ai-service && venv\Scripts\activate && uvicorn main:app --reload --port 8000"

echo All services are launching in separate windows.
