import React, { useEffect, useState, useRef } from 'react'
import { Waveform, Mic, Zap } from 'lucide-react'

interface AudioVisualizerProps {
  isListening: boolean
  isProcessing: boolean
}

interface VisualizerBar {
  height: number
  animated: boolean
}

export const ActiveUI: React.FC<AudioVisualizerProps> = ({ isListening, isProcessing }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationRef = useRef<number>()
  const [bars, setBars] = useState<VisualizerBar[]>(
    Array(32).fill({ height: 0, animated: false })
  )

  // Simulate audio waveform
  useEffect(() => {
    const updateBars = () => {
      setBars(prevBars =>
        prevBars.map(() => ({
          height: Math.random() * (isListening ? 100 : isProcessing ? 70 : 30),
          animated: isListening || isProcessing,
        }))
      )
      animationRef.current = requestAnimationFrame(updateBars)
    }

    if (isListening || isProcessing) {
      animationRef.current = requestAnimationFrame(updateBars)
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [isListening, isProcessing])

  // Draw waveform
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    ctx.clearRect(0, 0, canvas.width, canvas.height)
    const barWidth = canvas.width / bars.length
    const centerY = canvas.height / 2

    bars.forEach((bar, i) => {
      const barHeight = (bar.height / 100) * (canvas.height / 2)
      const x = i * barWidth + 2

      // Draw top bar
      ctx.fillStyle = isListening ? '#10b981' : isProcessing ? '#3b82f6' : '#64748b'
      ctx.fillRect(x, centerY - barHeight, barWidth - 4, barHeight)

      // Draw bottom bar (mirror)
      ctx.fillRect(x, centerY, barWidth - 4, barHeight)
    })
  }, [bars])

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-white flex items-center gap-2">
        <Waveform className="w-6 h-6 text-cyan-400" />
        Active UI - Unique Visual Feedback
      </h2>

      {/* Main Waveform Visualizer */}
      <div className="bg-slate-900 border border-slate-700 rounded-lg p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-300">Audio Waveform</h3>
          <div className="flex items-center gap-2">
            {isListening && (
              <div className="flex items-center gap-2 bg-green-900 text-green-300 px-3 py-1 rounded text-sm">
                <Mic className="w-4 h-4" />
                Listening
              </div>
            )}
            {isProcessing && (
              <div className="flex items-center gap-2 bg-blue-900 text-blue-300 px-3 py-1 rounded text-sm">
                <Zap className="w-4 h-4 animate-pulse" />
                Processing
              </div>
            )}
          </div>
        </div>

        <canvas
          ref={canvasRef}
          width={500}
          height={150}
          className="w-full bg-slate-950 rounded border border-slate-700"
        />
      </div>

      {/* Status Indicator Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Listening Status */}
        <div className={`border rounded-lg p-4 transition-colors ${
          isListening
            ? 'bg-green-900 border-green-700'
            : 'bg-slate-900 border-slate-700'
        }`}>
          <div className="flex items-center justify-between">
            <span className={isListening ? 'text-green-200' : 'text-slate-400'}>
              Listening Status
            </span>
            <div className={`w-3 h-3 rounded-full ${
              isListening 
                ? 'bg-green-400 animate-pulse' 
                : 'bg-slate-600'
            }`} />
          </div>
          <p className={`text-sm mt-2 ${isListening ? 'text-green-300' : 'text-slate-500'}`}>
            {isListening ? 'Microphone Active' : 'Waiting for input'}
          </p>
        </div>

        {/* Processing Status */}
        <div className={`border rounded-lg p-4 transition-colors ${
          isProcessing
            ? 'bg-blue-900 border-blue-700'
            : 'bg-slate-900 border-slate-700'
        }`}>
          <div className="flex items-center justify-between">
            <span className={isProcessing ? 'text-blue-200' : 'text-slate-400'}>
              Processing Status
            </span>
            <div className={`w-3 h-3 rounded-full ${
              isProcessing 
                ? 'bg-blue-400 animate-pulse' 
                : 'bg-slate-600'
            }`} />
          </div>
          <p className={`text-sm mt-2 ${isProcessing ? 'text-blue-300' : 'text-slate-500'}`}>
            {isProcessing ? 'Working on response' : 'Idle'}
          </p>
        </div>

        {/* Tool Indicator */}
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Active Tools</span>
            <div className="w-3 h-3 rounded-full bg-slate-600" />
          </div>
          <p className="text-sm text-slate-500 mt-2">No active tools</p>
        </div>
      </div>

      {/* Response Confidence Indicator */}
      <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Response Confidence</h3>
        <div className="space-y-3">
          {[
            { label: 'Speech Recognition', confidence: isListening ? 92 : 0 },
            { label: 'Intent Understanding', confidence: isProcessing ? 87 : 0 },
            { label: 'Response Generation', confidence: isProcessing ? 79 : 0 },
          ].map((item) => (
            <div key={item.label}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-slate-400">{item.label}</span>
                <span className="text-xs font-mono text-slate-300">{item.confidence}%</span>
              </div>
              <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-300 ${
                    item.confidence >= 80
                      ? 'bg-green-500'
                      : item.confidence >= 60
                      ? 'bg-blue-500'
                      : 'bg-slate-600'
                  }`}
                  style={{ width: `${item.confidence}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Animation Legend */}
      <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-slate-300 mb-3">Visual Feedback Legend</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse" />
            <span className="text-slate-300">Active/Listening</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 bg-blue-400 rounded-full animate-pulse" />
            <span className="text-slate-300">Processing</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 bg-slate-600 rounded-full" />
            <span className="text-slate-400">Idle</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 bg-red-400 rounded-full animate-pulse" />
            <span className="text-slate-300">Error/Warning</span>
          </div>
        </div>
      </div>
    </div>
  )
}
