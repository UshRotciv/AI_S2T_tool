# 資料庫與 AI RAG 系統的同步機制

本文檔旨在解釋 Admin 後台的卡片資料庫 (`scenarios.json`) 如何與 AI 的 RAG (Retrieval-Augmented Generation) 系統進行互動與同步，確保 AI 能夠基於最新的知識來回答問題。

---

## 1. RAG 系統與向量資料庫簡介

### 什麼是 RAG？

RAG (Retrieval-Augmented Generation) 是一種讓大型語言模型 (LLM) 在生成回答前，先從一個外部的、可信的知識庫中「檢索」相關資訊的技術。這能有效地解決以下問題：

-   **知識過時**：LLM 的內部知識停留在其訓練資料的截止日期。
-   **產生幻覺**：在缺乏特定知識時，LLM 可能會編造不實的資訊。

**RAG 的核心流程：**
1.  **接收問題**：使用者向 AI 提出問題。
2.  **檢索 (Retrieval)**：系統將問題轉換為「向量」，然後在「向量資料庫」中搜索最相似、最相關的知識片段。
3.  **增強 (Augmentation)**：將檢索到的知識片段，連同原始問題，一起作為新的提示 (Prompt) 提供給 LLM。
4.  **生成 (Generation)**：LLM 基於提供的上下文（原始問題 + 檢索到的知識）生成一個更準確、更具事實性的回答。

### 什麼是向量資料庫 (Vector Database)？

向量資料庫專門用於儲存和查詢「向量」。向量是將文字、圖片等非結構化資料轉換成的一串數字，它能捕捉資料的語意特徵。

在本專案中，我們使用 `ChromaDB` 作為向量資料庫，它儲存了所有卡片知識的向量表示。

---

## 2. 資料同步流程：從 Admin 更新到 RAG

當您在 Admin 後台新增、編輯或刪除一張卡片時，其實是更新了 `scenarios.json` 檔案。為了讓 AI 的 RAG 系統能學習到這些變動，我們設計了一個同步流程。

**核心流程如下：**

1.  **手動觸發同步**：
    -   目前系統的設計是，當 `scenarios.json` 的內容有重要更新後，需要**手動執行一個同步腳本**。這個腳本位於 `ai-service` 目錄下。

2.  **腳本執行過程 (`ai-service/main.py`)**：
    -   **讀取資料**：腳本首先會讀取 `app-server/scenarios.json` 的完整內容。
    -   **清空舊知識**：為了確保知識庫的純淨，腳本會先清空 `ChromaDB` 中所有舊的卡片資料。
    -   **文本轉換與切分**：腳本會遍歷每一張卡片 (`scenario`)，並將其內容（如 `title`, `question`, `answer` 等）組合成一段有意義的文本。
    -   **生成向量 (Embeddings)**：腳本會使用一個「嵌入模型 (Embedding Model)」，將每一段文本轉換成一個高維度的向量。
    -   **存入向量資料庫**：最後，腳本將生成的向量，連同其對應的原始文本和元資料 (Metadata)，一起存入 `ChromaDB`。

3.  **完成同步**：
    -   一旦所有新資料都已轉換並存入 `ChromaDB`，RAG 系統的知識庫就更新完成了。
    -   下次使用者向 AI 提問時，AI 就能檢索到這些最新的卡片知識。

**視覺化流程：**

```mermaid
graph TD
    A[Admin 後台操作] --> B(更新 scenarios.json);
    C(手動執行同步腳本<br/>`ai-service/main.py`) --> D{讀取 scenarios.json};
    D --> E{清空 ChromaDB 舊資料};
    E --> F{遍歷每張卡片};
    F --> G{生成文本向量 (Embeddings)};
    G --> H{將向量與文本存入 ChromaDB};
    H --> I(RAG 知識庫更新完成);
```

---

## 3. 關鍵元件說明

-   **`app-server/scenarios.json`**：
    -   **角色**：原始的、人類可讀的「知識來源 (Source of Truth)」。

-   **`ai-service/`**：
    -   **角色**：一個獨立的 Python 服務，負責所有與 AI 相關的任務。
    -   **`main.py`**：核心的同步腳本，扮演著 ETL (Extract, Transform, Load) 的角色，將 JSON 資料轉換並載入到向量資料庫。

-   **`ai-service/chroma_db/`**：
    -   **角色**：`ChromaDB` 的資料儲存目錄，是 RAG 系統的「大腦」，儲存了所有知識的向量化表示，供 AI 快速檢索。

## 4. 未來展望

為了提升效率，未來的系統可以考慮將「手動觸發」改為「自動化觸發」。例如，可以監聽 `scenarios.json` 檔案的變動，一旦檔案被修改，就自動執行同步腳本，實現無縫的知識更新。
