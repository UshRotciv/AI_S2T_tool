# ChromaDB 整合問題修復計畫

此計畫旨在解決 ChromaDB 在專案中未正確串接的問題。我們將透過一系列步驟，檢查、診斷並修復相關的程式碼。

## 診斷結果 (2025-08-07)

根據 `debug_log.txt` 和程式碼分析，問題核心已確認：

- **根本原因**：Python 腳本執行時，未使用專案的虛擬環境 (`venv`)，導致無法找到已安裝的 `chromadb` 模組。
- **證據**：日誌中明確顯示 `chromadb 導入失敗: No module named 'chromadb'`，儘管 `pip list` 顯示套件已安裝。

## 附註：工具與策略

-   **診斷工具**：`grep_search`、`view_file`
-   **修復策略**：回歸最簡單、最可靠的單一啟動腳本，放棄所有複雜功能，確保核心的四個服務能穩定啟動。

## 修復步驟

1.  **環境修正 (已完成)**
    - [x] **問題分析**：已確認問題為 Python 虛擬環境未啟用。
    - [x] **最終版啟動腳本 (極簡可靠版)**：已建立一個單一、簡潔的 `start-all.bat`，確保所有四個服務都能穩定啟動。
    - [x] **依賴問題修復**：啟動腳本已包含 `pip install` 和 `npm install --legacy-peer-deps`，自動處理所有依賴。

2.  **連線與路徑驗證**
    - [ ] **統一資料庫路徑**：檢查所有腳本 (`main.py`, `ingest.py`, `rag_diagnosis.py` 等)，確保 `chromadb.PersistentClient` 使用的路徑 (`path`) 一致且正確。
    - [ ] **執行連線測試**：在 **已啟用** 的虛擬環境中，執行 `check_index.py` 或 `env_doctor.py` 來驗證連線。

3.  **前端修復**
    - [x] **修復依賴衝突**：已在前端啟動腳本中加入 `--legacy-peer-deps` 參數，解決 `npm install` 錯誤。

4.  **資料寫入與讀取測試**
    - [ ] **執行資料寫入 (Ingestion)**：在虛擬環境中執行 `ingest.py`，確保資料能被成功處理並寫入 ChromaDB。
    - [ ] **啟動服務並測試 API**：啟動 `ai-service` 和 `app-server`，並透過 API 進行查詢，驗證完整的 RAG 流程是否正常運作。
