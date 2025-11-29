import React, { useState, useEffect } from 'react';
import api from '../services/api';

const Monitoring = () => {
  const [activeTab, setActiveTab] = useState('logs'); // logs, errors, alerts, services, metrics
  const [logs, setLogs] = useState([]);
  const [errors, setErrors] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [services, setServices] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
  // Filters
  const [logLevel, setLogLevel] = useState('all');
  const [serviceFilter, setServiceFilter] = useState('all');

  useEffect(() => {
    loadMonitoringData();
    
    // Auto-refresh every 15 seconds
    const interval = setInterval(() => {
      loadMonitoringData(true);
    }, 15000);
    
    return () => clearInterval(interval);
  }, [logLevel, serviceFilter]);

  const loadMonitoringData = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      
      // Load data based on active tab
      const promises = [
        api.get(`/monitoring/logs?level=${logLevel}&service=${serviceFilter}&limit=50`),
        api.get('/monitoring/errors'),
        api.get('/monitoring/alerts'),
        api.get('/dashboard/services/health'),
        api.get('/monitoring/metrics')
      ];
      
      const [logsRes, errorsRes, alertsRes, servicesRes, metricsRes] = await Promise.all(promises);
      
      if (logsRes.data.success) {
        setLogs(logsRes.data.data.logs);
      }
      
      if (errorsRes.data.success) {
        setErrors(errorsRes.data.data.errors);
      }
      
      if (alertsRes.data.success) {
        setAlerts(alertsRes.data.data.alerts);
      }
      
      if (servicesRes.data.success) {
        setServices(servicesRes.data.data.services);
      }
      
      if (metricsRes.data.success) {
        setMetrics(metricsRes.data.data);
      }
      
    } catch (error) {
      console.error('Failed to load monitoring data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const acknowledgeAlert = async (alertId) => {
    try {
      await api.post(`/monitoring/alerts/${alertId}/acknowledge`);
      loadMonitoringData(true);
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  const getLevelColor = (level) => {
    switch (level) {
      case 'error': return 'bg-red-100 text-red-800 border-red-200';
      case 'warning': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'info': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'debug': return 'bg-gray-100 text-gray-800 border-gray-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-500';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-500';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-500';
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-500';
      default: return 'bg-gray-100 text-gray-800 border-gray-500';
    }
  };

  const getServiceStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'bg-green-500';
      case 'unhealthy': return 'bg-red-500';
      case 'timeout': return 'bg-yellow-500';
      case 'unreachable': return 'bg-gray-500';
      default: return 'bg-gray-400';
    }
  };

  const LogsTab = () => (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="flex items-center gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Log Level</label>
            <select
              value={logLevel}
              onChange={(e) => setLogLevel(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Levels</option>
              <option value="error">Error</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
              <option value="debug">Debug</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Service</label>
            <select
              value={serviceFilter}
              onChange={(e) => setServiceFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Services</option>
              <option value="news-fetcher">News Fetcher</option>
              <option value="audio-generation">Audio Generation</option>
              <option value="video-generation">Video Generation</option>
              <option value="youtube-uploader">YouTube Uploader</option>
              <option value="iopaint">IOPaint</option>
            </select>
          </div>
        </div>
      </div>

      {/* Logs List */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="max-h-[600px] overflow-y-auto">
          {logs.length > 0 ? (
            <table className="w-full">
              <thead className="bg-gray-50 sticky top-0">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Level</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Service</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Message</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-500 whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getLevelColor(log.level)}`}>
                        {log.level.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">{log.service}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{log.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="text-center py-12 text-gray-400">
              <p>No logs found</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const ErrorsTab = () => (
    <div className="space-y-4">
      {errors.length > 0 ? (
        errors.map((error) => (
          <div key={error.id} className={`p-4 rounded-lg border-l-4 ${getSeverityColor(error.severity)}`}>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xl">🚨</span>
                  <h3 className="font-bold text-gray-800">{error.error_type}</h3>
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getSeverityColor(error.severity)}`}>
                    {error.severity.toUpperCase()}
                  </span>
                </div>
                <p className="text-sm text-gray-700 mb-2">{error.message}</p>
                <div className="flex items-center gap-4 text-xs text-gray-500">
                  <span>Service: {error.service}</span>
                  <span>Count: {error.count}</span>
                  <span>Last seen: {new Date(error.last_seen).toLocaleString()}</span>
                </div>
                {error.stack_trace && (
                  <details className="mt-3">
                    <summary className="cursor-pointer text-sm text-blue-600 hover:text-blue-800">
                      View stack trace
                    </summary>
                    <pre className="mt-2 p-3 bg-gray-50 rounded text-xs overflow-x-auto">
                      {error.stack_trace}
                    </pre>
                  </details>
                )}
              </div>
            </div>
          </div>
        ))
      ) : (
        <div className="bg-white rounded-lg shadow-md p-12 text-center text-gray-400">
          <p>No errors found</p>
        </div>
      )}
    </div>
  );

  const AlertsTab = () => (
    <div className="space-y-4">
      {alerts.length > 0 ? (
        alerts.map((alert) => (
          <div key={alert.id} className={`p-4 rounded-lg border-l-4 ${
            alert.severity === 'critical' ? 'bg-red-50 border-red-500' :
            alert.severity === 'warning' ? 'bg-yellow-50 border-yellow-500' :
            'bg-blue-50 border-blue-500'
          } ${alert.acknowledged ? 'opacity-50' : ''}`}>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xl">🔔</span>
                  <h3 className="font-bold text-gray-800">{alert.title}</h3>
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                    alert.severity === 'critical' ? 'bg-red-100 text-red-800' :
                    alert.severity === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {alert.severity.toUpperCase()}
                  </span>
                  {alert.acknowledged && (
                    <span className="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-600">
                      ACKNOWLEDGED
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-700 mb-2">{alert.message}</p>
                <div className="flex items-center gap-4 text-xs text-gray-500 mb-3">
                  <span>Service: {alert.service}</span>
                  <span>Time: {new Date(alert.timestamp).toLocaleString()}</span>
                </div>
                {alert.actions && alert.actions.length > 0 && (
                  <div className="mb-3">
                    <p className="text-xs font-semibold text-gray-600 mb-1">Suggested Actions:</p>
                    <ul className="list-disc list-inside text-xs text-gray-600">
                      {alert.actions.map((action, index) => (
                        <li key={index}>{action}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
              {!alert.acknowledged && (
                <button
                  onClick={() => acknowledgeAlert(alert.id)}
                  className="ml-4 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
                >
                  Acknowledge
                </button>
              )}
            </div>
          </div>
        ))
      ) : (
        <div className="bg-white rounded-lg shadow-md p-12 text-center text-gray-400">
          <p>No active alerts</p>
        </div>
      )}
    </div>
  );

  const ServicesTab = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {services.map((service, index) => (
        <div key={index} className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-gray-800">{service.name}</h3>
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${getServiceStatusColor(service.status)}`}></div>
              <span className="text-sm font-medium text-gray-600 capitalize">{service.status}</span>
            </div>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">URL:</span>
              <span className="text-gray-700 font-mono text-xs">{service.url}</span>
            </div>
            {service.response_time && (
              <div className="flex justify-between">
                <span className="text-gray-500">Response Time:</span>
                <span className="text-gray-700">{service.response_time.toFixed(2)} ms</span>
              </div>
            )}
            {service.error && (
              <div className="mt-2 p-2 bg-red-50 rounded text-xs text-red-700">
                Error: {service.error}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading monitoring data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-gray-700 to-gray-900 rounded-xl shadow-lg p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">System Monitoring</h1>
            <p className="mt-2 text-gray-300">
              Logs, errors, alerts, and service health monitoring
            </p>
          </div>
          <button
            onClick={() => loadMonitoringData(true)}
            disabled={refreshing}
            className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors flex items-center gap-2"
          >
            <span className={refreshing ? 'animate-spin' : ''}>🔄</span>
            <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="border-b border-gray-200">
          <nav className="flex gap-4 px-6">
            {[
              { id: 'logs', label: 'Logs', icon: '📜' },
              { id: 'errors', label: 'Errors', icon: '🚨' },
              { id: 'alerts', label: 'Alerts', icon: '🔔' },
              { id: 'services', label: 'Services', icon: '🔧' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 border-b-2 font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'logs' && <LogsTab />}
          {activeTab === 'errors' && <ErrorsTab />}
          {activeTab === 'alerts' && <AlertsTab />}
          {activeTab === 'services' && <ServicesTab />}
        </div>
      </div>
    </div>
  );
};

export default Monitoring;

