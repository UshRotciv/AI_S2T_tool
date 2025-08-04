# Confidential Expert AI 系統修復步驟

## 問題概述
1. 原始問題：Admin 模式下更新 scenario 時出現 404 錯誤 (`"Scenario not found"`)
2. 嘗試修復過程中，在 `scenarioController.js` 中添加了調試代碼
3. 前端出現 ESLint 相關依賴問題 (`Cannot find module './compile'`)
4. 目前狀態：整個網站無法正常打開

## 修復步驟

### 步驟 1: 終止所有進程
```powershell
# 終止所有 Node.js 進程
taskkill /F /IM node.exe
```

### 步驟 2: 修復後端代碼
1. 移除 `scenarioController.js` 中的調試代碼
2. 修改文件：`c:\Users\Victor\OneDrive - ASUS\ID_Work_\202505_資安宣導\03_tools\code\confidential-expert-ai\app-server\src\controllers\scenarioController.js`
3. 恢復 `updateScenario` 函數為原始狀態（刪除三行調試代碼）

### 步驟 3: 重建後端依賴
```powershell
# 進入後端目錄
cd "c:\Users\Victor\OneDrive - ASUS\ID_Work_\202505_資安宣導\03_tools\code\confidential-expert-ai\app-server"

# 清理並重新安裝依賴
rmdir /s /q node_modules
del package-lock.json
npm install
```

### 步驟 4: 重建前端依賴
```powershell
# 進入前端目錄
cd "c:\Users\Victor\OneDrive - ASUS\ID_Work_\202505_資安宣導\03_tools\code\confidential-expert-ai\client"

# 清理並重新安裝依賴
rmdir /s /q node_modules
del package-lock.json
npm install
```

### 步驟 5: 重新啟動應用
```powershell
# 回到主專案目錄
cd "c:\Users\Victor\OneDrive - ASUS\ID_Work_\202505_資安宣導\03_tools\code\confidential-expert-ai"

# 啟動所有服務
.\start-all.bat
```

### 步驟 6: 驗證系統恢復
1. 在瀏覽器中訪問應用
2. 確認前端和後端都正常運作
3. 檢查基本功能是否可用

## 原始 404 錯誤調查（系統恢復後）

在系統恢復正常後，我們將使用以下方法調查原始的 404 錯誤：

1. **使用瀏覽器開發者工具**:
   - 打開 Chrome DevTools (F12)
   - 觀察 Network 標籤中的請求
   - 特別關注 scenario 更新請求的 URL、參數和響應

2. **問題初步分析**:
   - 404 "Scenario not found" 錯誤通常表示找不到指定 ID 的 scenario
   - 可能是前端發送的 ID 有問題，或者後端查詢方式不正確
   - 需要調查資料庫中的 scenario ID 格式與前端發送的是否匹配
