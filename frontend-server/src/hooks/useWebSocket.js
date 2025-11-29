import { useEffect, useRef, useState, useCallback } from 'react';
import { io } from 'socket.io-client';

/**
 * Custom hook for WebSocket connection using Socket.IO
 * Provides real-time updates for job status and progress
 * 
 * @param {string} room - Room to join for specific updates (e.g., 'news-fetcher', 'audio-generation')
 * @param {Object} options - Configuration options
 * @returns {Object} WebSocket state and methods
 */
export const useWebSocket = (room = null, options = {}) => {
  const {
    autoConnect = true,
    reconnect = true,
    serverUrl = process.env.REACT_APP_WS_URL || 'http://localhost:8080'
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [error, setError] = useState(null);
  const socketRef = useRef(null);
  const listenersRef = useRef({});

  // Initialize socket connection
  useEffect(() => {
    if (!autoConnect) return;

    console.log(`🔌 Connecting to WebSocket server: ${serverUrl}`);

    // Create socket connection
    socketRef.current = io(serverUrl, {
      transports: ['websocket', 'polling'],
      reconnection: reconnect,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
      timeout: 10000
    });

    const socket = socketRef.current;

    // Connection event handlers
    socket.on('connect', () => {
      console.log('✅ WebSocket connected');
      setIsConnected(true);
      setError(null);

      // Join room if specified
      if (room) {
        socket.emit('join_room', { room });
        console.log(`👥 Joined room: ${room}`);
      }
    });

    socket.on('disconnect', (reason) => {
      console.log(`🔌 WebSocket disconnected: ${reason}`);
      setIsConnected(false);
    });

    socket.on('connect_error', (err) => {
      console.error('❌ WebSocket connection error:', err);
      setError(err.message);
      setIsConnected(false);
    });

    socket.on('connection_response', (data) => {
      console.log('📡 Connection response:', data);
    });

    socket.on('room_joined', (data) => {
      console.log('👥 Room joined:', data);
    });

    // Cleanup on unmount
    return () => {
      if (room && socket.connected) {
        socket.emit('leave_room', { room });
      }
      socket.disconnect();
      console.log('🔌 WebSocket disconnected (cleanup)');
    };
  }, [autoConnect, reconnect, serverUrl, room]);

  /**
   * Subscribe to a specific event
   * @param {string} event - Event name
   * @param {Function} callback - Callback function
   */
  const on = useCallback((event, callback) => {
    if (!socketRef.current) {
      console.warn('⚠️ Socket not initialized');
      return;
    }

    // Store listener reference for cleanup
    listenersRef.current[event] = callback;

    socketRef.current.on(event, (data) => {
      console.log(`📡 Received ${event}:`, data);
      setLastMessage({ event, data, timestamp: Date.now() });
      callback(data);
    });

    console.log(`👂 Listening to event: ${event}`);
  }, []);

  /**
   * Unsubscribe from a specific event
   * @param {string} event - Event name
   */
  const off = useCallback((event) => {
    if (!socketRef.current) return;

    socketRef.current.off(event);
    delete listenersRef.current[event];
    console.log(`🔇 Stopped listening to event: ${event}`);
  }, []);

  /**
   * Emit an event to the server
   * @param {string} event - Event name
   * @param {Object} data - Data to send
   */
  const emit = useCallback((event, data) => {
    if (!socketRef.current || !isConnected) {
      console.warn('⚠️ Socket not connected');
      return;
    }

    socketRef.current.emit(event, data);
    console.log(`📤 Emitted ${event}:`, data);
  }, [isConnected]);

  /**
   * Join a room
   * @param {string} roomName - Room name
   */
  const joinRoom = useCallback((roomName) => {
    emit('join_room', { room: roomName });
  }, [emit]);

  /**
   * Leave a room
   * @param {string} roomName - Room name
   */
  const leaveRoom = useCallback((roomName) => {
    emit('leave_room', { room: roomName });
  }, [emit]);

  /**
   * Manually connect to WebSocket
   */
  const connect = useCallback(() => {
    if (socketRef.current && !socketRef.current.connected) {
      socketRef.current.connect();
    }
  }, []);

  /**
   * Manually disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    if (socketRef.current && socketRef.current.connected) {
      socketRef.current.disconnect();
    }
  }, []);

  return {
    isConnected,
    lastMessage,
    error,
    on,
    off,
    emit,
    joinRoom,
    leaveRoom,
    connect,
    disconnect,
    socket: socketRef.current
  };
};

/**
 * Hook for news fetcher updates
 */
export const useNewsFetcherUpdates = (callback) => {
  const { on, off, isConnected } = useWebSocket('news-fetcher');

  useEffect(() => {
    if (isConnected && callback) {
      on('news_fetch_update', callback);
      return () => off('news_fetch_update');
    }
  }, [isConnected, callback, on, off]);

  return { isConnected };
};

/**
 * Hook for audio generation updates
 */
export const useAudioGenerationUpdates = (callback) => {
  const { on, off, isConnected } = useWebSocket('audio-generation');

  useEffect(() => {
    if (isConnected && callback) {
      on('audio_generation_update', callback);
      return () => off('audio_generation_update');
    }
  }, [isConnected, callback, on, off]);

  return { isConnected };
};

/**
 * Hook for video generation updates
 */
export const useVideoGenerationUpdates = (callback) => {
  const { on, off, isConnected } = useWebSocket('video-generation');

  useEffect(() => {
    if (isConnected && callback) {
      on('video_generation_update', callback);
      return () => off('video_generation_update');
    }
  }, [isConnected, callback, on, off]);

  return { isConnected };
};

/**
 * Hook for YouTube upload updates
 */
export const useYouTubeUploadUpdates = (callback) => {
  const { on, off, isConnected } = useWebSocket('youtube-upload');

  useEffect(() => {
    if (isConnected && callback) {
      on('youtube_upload_update', callback);
      return () => off('youtube_upload_update');
    }
  }, [isConnected, callback, on, off]);

  return { isConnected };
};

/**
 * Hook for image cleaning updates
 */
export const useImageCleaningUpdates = (callback) => {
  const { on, off, isConnected } = useWebSocket('image-cleaning');

  useEffect(() => {
    if (isConnected && callback) {
      on('image_cleaning_update', callback);
      return () => off('image_cleaning_update');
    }
  }, [isConnected, callback, on, off]);

  return { isConnected };
};

/**
 * Hook for general notifications
 */
export const useNotifications = (callback) => {
  const { on, off, isConnected } = useWebSocket();

  useEffect(() => {
    if (isConnected && callback) {
      on('notification', callback);
      return () => off('notification');
    }
  }, [isConnected, callback, on, off]);

  return { isConnected };
};

export default useWebSocket;

