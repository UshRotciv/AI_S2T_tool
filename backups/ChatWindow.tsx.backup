import React, { useState } from 'react';
import axios from 'axios';

// 簡單的 Markdown 渲染函數
const renderMarkdown = (text: string) => {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // **粗體**
    .replace(/\*(.*?)\*/g, '<em>$1</em>')              // *斜體*
    .replace(/`(.*?)`/g, '<code>$1</code>')            // `代碼`
    .replace(/### (.*?)\n/g, '<h3>$1</h3>')           // ### 標題3
    .replace(/## (.*?)\n/g, '<h2>$1</h2>')            // ## 標題2
    .replace(/# (.*?)\n/g, '<h1>$1</h1>')             // # 標題1
    .replace(/\n\n/g, '</p><p>')                       // 段落分隔
    .replace(/\n/g, '<br/>')                           // 換行
    .replace(/^(.*)$/, '<p>$1</p>');                   // 包裝段落
};

const ChatWindow = () => {
  const [messages, setMessages] = useState<{ sender: string; text: string }[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async () => {
    if (input.trim()) {
      const newMessages = [...messages, { sender: 'user', text: input }];
      setMessages(newMessages);
      setInput('');

      setIsLoading(true);
      try {
        const response = await axios.post('http://localhost:3001/api/ask', { question: input });
        setMessages([...newMessages, { sender: 'bot', text: response.data.answer }]);
      } catch (error) {
        console.error('Error fetching AI response:', error);
        setMessages([...newMessages, { sender: 'bot', text: 'Sorry, something went wrong.' }]);
      } finally {
        setIsLoading(false);
      }
    }
  };

  return (
    <div className="chat-window" style={{ resize: 'both', overflow: 'auto', minWidth: '400px', minHeight: '300px' }}>
      <div className="messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            {msg.sender === 'bot' ? (
              <div 
                dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.text) }}
                style={{ lineHeight: '1.6', wordBreak: 'break-word' }}
              />
            ) : (
              <div style={{ lineHeight: '1.6', wordBreak: 'break-word', whiteSpace: 'pre-wrap' }}>
                {msg.text}
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <div className="message bot">
            <div className="loading-indicator">
              <span>讓ADC資安小助手想想回答你</span>
              <span className="dot">.</span>
              <span className="dot">.</span>
              <span className="dot">.</span>
            </div>
          </div>
        )}
      </div>
      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
        />
        <button onClick={handleSend}>Send</button>
      </div>
    </div>
  );
};

export default ChatWindow;
