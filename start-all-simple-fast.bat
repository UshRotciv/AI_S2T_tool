@echo off
setlocal enabledelayedexpansion

echo.
echo ==========================================
echo    RAG AI System Launcher (Fast Version)
echo ==========================================
echo.

REM Create logs directory
if not exist logs mkdir logs
set LOG_FILE=logs\startup_fast.log

echo [%date% %time%] Starting RAG System >> %LOG_FILE%
echo Log file: %LOG_FILE%

echo [1/5] Cleaning up old processes...
echo [%date% %time%] Starting port cleanup >> %LOG_FILE%

REM Force kill processes that might occupy ports
for %%p in (11434 8001 3001 3000 3002) do (
    echo Cleaning port %%p...
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr :%%p') do (
        taskkill /f /pid %%a >nul 2>&1
    )
)

timeout /t 2 /nobreak >nul

echo [2/5] Starting AI Service...
echo [%date% %time%] Starting AI Service >> %LOG_FILE%
cd ai-service

REM Activate virtual environment and start AI Service
call venv\Scripts\activate
start "AI Service" cmd /c "call venv\Scripts\activate && python main.py"
cd ..

REM Simple wait for AI Service
echo Waiting for AI Service (15 seconds)...
timeout /t 15 /nobreak >nul

echo [3/5] Starting App Server...
echo [%date% %time%] Starting App Server >> %LOG_FILE%
cd app-server
start "App Server" cmd /c "npm start"
cd ..

REM Simple wait for App Server
echo Waiting for App Server (10 seconds)...
timeout /t 10 /nobreak >nul

echo [4/5] Starting React Client...
echo [%date% %time%] Starting React Client >> %LOG_FILE%
cd client
start "React Client" cmd /c "npm start"
cd ..

REM Simple wait for React Client
echo Waiting for React Client (15 seconds)...
timeout /t 15 /nobreak >nul

echo [5/5] Opening browser...
echo [%date% %time%] Opening browser >> %LOG_FILE%

REM Try both possible ports for React Client
start http://localhost:3000
timeout /t 2 /nobreak >nul
start http://localhost:3002

echo.
echo ==========================================
echo           System Startup Complete!
echo ==========================================
echo.
echo Service URLs:
echo   * AI Service:         http://localhost:8001
echo   * Backend Service:    http://localhost:3001
echo   * Frontend Interface: http://localhost:3000 or http://localhost:3002
echo.
echo Log file: %LOG_FILE%
echo [%date% %time%] System startup complete >> %LOG_FILE%

echo.
echo All services should be starting up now.
echo Please wait a moment and check the opened browser windows.
echo.
echo Press any key to close this window...
pause >nul
