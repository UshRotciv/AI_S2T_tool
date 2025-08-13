import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import {
  Paper,
  Box,
  Typography,
  TextField,
  IconButton,
  Avatar,
  Divider,
  CircularProgress,
  Fade,
  InputAdornment
} from '@mui/material';
import {
  Close as CloseIcon,
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as PersonIcon
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';

interface ChatWindowProps {
  onClose?: () => void;
}

// 簡單的 Markdown 渲染函數
const renderMarkdown = (text: string) => {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // **粗體**
    .replace(/\*(.*?)\*/g, '<em>$1</em>')              // *斜體*
    .replace(/`(.*?)`/g, '<code style="background-color: #f5f5f5; padding: 2px 4px; border-radius: 3px; font-family: monospace;">$1</code>')            // `代碼`
    .replace(/### (.*?)\n/g, '<h3 style="margin: 16px 0 8px 0; font-size: 1.1rem; font-weight: 600;">$1</h3>')           // ### 標題3
    .replace(/## (.*?)\n/g, '<h2 style="margin: 20px 0 12px 0; font-size: 1.25rem; font-weight: 600;">$1</h2>')            // ## 標題2
    .replace(/# (.*?)\n/g, '<h1 style="margin: 24px 0 16px 0; font-size: 1.5rem; font-weight: 700;">$1</h1>')             // # 標題1
    .replace(/\n\n/g, '</p><p style="margin: 12px 0;">')                       // 段落分隔
    .replace(/\n/g, '<br/>')                           // 換行
    .replace(/^(.*)$/, '<p style="margin: 8px 0;">$1</p>');                   // 包裝段落
};

const ChatWindow: React.FC<ChatWindowProps> = ({ onClose }) => {
  const [messages, setMessages] = useState<{ sender: string; text: string; timestamp: Date }[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // 自動滾動到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 自動聚焦輸入框
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  const handleSend = async () => {
    if (input.trim()) {
      const userMessage = { sender: 'user', text: input, timestamp: new Date() };
      const newMessages = [...messages, userMessage];
      setMessages(newMessages);
      setInput('');

      setIsLoading(true);
      try {
        const response = await axios.post('http://localhost:3001/api/ask', { question: input });
        const botMessage = { sender: 'bot', text: response.data.answer, timestamp: new Date() };
        setMessages([...newMessages, botMessage]);
      } catch (error) {
        console.error('Error fetching AI response:', error);
        const errorMessage = { 
          sender: 'bot', 
          text: '抱歉，AI 助手暫時無法回應。請稍後再試或檢查網路連線。', 
          timestamp: new Date() 
        };
        setMessages([...newMessages, errorMessage]);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9, y: 20 }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
    >
      <Paper
        elevation={8}
        sx={{
          width: 400,
          height: 500,
          display: 'flex',
          flexDirection: 'column',
          borderRadius: 3,
          overflow: 'hidden',
          boxShadow: '0 16px 32px rgba(0,0,0,0.2)'
        }}
      >
        {/* 聊天視窗標題列 */}
        <Box
          sx={{
            p: 2,
            backgroundColor: 'primary.main',
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <BotIcon sx={{ fontSize: 24 }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              ADC 資安小助手
            </Typography>
          </Box>
          {onClose && (
            <IconButton 
              onClick={onClose} 
              size="small" 
              sx={{ color: 'white' }}
            >
              <CloseIcon />
            </IconButton>
          )}
        </Box>

        {/* 訊息區域 */}
        <Box
          sx={{
            flex: 1,
            overflow: 'auto',
            p: 1,
            backgroundColor: '#f8f9fa'
          }}
        >
          <AnimatePresence>
            {messages.length === 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
              >
                <Box
                  sx={{
                    textAlign: 'center',
                    py: 4,
                    color: 'text.secondary'
                  }}
                >
                  <BotIcon sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
                  <Typography variant="body2">
                    您好！我是 ADC 資安小助手
                  </Typography>
                  <Typography variant="body2">
                    有任何資安問題都可以問我喔！
                  </Typography>
                </Box>
              </motion.div>
            )}
            
            {messages.map((msg, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    mb: 2,
                    justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start'
                  }}
                >
                  {msg.sender === 'bot' && (
                    <Avatar
                      sx={{
                        width: 32,
                        height: 32,
                        mr: 1,
                        backgroundColor: 'primary.main'
                      }}
                    >
                      <BotIcon sx={{ fontSize: 18 }} />
                    </Avatar>
                  )}
                  
                  <Paper
                    elevation={1}
                    sx={{
                      p: 2,
                      maxWidth: '75%',
                      backgroundColor: msg.sender === 'user' ? 'primary.main' : 'white',
                      color: msg.sender === 'user' ? 'white' : 'text.primary',
                      borderRadius: 2,
                      ...(msg.sender === 'user' && {
                        borderBottomRightRadius: 4
                      }),
                      ...(msg.sender === 'bot' && {
                        borderBottomLeftRadius: 4
                      })
                    }}
                  >
                    {msg.sender === 'bot' ? (
                      <div 
                        dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.text) }}
                        style={{ 
                          lineHeight: '1.6', 
                          wordBreak: 'break-word',
                          fontSize: '0.9rem'
                        }}
                      />
                    ) : (
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          lineHeight: 1.6, 
                          wordBreak: 'break-word', 
                          whiteSpace: 'pre-wrap'
                        }}
                      >
                        {msg.text}
                      </Typography>
                    )}
                  </Paper>
                  
                  {msg.sender === 'user' && (
                    <Avatar
                      sx={{
                        width: 32,
                        height: 32,
                        ml: 1,
                        backgroundColor: 'secondary.main'
                      }}
                    >
                      <PersonIcon sx={{ fontSize: 18 }} />
                    </Avatar>
                  )}
                </Box>
              </motion.div>
            ))}
            
            {isLoading && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <Box sx={{ display: 'flex', mb: 2 }}>
                  <Avatar
                    sx={{
                      width: 32,
                      height: 32,
                      mr: 1,
                      backgroundColor: 'primary.main'
                    }}
                  >
                    <BotIcon sx={{ fontSize: 18 }} />
                  </Avatar>
                  <Paper
                    elevation={1}
                    sx={{
                      p: 2,
                      backgroundColor: 'white',
                      borderRadius: 2,
                      borderBottomLeftRadius: 4,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1
                    }}
                  >
                    <CircularProgress size={16} />
                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                      正在思考中...
                    </Typography>
                  </Paper>
                </Box>
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </Box>

        <Divider />

        {/* 輸入區域 */}
        <Box sx={{ p: 2 }}>
          <TextField
            fullWidth
            multiline
            maxRows={3}
            variant="outlined"
            placeholder="輸入您的資安問題..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            inputRef={inputRef}
            disabled={isLoading}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={handleSend}
                    disabled={!input.trim() || isLoading}
                    color="primary"
                    size="small"
                  >
                    <SendIcon />
                  </IconButton>
                </InputAdornment>
              ),
            }}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
                '&:hover': {
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'primary.main'
                  }
                }
              }
            }}
          />
        </Box>
      </Paper>
    </motion.div>
  );
};

export default ChatWindow;
