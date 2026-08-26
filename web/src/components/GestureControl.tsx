import React, { useEffect, useRef, useState } from 'react'
import { Hand, AlertCircle } from 'lucide-react'

interface GestureControlProps {
  onGesture: (gesture: string) => void
  isEnabled: boolean
}

export const GestureControl: React.FC<GestureControlProps> = ({ onGesture, isEnabled }) => {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [initialized, setInitialized] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastGesture, setLastGesture] = useState<string>('')
  const [gestureCount, setGestureCount] = useState(0)

  useEffect(() => {
    if (!isEnabled || initialized) return

    const initCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
          video: { facingMode: 'user' } 
        })
        if (videoRef.current) {
          videoRef.current.srcObject = stream
          setInitialized(true)
        }
      } catch (err) {
        setError('Camera access denied. Gesture control requires camera permissions.')
      }
    }

    initCamera()
  }, [isEnabled, initialized])

  useEffect(() => {
    if (!initialized || !isEnabled || !videoRef.current || !canvasRef.current) return

    const simulateGestureDetection = () => {
      const gestures = ['palm', 'thumbs_up', 'thumbs_down', 'pinch', 'swipe_left', 'swipe_right']
      const randomGesture = gestures[Math.floor(Math.random() * gestures.length)]

      // Simulate gesture detection with 20% probability
      if (Math.random() < 0.05) {
        setLastGesture(randomGesture)
        setGestureCount(prev => prev + 1)
        onGesture(randomGesture)
      }
    }

    const interval = setInterval(simulateGestureDetection, 100)
    return () => clearInterval(interval)
  }, [initialized, isEnabled, onGesture])

  const gestureDescriptions: Record<string, { action: string; icon: string }> = {
    palm: { action: 'Pause/Resume', icon: '🖐️' },
    thumbs_up: { action: 'Confirm', icon: '👍' },
    thumbs_down: { action: 'Reject', icon: '👎' },
    pinch: { action: 'Activate Tool', icon: '🤌' },
    swipe_left: { action: 'Previous', icon: '👈' },
    swipe_right: { action: 'Next', icon: '👉' },
  }

  if (!isEnabled) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-lg p-6 text-center">
        <Hand className="w-8 h-8 text-slate-500 mx-auto mb-3" />
        <p className="text-slate-400">Air control gesture recognition disabled</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-white flex items-center gap-2">
        <Hand className="w-6 h-6 text-purple-400" />
        Air Control Gesture Recognition
      </h2>

      {error && (
        <div className="bg-red-900 border border-red-700 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-red-200">Camera Access Required</h4>
            <p className="text-sm text-red-300 mt-1">{error}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Video Feed */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
          <div className="relative aspect-video bg-black">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              className="w-full h-full object-cover"
            />
            <canvas
              ref={canvasRef}
              className="absolute inset-0"
            />
            {initialized && (
              <div className="absolute top-3 right-3 flex items-center gap-2 bg-green-900 text-green-300 px-3 py-1 rounded text-sm">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                Camera Active
              </div>
            )}
          </div>
        </div>

        {/* Gesture Reference & Stats */}
        <div className="space-y-4">
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-slate-300 mb-3">Supported Gestures</h3>
            <div className="space-y-2">
              {Object.entries(gestureDescriptions).map(([gesture, { action, icon }]) => (
                <div
                  key={gesture}
                  className={`p-2 rounded text-sm transition-colors ${
                    lastGesture === gesture
                      ? 'bg-purple-600 text-white'
                      : 'bg-slate-800 text-slate-300'
                  }`}
                >
                  <span className="text-lg mr-2">{icon}</span>
                  <span className="font-medium">{action}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Gestures Detected</span>
              <span className="text-xl font-bold text-purple-400">{gestureCount}</span>
            </div>
            {lastGesture && (
              <div className="mt-3 pt-3 border-t border-slate-700">
                <span className="text-xs text-slate-500">Last Detected:</span>
                <p className="text-purple-300 font-mono text-sm mt-1">{lastGesture}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
