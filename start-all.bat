@echo off
chcp 65001 > nul

:: Set the base directory to where the script is located
set "BASE_DIR=%~dp0"

:: Set window titles
set "OLLAMA_TITLE=Ollama Service"
set "AI_SERVICE_TITLE=AI Service (Python/FastAPI)"
set "APP_SERVER_TITLE=App Server (Node.js)"
set "CLIENT_TITLE=Client (React App)"

echo =================================================================
echo  Confidential Expert AI - Service Launcher
echo =================================================================
echo.
echo Launching all 4 services in separate windows...
echo Base directory: %BASE_DIR%
echo.

:: --- 1. Launch Ollama Service ---
echo [1/4] Launching Ollama Service...
echo      (First, ensuring the embedding model 'mxbai-embed-large' is available...)
start "%OLLAMA_TITLE%" cmd /k "ollama pull mxbai-embed-large && echo Model pull complete. Starting server... && ollama serve"

:: --- 2. Launch AI Service ---
echo [2/4] Launching AI Service (Python/FastAPI)...
start "%AI_SERVICE_TITLE%" /D "%BASE_DIR%ai-service" cmd /k "echo Activating virtual environment & call .\venv\Scripts\activate && echo Installing Python dependencies... & pip install -r requirements.txt && echo Starting FastAPI server... & uvicorn main:app --host 0.0.0.0 --port 8000"

echo.
echo Waiting for 10 seconds to allow AI service to initialize...
timeout /t 10 /nobreak
echo.

:: --- 3. Launch App Server ---
echo [3/4] Launching App Server (Node.js)...
start "%APP_SERVER_TITLE%" /D "%BASE_DIR%app-server" cmd /k "echo Installing Node.js dependencies... & npm install && echo Starting Node.js server... & node index.js"

:: --- 4. Launch Client ---
echo [4/4] Launching Client (React App)...
start "%CLIENT_TITLE%" /D "%BASE_DIR%client" cmd /k "echo Installing Node.js dependencies... & npm install --legacy-peer-deps && echo Starting React development server... & npm run start"

echo.
echo =================================================================
echo  All services have been launched.
echo  Please check the 4 new windows for status and logs.
echo =================================================================
