# 前端技術規格文檔 - React + TypeScript + Material-UI

## 技術棧概覽

### 核心框架
- **React**: 19.0.0 - 現代化函數組件與Hooks
- **TypeScript**: 5.3.3 - 完整類型安全
- **Create React App**: 5.0.1 - 零配置構建工具

### UI框架與樣式
- **Material-UI (MUI)**: 5.15.x - 現代化組件庫
- **@emotion/react**: 11.11.x - CSS-in-JS解決方案
- **@emotion/styled**: 11.11.x - 樣式化組件
- **react-masonry-css**: 2.0.1 - 瀑布流佈局
- **framer-motion**: 10.16.x - 動畫庫

### 國際化與工具
- **react-i18next**: 13.5.x - 多語言支持
- **@mui/icons-material**: 5.15.x - Material圖標庫

## 項目結構詳解

```
client/src/
├── components/
│   ├── HomePage.tsx          # 主頁面組件 (11KB)
│   ├── ScenarioCard.tsx      # 情境卡片組件 (9KB)
│   ├── ChatWindow.tsx        # AI聊天組件 (11KB)
│   └── AdminPage.tsx         # 管理頁面 (42KB)
├── styles/
│   ├── App.css              # 全局樣式 (4KB)
│   ├── masonry.css          # 瀑布流樣式 (1KB)
│   └── index.css            # 基礎樣式 (366B)
├── types/                   # TypeScript類型定義
├── i18n.ts                  # 國際化配置
├── App.tsx                  # 根組件
└── index.tsx                # 應用入口
```

## 核心組件詳細規格

### 1. HomePage.tsx - 主頁面組件

**功能**: 瀑布流佈局的情境卡片展示頁面

**關鍵技術實現**:
```typescript
// 瀑布流配置
const breakpointColumnsObj = {
  default: 4,
  1100: 3,
  700: 2,
  500: 1
};

// Material-UI主題配置
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#007BFF' },
    background: { default: '#F8F9FA' }
  },
  typography: {
    fontFamily: '"Inter", "Roboto", sans-serif'
  }
});
```

**狀態管理**:
- `scenarios`: 情境數據列表
- `filteredScenarios`: 過濾後的情境
- `searchTerm`: 搜索關鍵詞
- `selectedCategory`: 選中的分類
- `isChatOpen`: 聊天窗口狀態

**API集成**:
```typescript
useEffect(() => {
  fetch('http://localhost:3001/api/scenarios')
    .then(response => response.json())
    .then(data => setScenarios(data))
    .catch(error => console.error('Error:', error));
}, []);
```

### 2. ScenarioCard.tsx - 情境卡片組件

**功能**: 現代化卡片設計，支持懸停效果和Modal詳情

**卡片樣式配置**:
```typescript
const cardSx = {
  borderRadius: 3,
  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  '&:hover': {
    transform: 'translateY(-8px)',
    boxShadow: '0 12px 24px rgba(0,0,0,0.15)'
  }
};
```

**分類顏色映射**:
```typescript
const getCategoryColor = (category: string) => {
  const colors = {
    'A': '#2196F3', // 藍色
    'B': '#4CAF50', // 綠色  
    'C': '#FF9800', // 橙色
    'D': '#9C27B0'  // 紫色
  };
  return colors[category] || '#757575';
};
```

**Modal詳情視窗**:
- 使用Framer Motion動畫
- 響應式設計 (maxWidth: 800px)
- 結構化內容展示 (情境/解答/重點)

### 3. ChatWindow.tsx - AI聊天組件

**功能**: 浮動式AI聊天界面

**尺寸配置**:
```typescript
const chatWindowSx = {
  width: 800,        // 寬度2倍
  height: 600,       // 高度+20%
  maxWidth: '90vw',  // 響應式限制
  maxHeight: '85vh'  // 防止超出視窗
};
```

**消息類型定義**:
```typescript
interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
}
```

**AI API集成**:
```typescript
const sendMessage = async (message: string) => {
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, conversation_id: 'default' })
  });
  return response.json();
};
```

## 樣式系統詳解

### 1. Material-UI主題系統

**主題配置** (`HomePage.tsx`):
```typescript
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#007BFF',
      light: '#66B2FF',
      dark: '#0056B3'
    },
    secondary: {
      main: '#6C757D',
      light: '#ADB5BD',
      dark: '#495057'
    },
    background: {
      default: '#F8F9FA',
      paper: '#FFFFFF'
    },
    text: {
      primary: '#212529',
      secondary: '#6C757D'
    }
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 700,
      fontSize: '2.125rem'
    },
    h6: {
      fontWeight: 600,
      fontSize: '1.25rem'
    }
  },
  shape: {
    borderRadius: 12
  },
  shadows: [
    'none',
    '0 2px 4px rgba(0,0,0,0.1)',
    '0 4px 8px rgba(0,0,0,0.12)',
    // ... 自定義陰影級別
  ]
});
```

### 2. 瀑布流樣式 (`masonry.css`)

```css
.masonry-grid {
  display: flex;
  margin-left: -16px;
  width: auto;
}

.masonry-grid_column {
  padding-left: 16px;
  background-clip: padding-box;
}

.masonry-grid_column > div {
  margin-bottom: 16px;
  break-inside: avoid;
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

### 3. 全局樣式 (`App.css`)

**滾動條美化**:
```css
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
  transition: background 0.3s ease;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
```

## 響應式設計規格

### 斷點配置
```typescript
const breakpoints = {
  xs: 0,     // 手機
  sm: 600,   // 平板
  md: 900,   // 小型桌面
  lg: 1200,  // 大型桌面
  xl: 1536   // 超大桌面
};
```

### 瀑布流響應式
- **xl (1536px+)**: 4列
- **lg (1200px+)**: 3列  
- **md (900px+)**: 2列
- **sm (600px+)**: 1列

### 聊天窗口響應式
- **桌面**: 800x600px
- **平板**: 90vw x 85vh
- **手機**: 95vw x 90vh

## 性能優化策略

### 1. 組件優化
```typescript
// React.memo防止不必要重渲染
const ScenarioCard = React.memo(({ scenario, onCardClick }) => {
  // 組件實現
});

// useMemo緩存計算結果
const filteredScenarios = useMemo(() => {
  return scenarios.filter(scenario => 
    scenario.title.toLowerCase().includes(searchTerm.toLowerCase())
  );
}, [scenarios, searchTerm]);
```

### 2. 圖片懶加載
```typescript
const LazyImage = ({ src, alt, ...props }) => {
  const [loaded, setLoaded] = useState(false);
  
  return (
    <img
      src={loaded ? src : placeholder}
      alt={alt}
      onLoad={() => setLoaded(true)}
      {...props}
    />
  );
};
```

### 3. 虛擬滾動 (大數據集)
```typescript
import { FixedSizeList as List } from 'react-window';

const VirtualizedList = ({ items }) => (
  <List
    height={600}
    itemCount={items.length}
    itemSize={200}
    itemData={items}
  >
    {Row}
  </List>
);
```

## 構建與部署配置

### package.json關鍵配置
```json
{
  "name": "confidential-expert-ai-client",
  "version": "2.0.0",
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "dependencies": {
    "react": "^19.0.0",
    "typescript": "^5.3.3",
    "@mui/material": "^5.15.0",
    "@emotion/react": "^11.11.0",
    "framer-motion": "^10.16.0",
    "react-masonry-css": "^2.0.1"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
```

### 環境變量配置
```bash
# .env
REACT_APP_API_URL=http://localhost:3001
REACT_APP_AI_SERVICE_URL=http://localhost:8000
REACT_APP_VERSION=2.0.0
```

### 構建優化
```bash
# 生產構建
npm run build

# 構建分析
npm install -g webpack-bundle-analyzer
npx webpack-bundle-analyzer build/static/js/*.js
```

---

**文檔版本**: 1.0  
**最後更新**: 2025-08-13  
**技術負責**: 前端開發團隊
