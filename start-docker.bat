@echo off
echo ============================================================
echo  Confidential Expert AI - Docker 啟動腳本
echo ============================================================
echo.

REM 檢查 Docker 是否運行
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker 未安裝或未啟動，請先安裝並啟動 Docker Desktop
    pause
    exit /b 1
)

echo ✅ Docker 已就緒

REM 檢查 .env 檔案
if not exist .env (
    echo 📝 建立 .env 檔案...
    copy .env.example .env
    echo ✅ .env 檔案已建立，請根據需要修改設定
)

REM 確保資料遷移已完成
echo 🔍 檢查 SQLite 資料庫...
if not exist "app-server\sqlite\db.sqlite" (
    echo 📊 執行資料遷移...
    cd app-server
    npm run migrate
    cd ..
    echo ✅ 資料遷移完成
) else (
    echo ✅ SQLite 資料庫已存在
)

echo.
echo 🐳 啟動 Docker 容器...
echo.

REM 建置並啟動容器
docker-compose up --build -d

if %errorlevel% equ 0 (
    echo.
    echo ============================================================
    echo 🎉 容器啟動成功！
    echo ============================================================
    echo 📍 服務端點:
    echo    - App Server:  http://localhost:3001
    echo    - AI Service:  http://localhost:8000
    echo    - 健康檢查:    http://localhost:3001/health
    echo.
    echo 🔧 管理指令:
    echo    - 查看日誌:    docker-compose logs -f
    echo    - 停止服務:    docker-compose down
    echo    - 重啟服務:    docker-compose restart
    echo ============================================================
    echo.
    
    REM 等待服務啟動
    echo ⏳ 等待服務啟動中...
    timeout /t 10 /nobreak >nul
    
    REM 測試服務健康狀態
    echo 🧪 測試服務健康狀態...
    curl -s http://localhost:3001/health >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ App Server 健康檢查通過
    ) else (
        echo ⚠️ App Server 可能還在啟動中，請稍後再試
    )
    
    curl -s http://localhost:8000/status >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ AI Service 健康檢查通過
    ) else (
        echo ⚠️ AI Service 可能還在啟動中，請稍後再試
    )
    
) else (
    echo ❌ 容器啟動失敗，請檢查錯誤訊息
    docker-compose logs
)

echo.
pause
