# Confidential Expert AI
_版本: 3.0.0 | 最後更新: 2025-08-12_

> **🎉 重大更新**: 完成系統性改寫，升級為 SQLite + Docker 容器化架構，AI 服務全面優化！

## 1. 專案總覽

本專案旨在建立一個全新的、獨立的**一站式資安顧問平台**。此平台整合了**智慧問答**與**結構化知識庫**兩種模式，為設計師提供全面、易用的資訊安全指引。

### 1.1 核心功能

1. **智慧問答助理 (AI-Powered Q&A):** 
   - 利用本地部署的大型語言模型 (LLM) 與 RAG 技術
   - 讓使用者能以自然語言提問，並獲得針對具體情境的精準回答
   - 支援上下文記憶，提供連貫對話體驗

2. **情境式知識庫 (Scenario-Based Knowledge Base):** 
   - 提供結構清晰、分類明確的卡片式瀏覽介面
   - 系統性地整理不同主題下的資安情境與最佳實踐
   - 支援自訂分類與搜尋功能

3. **後台管理系統 (Admin Panel):** 
   - 安全的管理介面，支援權限控管
   - 輕鬆地新增、修改或刪除知識庫中的資安情境卡片
   - 卡片群組管理與拖曳排序功能

## 2. 系統架構

本專案採用現代化的三層式容器化架構，具備完整的資料同步機制和智能 AI 服務。

```mermaid
graph TD
    User[使用者] --> Frontend[前端 - React + TypeScript]
    Frontend --> AppServer[應用伺服器 - Node.js/Express]
    Frontend --> AIService[AI服務 - Python/FastAPI]
    AppServer --> SQLite[(SQLite 資料庫)]
    AppServer -->|自動同步| AIService
    AIService --> LLM[本地LLM - Ollama]
    AIService --> VectorDB[(向量資料庫 - ChromaDB)]
    
    subgraph Docker容器化環境
        AppServer
        AIService
        SQLite
        VectorDB
    end
```

### 2.1 技術堆疊 (v3.0)

| 元件 | 技術選擇 | 主要職責 | 新功能 |
|------|----------|----------|--------|
| 前端 | React + TypeScript | 使用者介面，問答、卡片瀏覽、後台管理 | - |
| 應用伺服器 | Node.js + Express + SQLite | 結構化資料管理，CRUD API，權限驗證 | **SQLite 升級** + **自動同步** |
| AI服務 | Python + FastAPI | RAG流程，向量化查詢，智能回答生成 | **提示工程優化** + **智能檢索** |
| LLM服務 | Ollama | 本地語言模型與向量化模型 | - |
| 向量資料庫 | ChromaDB | 向量化知識儲存，語意搜尋 | **增量同步** |
| 容器化 | Docker + Docker Compose | 一鍵部署，環境一致性 | **🆕 新增** |

## 3. 快速開始

### 3.1 環境需求

**🐳 Docker 部署 (推薦)**
- Docker Desktop
- Docker Compose
- Ollama (已安裝並運行)
- 建議硬體配置: 16GB RAM, 支援CUDA的GPU (非必須但建議)

**📦 傳統部署**
- Node.js v20+
- Python 3.11+
- Ollama (已安裝並運行)

### 3.2 一鍵 Docker 部署 (推薦)

1. **克隆專案:**
   ```bash
   git clone https://github.com/your-org/confidential-expert-ai.git
   cd confidential-expert-ai
   ```

2. **一鍵啟動:**
   ```bash
   # Windows
   ./start-docker.bat
   
   # Linux/Mac
   docker-compose up --build -d
   ```

3. **訪問服務:**
   - 前端介面: http://localhost:3000
   - App Server: http://localhost:3001
   - AI Service: http://localhost:8000

### 3.3 傳統安裝步驟

1. **安裝前端依賴:**
   ```bash
   cd client
   npm install
   ```

3. **安裝AI服務依賴:**
   ```bash
   cd ai-service
   pip install -r requirements.txt
   cd ..
   ```

4. **設定環境變數:**
   - 複製 `.env.example` 為 `.env` 並填入必要設置

5. **啟動服務:**
   ```bash
   # 啟動應用伺服器
   node app-server/index.js
   
   # 啟動AI服務
   cd ai-service
   python main.py
   ```

## 4. 文件導航

更詳細的文件請參考:

- [系統架構與數據結構](./System_Architecture.md) - 資料庫結構與系統模組詳解
- [AI系統與RAG機制](./AI_System.md) - AI服務設計與RAG系統說明
- [前端顯示與互動設計](./Frontend_Guide.md) - UI/UX設計與卡片顯示優化
- [管理後台使用與開發指南](./Admin_Guide.md) - 管理介面功能與卡片管理

## 5. 目前狀態與里程碑

- [x] 基礎系統架構設計完成
- [x] 卡片管理後台功能實現
- [x] RAG系統基礎功能實現
- [ ] AI回答品質優化
- [ ] 卡片結構擴展與UI優化
- [ ] RAG同步自動化實現
- [ ] 最終整合與部署

## 6. 貢獻指南

若要貢獻代碼，請遵循以下流程:
1. Fork 專案
2. 建立功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 7. 許可證

本專案採用 [MIT 許可證](LICENSE)。
