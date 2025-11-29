import React, { useState, useEffect } from 'react';
import api from '../services/api';

const Workflow = () => {
  const [workflowData, setWorkflowData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadWorkflowStatus();
    
    // Auto-refresh every 10 seconds
    const interval = setInterval(() => {
      loadWorkflowStatus(true);
    }, 10000);
    
    return () => clearInterval(interval);
  }, []);

  const loadWorkflowStatus = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      
      const response = await api.get('/dashboard/workflow/status');
      
      if (response.data.success) {
        setWorkflowData(response.data.data);
      }
      
    } catch (error) {
      console.error('Failed to load workflow status:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'processing': return 'bg-blue-500';
      case 'idle': return 'bg-gray-400';
      case 'error': return 'bg-red-500';
      case 'success': return 'bg-green-500';
      default: return 'bg-gray-300';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'processing': return 'Processing';
      case 'idle': return 'Idle';
      case 'error': return 'Error';
      case 'success': return 'Success';
      default: return 'Unknown';
    }
  };

  const WorkflowStage = ({ stage, isLast }) => (
    <div className="flex items-center">
      <div className="flex-1">
        <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow">
          {/* Stage Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="text-4xl">{stage.icon}</div>
              <div>
                <h3 className="text-lg font-bold text-gray-800">{stage.name}</h3>
                <p className="text-sm text-gray-500">{stage.description}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${getStatusColor(stage.status)} ${stage.status === 'processing' ? 'animate-pulse' : ''}`}></div>
              <span className="text-sm font-medium text-gray-600">{getStatusText(stage.status)}</span>
            </div>
          </div>

          {/* Progress Bar (if processing) */}
          {stage.status === 'processing' && stage.current_progress !== undefined && (
            <div className="mb-4">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-gray-600">Progress</span>
                <span className="text-xs font-semibold text-blue-600">{stage.current_progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-500" 
                  style={{ width: `${stage.current_progress}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Stage Stats */}
          <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-100">
            <div>
              <p className="text-xs text-gray-500">Processed</p>
              <p className="text-lg font-bold text-gray-800">{stage.items_processed}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Success Rate</p>
              <p className="text-lg font-bold text-green-600">{stage.success_rate}%</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Avg Duration</p>
              <p className="text-lg font-bold text-blue-600">{stage.avg_duration}s</p>
            </div>
          </div>

          {/* Last Run */}
          <div className="mt-3 pt-3 border-t border-gray-100">
            <p className="text-xs text-gray-500">
              Last run: {new Date(stage.last_run).toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Arrow Connector */}
      {!isLast && (
        <div className="px-4">
          <div className="text-3xl text-gray-300">→</div>
        </div>
      )}
    </div>
  );

  const BottleneckAlert = ({ bottleneck }) => (
    <div className={`p-4 rounded-lg border-l-4 ${
      bottleneck.severity === 'high' 
        ? 'bg-red-50 border-red-500' 
        : 'bg-yellow-50 border-yellow-500'
    }`}>
      <div className="flex items-center gap-3">
        <span className="text-2xl">⚠️</span>
        <div className="flex-1">
          <p className="font-semibold text-gray-800">Bottleneck Detected: {bottleneck.name}</p>
          <p className="text-sm text-gray-600">
            {bottleneck.backlog} items waiting to be processed
          </p>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
          bottleneck.severity === 'high' 
            ? 'bg-red-100 text-red-800' 
            : 'bg-yellow-100 text-yellow-800'
        }`}>
          {bottleneck.severity.toUpperCase()}
        </span>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading workflow status...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-purple-800 rounded-xl shadow-lg p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Workflow Pipeline</h1>
            <p className="mt-2 text-purple-100">
              Real-time status of your news processing pipeline
            </p>
          </div>
          <button
            onClick={() => loadWorkflowStatus(true)}
            disabled={refreshing}
            className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors flex items-center gap-2"
          >
            <span className={refreshing ? 'animate-spin' : ''}>🔄</span>
            <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
          </button>
        </div>
      </div>

      {/* Overall Health Status */}
      {workflowData && (
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">
                {workflowData.overall_health === 'good' ? '✅' : '⚠️'}
              </span>
              <div>
                <h2 className="text-xl font-bold text-gray-800">Pipeline Health</h2>
                <p className="text-sm text-gray-500">
                  {workflowData.overall_health === 'good' 
                    ? 'All stages operating normally' 
                    : 'Some stages need attention'}
                </p>
              </div>
            </div>
            <div className={`px-4 py-2 rounded-full font-semibold ${
              workflowData.overall_health === 'good' 
                ? 'bg-green-100 text-green-800' 
                : 'bg-yellow-100 text-yellow-800'
            }`}>
              {workflowData.overall_health === 'good' ? 'HEALTHY' : 'NEEDS ATTENTION'}
            </div>
          </div>
        </div>
      )}

      {/* Bottleneck Alerts */}
      {workflowData && workflowData.bottlenecks && workflowData.bottlenecks.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-xl font-bold text-gray-800">⚠️ Bottlenecks Detected</h2>
          {workflowData.bottlenecks.map((bottleneck, index) => (
            <BottleneckAlert key={index} bottleneck={bottleneck} />
          ))}
        </div>
      )}

      {/* Workflow Stages */}
      {workflowData && workflowData.stages && (
        <div className="space-y-6">
          <h2 className="text-xl font-bold text-gray-800">Pipeline Stages</h2>
          <div className="flex flex-col gap-6">
            {workflowData.stages.map((stage, index) => (
              <WorkflowStage 
                key={stage.id} 
                stage={stage} 
                isLast={index === workflowData.stages.length - 1}
              />
            ))}
          </div>
        </div>
      )}

      {/* Pipeline Visualization (Horizontal) */}
      {workflowData && workflowData.stages && (
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-6">Pipeline Overview</h2>
          <div className="flex items-center justify-between overflow-x-auto pb-4">
            {workflowData.stages.map((stage, index) => (
              <React.Fragment key={stage.id}>
                <div className="flex-1 min-w-[150px] text-center">
                  <div className={`w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-3 ${
                    stage.status === 'processing' ? 'bg-blue-100 animate-pulse' :
                    stage.status === 'error' ? 'bg-red-100' :
                    'bg-gray-100'
                  }`}>
                    <span className="text-3xl">{stage.icon}</span>
                  </div>
                  <p className="font-semibold text-sm text-gray-800">{stage.name}</p>
                  <p className="text-xs text-gray-500 mt-1">{stage.items_processed} items</p>
                  {stage.current_progress !== undefined && (
                    <p className="text-xs text-blue-600 font-semibold mt-1">{stage.current_progress}%</p>
                  )}
                </div>
                {index < workflowData.stages.length - 1 && (
                  <div className="text-2xl text-gray-300 px-2">→</div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Workflow;

