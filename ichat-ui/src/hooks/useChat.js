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
  const [currentStreamController, setCurrentStreamController] = useState(null);

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

  const stopStream = useCallback(() => {
    if (currentStreamController) {
      currentStreamController.abort();
      setCurrentStreamController(null);
      setIsTyping(false);

      // Mark the current streaming message as stopped
      setMessages(prev => prev.map(msg =>
        msg.isStreaming
          ? { ...msg, isStreaming: false, text: msg.text + '\n\n[Response stopped by user]' }
          : msg
      ));
    }
  }, [currentStreamController]);

  const handleSend = useCallback(async (text) => {
    // Stop any existing stream
    if (currentStreamController) {
      currentStreamController.abort();
    }

    const userMessage = {
      id: Date.now(),
      text,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);

    // Create assistant message placeholder for streaming
    const assistantMessageId = Date.now() + 1;
    const assistantMessage = {
      id: assistantMessageId,
      text: '',
      sender: 'assistant',
      timestamp: new Date(),
      isStreaming: true
    };

    setMessages(prev => [...prev, assistantMessage]);

    // Create abort controller for this stream
    const controller = new AbortController();
    setCurrentStreamController(controller);

    try {
      await apiService.streamChatMessage(
        text,
        {
          useRag: true, // Enable RAG for better responses
          sessionId: `web-session-${Date.now()}`,
          signal: controller.signal // Pass abort signal
        },
        // onChunk callback
        (chunk) => {
          console.log('Received chunk:', chunk);
          console.log('Chunk keys:', Object.keys(chunk));
          console.log('Chunk type:', chunk.type);
          console.log('Chunk content:', chunk.content);

          // Handle different chunk formats
          if (chunk.type === 'token' && chunk.content) {
            // Update the assistant message with new token content
            setMessages(prev => prev.map(msg =>
              msg.id === assistantMessageId
                ? { ...msg, text: msg.text + chunk.content }
                : msg
            ));
          } else if (chunk.content && !chunk.type) {
            // Handle direct content chunks (fallback)
            setMessages(prev => prev.map(msg =>
              msg.id === assistantMessageId
                ? { ...msg, text: msg.text + chunk.content }
                : msg
            ));
          } else if (typeof chunk === 'string') {
            // Handle string chunks directly
            setMessages(prev => prev.map(msg =>
              msg.id === assistantMessageId
                ? { ...msg, text: msg.text + chunk }
                : msg
            ));
          } else if (chunk.type === 'metadata') {
            setConnectionStatus('connected');
            console.log('Streaming metadata:', chunk);
          } else if (chunk.type === 'chunk_start') {
            console.log(`Starting chunk ${chunk.chunk_index + 1}/${chunk.total_chunks}`);
          } else if (chunk.type === 'chunk_complete') {
            console.log(`Completed chunk ${chunk.chunk_index + 1}/${chunk.total_chunks}`);
          } else if (chunk.type === 'complete') {
            console.log('Stream completed');
          } else {
            console.log('Unknown chunk format:', chunk);
          }
        },
        // onComplete callback
        () => {
          console.log('Streaming completed');
          setIsTyping(false);
          setCurrentStreamController(null);
          // Mark message as no longer streaming
          setMessages(prev => prev.map(msg =>
            msg.id === assistantMessageId
              ? { ...msg, isStreaming: false }
              : msg
          ));
        },
        // onError callback
        (error) => {
          console.error('Streaming error:', error);
          setIsTyping(false);
          setCurrentStreamController(null);

          if (error.name === 'AbortError') {
            // Stream was intentionally stopped
            return;
          }

          setConnectionStatus('disconnected');

          // Update assistant message with error
          setMessages(prev => prev.map(msg =>
            msg.id === assistantMessageId
              ? {
                  ...msg,
                  text: 'Sorry, I\'m having trouble connecting to the server. Please check your connection and try again.',
                  isStreaming: false
                }
              : msg
          ));
        }
      );
    } catch (error) {
      console.error('Send message failed:', error);
      setIsTyping(false);
      setCurrentStreamController(null);

      if (error.name === 'AbortError') {
        // Stream was intentionally stopped
        return;
      }

      setConnectionStatus('disconnected');

      // Update assistant message with error
      setMessages(prev => prev.map(msg =>
        msg.id === assistantMessageId
          ? {
              ...msg,
              text: 'Sorry, I\'m having trouble connecting to the server. Please check your connection and try again.',
              isStreaming: false
            }
          : msg
      ));
    }
  }, [currentStreamController]);

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
    stopStream,
    checkConnection,
    clearMessages,
    canStop: !!currentStreamController
  };
};
