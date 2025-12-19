// Application-wide constants

export const APP_NAME = 'News Automation System';
export const APP_VERSION = '1.0.0';

// API Configuration
export const API_BASE_URL = '/api';
export const API_TIMEOUT = 30000; // 30 seconds

// Routes
export const ROUTES = {
  DASHBOARD: '/',
  NEWS_FETCHER: '/news-fetcher',
  IMAGE_CLEANING: '/image-cleaning',
  VOICE_LLM: '/voice-llm',
  YOUTUBE: '/youtube',
};

// Navigation Items
export const NAV_ITEMS = [
  { 
    path: ROUTES.DASHBOARD, 
    icon: '📊', 
    label: 'Dashboard',
    description: 'Overview and statistics'
  },
  { 
    path: ROUTES.NEWS_FETCHER, 
    icon: '📰', 
    label: 'News Fetcher',
    description: 'Manage news sources and articles'
  },
  { 
    path: ROUTES.IMAGE_CLEANING, 
    icon: '🖼️', 
    label: 'Image Cleaning',
    description: 'Remove watermarks from images'
  },
  {
    path: ROUTES.VOICE_LLM,
    icon: '🎤',
    label: 'Audio Processing',
    description: 'Voice configuration and audio gallery'
  },
  {
    path: ROUTES.YOUTUBE,
    icon: '📺',
    label: 'YouTube Uploader',
    description: 'Upload videos to YouTube'
  },
];

// Status Colors
export const STATUS_COLORS = {
  SUCCESS: '#10b981',
  ERROR: '#ef4444',
  WARNING: '#f59e0b',
  INFO: '#3b82f6',
  PENDING: '#6b7280',
};

// Pagination
export const DEFAULT_PAGE_SIZE = 25;
export const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

// WebSocket Events (for future use)
export const WS_EVENTS = {
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  NEWS_FETCHED: 'news_fetched',
  AUDIO_GENERATED: 'audio_generated',
  VIDEO_GENERATED: 'video_generated',
  YOUTUBE_UPLOADED: 'youtube_uploaded',
  JOB_STATUS: 'job_status',
};

