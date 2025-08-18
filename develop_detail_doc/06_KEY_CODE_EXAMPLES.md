# 關鍵代碼示例文檔

## 前端核心代碼示例

### 1. 瀑布流佈局實現 (HomePage.tsx)

```typescript
import Masonry from 'react-masonry-css';

const breakpointColumnsObj = {
  default: 4,
  1100: 3,
  700: 2,
  500: 1
};

// 瀑布流渲染
<Masonry
  breakpointCols={breakpointColumnsObj}
  className="masonry-grid"
  columnClassName="masonry-grid_column"
>
  {filteredScenarios.map((scenario) => (
    <motion.div
      key={scenario.id}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <ScenarioCard
        scenario={scenario}
        onCardClick={handleCardClick}
      />
    </motion.div>
  ))}
</Masonry>
```

### 2. Material-UI主題配置

```typescript
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#007BFF' },
    background: { default: '#F8F9FA' }
  },
  typography: {
    fontFamily: '"Inter", "Roboto", sans-serif'
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
          '&:hover': {
            transform: 'translateY(-8px)',
            boxShadow: '0 12px 24px rgba(0,0,0,0.15)'
          }
        }
      }
    }
  }
});
```

### 3. AI聊天組件 (ChatWindow.tsx)

```typescript
const sendMessage = async (message: string) => {
  try {
    const response = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        message, 
        conversation_id: 'default' 
      })
    });
    
    const data = await response.json();
    
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      text: data.response,
      sender: 'ai',
      timestamp: new Date()
    }]);
  } catch (error) {
    console.error('發送消息失敗:', error);
  }
};
```

## 後端核心代碼示例

### 1. Express服務器配置 (index.js)

```javascript
const express = require('express');
const cors = require('cors');
const sqlite3 = require('sqlite3').verbose();

const app = express();
const PORT = 3001;

// 中間件配置
app.use(cors({
  origin: ['http://localhost:3002'],
  credentials: true
}));
app.use(express.json({ limit: '50mb' }));

// 數據庫連接
const db = new sqlite3.Database('./database.db');

// API端點
app.get('/api/scenarios', (req, res) => {
  const query = `
    SELECT id, title, category, question, answer, 
           key_points as keyPoints, difficulty, tags
    FROM scenarios ORDER BY id ASC
  `;
  
  db.all(query, [], (err, rows) => {
    if (err) {
      res.status(500).json({ error: '數據庫查詢失敗' });
    } else {
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

### 2. 數據庫初始化

```javascript
function initializeDatabase() {
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
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);
}
```

## AI服務核心代碼示例

### 1. FastAPI主服務 (main.py)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import chromadb
from sentence_transformers import SentenceTransformer
import requests

app = FastAPI(title="ADC資安情境庫 AI服務")

# 初始化組件
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(
    name="cybersecurity_scenarios"
)

class ChatRequest(BaseModel):
    message: str
    conversation_id: str = "default"

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # 1. 語義搜索
    query_embedding = embedding_model.encode(request.message)
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=5
    )
    
    # 2. 構建RAG提示詞
    context = "\n\n".join(results["documents"][0][:3])
    prompt = f"""基於以下資安情境回答問題:

{context}

問題: {request.message}
回答:"""
    
    # 3. 調用LLM
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.1:8b",
            "prompt": prompt,
            "stream": False
        }
    )
    
    return {"response": response.json()["response"]}
```

### 2. 數據攝取腳本 (ingest.py)

```python
import json
import chromadb
from sentence_transformers import SentenceTransformer

def ingest_scenarios():
    # 初始化
    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection("cybersecurity_scenarios")
    
    # 讀取數據
    with open("../app-server/scenarios.json", 'r', encoding='utf-8') as f:
        scenarios = json.load(f)
    
    # 處理並索引
    for scenario in scenarios:
        content = f"""
        標題: {scenario['title']}
        分類: {scenario['category']}
        問題: {scenario['question']}
        答案: {scenario['answer']}
        """
        
        embedding = model.encode(content)
        
        collection.add(
            documents=[content],
            embeddings=[embedding.tolist()],
            metadatas=[{
                "id": str(scenario['id']),
                "title": scenario['title'],
                "category": scenario['category']
            }],
            ids=[f"scenario_{scenario['id']}"]
        )
    
    print(f"成功索引 {len(scenarios)} 個情境")
```

## 關鍵配置文件

### 1. package.json (前端)

```json
{
  "name": "confidential-expert-ai-client",
  "version": "2.0.0",
  "dependencies": {
    "react": "^19.0.0",
    "typescript": "^5.3.3",
    "@mui/material": "^5.15.0",
    "@emotion/react": "^11.11.0",
    "framer-motion": "^10.16.0",
    "react-masonry-css": "^2.0.1",
    "react-i18next": "^13.5.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build"
  }
}
```

### 2. requirements.txt (AI服務)

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
chromadb==0.4.15
sentence-transformers==2.2.2
transformers==4.35.0
torch==2.1.0
requests==2.31.0
pydantic==2.4.2
```

### 3. docker-compose.yml

```yaml
version: '3.8'
services:
  client:
    build: ./client
    ports: ["3002:3000"]
    environment:
      - REACT_APP_API_URL=http://localhost:3001
  
  app-server:
    build: ./app-server
    ports: ["3001:3001"]
    volumes: ["./app-server:/app"]
  
  ai-service:
    build: ./ai-service
    ports: ["8000:8000"]
    volumes: ["./ai-service:/app"]
```

---

**文檔版本**: 1.0  
**最後更新**: 2025-08-13
