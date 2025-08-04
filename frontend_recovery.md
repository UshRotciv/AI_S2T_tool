# Frontend Recovery Plan for Confidential Expert AI

## 問題診斷
1. **主要錯誤**: 前端頁面出現 "Failed to fetch" 錯誤
2. **原因分析**: 
   - 後端伺服器 (app-server) 未正常運行於端口 3001
   - 前端代碼嘗試從 `http://localhost:3001/api/scenarios` 獲取數據但連接失敗
   - 前端應用(端口 3002)和 AI 服務(端口 8000)運行正常

## 修復步驟

### 步驟 1: 檢查 app-server 配置
檢查後端 app-server 的配置問題：
1. app-server 的 package.json 缺少 `dev` 腳本，但 start-all.bat 嘗試以 `npm run dev` 啟動
2. 後端伺服器設置為在端口 3001 運行，但無法正確啟動

### 步驟 2: 修復 app-server 的啟動腳本
修改 app-server 的 package.json，添加 dev 腳本：

```json
{
  "scripts": {
    "test": "echo \"Error: no test specified\" && exit 1",
    "start": "node index.js",
    "dev": "node index.js"
  }
}
```

### 步驟 3: 確保 scenarios.json 文件存在
在 app-server 目錄中創建 scenarios.json 文件，避免啟動錯誤：

```json
{
  "data": []
}
```

### 步驟 4: 修改後端響應格式以匹配前端期望
前端代碼期望響應格式為 `{ data: [...] }`，但後端直接返回數組。
修改 app-server/index.js 中的 GET /api/scenarios 路由：

```javascript
app.get('/api/scenarios', (req, res) => {
  res.json({ data: scenarios });
});
```

### 步驟 5: 重新啟動所有服務
1. 終止所有正在運行的 Node.js 進程
2. 使用修改後的 start-all.bat 重新啟動所有服務

### 步驟 6: 驗證系統恢復
1. 檢查後端服務是否在端口 3001 運行
2. 在瀏覽器中訪問前端應用 (http://localhost:3002)
3. 確認不再出現 "Failed to fetch" 錯誤

## 預防措施
1. 在 start-all.bat 中添加錯誤處理，確保所有服務正確啟動
2. 改進前端錯誤處理，在 API 連接失敗時提供更好的用戶反饋
3. 考慮添加健康檢查端點，以便更容易診斷服務問題
