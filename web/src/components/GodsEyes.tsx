import React, { useEffect, useState } from 'react'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Activity, AlertCircle, Zap } from 'lucide-react'

interface Metrics {
  timestamp: string
  state: string
  memory_usage_percent: number
  active_connections: number
  avg_response_time_ms: number
  health_score: number
  api_calls_total: number
  api_calls_failed: number
  tool_execution_count: number
}

interface GodsEyesProps {
  metrics: Metrics | null
}

export const GodsEyes: React.FC<GodsEyesProps> = ({ metrics }) => {
  const [metricsHistory, setMetricsHistory] = useState<Metrics[]>([])

  useEffect(() => {
    if (metrics) {
      setMetricsHistory(prev => [...prev.slice(-59), metrics])
    }
  }, [metrics])

  if (!metrics) {
    return (
      <div className="flex items-center justify-center h-96 bg-slate-900 rounded-lg border border-slate-700">
        <p className="text-slate-400">Waiting for metrics...</p>
      </div>
    )
  }

  const getStateColor = (state: string) => {
    switch (state) {
      case 'active':
        return 'text-green-400'
      case 'processing':
        return 'text-blue-400'
      case 'error':
        return 'text-red-400'
      default:
        return 'text-yellow-400'
    }
  }

  const getHealthIndicator = (score: number) => {
    if (score >= 80) return { bg: 'bg-green-600', text: 'Excellent' }
    if (score >= 60) return { bg: 'bg-blue-600', text: 'Good' }
    if (score >= 40) return { bg: 'bg-yellow-600', text: 'Fair' }
    return { bg: 'bg-red-600', text: 'Critical' }
  }

  const health = getHealthIndicator(metrics.health_score)

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-white flex items-center gap-2">
        <Activity className="w-6 h-6 text-blue-400" />
        God's Eyes - Live Monitoring
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* System Status Card */}
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Agent State</span>
            <span className={`font-bold uppercase ${getStateColor(metrics.state)} flex items-center gap-1`}>
              <Zap className="w-4 h-4" />
              {metrics.state}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Health Score</span>
            <div className="flex items-center gap-2">
              <div className={`${health.bg} text-white font-bold px-3 py-1 rounded`}>
                {metrics.health_score}%
              </div>
              <span className="text-sm text-slate-400">{health.text}</span>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Active Connections</span>
            <span className="text-green-400 font-mono">{metrics.active_connections}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Memory Usage</span>
            <span className="text-blue-400 font-mono">{metrics.memory_usage_percent.toFixed(1)}%</span>
          </div>
        </div>

        {/* Performance Metrics Card */}
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Avg Response Time</span>
            <span className="text-cyan-400 font-mono">{metrics.avg_response_time_ms.toFixed(1)}ms</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">API Calls</span>
            <span className="text-purple-400 font-mono">
              {metrics.api_calls_total} 
              {metrics.api_calls_failed > 0 && (
                <span className="text-red-400 ml-2">({metrics.api_calls_failed} failed)</span>
              )}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Tool Executions</span>
            <span className="text-amber-400 font-mono">{metrics.tool_execution_count}</span>
          </div>
          <div className="text-xs text-slate-500 pt-2 border-t border-slate-700">
            Updated: {new Date(metrics.timestamp).toLocaleTimeString()}
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Response Time Chart */}
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-slate-300 mb-3">Response Time (ms)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={metricsHistory}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="timestamp" stroke="#9ca3af" style={{ fontSize: '12px' }} />
              <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Line 
                type="monotone" 
                dataKey="avg_response_time_ms" 
                stroke="#06b6d4" 
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Memory Usage Chart */}
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-slate-300 mb-3">Memory Usage (%)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={metricsHistory}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="timestamp" stroke="#9ca3af" style={{ fontSize: '12px' }} />
              <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Area 
                type="monotone" 
                dataKey="memory_usage_percent" 
                fill="#3b82f6" 
                stroke="#0ea5e9"
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Warnings/Alerts */}
      {metrics.health_score < 60 && (
        <div className="bg-red-900 border border-red-700 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-red-200">System Health Warning</h4>
            <p className="text-sm text-red-300 mt-1">
              Health score below optimal levels. Check active connections and API failure rate.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
