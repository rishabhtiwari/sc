import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const Dashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalNews: 0,
    withAudio: 0,
    withVideo: 0,
    uploaded: 0,
    processing: 0,
    failed: 0
  });
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadDashboardData();

    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      loadDashboardData(true);
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      // Fetch stats and activities in parallel
      const [statsResponse, activityResponse] = await Promise.all([
        api.get('/dashboard/stats'),
        api.get('/dashboard/activity')
      ]);

      if (statsResponse.data.success) {
        setStats(statsResponse.data.data);
      }

      if (activityResponse.data.success) {
        setActivities(activityResponse.data.data);
      }

    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const StatCard = ({ icon, label, value, color, percentage, trend }) => (
    <div className="bg-white rounded-xl shadow-md p-6 border-l-4 hover:shadow-lg transition-shadow" style={{ borderColor: color }}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-500 text-sm font-medium">{label}</p>
          <p className="text-3xl font-bold mt-2" style={{ color }}>{value}</p>
          <div className="flex items-center gap-2 mt-1">
            {percentage !== undefined && (
              <p className="text-sm text-gray-400">{percentage}% of total</p>
            )}
            {trend && (
              <span className={`text-xs font-semibold ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
                {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}%
              </span>
            )}
          </div>
        </div>
        <div className="text-5xl opacity-20">{icon}</div>
      </div>
    </div>
  );

  const ActivityItem = ({ activity }) => {
    const getStatusColor = (status) => {
      switch (status) {
        case 'success': return 'bg-green-50 border-green-200';
        case 'processing': return 'bg-blue-50 border-blue-200';
        case 'error': return 'bg-red-50 border-red-200';
        default: return 'bg-gray-50 border-gray-200';
      }
    };

    const getTimeAgo = (timestamp) => {
      const now = new Date();
      const time = new Date(timestamp);
      const diffMs = now - time;
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins} min ago`;
      if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
      return time.toLocaleDateString();
    };

    return (
      <div className={`flex items-center gap-3 p-3 rounded-lg border ${getStatusColor(activity.status)}`}>
        <span className="text-xl">{activity.icon}</span>
        <div className="flex-1">
          <p className="font-medium text-sm">{activity.title}</p>
          <p className="text-xs text-gray-500">{activity.description}</p>
          {activity.progress !== undefined && (
            <div className="mt-2">
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div
                  className="bg-blue-600 h-1.5 rounded-full transition-all"
                  style={{ width: `${activity.progress}%` }}
                ></div>
              </div>
              <p className="text-xs text-gray-500 mt-1">{activity.progress}% complete</p>
            </div>
          )}
        </div>
        <span className="text-xs text-gray-400">{getTimeAgo(activity.timestamp)}</span>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 rounded-xl shadow-lg p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Welcome to News Automation System</h1>
            <p className="mt-2 text-blue-100">
              Manage your entire news workflow from fetching to YouTube upload
            </p>
          </div>
          <button
            onClick={() => loadDashboardData(true)}
            disabled={refreshing}
            className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors flex items-center gap-2"
          >
            <span className={refreshing ? 'animate-spin' : ''}>🔄</span>
            <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon="📰"
          label="Total News Articles"
          value={stats.totalNews}
          color="#3b82f6"
          trend={5.2}
        />
        <StatCard
          icon="🎤"
          label="With Audio"
          value={stats.withAudio}
          color="#10b981"
          percentage={stats.totalNews > 0 ? Math.round((stats.withAudio / stats.totalNews) * 100) : 0}
          trend={3.8}
        />
        <StatCard
          icon="🎬"
          label="With Video"
          value={stats.withVideo}
          color="#f59e0b"
          percentage={stats.totalNews > 0 ? Math.round((stats.withVideo / stats.totalNews) * 100) : 0}
          trend={-1.2}
        />
        <StatCard
          icon="📺"
          label="Uploaded to YouTube"
          value={stats.uploaded}
          color="#ef4444"
          percentage={stats.totalNews > 0 ? Math.round((stats.uploaded / stats.totalNews) * 100) : 0}
          trend={2.5}
        />
      </div>

      {/* Additional Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-gray-800">Processing Status</h3>
            <span className="text-2xl">⚙️</span>
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">In Progress</span>
              <span className="text-lg font-bold text-blue-600">{stats.processing}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Failed</span>
              <span className="text-lg font-bold text-red-600">{stats.failed}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Success Rate</span>
              <span className="text-lg font-bold text-green-600">
                {stats.totalNews > 0 ? Math.round(((stats.totalNews - stats.failed) / stats.totalNews) * 100) : 0}%
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-gray-800">Quick Stats</h3>
            <span className="text-2xl">📊</span>
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Completion Rate</span>
              <span className="text-lg font-bold text-purple-600">
                {stats.totalNews > 0 ? Math.round((stats.uploaded / stats.totalNews) * 100) : 0}%
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Pending Videos</span>
              <span className="text-lg font-bold text-orange-600">{stats.withAudio - stats.withVideo}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Pending Uploads</span>
              <span className="text-lg font-bold text-indigo-600">{stats.withVideo - stats.uploaded}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <button
            onClick={() => navigate('/news-fetcher')}
            className="flex items-center gap-3 p-4 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
          >
            <span className="text-2xl">🚀</span>
            <div className="text-left">
              <p className="font-semibold text-blue-900">Fetch News</p>
              <p className="text-xs text-blue-600">Run news fetcher</p>
            </div>
          </button>
          <button
            onClick={() => navigate('/voice-llm')}
            className="flex items-center gap-3 p-4 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors"
          >
            <span className="text-2xl">🤖</span>
            <div className="text-left">
              <p className="font-semibold text-purple-900">Configure LLM</p>
              <p className="text-xs text-purple-600">Prompts & Voice</p>
            </div>
          </button>
          <button
            onClick={() => navigate('/workflow')}
            className="flex items-center gap-3 p-4 bg-green-50 hover:bg-green-100 rounded-lg transition-colors"
          >
            <span className="text-2xl">🔄</span>
            <div className="text-left">
              <p className="font-semibold text-green-900">View Workflow</p>
              <p className="text-xs text-green-600">Pipeline status</p>
            </div>
          </button>
          <button
            onClick={() => navigate('/youtube-uploader')}
            className="flex items-center gap-3 p-4 bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
          >
            <span className="text-2xl">📺</span>
            <div className="text-left">
              <p className="font-semibold text-red-900">YouTube</p>
              <p className="text-xs text-red-600">Upload videos</p>
            </div>
          </button>
          <button
            onClick={() => navigate('/monitoring')}
            className="flex items-center gap-3 p-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <span className="text-2xl">📊</span>
            <div className="text-left">
              <p className="font-semibold text-gray-900">Monitoring</p>
              <p className="text-xs text-gray-600">Logs & alerts</p>
            </div>
          </button>
        </div>
      </div>

      {/* Workflow Pipeline */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4">News Processing Pipeline</h2>
        <div className="flex items-center justify-between">
          <div className="flex-1 text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-2">
              <span className="text-2xl">📰</span>
            </div>
            <p className="font-semibold text-sm">Fetch News</p>
            <p className="text-xs text-gray-500 mt-1">GNews API</p>
          </div>
          <div className="text-2xl text-gray-300">→</div>
          <div className="flex-1 text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-2">
              <span className="text-2xl">🤖</span>
            </div>
            <p className="font-semibold text-sm">LLM Enrichment</p>
            <p className="text-xs text-gray-500 mt-1">Summarize</p>
          </div>
          <div className="text-2xl text-gray-300">→</div>
          <div className="flex-1 text-center">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-2">
              <span className="text-2xl">🎤</span>
            </div>
            <p className="font-semibold text-sm">Generate Audio</p>
            <p className="text-xs text-gray-500 mt-1">TTS</p>
          </div>
          <div className="text-2xl text-gray-300">→</div>
          <div className="flex-1 text-center">
            <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-2">
              <span className="text-2xl">🎬</span>
            </div>
            <p className="font-semibold text-sm">Create Video</p>
            <p className="text-xs text-gray-500 mt-1">FFmpeg</p>
          </div>
          <div className="text-2xl text-gray-300">→</div>
          <div className="flex-1 text-center">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-2">
              <span className="text-2xl">📺</span>
            </div>
            <p className="font-semibold text-sm">Upload</p>
            <p className="text-xs text-gray-500 mt-1">YouTube</p>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-800">Recent Activity</h2>
          <button
            onClick={() => navigate('/monitoring')}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            View All →
          </button>
        </div>
        <div className="space-y-3">
          {activities.length > 0 ? (
            activities.slice(0, 5).map((activity) => (
              <ActivityItem key={activity.id} activity={activity} />
            ))
          ) : (
            <div className="text-center py-8 text-gray-400">
              <p>No recent activity</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

