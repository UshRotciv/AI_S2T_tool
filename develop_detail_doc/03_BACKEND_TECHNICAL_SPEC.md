# 後端技術規格文檔 - Node.js + Express + SQLite

## 技術棧概覽

### 核心框架
- **Node.js**: 18.17.0+ - JavaScript運行環境
- **Express.js**: 4.18.2 - Web應用框架
- **SQLite3**: 5.1.6 - 輕量級關係數據庫
- **CORS**: 2.8.5 - 跨域資源共享中間件

### 開發工具
- **nodemon**: 3.0.1 - 開發時自動重啟
- **dotenv**: 16.3.1 - 環境變量管理

## 服務器架構

### 主服務器配置 (`app-server/index.js`)

**基本設置**:
```javascript
const express = require('express');
const cors = require('cors');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3001;

// 中間件配置
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:3002'],
  credentials: true
}));
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));
```

**數據庫連接**:
```javascript
const db = new sqlite3.Database('./database.db', (err) => {
  if (err) {
    console.error('數據庫連接錯誤:', err.message);
  } else {
    console.log('已連接到SQLite數據庫');
    initializeDatabase();
  }
});
```

## API端點詳細規格

### 1. 情境管理API

#### GET /api/scenarios
**功能**: 獲取所有情境數據  
**響應格式**:
```json
[
  {
    "id": 1,
    "title": "使用弱密碼的危險性",
    "category": "A",
    "question": "你在設定新帳戶時...",
    "answer": "使用強密碼是...",
    "keyPoints": ["密碼複雜度", "定期更換"],
    "difficulty": "初級",
    "tags": ["密碼安全", "帳戶保護"]
  }
]
```

**實現代碼**:
```javascript
app.get('/api/scenarios', (req, res) => {
  const query = `
    SELECT id, title, category, question, answer, 
           key_points as keyPoints, difficulty, tags
    FROM scenarios 
    ORDER BY id ASC
  `;
  
  db.all(query, [], (err, rows) => {
    if (err) {
      console.error('查詢錯誤:', err);
      res.status(500).json({ error: '數據庫查詢失敗' });
    } else {
      // 處理JSON字段
      const processedRows = rows.map(row => ({
        ...row,
        keyPoints: JSON.parse(row.keyPoints || '[]'),
        tags: JSON.parse(row.tags || '[]')
      }));
      res.json(processedRows);
    }
  });
});
```

#### GET /api/scenarios/:id
**功能**: 獲取特定情境詳情  
**參數**: `id` - 情境ID  
**響應**: 單個情境對象

#### POST /api/scenarios
**功能**: 創建新情境  
**權限**: 管理員  
**請求體**:
```json
{
  "title": "情境標題",
  "category": "A",
  "question": "情境問題",
  "answer": "標準答案",
  "keyPoints": ["重點1", "重點2"],
  "difficulty": "中級",
  "tags": ["標籤1", "標籤2"]
}
```

#### PUT /api/scenarios/:id
**功能**: 更新情境  
**參數**: `id` - 情境ID  
**請求體**: 更新的情境數據

#### DELETE /api/scenarios/:id
**功能**: 刪除情境  
**參數**: `id` - 情境ID

### 2. 分類管理API

#### GET /api/categories
**功能**: 獲取所有分類  
**響應格式**:
```json
[
  {
    "id": "A",
    "name": "基礎安全",
    "description": "基本的資安概念",
    "color": "#2196F3",
    "count": 15
  }
]
```

### 3. 統計API

#### GET /api/stats
**功能**: 獲取系統統計數據  
**響應格式**:
```json
{
  "totalScenarios": 45,
  "categoryCounts": {
    "A": 15,
    "B": 12,
    "C": 10,
    "D": 8
  },
  "difficultyDistribution": {
    "初級": 20,
    "中級": 15,
    "高級": 10
  }
}
```

## 數據庫設計

### 數據庫初始化
```javascript
function initializeDatabase() {
  // 創建情境表
  db.run(`
    CREATE TABLE IF NOT EXISTS scenarios (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      category TEXT NOT NULL,
      question TEXT NOT NULL,
      answer TEXT NOT NULL,
      key_points TEXT DEFAULT '[]',
      difficulty TEXT DEFAULT '中級',
      tags TEXT DEFAULT '[]',
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // 創建分類表
  db.run(`
    CREATE TABLE IF NOT EXISTS categories (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      description TEXT,
      color TEXT DEFAULT '#757575',
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // 創建用戶會話表
  db.run(`
    CREATE TABLE IF NOT EXISTS user_sessions (
      id TEXT PRIMARY KEY,
      user_data TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      last_active DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // 插入默認分類
  insertDefaultCategories();
}
```

### 數據表結構

#### scenarios表
```sql
CREATE TABLE scenarios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,                    -- 情境標題
  category TEXT NOT NULL,                 -- 分類 (A/B/C/D)
  question TEXT NOT NULL,                 -- 情境問題
  answer TEXT NOT NULL,                   -- 標準答案
  key_points TEXT DEFAULT '[]',           -- 學習重點 (JSON)
  difficulty TEXT DEFAULT '中級',         -- 難度級別
  tags TEXT DEFAULT '[]',                 -- 標籤 (JSON)
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### categories表
```sql
CREATE TABLE categories (
  id TEXT PRIMARY KEY,                    -- 分類ID (A/B/C/D)
  name TEXT NOT NULL,                     -- 分類名稱
  description TEXT,                       -- 分類描述
  color TEXT DEFAULT '#757575',           -- 分類顏色
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 中間件與安全

### 1. CORS配置
```javascript
const corsOptions = {
  origin: function (origin, callback) {
    const allowedOrigins = [
      'http://localhost:3000',
      'http://localhost:3002',
      'http://127.0.0.1:3000',
      'http://127.0.0.1:3002'
    ];
    
    if (!origin || allowedOrigins.indexOf(origin) !== -1) {
      callback(null, true);
    } else {
      callback(new Error('不允許的CORS來源'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
};

app.use(cors(corsOptions));
```

### 2. 請求日誌中間件
```javascript
app.use((req, res, next) => {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${req.method} ${req.path}`);
  next();
});
```

### 3. 錯誤處理中間件
```javascript
app.use((err, req, res, next) => {
  console.error('服務器錯誤:', err.stack);
  res.status(500).json({
    error: '內部服務器錯誤',
    message: process.env.NODE_ENV === 'development' ? err.message : '服務暫時不可用'
  });
});
```

### 4. 輸入驗證
```javascript
const validateScenario = (req, res, next) => {
  const { title, category, question, answer } = req.body;
  
  if (!title || !category || !question || !answer) {
    return res.status(400).json({
      error: '缺少必要字段',
      required: ['title', 'category', 'question', 'answer']
    });
  }
  
  if (!['A', 'B', 'C', 'D'].includes(category)) {
    return res.status(400).json({
      error: '無效的分類',
      validCategories: ['A', 'B', 'C', 'D']
    });
  }
  
  next();
};
```

## 數據處理與工具函數

### 1. JSON字段處理
```javascript
const processScenarioData = (row) => {
  return {
    ...row,
    keyPoints: JSON.parse(row.key_points || '[]'),
    tags: JSON.parse(row.tags || '[]')
  };
};

const prepareScenarioForDB = (data) => {
  return {
    ...data,
    key_points: JSON.stringify(data.keyPoints || []),
    tags: JSON.stringify(data.tags || [])
  };
};
```

### 2. 分頁處理
```javascript
const getPaginatedResults = (req, res, baseQuery, countQuery) => {
  const page = parseInt(req.query.page) || 1;
  const limit = parseInt(req.query.limit) || 10;
  const offset = (page - 1) * limit;
  
  // 獲取總數
  db.get(countQuery, [], (err, countResult) => {
    if (err) {
      return res.status(500).json({ error: '查詢失敗' });
    }
    
    const total = countResult.count;
    const totalPages = Math.ceil(total / limit);
    
    // 獲取分頁數據
    const paginatedQuery = `${baseQuery} LIMIT ? OFFSET ?`;
    db.all(paginatedQuery, [limit, offset], (err, rows) => {
      if (err) {
        return res.status(500).json({ error: '查詢失敗' });
      }
      
      res.json({
        data: rows.map(processScenarioData),
        pagination: {
          page,
          limit,
          total,
          totalPages,
          hasNext: page < totalPages,
          hasPrev: page > 1
        }
      });
    });
  });
};
```

## 性能優化

### 1. 數據庫索引
```javascript
function createIndexes() {
  db.run('CREATE INDEX IF NOT EXISTS idx_scenarios_category ON scenarios(category)');
  db.run('CREATE INDEX IF NOT EXISTS idx_scenarios_difficulty ON scenarios(difficulty)');
  db.run('CREATE INDEX IF NOT EXISTS idx_scenarios_created_at ON scenarios(created_at)');
}
```

### 2. 連接池管理
```javascript
const dbPool = {
  connections: [],
  maxConnections: 10,
  
  getConnection() {
    if (this.connections.length > 0) {
      return this.connections.pop();
    }
    return new sqlite3.Database('./database.db');
  },
  
  releaseConnection(db) {
    if (this.connections.length < this.maxConnections) {
      this.connections.push(db);
    } else {
      db.close();
    }
  }
};
```

### 3. 緩存策略
```javascript
const NodeCache = require('node-cache');
const cache = new NodeCache({ stdTTL: 600 }); // 10分鐘緩存

app.get('/api/scenarios', (req, res) => {
  const cacheKey = 'all_scenarios';
  const cachedData = cache.get(cacheKey);
  
  if (cachedData) {
    return res.json(cachedData);
  }
  
  // 數據庫查詢...
  db.all(query, [], (err, rows) => {
    if (!err) {
      const processedData = rows.map(processScenarioData);
      cache.set(cacheKey, processedData);
      res.json(processedData);
    }
  });
});
```

## 部署配置

### package.json
```json
{
  "name": "confidential-expert-ai-server",
  "version": "2.0.0",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "dev": "nodemon index.js",
    "test": "jest",
    "migrate": "node scripts/migrate.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "sqlite3": "^5.1.6",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1"
  },
  "devDependencies": {
    "nodemon": "^3.0.1",
    "jest": "^29.7.0"
  }
}
```

### 環境變量 (.env)
```bash
NODE_ENV=production
PORT=3001
DB_PATH=./database.db
CORS_ORIGIN=http://localhost:3002
LOG_LEVEL=info
```

### 啟動腳本
```bash
#!/bin/bash
# start-server.sh

echo "啟動後端服務器..."
cd app-server
npm install
npm start
```

---

**文檔版本**: 1.0  
**最後更新**: 2025-08-13  
**技術負責**: 後端開發團隊
