import React, { useState, useMemo, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Container,
  Typography,
  TextField,
  Chip,
  InputAdornment,
  AppBar,
  Toolbar,
  ThemeProvider,
  createTheme,
  CssBaseline,
  Fab,
  Fade
} from '@mui/material';
import {
  Search as SearchIcon,
  Chat as ChatIcon,
  Security as SecurityIcon
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import Masonry from 'react-masonry-css';
import ScenarioCard from './ScenarioCard';
import ChatWindow from './ChatWindow';
import './masonry.css';

interface Scenario {
  id: number;
  category: string;
  title: string;
  question: string;
  answer: string;
  learnings: string[];
  order?: number;
  groupId?: string | null;
}

// 創建明亮主題
const lightTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#007BFF',
      light: '#4DA3FF',
      dark: '#0056CC'
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
      primary: '#1A1A1A',
      secondary: '#666666'
    }
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 700,
      fontSize: '2.5rem'
    },
    h2: {
      fontWeight: 600,
      fontSize: '2rem'
    },
    h6: {
      fontWeight: 600
    }
  },
  shape: {
    borderRadius: 12
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          '&:hover': {
            boxShadow: '0 12px 24px rgba(0,0,0,0.15)'
          }
        }
      }
    }
  }
});

const HomePage = () => {
  const { t, i18n } = useTranslation();
  const [searchTerm, setSearchTerm] = useState('');
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [isChatOpen, setIsChatOpen] = useState(false);


  useEffect(() => {
    fetch('http://localhost:3001/api/scenarios')
      .then(res => res.json())
      .then(data => setScenarios(data?.data || []));
  }, []);

  const filteredScenarios = useMemo(() => {
    // 先按照 order 屬性排序場景
    const sortedScenarios = [...scenarios].sort((a, b) => {
      // 如果 order 都存在，按 order 排序
      if (a.order !== undefined && b.order !== undefined) {
        return a.order - b.order;
      }
      // 如果只有一個有 order，有 order 的優先
      if (a.order !== undefined) return -1;
      if (b.order !== undefined) return 1;
      // 都沒有 order，保持原順序
      return 0;
    });
    
    return sortedScenarios.filter(scenario => {
      // 分類篩選
      const categoryMatch = selectedCategory === 'all' || scenario.category.includes(selectedCategory);
      
      // 搜尋篩選
      const searchContent = (
        scenario.category +
        scenario.title +
        scenario.question +
        scenario.answer +
        scenario.learnings.join(' ')
      ).toLowerCase();
      const searchMatch = searchContent.includes(searchTerm.toLowerCase());
      
      return categoryMatch && searchMatch;
    });
  }, [searchTerm, scenarios, selectedCategory]);

  // 分類選項
  const categories = useMemo(() => [
    { key: 'all', label: '全部分類', color: '#007BFF' },
    { key: 'Part A', label: 'A: 基礎習慣', color: '#2196F3' },
    { key: 'Part B', label: 'B: 檔案傳遞', color: '#4CAF50' },
    { key: 'Part C', label: 'C: 機敏資料', color: '#FF9800' },
    { key: 'Part D', label: 'D: 智慧財產', color: '#9C27B0' }
  ], []);

  // 瀑布流斷點配置
  const breakpointColumnsObj = {
    default: 4,
    1400: 3,
    1000: 2,
    700: 1
  };

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
  };

  const handleCategoryChange = (categoryKey: string) => {
    setSelectedCategory(categoryKey);
  };

  const toggleChat = () => {
    setIsChatOpen(!isChatOpen);
  };

  return (
    <ThemeProvider theme={lightTheme}>
      <CssBaseline />
      <Box sx={{ minHeight: '100vh', backgroundColor: 'background.default' }}>
        {/* 頂部導航列 */}
        <AppBar 
          position="sticky" 
          elevation={0}
          sx={{ 
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
            borderBottom: '1px solid rgba(0,0,0,0.08)'
          }}
        >
          <Toolbar sx={{ justifyContent: 'space-between', py: 1 }}>
            {/* Logo 區域 */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <SecurityIcon sx={{ fontSize: 32, color: 'primary.main' }} />
              <Typography 
                variant="h6" 
                component="h1" 
                sx={{ 
                  fontWeight: 700, 
                  color: 'text.primary',
                  fontSize: '1.5rem'
                }}
              >
                {t('appTitle', 'ADC資安情境庫')}
              </Typography>
            </Box>

            {/* 語言切換 */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Chip
                label="中文"
                size="small"
                variant={i18n.language === 'zh' ? 'filled' : 'outlined'}
                onClick={() => changeLanguage('zh')}
                sx={{ cursor: 'pointer' }}
              />
              <Chip
                label="EN"
                size="small"
                variant={i18n.language === 'en' ? 'filled' : 'outlined'}
                onClick={() => changeLanguage('en')}
                sx={{ cursor: 'pointer' }}
              />
            </Box>
          </Toolbar>
        </AppBar>

        {/* 主要內容區域 */}
        <Container maxWidth="xl" sx={{ py: 4 }}>
          {/* 搜尋和篩選區域 */}
          <Box sx={{ mb: 4 }}>
            {/* 搜尋框 */}
            <Box sx={{ mb: 3, display: 'flex', justifyContent: 'center' }}>
              <TextField
                fullWidth
                variant="outlined"
                placeholder={t('searchPlaceholder', '搜尋資安情境...')}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon sx={{ color: 'text.secondary' }} />
                    </InputAdornment>
                  ),
                }}
                sx={{
                  maxWidth: 600,
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 3,
                    backgroundColor: 'background.paper',
                    '&:hover': {
                      '& .MuiOutlinedInput-notchedOutline': {
                        borderColor: 'primary.main'
                      }
                    }
                  }
                }}
              />
            </Box>

            {/* 分類篩選標籤 */}
            <Box sx={{ display: 'flex', justifyContent: 'center', flexWrap: 'wrap', gap: 1 }}>
              {categories.map((category) => (
                <motion.div
                  key={category.key}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Chip
                    label={category.label}
                    variant={selectedCategory === category.key ? 'filled' : 'outlined'}
                    onClick={() => handleCategoryChange(category.key)}
                    sx={{
                      cursor: 'pointer',
                      fontWeight: 600,
                      px: 2,
                      py: 0.5,
                      ...(selectedCategory === category.key && {
                        backgroundColor: category.color,
                        color: 'white',
                        '&:hover': {
                          backgroundColor: category.color
                        }
                      })
                    }}
                  />
                </motion.div>
              ))}
            </Box>
          </Box>

          {/* 情境卡片瀑布流 */}
          <AnimatePresence>
            {filteredScenarios.length > 0 ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
              >
                <Masonry
                  breakpointCols={breakpointColumnsObj}
                  className="masonry-grid"
                  columnClassName="masonry-grid_column"
                >
                  {filteredScenarios.map((scenario, index) => (
                    <motion.div
                      key={scenario.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ 
                        duration: 0.4, 
                        delay: index * 0.1,
                        ease: 'easeOut'
                      }}
                      style={{ marginBottom: '24px' }}
                    >
                      <ScenarioCard scenario={scenario} />
                    </motion.div>
                  ))}
                </Masonry>
              </motion.div>
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
              >
                <Box
                  sx={{
                    textAlign: 'center',
                    py: 8,
                    color: 'text.secondary'
                  }}
                >
                  <SecurityIcon sx={{ fontSize: 64, mb: 2, opacity: 0.3 }} />
                  <Typography variant="h6" sx={{ mb: 1 }}>
                    沒有找到相關的資安情境
                  </Typography>
                  <Typography variant="body2">
                    請嘗試調整搜尋關鍵字或分類篩選
                  </Typography>
                </Box>
              </motion.div>
            )}
          </AnimatePresence>
        </Container>

        {/* 浮動聊天按鈕 */}
        <Fab
          color="primary"
          onClick={toggleChat}
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            zIndex: 1000,
            boxShadow: '0 8px 24px rgba(0,123,255,0.3)',
            fontSize: '1.2rem',
            fontWeight: 700
          }}
        >
          AI
        </Fab>

        {/* 聊天視窗 */}
        <Fade in={isChatOpen}>
          <Box
            sx={{
              position: 'fixed',
              bottom: 100,
              right: 24,
              zIndex: 999,
              display: isChatOpen ? 'block' : 'none'
            }}
          >
            <ChatWindow onClose={() => setIsChatOpen(false)} />
          </Box>
        </Fade>
      </Box>
    </ThemeProvider>
  );
}

export default HomePage;