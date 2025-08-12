@echo off
chcp 65001 > nul
echo ================================================
echo  智能 AI 服務啟動器
echo ================================================
echo.

cd /d "C:\Users\Victor\OneDrive - ASUS\ID_Work_\202505_資安宣導\03_tools\code\confidential-expert-ai"
python smart_service_manager.py --start

pause
