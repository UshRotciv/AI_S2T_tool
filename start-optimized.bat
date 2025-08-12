@echo off
echo.
echo ==========================================
echo    RAG System Optimized Launcher
echo ==========================================
echo.

echo [1/5] Cleaning up processes...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/5] Starting Ollama (required for AI)...
ollama --version >nul 2>&1
if not errorlevel 1 (
    start "Ollama Service" cmd /k "ollama serve"
    echo Waiting for Ollama to start...
    timeout /t 10 /nobreak >nul
    echo OK: Ollama should be ready
) else (
    echo ERROR: Ollama not found! AI Service will fail without Ollama.
    echo Please install Ollama first: https://ollama.ai
    pause
    exit /b 1
)

echo [3/5] Starting AI Service (optimized)...
cd ai-service
echo Starting AI Service with optimizations...
start "AI Service" cmd /k "call venv\Scripts\activate && echo Starting AI Service... && python main.py"
cd ..

echo Waiting for AI Service to initialize...
echo This may take 30-60 seconds for first startup...
timeout /t 45 /nobreak >nul

echo [4/5] Testing AI Service...
python quick_ai_test.py
if errorlevel 1 (
    echo WARNING: AI Service test failed, but continuing...
) else (
    echo OK: AI Service test passed!
)

echo [5/5] Starting remaining services...
cd app-server
start "App Server" cmd /k "npm start"
cd ..

timeout /t 10 /nobreak >nul

cd client
start "React Client" cmd /k "npm start"
cd ..

echo.
echo ==========================================
echo           Optimized Startup Complete!
echo ==========================================
echo.
echo Service URLs:
echo   * Ollama Service:     http://localhost:11434
echo   * AI Service:         http://localhost:8001
echo   * Backend Service:    http://localhost:3001
echo   * Frontend Interface: http://localhost:3000
echo.
echo Please wait for all services to fully load, then test:
echo http://localhost:3000
echo.
echo If AI is still not working, run: python quick_ai_test.py
echo.
pause
