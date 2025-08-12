@echo off
setlocal enabledelayedexpansion

:: Set log file
set LOG_DIR=logs
set LOG_FILE=%LOG_DIR%\startup.log

:: Create log directory
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

:: Clear old log
echo. > "%LOG_FILE%"

:: Log function
call :log "=========================================="
call :log "Intelligent Full-Stack Service Launcher - Starting"
call :log "Time: %date% %time%"
call :log "=========================================="

:: Step 1: Force cleanup ports
call :log "Step 1: Cleaning ports 8001, 3001, 3000, 11434"
echo Cleaning ports...

for %%p in (8001 3001 3000 11434) do (
    call :log "Checking port %%p"
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr :%%p') do (
        call :log "Found process %%a using port %%p, terminating..."
        taskkill /f /pid %%a >nul 2>&1
        if !errorlevel! equ 0 (
            call :log "Successfully terminated process %%a"
        ) else (
            call :log "Cannot terminate process %%a or process already ended"
        )
    )
)

call :log "Port cleanup completed"
timeout /t 2 >nul

:: Step 2: Start Ollama service
call :log "Step 2: Starting Ollama service"
echo Starting Ollama service...
start "Ollama Service" cmd /k "ollama serve"
call :log "Ollama service started"
timeout /t 5 >nul

:: Step 3: Pull required models
call :log "Step 3: Pulling Ollama models"
echo Pulling Ollama models...
call :log "Pulling mxbai-embed-large model"
ollama pull mxbai-embed-large
if !errorlevel! equ 0 (
    call :log "mxbai-embed-large model pulled successfully"
) else (
    call :log "mxbai-embed-large model pull failed"
)

call :log "Pulling qwen2 model"
ollama pull qwen2
if !errorlevel! equ 0 (
    call :log "qwen2 model pulled successfully"
) else (
    call :log "qwen2 model pull failed"
)

:: Step 4: Execute data loading
call :log "Step 4: Executing data loading (ingest.py)"
echo Loading data to ChromaDB...
cd ai-service
call venv\Scripts\activate
python ingest.py
if !errorlevel! equ 0 (
    call :log "Data loading successful"
) else (
    call :log "Data loading failed, error code: !errorlevel!"
)
cd ..

:: Step 5: Start AI Service (FastAPI)
call :log "Step 5: Starting AI Service (FastAPI)"
echo Starting AI Service...
cd ai-service
start "AI Service" cmd /k "call venv\Scripts\activate && uvicorn main:app --host 0.0.0.0 --port 8001"
cd ..
call :log "AI Service start command executed"

:: Step 6: Intelligent health check loop
call :log "Step 6: Starting AI Service health check"
echo Waiting for AI Service to be ready...

set /a retry_count=0
set /a max_retries=24
set check_interval=5

:health_check_loop
set /a retry_count+=1
call :log "Health check attempt !retry_count!/!max_retries!"

:: Use curl to check health status
curl -s -o nul -w "%%{http_code}" http://localhost:8001/api/status > temp_status.txt 2>nul
set /p http_code=<temp_status.txt
del temp_status.txt >nul 2>&1

if "!http_code!"=="200" (
    call :log "AI Service health check successful! HTTP status code: !http_code!"
    echo AI Service is ready!
    goto :continue_startup
)

call :log "AI Service not ready yet, HTTP status code: !http_code!"
echo Waiting for AI Service to start... (!retry_count!/!max_retries!)

if !retry_count! geq !max_retries! (
    call :log "Health check timeout! AI Service may have failed to start"
    echo Error: AI Service health check timeout, please check AI Service window for error messages
    pause
    exit /b 1
)

timeout /t !check_interval! >nul
goto :health_check_loop

:continue_startup
:: Step 7: Start App Server
call :log "Step 7: Starting App Server"
echo Starting App Server...
cd app-server
start "App Server" cmd /k "npm start"
cd ..
call :log "App Server start command executed"
timeout /t 3 >nul

:: Step 8: Start React Client
call :log "Step 8: Starting React Client"
echo Starting React Client...
cd client
start "React Client" cmd /k "npm start"
cd ..
call :log "React Client start command executed"

:: Completion
call :log "=========================================="
call :log "All services startup completed!"
call :log "- Ollama Service: http://localhost:11434"
call :log "- AI Service: http://localhost:8001"
call :log "- App Server: http://localhost:3001"
call :log "- React Client: http://localhost:3000"
call :log "=========================================="

echo.
echo ========================================
echo All services have been successfully started!
echo ========================================
echo Service Status:
echo   - Ollama Service: http://localhost:11434
echo   - AI Service: http://localhost:8001
echo   - App Server: http://localhost:3001
echo   - React Client: http://localhost:3000
echo.
echo Log file: %LOG_FILE%
echo If there are issues, please check the output messages in each service window
echo ========================================
pause
exit /b 0

:: Log function
:log
echo %date% %time% - %~1 >> "%LOG_FILE%"
echo %~1
goto :eof
