@echo off
chcp 65001 > nul
echo =================================================================
echo  Confidential Expert AI - 分步啟動服務
echo =================================================================
echo.

:: 設定基礎目錄
set "BASE_DIR=%~dp0"
echo 基礎目錄: %BASE_DIR%
echo.

echo 請按照以下步驟手動啟動服務：
echo.

echo ==============================
echo 步驟 1: 啟動 Ollama 服務
echo ==============================
echo 請在新的命令視窗執行：
echo   ollama serve
echo.
echo 然後確認模型已下載：
echo   ollama pull mxbai-embed-large
echo.
pause

echo ==============================
echo 步驟 2: 啟動 AI Service
echo ==============================
echo 請在新的命令視窗執行：
echo   cd "%BASE_DIR%ai-service"
echo   python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
echo.
echo 等待看到 "Application startup complete" 訊息
echo.
pause

echo ==============================
echo 步驟 3: 測試 AI Service
echo ==============================
echo 正在測試 AI Service...
python "%BASE_DIR%test_api_chain.py"
echo.
echo 如果 AI Service 測試失敗，請檢查上一步的錯誤訊息
echo.
pause

echo ==============================
echo 步驟 4: 啟動 App Server
echo ==============================
echo 請在新的命令視窗執行：
echo   cd "%BASE_DIR%app-server"
echo   npm install
echo   node index.js
echo.
echo 等待看到 "Server running on port 3001" 訊息
echo.
pause

echo ==============================
echo 步驟 5: 啟動前端
echo ==============================
echo 請在新的命令視窗執行：
echo   cd "%BASE_DIR%client"
echo   npm install --legacy-peer-deps
echo   npm start
echo.
echo 等待瀏覽器自動開啟 http://localhost:3000
echo.
pause

echo ==============================
echo 步驟 6: 最終測試
echo ==============================
echo 正在執行完整 API 串接測試...
python "%BASE_DIR%test_api_chain.py"
echo.

echo =================================================================
echo 啟動完成！
echo 如果所有測試都通過，您現在可以在瀏覽器中測試 AI 功能
echo =================================================================
pause
