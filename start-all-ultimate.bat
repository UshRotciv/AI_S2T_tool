@echo off
setlocal enabledelayedexpansion

echo.
echo ==========================================
echo    RAG AI System Launcher (Ultimate Fix)
echo ==========================================
echo.

REM Create logs directory
if not exist logs mkdir logs
set LOG_FILE=logs\startup_ultimate.log

echo [%date% %time%] Starting RAG System >> %LOG_FILE%
echo Log file: %LOG_FILE%

echo [1/6] Cleaning up old processes...
echo [%date% %time%] Starting cleanup >> %LOG_FILE%

REM Kill all related processes
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1
taskkill /f /im ollama.exe >nul 2>&1

REM Force kill processes on specific ports
for %%p in (11434 8001 3001 3000 3002) do (
    echo Cleaning port %%p...
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr :%%p') do (
        taskkill /f /pid %%a >nul 2>&1
    )
)

timeout /t 3 /nobreak >nul

echo [2/6] Starting Ollama (if available)...
echo [%date% %time%] Starting Ollama >> %LOG_FILE%
ollama --version >nul 2>&1
if not errorlevel 1 (
    start "Ollama Service" cmd /k "ollama serve"
    timeout /t 8 /nobreak >nul
    echo OK: Ollama started
) else (
    echo WARNING: Ollama not found, skipping
)

echo [3/6] Starting AI Service...
echo [%date% %time%] Starting AI Service >> %LOG_FILE%
cd ai-service

REM Ensure virtual environment exists
if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Start AI Service in a new window
start "AI Service" cmd /k "call venv\Scripts\activate && python main.py"
cd ..

REM Wait for AI Service to be ready
echo Waiting for AI Service to start...
set /a ai_count=0
:wait_ai
set /a ai_count+=1
if %ai_count% gtr 30 (
    echo ERROR: AI Service failed to start
    goto :error_exit
)
timeout /t 2 /nobreak >nul
netstat -an | findstr ":8001" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo Waiting for AI Service... (%ai_count%/30)
    goto :wait_ai
)
echo OK: AI Service is listening on port 8001

echo [4/6] Starting App Server...
echo [%date% %time%] Starting App Server >> %LOG_FILE%
cd app-server

REM Ensure dependencies are installed
if not exist node_modules (
    echo Installing Node.js dependencies...
    npm install
)

REM Start App Server in a new window
start "App Server" cmd /k "npm start"
cd ..

REM Wait for App Server to be ready
echo Waiting for App Server to start...
set /a app_count=0
:wait_app
set /a app_count+=1
if %app_count% gtr 20 (
    echo ERROR: App Server failed to start
    goto :error_exit
)
timeout /t 2 /nobreak >nul
netstat -an | findstr ":3001" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo Waiting for App Server... (%app_count%/20)
    goto :wait_app
)
echo OK: App Server is listening on port 3001

echo [5/6] Starting React Client...
echo [%date% %time%] Starting React Client >> %LOG_FILE%
cd client

REM Ensure dependencies are installed
if not exist node_modules (
    echo Installing React dependencies...
    npm install
)

REM Start React Client in a new window
start "React Client" cmd /k "npm start"
cd ..

REM Wait for React Client to be ready
echo Waiting for React Client to start...
set /a react_count=0
:wait_react
set /a react_count+=1
if %react_count% gtr 30 (
    echo WARNING: React Client may need more time
    goto :continue_startup
)
timeout /t 2 /nobreak >nul
netstat -an | findstr ":3000" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo OK: React Client is listening on port 3000
    set CLIENT_PORT=3000
    goto :continue_startup
)
netstat -an | findstr ":3002" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo OK: React Client is listening on port 3002
    set CLIENT_PORT=3002
    goto :continue_startup
)
echo Waiting for React Client... (%react_count%/30)
goto :wait_react

:continue_startup
echo [6/6] Running system verification...
echo [%date% %time%] Starting verification >> %LOG_FILE%

REM Wait a bit more for all services to be fully ready
timeout /t 5 /nobreak >nul

REM Run verification test
python test_all_fixes.py
if errorlevel 1 (
    echo WARNING: Some tests failed, but services are running
) else (
    echo OK: All tests passed!
)

echo.
echo ==========================================
echo           System Startup Complete!
echo ==========================================
echo.
echo Service Status:
echo   * Ollama Service:     http://localhost:11434
echo   * AI Service:         http://localhost:8001
echo   * Backend Service:    http://localhost:3001
if defined CLIENT_PORT (
    echo   * Frontend Interface: http://localhost:%CLIENT_PORT%
) else (
    echo   * Frontend Interface: http://localhost:3000 or http://localhost:3002
    set CLIENT_PORT=3000
)
echo.
echo Opening browser...
echo [%date% %time%] Opening browser >> %LOG_FILE%

REM Open browser only once
timeout /t 2 /nobreak >nul
start http://localhost:%CLIENT_PORT%

echo.
echo All services are now running in separate windows.
echo You can close this window safely.
echo.
echo Press any key to close this launcher...
pause >nul
goto :eof

:error_exit
echo.
echo ERROR: System startup failed!
echo Please check the service windows for error messages.
echo Log file: %LOG_FILE%
echo [%date% %time%] System startup failed >> %LOG_FILE%
pause
exit /b 1
