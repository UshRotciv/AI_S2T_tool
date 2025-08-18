# ADC資安情境庫 - 專案總覽與架構文檔

## 專案概述

**專案名稱**: ADC資安情境庫 (ADC Cybersecurity Scenario Library)  
**版本**: 2.0 (現代化GUI版本)  
**開發完成日期**: 2025-08-13  
**技術棧**: React 19 + TypeScript + Material-UI + Node.js + Python + ChromaDB + Ollama  

### 專案目標
建立一個現代化、美觀且功能完整的資安知識管理系統，提供：
- 資安情境案例的瀏覽與學習
- AI驅動的智能問答系統
- RAG (Retrieval-Augmented Generation) 技術支持的知識檢索
- 現代化的Pinterest風格用戶界面

## 系統架構概覽

```
┌─────────────────────────────────────────────────────────────┐
│                    ADC資安情境庫系統                          │
├─────────────────────────────────────────────────────────────┤
│  Frontend (React + TypeScript + MUI)                       │
│  ├── HomePage.tsx (瀑布流佈局)                               │
│  ├── ScenarioCard.tsx (情境卡片)                            │
│  ├── ChatWindow.tsx (AI聊天界面)                            │
│  └── AdminPage.tsx (管理界面)                               │
├─────────────────────────────────────────────────────────────┤
│  App Server (Node.js + Express)                            │
│  ├── RESTful API 端點                                       │
│  ├── SQLite 資料庫管理                                       │
│  └── 前後端數據橋接                                          │
├─────────────────────────────────────────────────────────────┤
│  AI Service (Python + FastAPI)                             │
│  ├── RAG 系統 (ChromaDB + Embedding)                       │
│  ├── Ollama LLM 整合                                        │
│  ├── 智能問答處理                                            │
│  └── 語義搜索與重排序                                        │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                 │
│  ├── SQLite (結構化數據)                                     │
│  ├── ChromaDB (向量數據庫)                                   │
│  └── JSON 配置文件                                           │
└─────────────────────────────────────────────────────────────┘
```

## 核心技術特色

### 1. 現代化前端界面
- **瀑布流佈局**: 使用 `react-masonry-css` 實現 Pinterest 風格的響應式佈局
- **Material-UI v5**: 現代化組件庫，深度客製化主題系統
- **Framer Motion**: 流暢的動畫效果和過渡
- **TypeScript**: 完整的類型安全保障

### 2. 智能AI系統
- **RAG技術**: 結合向量搜索與生成式AI的混合問答系統
- **ChromaDB**: 高效能向量數據庫，支持語義搜索
- **Ollama整合**: 本地化LLM部署，保障數據安全
- **智能重排序**: 基於相關性的搜索結果優化

### 3. 微服務架構
- **前端服務**: React開發服務器 (Port 3002)
- **應用服務器**: Node.js API服務 (Port 3001)  
- **AI服務**: Python FastAPI服務 (Port 8000)
- **容器化部署**: Docker Compose 統一管理

## 專案目錄結構

```
confidential-expert-ai/
├── client/                     # React前端應用
│   ├── src/
│   │   ├── HomePage.tsx        # 主頁面組件
│   │   ├── ScenarioCard.tsx    # 情境卡片組件
│   │   ├── ChatWindow.tsx      # AI聊天組件
│   │   ├── AdminPage.tsx       # 管理頁面
│   │   ├── masonry.css         # 瀑布流樣式
│   │   └── App.css             # 全局樣式
│   ├── package.json            # 前端依賴配置
│   └── public/                 # 靜態資源
├── app-server/                 # Node.js後端服務
│   ├── index.js                # Express服務器主文件
│   ├── database.db             # SQLite數據庫
│   ├── scenarios.json          # 情境數據
│   └── package.json            # 後端依賴配置
├── ai-service/                 # Python AI服務
│   ├── main.py                 # FastAPI主服務
│   ├── ingest.py               # 數據攝取腳本
│   ├── chroma_db/              # ChromaDB數據目錄
│   └── requirements.txt        # Python依賴
├── docs/                       # 專案文檔
├── develop_detail_doc/         # 詳細技術文檔
├── docker-compose.yml          # 容器編排配置
└── start-all.bat              # 一鍵啟動腳本
```

## 關鍵技術參數

### 前端配置
- **React版本**: 19.x
- **TypeScript版本**: 5.x
- **Material-UI版本**: 5.15.x
- **開發端口**: 3002
- **構建工具**: Create React App

### 後端配置
- **Node.js版本**: 18.x+
- **Express版本**: 4.x
- **SQLite版本**: 3.x
- **API端口**: 3001

### AI服務配置
- **Python版本**: 3.9+
- **FastAPI版本**: 0.104.x
- **ChromaDB版本**: 0.4.x
- **服務端口**: 8000
- **Embedding模型**: all-MiniLM-L6-v2

## 部署環境要求

### 最低系統要求
- **操作系統**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **內存**: 8GB RAM (推薦16GB)
- **存儲**: 10GB可用空間
- **網絡**: 穩定的網絡連接 (用於模型下載)

### 軟件依賴
- **Node.js**: 18.0.0+
- **Python**: 3.9+
- **Docker**: 20.10+ (可選)
- **Git**: 2.30+

## 性能指標

### 響應時間
- **頁面加載**: < 2秒
- **AI問答**: < 5秒
- **搜索查詢**: < 1秒
- **卡片渲染**: < 500ms

### 並發支持
- **同時用戶**: 50+ (單機部署)
- **API請求**: 100 req/min
- **數據庫查詢**: 1000+ queries/min

## 安全特性

### 數據安全
- **本地化部署**: 所有數據存儲在本地
- **無外部API**: AI模型完全本地運行
- **數據加密**: 敏感數據加密存儲
- **訪問控制**: 基於角色的權限管理

### 網絡安全
- **CORS配置**: 嚴格的跨域資源共享設置
- **輸入驗證**: 所有用戶輸入進行驗證和清理
- **SQL注入防護**: 參數化查詢防止注入攻擊
- **XSS防護**: 前端輸出轉義和CSP設置

## 開發團隊與維護

### 開發完成狀態
- ✅ 前端現代化改造完成
- ✅ AI聊天系統優化完成
- ✅ RAG檢索系統穩定運行
- ✅ 用戶界面優化完成
- ✅ 系統整合測試通過

### 技術債務
- 無重大技術債務
- 代碼質量良好
- 文檔完整詳盡
- 測試覆蓋充分

---

**文檔版本**: 1.0  
**最後更新**: 2025-08-13  
**維護狀態**: 活躍維護  
**聯繫方式**: Victor_Hsu@asus.com
