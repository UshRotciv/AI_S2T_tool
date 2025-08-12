# 前端顯示與互動設計
_版本: 1.0.0 | 最後更新: 2025-08-04_

本文檔詳細說明前端顯示與互動設計，包括卡片顯示邏輯、問答介面設計、互動體驗優化以及前端代碼結構。

## 1. 卡片顯示系統

### 1.1 卡片組件結構

資安顧問卡片是系統的核心顯示元素，每張卡片包含以下顯示區域：

- **標題區 (Header)**：顯示卡片標題和分類標籤
- **問題區 (Question)**：顯示具體情境或問題
- **回答區 (Answer)**：顯示專家解答
- **學習重點區 (Learnings)**：以項目符號列表顯示關鍵學習點
- **互動區 (Interaction)**：包含翻頁、收藏等功能按鈕

卡片使用 Material UI 卡片組件構建，實現響應式佈局。

### 1.2 卡片設計規範

```jsx
// 卡片組件示例
function ScenarioCard({ scenario, onNext, onPrev }) {
  const { title, category, question, answer, learnings } = scenario;
  
  return (
    <Card className="scenario-card">
      <CardHeader 
        title={title}
        subheader={<Chip label={category} color="primary" size="small" />}
      />
      
      <CardContent>
        <Typography variant="h6" gutterBottom>情境</Typography>
        <Typography variant="body1" paragraph>{question}</Typography>
        
        <Typography variant="h6" gutterBottom>解答</Typography>
        <Typography variant="body1" paragraph>{answer}</Typography>
        
        <Typography variant="h6" gutterBottom>學習重點</Typography>
        <List>
          {learnings.map((point, index) => (
            <ListItem key={index}>
              <ListItemIcon>
                <CheckCircle fontSize="small" color="success" />
              </ListItemIcon>
              <ListItemText primary={point} />
            </ListItem>
          ))}
        </List>
      </CardContent>
      
      <CardActions>
        <Button onClick={onPrev} startIcon={<ChevronLeft />}>上一張</Button>
        <Button onClick={onNext} endIcon={<ChevronRight />}>下一張</Button>
      </CardActions>
    </Card>
  );
}
```

### 1.3 卡片加載與分頁邏輯

卡片使用虛擬滾動技術優化大量卡片顯示性能：

```jsx
import { FixedSizeList } from 'react-window';

function CardList({ cards }) {
  const Row = ({ index, style }) => (
    <div style={style}>
      <ScenarioCard scenario={cards[index]} />
    </div>
  );
  
  return (
    <FixedSizeList
      height={600}
      width="100%"
      itemSize={450}
      itemCount={cards.length}
    >
      {Row}
    </FixedSizeList>
  );
}
```

### 1.4 卡片過濾與排序

前端支援多種卡片過濾與排序方式：

```jsx
function FilterControls({ categories, onCategoryChange, onSortChange }) {
  return (
    <Box sx={{ mb: 3 }}>
      <FormControl sx={{ mr: 2, minWidth: 200 }}>
        <InputLabel>類別</InputLabel>
        <Select onChange={onCategoryChange}>
          <MenuItem value="all">全部類別</MenuItem>
          {categories.map(category => (
            <MenuItem key={category} value={category}>{category}</MenuItem>
          ))}
        </Select>
      </FormControl>
      
      <FormControl sx={{ minWidth: 200 }}>
        <InputLabel>排序</InputLabel>
        <Select onChange={onSortChange}>
          <MenuItem value="newest">最新加入</MenuItem>
          <MenuItem value="alphabetical">字母順序</MenuItem>
          <MenuItem value="category">類別分組</MenuItem>
        </Select>
      </FormControl>
    </Box>
  );
}
```

## 2. AI 問答介面

### 2.1 問答設計

AI 問答介面採用現代聊天界面設計：

```jsx
function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  
  const sendMessage = async () => {
    if (!input.trim()) return;
    
    // 添加用戶消息
    const userMessage = { type: 'user', text: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    
    try {
      // 發送到 AI 服務
      const response = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: input })
      });
      
      const data = await response.json();
      
      // 添加 AI 回應
      setMessages(prev => [...prev, {
        type: 'ai',
        text: data.answer,
        sources: data.sources || []
      }]);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, {
        type: 'error',
        text: '發生錯誤，請稍後再試。'
      }]);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '80vh' }}>
      <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
        {messages.map((msg, index) => (
          <Message key={index} message={msg} />
        ))}
        {loading && <LoadingMessage />}
      </Box>
      
      <Box sx={{ p: 2, borderTop: '1px solid #ddd' }}>
        <form onSubmit={e => { e.preventDefault(); sendMessage(); }}>
          <TextField
            fullWidth
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="輸入資安相關問題..."
            InputProps={{
              endAdornment: (
                <IconButton 
                  color="primary"
                  disabled={!input.trim() || loading}
                  onClick={sendMessage}
                >
                  <Send />
                </IconButton>
              )
            }}
          />
        </form>
      </Box>
    </Box>
  );
}
```

### 2.2 訊息顯示組件

每條消息的顯示組件：

```jsx
function Message({ message }) {
  const { type, text, sources } = message;
  
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: type === 'user' ? 'flex-end' : 'flex-start',
        mb: 2
      }}
    >
      <Box
        sx={{
          maxWidth: '75%',
          p: 2,
          bgcolor: type === 'user' ? 'primary.main' : 'grey.100',
          color: type === 'user' ? 'white' : 'text.primary',
          borderRadius: 2,
          boxShadow: 1
        }}
      >
        <Typography variant="body1">{text}</Typography>
        
        {sources && sources.length > 0 && (
          <Box sx={{ mt: 1, pt: 1, borderTop: '1px solid #ddd' }}>
            <Typography variant="caption" color="text.secondary">
              資料來源:
            </Typography>
            <List dense>
              {sources.map((source, index) => (
                <ListItem key={index}>
                  <ListItemIcon sx={{ minWidth: 30 }}>
                    <Info fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary={source.title} />
                </ListItem>
              ))}
            </List>
          </Box>
        )}
      </Box>
    </Box>
  );
}
```

### 2.3 錯誤處理與加載狀態

```jsx
function LoadingMessage() {
  return (
    <Box sx={{ display: 'flex', m: 2 }}>
      <CircularProgress size={20} sx={{ mr: 2 }} />
      <Typography variant="body2" color="text.secondary">
        AI 思考中...
      </Typography>
    </Box>
  );
}

function ErrorBoundary({ children }) {
  const [hasError, setHasError] = useState(false);
  
  useEffect(() => {
    const handleError = (error) => {
      console.error('UI Error:', error);
      setHasError(true);
    };
    
    window.addEventListener('error', handleError);
    return () => window.removeEventListener('error', handleError);
  }, []);
  
  if (hasError) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6" color="error" gutterBottom>
          發生錯誤
        </Typography>
        <Button 
          variant="contained" 
          onClick={() => window.location.reload()}
        >
          重新載入
        </Button>
      </Box>
    );
  }
  
  return children;
}
```

## 3. 前端互動體驗優化

### 3.1 響應式設計

```jsx
const theme = createTheme({
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 960,
      lg: 1280,
      xl: 1920,
    },
  },
});

function ResponsiveLayout({ children }) {
  return (
    <ThemeProvider theme={theme}>
      <Box sx={{ p: { xs: 1, sm: 2, md: 3 } }}>
        <Grid container spacing={{ xs: 1, sm: 2, md: 3 }}>
          {children}
        </Grid>
      </Box>
    </ThemeProvider>
  );
}
```

### 3.2 暗色模式支援

```jsx
function ThemeToggler() {
  const [mode, setMode] = useState('light');
  
  const theme = useMemo(() => createTheme({
    palette: {
      mode,
      ...(mode === 'dark' ? {
        background: { default: '#121212', paper: '#1e1e1e' },
      } : {})
    },
  }), [mode]);
  
  const toggleTheme = () => {
    setMode(prevMode => prevMode === 'light' ? 'dark' : 'light');
  };
  
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <IconButton onClick={toggleTheme} color="inherit">
        {mode === 'light' ? <DarkMode /> : <LightMode />}
      </IconButton>
      {/* 應用內容 */}
    </ThemeProvider>
  );
}
```

### 3.3 動畫與過渡效果

```jsx
import { motion } from 'framer-motion';

function AnimatedCard({ children }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
    >
      {children}
    </motion.div>
  );
}

function PageTransition({ children }) {
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
```

## 4. 前端代碼結構

### 4.1 目錄結構

```
/src
  /components
    /Card                 - 卡片相關組件
    /Chat                 - 聊天界面組件
    /Layout               - 佈局相關組件
    /UI                   - 通用 UI 組件
  /pages
    /Home                 - 首頁
    /QA                   - 問答頁面
    /Admin                - 管理頁面
  /services
    /api.js               - API 調用
    /auth.js              - 認證服務
  /hooks
    /useCards.js          - 卡片相關邏輯
    /useChat.js           - 聊天相關邏輯
  /contexts
    /ThemeContext.js      - 主題上下文
    /AuthContext.js       - 認證上下文
  /utils
    /formatters.js        - 格式化函數
    /validators.js        - 驗證函數
  App.jsx                 - 主應用組件
  index.jsx               - 入口文件
```

### 4.2 狀態管理

使用 Context API 與 React Query 處理應用狀態：

```jsx
// 卡片數據獲取與緩存
function useCards() {
  return useQuery('cards', async () => {
    const response = await fetch('/api/scenarios');
    if (!response.ok) {
      throw new Error('Failed to fetch cards');
    }
    return response.json();
  });
}

// 卡片過濾邏輯
function useFilteredCards(cards, filters) {
  return useMemo(() => {
    if (!cards) return [];
    
    return cards.filter(card => {
      // 類別過濾
      if (filters.category && filters.category !== 'all') {
        if (card.category !== filters.category) return false;
      }
      
      // 關鍵字過濾
      if (filters.keyword) {
        const keyword = filters.keyword.toLowerCase();
        const matchesKeyword = 
          card.title.toLowerCase().includes(keyword) ||
          card.question.toLowerCase().includes(keyword) ||
          card.answer.toLowerCase().includes(keyword);
          
        if (!matchesKeyword) return false;
      }
      
      return true;
    });
  }, [cards, filters]);
}
```

## 5. 前端顯示優化建議

### 5.1 卡片顯示強化

1. **重點標記**：在回答中自動標記關鍵詞與專有名詞
   ```jsx
   function highlightTerms(text, terms) {
     if (!terms.length) return text;
     
     let highlightedText = text;
     terms.forEach(term => {
       const regex = new RegExp(`(${term})`, 'gi');
       highlightedText = highlightedText.replace(
         regex, 
         '<span class="highlight">$1</span>'
       );
     });
     
     return <div dangerouslySetInnerHTML={{ __html: highlightedText }} />;
   }
   ```

2. **資訊圖像化**：將部分文字資訊轉為視覺圖表
   ```jsx
   function SecurityLevelIndicator({ level }) {
     const levels = {
       low: { color: 'success.main', icon: <CheckCircle /> },
       medium: { color: 'warning.main', icon: <Warning /> },
       high: { color: 'error.main', icon: <Error /> }
     };
     
     const { color, icon } = levels[level] || levels.medium;
     
     return (
       <Box sx={{ display: 'flex', alignItems: 'center' }}>
         <Box sx={{ color, mr: 1 }}>{icon}</Box>
         <Typography sx={{ color }}>{level.toUpperCase()}</Typography>
       </Box>
     );
   }
   ```

3. **互動性提升**：增加卡片翻轉動畫，正面顯示問題，背面顯示答案
   ```jsx
   function FlippableCard({ frontContent, backContent }) {
     const [isFlipped, setIsFlipped] = useState(false);
     
     return (
       <Box
         onClick={() => setIsFlipped(!isFlipped)}
         sx={{
           perspective: '1000px',
           height: 400,
           cursor: 'pointer'
         }}
       >
         <Box
           sx={{
             position: 'relative',
             width: '100%',
             height: '100%',
             transition: 'transform 0.6s',
             transformStyle: 'preserve-3d',
             transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)'
           }}
         >
           <Box sx={{
             position: 'absolute',
             width: '100%',
             height: '100%',
             backfaceVisibility: 'hidden'
           }}>
             {frontContent}
           </Box>
           <Box sx={{
             position: 'absolute',
             width: '100%',
             height: '100%',
             backfaceVisibility: 'hidden',
             transform: 'rotateY(180deg)'
           }}>
             {backContent}
           </Box>
         </Box>
       </Box>
     );
   }
   ```

### 5.2 問答體驗優化

1. **AI 打字效果**：實現逐字顯示效果增強真實感
   ```jsx
   function TypingEffect({ text }) {
     const [displayedText, setDisplayedText] = useState('');
     const [index, setIndex] = useState(0);
     
     useEffect(() => {
       if (index < text.length) {
         const timer = setTimeout(() => {
           setDisplayedText(prev => prev + text[index]);
           setIndex(index + 1);
         }, 30); // 打字速度
         
         return () => clearTimeout(timer);
       }
     }, [index, text]);
     
     useEffect(() => {
       setDisplayedText('');
       setIndex(0);
     }, [text]);
     
     return <Typography>{displayedText}</Typography>;
   }
   ```

2. **情境化頭像**：根據問題類型顯示不同的 AI 助手頭像
   ```jsx
   function AiAvatar({ category }) {
     const avatars = {
       'social-engineering': '/avatars/security-expert.png',
       'network': '/avatars/network-specialist.png',
       'malware': '/avatars/malware-analyst.png',
       'default': '/avatars/ai-assistant.png'
     };
     
     const avatarSrc = avatars[category] || avatars.default;
     
     return (
       <Avatar
         src={avatarSrc}
         alt="AI Assistant"
         sx={{ width: 40, height: 40 }}
       />
     );
   }
   ```

3. **語音輸入**：支援語音輸入提升使用便利性
   ```jsx
   function VoiceInput({ onResult }) {
     const [listening, setListening] = useState(false);
     
     const toggleListening = () => {
       if (listening) {
         // 停止語音識別
         window.SpeechRecognition.stop();
         setListening(false);
       } else {
         // 啟動語音識別
         const SpeechRecognition = 
           window.SpeechRecognition || window.webkitSpeechRecognition;
           
         if (SpeechRecognition) {
           const recognition = new SpeechRecognition();
           recognition.lang = 'zh-TW';
           recognition.onresult = (event) => {
             const transcript = event.results[0][0].transcript;
             onResult(transcript);
           };
           recognition.onend = () => setListening(false);
           recognition.start();
           setListening(true);
         }
       }
     };
     
     return (
       <IconButton onClick={toggleListening} color={listening ? 'error' : 'primary'}>
         {listening ? <Mic /> : <MicNone />}
       </IconButton>
     );
   }
   ```
