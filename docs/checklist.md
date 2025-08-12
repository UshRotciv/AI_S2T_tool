# Confidential Expert AI - 開發檢查清單

## Phase 1: 環境建置與基礎設定

- [x] **專案結構初始化**
  - [x] 建立 `confidential-expert-ai` 根目錄
  - [x] 建立前端 React 專案 (`client`)
  - [x] 建立後端 Node.js 專案 (`app-server`)
  - [x] 建立後端 Python AI 服務專案 (`ai-service`)
- [x] **建立初始資料**
  - [x] 將 `ADC_IT資安專家對談紀錄.pdf` 和 `ADC_confidential_awareness_game.txt` 的內容整理成結構化的 `scenarios.json` 檔案。
- [x] **安裝與設定 Ollama**
  - [x] 確認 Ollama 已在開發環境中安裝並啟動
  - [x] 下載指定的 LLM (如 `gemma:latest`)
  - [x] 下載指定的嵌入模型 (如 `mxbai-embed-large`)

## Phase 2: 核心後端建置 (App Server)

- [x] **建立 Node.js 環境**
  - [x] 初始化 `package.json`
  - [x] 安裝 Express, cors, body-parser 等必要套件
- [x] **開發情境資料 API**
  - [x] 實作 `GET /api/scenarios`：取得所有情境資料
  - [x] 實作 `GET /api/scenarios/:id`：取得單一情境資料
  - [x] 實作 `POST /api/scenarios`：新增一筆情境
  - [x] 實作 `PUT /api/scenarios/:id`：更新指定情境
  - [x] 實作 `DELETE /api/scenarios/:id`：刪除指定情境
- [ ] **(可選) 建立使用者認證**
  - [ ] 增加 `/login` 端點，用於後台管理員登入
  - [ ] 為所有非 GET 的 API 加上權限保護
/
## Phase 3: 核心前端建置 (Client)

- [x] **安裝前端套件**
  - [x] 安裝 `react-router-dom` 用於路由管理
  - [x] 安裝 `axios` 或使用 `fetch` 進行 API 請求
- [x] **開發情境瀏覽介面**
  - [x] 建立 `HomePage.tsx`，以分類和卡片形式顯示所有情境
  - [x] 建立 `ScenarioCard.tsx` 元件，點擊可展開詳細資訊
  - [x] 串接 `GET /api/scenarios` API
- [x] **開發後台管理介面**
  - [x] 建立 `AdminPage.tsx`，作為後台管理的進入點
  - [x] 建立表單用於新增/編輯情境
  - [x] 建立表格顯示所有情境，並包含編輯/刪除按鈕
  - [x] 串接所有 CRUD API (`GET`, `POST`, `PUT`, `DELETE`)

## Phase 4: AI 後端服務建置 (AI Service)

- [x] **建立 Python 環境**
  - [x] 設定 `venv` 或 `conda` 虛擬環境
  - [x] 安裝 FastAPI, ChromaDB, Ollama, aiohttp 等必要套件
- [x] **資料庫初始化腳本 (`ingest.py`)**
  - [x] 讀取 `scenarios.json`
  - [x] 使用 Ollama 的嵌入模型將每個情境向量化
  - [x] 將向量化後的資料存入 ChromaDB
- [x] **開發 FastAPI 應用 (`main.py`)**
  - [x] 建立 API 端點 `POST /api/ask`
  - [x] 實現完整的 RAG 核心邏輯 (向量化 -> 搜尋 -> 生成)

## Phase 5: AI 功能前端整合 (Client)

- [x] **建立聊天介面元件**
  - [x] 建立 `ChatWindow.tsx` 元件
- [x] **API 串接**
  - [x] 在 `ChatWindow.tsx` 中，當使用者送出問題時，呼叫 AI 服務的 `POST /api/ask`
  - [x] 將回傳的答案顯示在聊天介面上
- [x] **整合至主頁面**
  - [x] 將 `ChatWindow.tsx` 元件以懸浮按鈕或固定視窗的形式加入到 `HomePage.tsx`

## Phase 6: 測試與部署

- [ ] **端對端測試**
  - [ ] 測試 CRUD 功能是否正常
  - [ ] 測試 AI 問答流程與回答品質
- [ ] **撰寫部署文件**
  - [ ] 說明如何啟動所有服務 (Client, App Server, AI Service, Ollama)
