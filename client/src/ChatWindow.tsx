import React, { useState } from 'react';
import axios from 'axios';

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
    <div className="chat-window">
      <div className="messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            {msg.text}
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
