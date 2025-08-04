# 資訊卡片系統：資料庫結構與前端對應設計

本文檔旨在說明本專案後端資料儲存的結構，以及前端 React 應用程式如何解析並呈現這些資料。

---

## 1. 後端資料庫結構

本專案採用兩個核心的 JSON 檔案作為輕量級資料庫，分別儲存「群組」和「卡片（情境）」的資料。這種設計簡潔且易於管理。

### `groups.json` - 群組資料

此檔案定義了所有卡片可以歸屬的群組。

- **用途**：建立卡片的分類容器，例如「基礎概念」、「進階技巧」等。
- **結構**：一個包含多個 `Group` 物件的陣列。

**欄位說明：**

| 欄位 | 型別 | 描述 |
| :--- | :--- | :--- |
| `id` | `string` | 群組的唯一識別碼，作為主鍵（Primary Key）。 |
| `name` | `string` | 顯示在介面上的群組名稱。 |
| `order`| `number` | 用於對群組本身進行排序的數字。 |

**範例 (`groups.json`)：**
```json
[
  {
    "id": "group-1",
    "name": "基礎概念",
    "order": 1
  },
  {
    "id": "group-2",
    "name": "社交工程案例",
    "order": 2
  }
]
```

### `scenarios.json` - 卡片資料

此檔案定義了系統中所有的獨立卡片（情境）。

- **用途**：儲存每張卡片的具體內容。
- **結構**：一個包含多個 `Scenario` 物件的陣列。

**欄位說明：**

| 欄位 | 型別 | 描述 |
| :--- | :--- | :--- |
| `id` | `string` | 卡片的唯一識別碼，作為主鍵。 |
| `category` | `string` | 卡片的分類標籤。 |
| `title` | `string` | 卡片的標題。 |
| `question` | `string` | 卡片呈現的問題或情境。 |
| `answer` | `string` | 對應問題的解答。 |
| `learnings` | `string[]` | 一個包含多個學習重點的字串陣列。 |
| `groupId` | `string` | **核心關聯欄位**。此 ID 對應 `groups.json` 中的某個 `id`，表示這張卡片屬於哪個群組。 |
| `order` | `number` | 用於對群組內的卡片進行排序。 |

**範例 (`scenarios.json`)：**
```json
[
  {
    "id": "scenario-1722398167476-c5a38f",
    "category": "社交工程",
    "title": "可疑的釣魚郵件",
    "question": "您收到一封來自銀行的緊急郵件，要求立即點擊連結更新帳戶資訊，您該怎麼做？",
    "answer": "切勿點擊郵件中的任何連結。直接前往銀行官方網站，或使用官方 App 登入檢查帳戶狀態。",
    "learnings": [
      "警惕緊急或威脅性用語",
      "檢查寄件者 Email 地址",
      "不透過不明連結登入敏感帳戶"
    ],
    "groupId": "group-2",
    "order": 1
  }
]
```

---

## 2. 前後端對應與渲染邏輯

前端 `AdminPage.tsx` 元件透過 API 從後端取得資料後，依據 `groupId` 的關聯性，動態地將卡片組織到對應的群組中顯示。

**渲染流程如下：**

1.  **載入資料**：
    -   `AdminPage` 元件掛載後，會呼叫後端 API（`/api/groups` 和 `/api/scenarios`）。
    -   取得的群組和卡片資料分別存入 React 的 `groups` 和 `scenarios` 狀態（State）中。

2.  **遍歷群組 (Outer Loop)**：
    -   React 介面會 `map`（遍歷）`groups` 陣列。
    -   對於每一個 `group` 物件，它會先渲染出一個群組的容器，並顯示 `group.name` 作為標題。

3.  **篩選與渲染卡片 (Inner Loop)**：
    -   在每個群組的渲染過程中，程式會 `filter`（篩選）完整的 `scenarios` 陣列。
    -   篩選條件是：找出所有 `scenario.groupId` 等於當前 `group.id` 的卡片。
    -   最後，程式會 `map`（遍歷）這個篩選出來的卡片子集，並在該群組容器內渲染出每一張卡片的詳細內容（標題、問題等）。

**視覺化流程：**

```mermaid
graph TD
    A[後端 API] -- /api/groups --> B(前端 groups 狀態);
    A -- /api/scenarios --> C(前端 scenarios 狀態);

    D{渲染 AdminPage} --> E[遍歷 groups 狀態];
    E -- 對於每個 group --> F{渲染群組容器 (顯示 group.name)};
    F --> G[從 scenarios 狀態中篩選卡片<br/>(scenario.groupId === group.id)];
    G --> H[遍歷篩選後的卡片];
    H -- 對於每張 scenario --> I(在群組容器內渲染卡片);
```

---

## 3. 總結

本專案的資料庫設計採用了類似「關聯式資料庫」的概念，但實作上僅使用兩個 JSON 檔案。透過 `groupId` 這個「外鍵 (Foreign Key)」，成功地在 `scenarios` 和 `groups` 之間建立了清晰的一對多（One-to-Many）關係。

這種設計的優點是：
-   **結構清晰**：資料分開儲存，職責分明。
-   **擴充性佳**：未來可以輕易地為群組或卡片增加新欄位。
-   **渲染高效**：前端透過簡單的遍歷和篩選，就能輕鬆建構出巢狀的視覺結構，無需複雜的資料查詢。
