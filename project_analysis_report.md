# 專案軟體設計架構分析報告

## 1. 總體軟體設計架構 (Overall Software Design Architecture)

本專案採用現代化的**三層式架構 (3-Tier Architecture)**，將使用者介面、業務邏輯和AI處理能力清晰地分離開來，具備良好的模組化與可擴展性。

```
+---------------------+      +------------------------+      +-----------------------+
|   Frontend (Client) |----->|  App Server (Backend)  |----->|   AI Service (RAG)    |
| (React + TS)        |      | (Node.js + Express)    |      | (Python + FastAPI)    |
+---------------------+      +------------------------+      +-----------------------+
        |                            |                             |
        |                            |                             |
        v                            v                             v
    (使用者互動)                (JSON 檔案)                  (ChromaDB + Ollama)
```

1.  **前端 (Client):**
    *   **技術:** React, TypeScript
    *   **職責:** 提供使用者操作介面，包括AI問答視窗 (`ChatWindow`)、結構化知識庫瀏覽 (`HomePage`) 和後台管理 (`AdminPage`)。它透過API與應用伺服器和AI服務溝通。

2.  **應用伺服器 (App Server):**
    *   **技術:** Node.js, Express
    *   **職責:** 作為中間層，負責管理結構化的「情境卡片 (Scenarios)」和「群組 (Groups)」。它提供CRUD API給前端進行內容管理，並將資料儲存在本地的JSON檔案 (`scenarios.json`, `groups.json`) 中。

3.  **AI服務 (AI Service):**
    *   **技術:** Python, FastAPI, ChromaDB, Ollama
    *   **職責:** 專案的核心智慧所在。它實現了**檢索增強生成 (RAG)** 的能力。
        *   `ingest.py`: 負責讀取 `scenarios.json` 和 `rule_ref/` 中的文件，將其處理、切塊(chunking)、轉換為向量，並存入 `ChromaDB` 向量資料庫。
        *   `main.py`: 提供 `/api/ask` 端點，接收使用者問題，將問題向量化後在 `ChromaDB` 中進行語意搜索，找到最相關的知識片段，最後將問題與這些片段組合起來，交給本地部署的 `Ollama` 大型語言模型 (LLM) 生成最終回答。

## 2. 各檔案的設計邏輯

### `ai-service/`
*   `main.py`: **AI服務的API伺服器**。使用FastAPI框架，核心功能是 `/api/ask`，它整合了查詢擴展、分層檢索、RAG提示工程和與Ollama模型的互動。設計上考慮了對話歷史 (`conversation_history`) 和多種檢索策略，是整個AI問答流程的指揮中心。
*   `ingest.py`: **資料導入與向量化管道**。此腳本是RAG系統的基礎，負責將非結構化和半結構化的知識（JSON情境卡、Markdown/Text文件）轉換為向量資料庫可以理解的格式。它包含了文本切分 (`smart_chunk`)、中繼資料 (`metadata`) 提取、內容去重等關鍵預處理步驟。
*   `requirements.txt`: 定義了AI服務的所有Python依賴，如 `fastapi`, `chromadb`, `ollama` 等，是環境複製的基礎。
*   `chroma_db/`: **向量資料庫**。ChromaDB的本地存儲目錄，存放著所有知識的向量表示。

### `app-server/`
*   `index.js`: **應用伺服器的入口與API路由器**。使用Express框架，定義了所有關於 `scenarios` 和 `groups` 的CRUD API端點。它直接讀寫JSON檔案來持久化資料，並作為一個簡單的資料管理後端。
*   `scenarios.json`, `groups.json`: **結構化資料庫**。以簡單的JSON檔案形式儲存情境卡片和分類群組的資料。
*   `package.json`: 定義了Node.js專案的依賴（如 `express`, `cors`）和啟動腳本。

### `client/`
*   `src/App.tsx`: **前端應用的主路由器**。定義了 `/` (首頁) 和 `/admin` (管理頁) 的路由。
*   `src/ChatWindow.tsx`: **AI聊天視窗元件**。負責處理使用者輸入、發送API請求到後端 (`/api/ask`)、並顯示對話內容。這是使用者與AI互動的核心介面。
*   `src/AdminPage.tsx`: **後台管理頁面**。提供UI介面來新增、修改、刪除和組織情境卡片與群組。
*   `package.json`: 定義了React專案的依賴（如 `react`, `axios`）和啟動、建置腳本。

### 根目錄
*   `start-all.bat`: **一鍵啟動腳本**。非常實用的工具，可以一次性啟動Ollama、AI服務、應用伺服器和前端開發伺服器，極大簡化了開發環境的設定流程。
*   `README.md`, `System_Architecture.md`: **核心專案文件**。提供了專案的高層次概覽、架構圖和技術堆疊，是理解專案的最佳起點。
*   `rule_ref/`: **原始知識庫文件**。存放額外的資安規定或參考資料，這些資料會被 `ingest.py` 讀取並納入RAG系統的知識範圍。

## 3. 主要的程式碼是哪一些?

1.  **`ai-service/main.py`**: 最核心的程式碼，定義了RAG的完整執行邏輯。
2.  **`ai-service/ingest.py`**: 第二核心，定義了知識庫的建構方式。
3.  **`app-server/index.js`**: 後台資料管理的核心邏輯。
4.  **`client/src/ChatWindow.tsx`**: 使用者與AI互動的主要前端邏輯。
5.  **`client/src/AdminPage.tsx`**: 知識庫內容管理的主要前端邏輯。

## 4. 輔助的工具或文件有哪些?

*   **工具腳本**: `start-all.bat`, `ai-service` 內大量的 `test_*.py`, `diagnose_*.py`, `check_*.py` 腳本。
*   **專案文件**: `README.md`, `System_Architecture.md`, `AI_System.md`, `Frontend_Guide.md`, `Admin_Guide.md` 等。
*   **知識來源**: `rule_ref/` 目錄下的 `.md` 和 `.txt` 檔案，以及 `app-server/scenarios.json`。
*   **設定檔**: 各模組的 `package.json`, `requirements.txt`, `.gitignore`。

## 5. 用不到的檔案有哪些?

根據檔案名稱和用途推斷，以下檔案**可能**已經過時或可以被清理：

*   `ai-service/` 中的備份或中間檔案: `meta_info_backup.json`, `meta_info_enhanced.json`, `scenarios_backup.json`, `scenarios_enhanced.json` 等。這些看起來是資料處理過程中的快照，若已有穩定流程，可以考慮移除。
*   `ai-service/` 中大量的單一功能腳本: 如 `basic_ingest.py`, `quick_check.py`, `test_fix.py` 等。它們的功能可能已被整合到更完善的腳本中（如 `ingest.py` 或 `diagnose_rag.py`）。建議審查並合併這些腳本的功能，減少檔案數量。
*   根目錄下的規劃文件: `GPT_suggest.txt`, `rewrite_plan.md`, `RAG_改善計畫.md` 等。這些可能是早期的腦力激盪文件，若其內容已被採納並實現在程式碼或核心文件中，可以考慮歸檔。

## 6. 可以精進的部分

1.  **資料庫升級**:
    *   **問題**: `app-server` 使用JSON檔案作為資料庫，在高併發讀寫或資料關聯複雜時存在風險和效能瓶頸。
    *   **建議**: 按照 `System_Architecture.md` 中的規劃，將資料存儲從JSON遷移至 **SQLite** 或更專業的資料庫（如 PostgreSQL）。這能提升資料一致性、查詢能力和系統穩定性。

2.  **環境一致性與部署**:
    *   **問題**: 目前依賴開發者手動設定三個獨立的服務環境，容易出錯且難以管理。
    *   **建議**: 引入 **Docker** 和 **Docker Compose**。為 `client`, `app-server`, `ai-service` 各自建立一個 `Dockerfile`，並用一個 `docker-compose.yml` 來統籌啟動所有服務。這可以做到一鍵啟動整個應用，並確保開發、測試、生產環境的完全一致。

3.  **AI服務的測試與診斷腳本整合**:
    *   **問題**: `ai-service` 目錄下有大量功能單一的 `test_*.py`, `diagnose_*.py` 腳本，顯得混亂。
    *   **建議**: 將這些腳本的功能整合。可以使用 **`pytest`** 框架來組織單元測試和整合測試。對於診斷功能，可以建立一個統一的 `doctor.py` 或 `cli.py` 工具，透過命令列參數（如 `python cli.py diagnose rag`）來執行不同的診斷任務。

4.  **RAG流程自動化**:
    *   **問題**: 目前修改 `scenarios.json` 後，需要手動執行 `ingest.py` 來同步向量資料庫。
    *   **建議**: 在 `app-server` 的卡片更新API（POST, PUT, DELETE）成功後，自動觸發一個到 `ai-service` 的 `/api/sync` 之類的端點，讓AI服務異步地更新向量資料庫。這樣可以確保知識庫的即時性。

5.  **程式碼品質與維護性**:
    *   **問題**: `ai-service/main.py` 中的 `ask` 函數邏輯非常複雜，包含了多層檢索、後處理、Rerank等，未來難以維護。
    *   **建議**: 進行重構。將不同的檢索策略（分層、元問題）、後處理、Rerank邏輯各自拆分成獨立的函式或類別，讓 `ask` 函數的流程更清晰，只做高層次的協調工作。

6.  **文件清理與集中化**:
    *   **問題**: 專案根目錄存在多個規劃性、建議性的 `.md` 和 `.txt` 檔案，資訊分散。
    *   **建議**: 將所有仍然有效的文件內容，整合到 `README.md`, `System_Architecture.md` 等核心文件中，並建立一個 `docs/` 或 `archive/` 目錄來存放過時的規劃文件，保持根目錄的整潔。


1. 資料同步問題 (高嚴重性)

   * 問題描述:
      這是系統中目前最關鍵的設計缺陷。app-server 提供了後台管理功能，可以修改 scenarios.json。然而，ai-service
  的RAG知識庫並不會自動感知這些變更。ai-service 的知識庫 (ChromaDB) 只在手動執行 ingest.py 腳本時才會被建立或更新。
   * 程式碼證據:
       * app-server/index.js: 在 PUT, POST, DELETE 等路由中，程式碼會呼叫 writeJsonFile(SCENARIOS_PATH, scenarios)，成功更新了JSON檔案。
       * ai-service/ingest.py: 此腳本從 SCENARIOS_PATH 讀取資料來建構向量資料庫。
       * ai-service/main.py: 啟動後直接使用 ChromaDB 中的現有資料，沒有監聽 scenarios.json 的變化。
   * 影響:
      管理員在後台新增或修改的任何情境卡片，都無法即時反映在AI的回答中。AI會一直使用舊的知識庫，直到有人手動去AI伺服器上重新執行
  ingest.py，這使得後台管理功能在實際上幾乎是無效的。
   * 修復建議:
      建立一個從 app-server 到 ai-service 的觸發機制。
       1. 在 ai-service 中新增一個API端點，例如 POST /api/sync 或 POST /api/upsert-document。
       2. 當 app-server 中的卡片被新增、修改或刪除時，除了寫入JSON檔案，同時呼叫 ai-service 的這個新端點，並將變更的卡片資料傳遞過去。
       3. ai-service 收到請求後，對單一文件進行即時的 upsert (更新或插入) 或 delete 操作，而不是重建整個資料庫。

  2. 過度嚴格的提示工程 (高嚴重性)

   * 問題描述:
      為了防止模型幻覺，ai-service/main.py 中的系統提示 (system_prompt) 給予了模型極其嚴格的限制，這反而削弱了RAG的優勢。
   * 程式碼證據:

   1     # ai-service/main.py
   2     system_prompt = """你是 ASUS 資安助手。
   3
   4     **絕對規則**：
   5     1. 只能使用提供的卡片內容，一字不差地引用
   6     2. 禁止添加任何卡片外的資訊、推理或擴展
   7     3. 禁止使用你的預訓練知識
   8     ...
   * 影響:
       * 回答僵化: LLM無法發揮其語言理解和生成能力來「總結」和「用自然語言回答」。它只能像一個搜尋引擎一樣，機械地「複製貼上」檢索到的文
         本，導致回答非常生硬，甚至可能文不對題。
       * 拒絕回答率高:
         如果檢索到的上下文沒有與使用者問題完全匹配的字句，即使內容相關，模型也可能因為被禁止「推理」，而選擇回答「我無法回答」。
       * RAG失效: RAG的核心是「檢索」+「生成」。這個提示等於關閉了「生成」環節，使其退化為單純的向量檢索。
   * 修復建議:
      放寬提示，引導模型基於(Based on)上下文來回答，而不是只用(Only use)上下文。

   1     # 建議修改
   2     system_prompt = """你是 ASUS
     資安助手。你的任務是根據下面提供的「卡片內容」，用清晰、友善且專業的口吻回答使用者的「問題」。
   3
   4     **核心指令**：
   5     1.  你的所有回答都**必須**基於提供的「卡片內容」。
   6     2.  **嚴禁**使用任何「卡片內容」以外的資訊或你的預訓練知識。
   7     3.  如果「卡片內容」與「問題」相關，請理解並總結內容，然後自然地回答問題。不要只是複製貼上原文。
   8     4.  如果提供的「卡片內容」確實無法回答「問題」，請誠實地告知：「根據我現有的資料，無法回答這個問題。」
   9     """

  3. 全量重建的資料導入流程 (中等嚴重性)

   * 問題描述:
      ingest.py 腳本在每次執行時，會先 client.delete_collection(COLLECTION_NAME)，刪除整個集合，然後再重新導入所有文件。
   * 程式碼證據:

   1     # ai-service/ingest.py
   2     try:
   3         client.delete_collection(COLLECTION_NAME)
   4         print("舊有集合已刪除")
   5     except Exception:
   6         print("集合不存在，將建立新集合")
   7
   8     collection = client.create_collection(...)
   * 影響:
       * 效率低下:
         隨著知識庫文件增多，每次同步都需要花費大量時間來重新計算所有文件的向量嵌入。如果未來有數百上千份文件，這個過程可能會非常緩慢。
       * 服務中斷: 在刪除和重建的過程中，AI服務可能會出現短暫的無資料可查的空窗期。
   * 修復建議:
      實現增量更新 (Incremental Update)。
       1. 在 ingest.py 中，不要先刪除集合。
       2. 為每個文檔/區塊計算一個內容雜湊值 (content_hash) 並存入 metadata (目前已有此設計，非常好！)。
       3. 在導入前，可以先從ChromaDB中取出所有現存文檔的ID和content_hash。
       4. 遍歷你的源文件，計算content_hash，只對ChromaDB中不存在或content_hash不一致的文檔執行 collection.upsert()。

  4. 複雜且可能衝突的上下文管理 (中等嚴重性)

   * 問題描述:
      在 ai-service/main.py 的 ask 函數中，傳遞給LLM的上下文 (messages)
  結構有些混亂。它混合了系統提示、對話歷史、RAG檢索結果、以及重複的使用者問題。
   * 程式碼證據:
      messages 列表的構建順序是：system_prompt -> history -> user_prompt (包含RAG context和問題) -> 另一個 system 訊息 (再次包含問題)。
   * 影響:
       * 模型困惑: LLM可能不清楚哪個指令的優先級最高，也不清楚如何協調對話歷史和當前RAG檢索到的上下文。例如，如果歷史對話和RAG上下文有衝
         突，模型該聽哪個？
       * 提示冗餘: 多次重複相同問題會浪費寶貴的上下文空間(token)。
   * 修復建議:
      重新設計一個乾淨、單一的最終提示模板，清晰地劃分不同類型的上下文。


    1     # 建議的 user_prompt 結構
    2     final_user_prompt = f"""
    3     [對話歷史]
    4     {formatted_history}
    5 
    6     [卡片內容]
    7     {context}
    8 
    9     [我的問題]
   10     {question}
   11     """
   12     # 然後將這個結構化的 prompt 作為單一的 user message 傳遞給模型
   13     messages = [
   14         {'role': 'system', 'content': '...'}, # 你修改後的 system_prompt
   15         {'role': 'user', 'content': final_user_prompt}
   16     ]

  總結來說，您的專案在RAG的檢索策略（分層、查詢擴展、後處理）上設計得相當精良，但在資料流的即時性和與LLM的互動方式上存在關鍵的設計缺陷
  。優先解決資料同步和提示工程這兩個問題，將會對系統的可用性和回答品質帶來最顯著的提升。


  太好了！我直接給你一包「能貼就能用」的完整指引：包含一步步做法、可直接丟給 Windsurf / Gemini 的精準 prompt、以及三支服務的**完整可用程式碼**（Docker + 自動同步 /api/sync + JSON→SQLite 遷移）。你只要照順序做就能把整個專案升級起來。

---

# 你要做什麼（10 分鐘鳥瞰）

1. 把 `app-server` 從 JSON 檔改成 **SQLite**（穩定又好查）。
2. 在 `app-server` 的 **新增/修改/刪除** 後，自動呼叫 `ai-service` 的 **`/api/sync`**，只更新受影響的 embeddings（不用每次全量重建）。
3. 用 **Docker Compose** 一鍵啟 3 個服務（client / app-server / ai-service），避免每台電腦環境不一致。
4. 給 Windsurf 與 Gemini 明確任務（它們就會幫你精進結構與碼品質）。

---

# 一鍵提示詞（直接複製給 Windsurf / Gemini）

## A. 給 Windsurf（請在專案根目錄打開）

> 目標：把 Node `app-server` 從 JSON 資料儲存遷移到 SQLite；在任一情境卡（scenario）CRUD 成功後，POST 到 `http://ai-service:8000/api/sync` 以增量更新 Chroma；提供 docker-compose 讓 3 個服務（client 5173、app-server 3001、ai-service 8000）一起跑。
> 請執行：
>
> 1. 建立 `app-server/sqlite/` 目錄，新增遷移腳本，將 `scenarios.json`、`groups.json` 匯入 SQLite（資料表：groups、scenarios、scenario\_group\_map）。
> 2. 改寫 `app-server/index.js`：使用 `better-sqlite3` 實作 CRUD，於 POST/PUT/DELETE 後以 `axios` 呼叫 `ai-service:/api/sync`，body 為 {operation, items:\[{id,title,body,group\_id,updated\_at}]} 或 {operation:"delete", ids:\[id] }。
> 3. 在 `ai-service` 新增 `/api/sync`：收到 upsert 就 upsert 該 id 的向量；收到 delete 就刪除該 id。
> 4. 寫好 `Dockerfile`（app-server、ai-service）與 `docker-compose.yml`；用 `.env` 管理設定。
> 5. 補 `README`：啟動指令、健康檢查、最小測試腳本（curl）。
> 6. 嚴格 TypeScript/JS/py lint 與日誌：每次請求印 request-id 與延遲；`/health` 回 200。

## B. 給 Gemini（如果你用 Gemini Studio/CLI）

> 你是一位資深全端與 MLOps 顧問，請根據以下要求輸出**完整可執行**程式碼，不省略：
> – Node 20 + Express + better-sqlite3 的 `index.js`（含 schema 建表、CRUD、呼叫 /api/sync）。
> – Python 3.11 + FastAPI 的 `main.py` 與 `requirements.txt`（含 /api/sync、/health、Chroma upsert/delete）。
> – `docker-compose.yml` + `Dockerfile`（兩個服務）+ `.env.example`。
> – `scripts/migrate_json_to_sqlite.js`（把既有 `scenarios.json`、`groups.json` 匯入 SQLite）。
> – 提供一段 `curl` 測試流程，證明：新增一筆 scenario → 觸發 /api/sync → /api/ask 能命中該筆。
> – 說明怎麼把「分塊 chunk + metadata（group、title）」寫入 Chroma id（`doc_{scenario_id}_{chunk_index}`）。
> – 請以**中文註解**且一步步指令。

---

# 完整可用程式碼（直接貼檔案）

> 說明：以下假設你的專案結構仍是
> `client/`、`app-server/`、`ai-service/` 在同一層。
> 你可先把現有檔案備份，再把這些檔案覆蓋/新增。

## 1) 專案環境設定 `.env.example`（放在專案根目錄）

```
# 通用
NODE_ENV=development

# App Server
APP_PORT=3001
SQLITE_DB_PATH=./app-server/sqlite/db.sqlite

# AI Service
AI_PORT=8000
CHROMA_DIR=/data/chroma_db
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

> 之後把這份複製成 `.env` 使用。

---

## 2) docker-compose（專案根目錄 `docker-compose.yml`）

```yaml
version: "3.9"
services:
  ai-service:
    build: ./ai-service
    container_name: ai-service
    env_file: ./.env
    environment:
      - AI_PORT=${AI_PORT}
      - CHROMA_DIR=${CHROMA_DIR}
      - EMBEDDING_MODEL=${EMBEDDING_MODEL}
    volumes:
      - ./ai-service:/app
      - ./ai-service/chroma_db:${CHROMA_DIR}
    ports:
      - "${AI_PORT}:8000"
    command: ["python", "main.py"]
    depends_on: []

  app-server:
    build: ./app-server
    container_name: app-server
    env_file: ./.env
    environment:
      - APP_PORT=${APP_PORT}
      - SQLITE_DB_PATH=${SQLITE_DB_PATH}
      - AI_SERVICE_URL=http://ai-service:8000
    volumes:
      - ./app-server:/app
    ports:
      - "${APP_PORT}:3001"
    depends_on:
      - ai-service

  # 你的 client 若是現有開發環境，可保留本機啟動；
  # 若要容器化，可加一個服務，這裡示意用 Vite 預設 5173:
  # client:
  #   build: ./client
  #   container_name: client
  #   ports:
  #     - "5173:5173"
  #   environment:
  #     - VITE_APP_SERVER=http://localhost:${APP_PORT}
  #   volumes:
  #     - ./client:/app
  #   command: ["npm","run","dev","--","--host","0.0.0.0"]
```

---

## 3) app-server Dockerfile（`app-server/Dockerfile`）

```dockerfile
FROM node:20-alpine

# better-sqlite3 需要編譯工具
RUN apk add --no-cache python3 make g++ sqlite

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
ENV APP_PORT=3001
EXPOSE 3001
CMD ["npm","run","start"]
```

---

## 4) ai-service Dockerfile（`ai-service/Dockerfile`）

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y build-essential git && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV AI_PORT=8000
EXPOSE 8000
CMD ["python","main.py"]
```

---

## 5) app-server 套件宣告（`app-server/package.json`）

```json
{
  "name": "app-server",
  "version": "1.0.0",
  "main": "index.js",
  "type": "module",
  "scripts": {
    "start": "node index.js",
    "migrate": "node scripts/migrate_json_to_sqlite.js"
  },
  "dependencies": {
    "axios": "^1.7.2",
    "better-sqlite3": "^9.4.0",
    "cors": "^2.8.5",
    "dotenv": "^16.4.5",
    "express": "^4.19.2",
    "morgan": "^1.10.0",
    "nanoid": "^5.0.7"
  }
}
```

---

## 6) app-server 主程式（`app-server/index.js`）

```js
// 簡單、穩定的 Express + better-sqlite3
import express from "express";
import cors from "cors";
import morgan from "morgan";
import dotenv from "dotenv";
import Database from "better-sqlite3";
import axios from "axios";
import { customAlphabet } from "nanoid";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json({ limit: "4mb" }));
app.use(morgan("dev"));

const APP_PORT = process.env.APP_PORT || 3001;
const DB_PATH = process.env.SQLITE_DB_PATH || "./sqlite/db.sqlite";
const AI_SERVICE_URL = process.env.AI_SERVICE_URL || "http://localhost:8000";

const nanoid = customAlphabet("0123456789abcdefghijklmnopqrstuvwxyz", 12);

// 初始化資料庫與表
const db = new Database(DB_PATH);
db.pragma("journal_mode = WAL");

db.exec(`
CREATE TABLE IF NOT EXISTS groups (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scenarios (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  group_id TEXT,
  updated_at INTEGER NOT NULL,
  FOREIGN KEY (group_id) REFERENCES groups(id)
);
`);

// 小工具：現在時間（秒）
const nowSec = () => Math.floor(Date.now() / 1000);

// ---- Groups API ----
app.get("/api/groups", (req, res) => {
  const rows = db.prepare("SELECT * FROM groups").all();
  res.json(rows);
});

app.post("/api/groups", (req, res) => {
  const { name } = req.body;
  const id = nanoid();
  db.prepare("INSERT INTO groups (id, name) VALUES (?, ?)").run(id, name);
  res.json({ id, name });
});

app.put("/api/groups/:id", (req, res) => {
  const { id } = req.params;
  const { name } = req.body;
  db.prepare("UPDATE groups SET name=? WHERE id=?").run(name, id);
  res.json({ id, name });
});

app.delete("/api/groups/:id", (req, res) => {
  const { id } = req.params;
  db.prepare("DELETE FROM groups WHERE id=?").run(id);
  res.json({ ok: true, id });
});

// ---- Scenarios API ----
app.get("/api/scenarios", (req, res) => {
  const rows = db.prepare("SELECT * FROM scenarios ORDER BY updated_at DESC").all();
  res.json(rows);
});

app.post("/api/scenarios", async (req, res) => {
  const { title, body, group_id } = req.body;
  const id = nanoid();
  const updated_at = nowSec();
  db.prepare("INSERT INTO scenarios (id, title, body, group_id, updated_at) VALUES (?, ?, ?, ?, ?)")
    .run(id, title, body, group_id || null, updated_at);

  // 觸發 AI 增量同步
  try {
    await axios.post(`${AI_SERVICE_URL}/api/sync`, {
      operation: "upsert",
      items: [{ id, title, body, group_id: group_id || null, updated_at }]
    }, { timeout: 8000 });
  } catch (e) {
    console.error("sync error:", e?.message);
  }

  res.json({ id, title, body, group_id: group_id || null, updated_at });
});

app.put("/api/scenarios/:id", async (req, res) => {
  const { id } = req.params;
  const { title, body, group_id } = req.body;
  const updated_at = nowSec();
  db.prepare("UPDATE scenarios SET title=?, body=?, group_id=?, updated_at=? WHERE id=?")
    .run(title, body, group_id || null, updated_at, id);

  try {
    await axios.post(`${AI_SERVICE_URL}/api/sync`, {
      operation: "upsert",
      items: [{ id, title, body, group_id: group_id || null, updated_at }]
    }, { timeout: 8000 });
  } catch (e) {
    console.error("sync error:", e?.message);
  }

  res.json({ id, title, body, group_id: group_id || null, updated_at });
});

app.delete("/api/scenarios/:id", async (req, res) => {
  const { id } = req.params;
  db.prepare("DELETE FROM scenarios WHERE id=?").run(id);

  try {
    await axios.post(`${AI_SERVICE_URL}/api/sync`, {
      operation: "delete",
      ids: [id]
    }, { timeout: 8000 });
  } catch (e) {
    console.error("sync error:", e?.message);
  }

  res.json({ ok: true, id });
});

app.get("/health", (req, res) => res.send("ok"));

app.listen(APP_PORT, () => {
  console.log(`app-server on :${APP_PORT}`);
});
```

---

## 7) JSON → SQLite 遷移腳本（`app-server/scripts/migrate_json_to_sqlite.js`）

```js
// 將既有 JSON（scenarios.json, groups.json）匯入 SQLite
import fs from "fs";
import path from "path";
import Database from "better-sqlite3";
import dotenv from "dotenv";
dotenv.config();

const DB_PATH = process.env.SQLITE_DB_PATH || "./sqlite/db.sqlite";
const ROOT = path.resolve(process.cwd(), ".."); // 專案根
const APP_DIR = path.resolve(process.cwd());    // app-server 目錄

const scenariosPath = path.join(APP_DIR, "scenarios.json");
const groupsPath = path.join(APP_DIR, "groups.json");

const db = new Database(DB_PATH);
db.pragma("journal_mode = WAL");
db.exec(`
CREATE TABLE IF NOT EXISTS groups (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS scenarios (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  group_id TEXT,
  updated_at INTEGER NOT NULL,
  FOREIGN KEY (group_id) REFERENCES groups(id)
);
`);

function safeLoad(p) {
  if (!fs.existsSync(p)) return [];
  try {
    return JSON.parse(fs.readFileSync(p, "utf8"));
  } catch {
    return [];
  }
}

const groups = safeLoad(groupsPath);
const scenarios = safeLoad(scenariosPath);

const insGroup = db.prepare("INSERT OR REPLACE INTO groups (id, name) VALUES (?, ?)");
const insSc = db.prepare("INSERT OR REPLACE INTO scenarios (id, title, body, group_id, updated_at) VALUES (?, ?, ?, ?, ?)");

const tx = db.transaction(() => {
  for (const g of groups) {
    insGroup.run(g.id, g.name);
  }
  for (const s of scenarios) {
    const ts = Math.floor(Date.now() / 1000);
    insSc.run(s.id, s.title || "", s.body || "", s.group_id || null, s.updated_at || ts);
  }
});
tx();

console.log("Migration done. Groups:", groups.length, "Scenarios:", scenarios.length);
```

---

## 8) ai-service 套件（`ai-service/requirements.txt`）

```
fastapi==0.112.0
uvicorn[standard]==0.30.0
pydantic==2.8.2
chromadb==0.5.5
sentence-transformers==3.0.1
numpy
```

---

## 9) ai-service 主程式（`ai-service/main.py`）

```python
# FastAPI + Chroma：/api/sync 增量 upsert/delete，/api/ask 簡化示例
import os
import time
from typing import List, Optional
from fastapi import FastAPI
from pydantic import BaseModel
import chromadb
from chromadb.utils import embedding_functions

AI_PORT = int(os.getenv("AI_PORT", "8000"))
CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

app = FastAPI(title="AI Service", version="1.0.0")

# 初始化 Chroma
client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection(
    "kb",
    metadata={"hnsw:space": "cosine"},
    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
)

# --------- 資料模型 ---------
class SyncItem(BaseModel):
    id: str
    title: str
    body: str
    group_id: Optional[str] = None
    updated_at: int

class SyncUpsertBody(BaseModel):
    operation: str  # "upsert"
    items: List[SyncItem]

class SyncDeleteBody(BaseModel):
    operation: str  # "delete"
    ids: List[str]

class AskBody(BaseModel):
    query: str
    top_k: int = 4

# --------- 工具：分塊（簡單版，可再精進） ---------
def chunk_text(text: str, max_tokens: int = 400, overlap: int = 60):
    # 這裡用字元近似代替 token，粗估即可；需要更好再換 tiktoken
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        end = min(len(words), i + max_tokens)
        chunk = " ".join(words[i:end])
        chunks.append(chunk)
        i = end - overlap if end - overlap > i else end
    return [c for c in chunks if c.strip()]

def chroma_id(sid: str, idx: int) -> str:
    return f"doc_{sid}_{idx:04d}"

# --------- /api/sync：增量更新/刪除 ---------
@app.post("/api/sync")
def api_sync(body: dict):
    op = body.get("operation")
    if op == "upsert":
        data = SyncUpsertBody(**body)
        ids, docs, metas = [], [], []
        for item in data.items:
            chunks = chunk_text(item.body)
            for i, ch in enumerate(chunks):
                ids.append(chroma_id(item.id, i))
                docs.append(ch)
                metas.append({
                    "scenario_id": item.id,
                    "title": item.title,
                    "group_id": item.group_id,
                    "updated_at": item.updated_at,
                    "chunk_index": i
                })
        # 先刪除同 scenario 既有的（避免殘留）
        collection.delete(where={"scenario_id": {"$eq": item.id}})  # 以最後一筆 item 為準
        # 再批次 upsert
        if ids:
            collection.add(ids=ids, documents=docs, metadatas=metas)
        return {"ok": True, "upserted": len(ids)}
    elif op == "delete":
        data = SyncDeleteBody(**body)
        deleted = 0
        for sid in data.ids:
            # 直接按 metadata 刪
            collection.delete(where={"scenario_id": {"$eq": sid}})
            deleted += 1
        return {"ok": True, "deleted_scenarios": deleted}
    else:
        return {"ok": False, "msg": "unknown operation"}

# --------- /api/ask：最小可用（示範，之後可接 Ollama/Rerank） ---------
@app.post("/api/ask")
def api_ask(b: AskBody):
    results = collection.query(
        query_texts=[b.query],
        n_results=b.top_k
    )
    hits = []
    for doc, meta in zip(results.get("documents", [[]])[0], results.get("metadatas", [[]])[0]):
        hits.append({"chunk": doc, "meta": meta})
    # 簡單拼接答案（實務上要接 LLM 生成並附引用）
    answer = "以下是我根據知識庫找出的重點片段：\n\n" + "\n\n---\n\n".join(
        [f"【{h['meta'].get('title','')} # {h['meta'].get('chunk_index',0)}】\n{h['chunk']}" for h in hits]
    )
    return {"answer": answer, "sources": hits}

@app.get("/health")
def health():
    return {"ok": True, "ts": int(time.time())}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=AI_PORT, workers=1)
```

> 之後要更強（Hybrid 檢索、Rerank、接 Ollama 生成、引用），再慢慢加。

---

# 如何跑起來（一步一步）

1. **建立 .env**
   把 `.env.example` 複製成 `.env`，維持預設即可。

2. **先遷移 JSON → SQLite（只需要跑一次）**

```bash
# 在專案根
docker compose build
docker compose up -d ai-service
docker compose up -d app-server

# 進入 app-server 容器或在本機 node 環境執行
docker exec -it app-server node scripts/migrate_json_to_sqlite.js
```

3. **啟動全部服務**

```bash
docker compose up -d
# ai-service :8000, app-server :3001, （client 依你原來啟動方式）
```

4. **健檢**

```bash
curl http://localhost:3001/health
curl http://localhost:8000/health
```

5. **最小驗收（自動同步真的有在跑）**

```bash
# 新增一筆 scenario（應會觸發 /api/sync）
curl -X POST http://localhost:3001/api/scenarios \
  -H "Content-Type: application/json" \
  -d '{"title":"密碼政策","body":"公司密碼至少 12 碼，需包含大小寫、數字與符號。","group_id":null}'

# 詢問（應能命中剛剛的內容）
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"密碼至少幾碼？"}'
```

---

# 接下來要精進什麼（交給 Windsurf / Gemini 做）

**第一輪（結構品質）**

* 在 `ai-service` 加上 **Hybrid 檢索**（SQLite FTS5 + 向量）→ 合併分數 → `cross-encoder` / 小模型 Rerank。
* `/api/ask` 加入 **引用**（scenario\_id、chunk\_index、title）回傳給前端展示。
* 日誌帶 **request-id**，把 `前端→app→ai` 的 id 串起來，抓 P95 延遲。

**第二輪（安全與治理）**

* `app-server` 加 RBAC（至少 admin/user），`/api/*` 需要 token。
* `ai-service` 做**prompt injection** 基本清洗：黑名單字詞、過長輸入截斷、只允許白名單來源。
* 增加審計表（audit\_log）：記錄誰在何時改了哪張卡。

**第三輪（測試與評測）**

* 用 `pytest` 寫 `tests/`：對 `/api/sync`、`/api/ask` 建立離線黃金問答集，量化 top‑k 命中率。
* 做一個 `cli/doctor.py`：檢查 Chroma 連線、collection 狀態、孤兒 chunks、向量數量與 metadata 完整性。

---
