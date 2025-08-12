# 全棧服務啟動器改進方案

## 1. 問題根因分析 (Root Cause Analysis)

目前的 `start-all-robust.bat` 腳本雖然解決了連接埠衝突問題，但仍然存在一個核心的**競爭條件 (Race Condition)** 問題。

- **錯誤的假設**: 腳本假設在固定的等待時間（例如 30 秒）後，AI Service (FastAPI) 就一定準備好接受網路連線。這是一個不可靠的 "硬編碼" 解決方案，因為服務的實際啟動時間會受到多種因素影響，例如：
  - **機器負載**: CPU 和記憶體的使用情況。
  - **網路狀況**: `pip install` 或 `ollama pull` 的速度。
  - **資料載入時間**: `ingest.py` 處理的資料量大小。
- **缺乏健康檢查 (Health Check)**: 腳本沒有一個機制來**確認** AI Service 是否**真正**準備好，只是盲目地等待。這導致 App Server 在 AI Service 尚未完全啟動時就嘗試連接，從而引發 `ECONNREFUSED` (連線被拒絕) 錯誤。
- **日誌記錄不足**: 啟動過程缺乏詳細的日誌，導致每次失敗後都需要手動檢查各個視窗的輸出，診斷效率低下。

## 2. 解決方案：智慧型健康檢查啟動器

我們將放棄簡單的 `timeout` 等待，改用一個**主動的、基於健康檢查的循環 (Active Health Check Loop)** 機制。這將確保服務之間的依賴關係得到滿足後，才會繼續下一步。

### 2.1. 建立 `start-all-intelligent.bat`

這個新的智慧型啟動腳本將實現以下功能：

1.  **強力連接埠清理**: 保留現有的連接埠清理邏輯，確保啟動環境乾淨。
2.  **非同步啟動核心服務**: 同時啟動 Ollama 和 AI Service，因為它們是 App Server 的前置依賴。
3.  **智慧型健康檢查循環**:
    - 在啟動 App Server 之前，腳本會進入一個循環。
    - 在循環中，它會定期（例如每 5 秒）嘗試訪問 AI Service 的健康檢查端點 (例如 `http://localhost:8001/api/status`)。
    - **成功**: 如果收到成功的 HTTP 回應 (狀態碼 200)，則跳出循環，繼續啟動 App Server。
    - **失敗**: 如果連線失敗或超時，則繼續等待並重試，直到達到最大重試次數（例如 12 次，總計約 60 秒）。
4.  **詳細日誌記錄**: 
    - 建立一個 `logs` 目錄。
    - 將所有啟動步驟的輸出（包括成功、失敗、時間戳）記錄到 `logs/startup.log` 檔案中。
    - 這將極大地簡化未來的故障排除。

### 2.2. 在 AI Service 中新增 `/api/status` 端點

為了支持健康檢查，我們需要在 `ai-service/main.py` 中新增一個簡單的 API 端點，它只返回一個成功的 JSON 回應，表示服務已啟動並可正常運作。

```python
@app.get("/api/status")
def get_status():
    return {"status": "ok"}
```

## 3. 實施步驟

1.  **修改 `ai-service/main.py`**: 加入上述 `/api/status` 端點。
2.  **建立 `start-all-intelligent.bat`**: 實現上述所有功能，包括連接埠清理、非同步啟動、健康檢查循環和日誌記錄。
3.  **測試與驗證**: 執行新腳本，並檢查 `startup.log` 以確認所有步驟都按預期工作。
4.  **清理舊腳本**: 成功後，刪除 `start-all-robust.bat`，只保留 `start-all-working.bat` (原始備份) 和新的 `start-all-intelligent.bat`。

這個方案將從根本上解決啟動時序問題，使整個系統的啟動過程更加健壯和可靠。
