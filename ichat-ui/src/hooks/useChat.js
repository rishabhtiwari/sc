import { useState, useCallback } from 'react';
import apiService from '../services/apiService';

export const useChat = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hello! I'm your iChat Assistant. How can I help you today?",
      sender: 'assistant',
      timestamp: new Date()
    }
  ]);

  const [isTyping, setIsTyping] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('checking');

  const checkConnection = useCallback(async () => {
    try {
      const response = await apiService.checkHealth();
      if (response.status === 'healthy' || response.status === 'ok') {
        setConnectionStatus('connected');
      } else {
        setConnectionStatus('disconnected');
      }
    } catch (error) {
      console.error('Connection check failed:', error);
      setConnectionStatus('disconnected');
    }
  }, []);

  const handleSend = useCallback(async (text) => {
    const userMessage = {
      id: Date.now(),
      text,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);

    try {
      const response = await apiService.sendChatMessage(text, {
        useRag: false,
        sessionId: `web-session-${Date.now()}`
      });

      if (response.status === 'success') {
        setConnectionStatus('connected');

        const assistantMessage = {
          id: Date.now() + 1,
          text: response.response || response.message || 'I received your message but had trouble generating a response.',
          sender: 'assistant',
          timestamp: new Date()
        };

        setMessages(prev => [...prev, assistantMessage]);
      } else {
        const errorMessage = {
          id: Date.now() + 1,
          text: `Sorry, I encountered an error: ${response.error || 'Unknown error occurred'}`,
          sender: 'assistant',
          timestamp: new Date()
        };

        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Send message failed:', error);
      setConnectionStatus('disconnected');

      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I\'m having trouble connecting to the server. Please check your connection and try again.',
        sender: 'assistant',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([
      {
        id: 1,
        text: "Hello! I'm your iChat Assistant. How can I help you today?",
        sender: 'assistant',
        timestamp: new Date()
      }
    ]);
  }, []);

  return {
    messages,
    isTyping,
    connectionStatus,
    handleSend,
    checkConnection,
    clearMessages
  };
};
