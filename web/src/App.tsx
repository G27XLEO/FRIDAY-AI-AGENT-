import { useCallback, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import {
  Activity, AlertTriangle, ArrowUpRight, CheckCircle2,
  CircleDot, Clock3, Cpu, Gauge, Radio, RefreshCw, Server, ShieldCheck,
  Signal, Wifi, WifiOff, Zap,
} from 'lucide-react'

type Metrics = {
  timestamp?: string
  state?: string
  uptime_seconds?: number
  memory_usage_percent?: number
  active_connections?: number
  api_calls_total?: number
  api_calls_failed?: number
  avg_response_time_ms?: number
  tool_execution_count?: number
  tool_execution_failures?: number
  health_score?: number
  system?: { platform?: string; python_version?: string }
}
type EventItem = { timestamp?: string; time?: string; level?: string; event?: string; message?: string; name?: string }
type StatusPayload = { identity?: string; metrics?: Metrics; memory?: Record<string, unknown> }

const number = (value: number | undefined, digits = 0) =>
  typeof value === 'number' && Number.isFinite(value)
    ? value.toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits })
    : '—'
const percent = (value: number | undefined) => typeof value === 'number' ? `${number(value, 1)}%` : '—'
const duration = (value: number | undefined) => {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '—'
  const seconds = Math.max(0, Math.floor(value))
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return hours ? `${hours}h ${minutes}m` : minutes ? `${minutes}m ${seconds % 60}s` : `${seconds}s`
}
const time = (value?: string) => {
  if (!value) return 'Awaiting telemetry'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? 'Time unavailable' : date.toLocaleTimeString()
}

function App() {
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [identity, setIdentity] = useState('FRIDAY')
  const [events, setEvents] = useState<EventItem[]>([])
  const [connected, setConnected] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<string>()
  const [error, setError] = useState<string>()
  const [refreshing, setRefreshing] = useState(false)

  const refresh = useCallback(async (manual = false) => {
    if (manual) setRefreshing(true)
    try {
      const [statusResponse, metricsResponse, eventsResponse] = await Promise.all([
        fetch('/api/status', { headers: { Accept: 'application/json' } }),
        fetch('/api/metrics', { headers: { Accept: 'application/json' } }),
        fetch('/api/events?limit=8', { headers: { Accept: 'application/json' } }),
      ])
      if (!statusResponse.ok || !metricsResponse.ok) throw new Error('FRIDAY API returned an unsuccessful response')
      const status = await statusResponse.json() as StatusPayload
      const nextMetrics = await metricsResponse.json() as Metrics
      setIdentity(status.identity || 'FRIDAY')
      setMetrics({ ...status.metrics, ...nextMetrics })
      if (eventsResponse.ok) {
        const nextEvents = await eventsResponse.json() as EventItem[]
        setEvents(Array.isArray(nextEvents) ? nextEvents.slice(-8).reverse() : [])
      }
      setConnected(true)
      setError(undefined)
      setLastUpdated(new Date().toISOString())
    } catch (cause) {
      setConnected(false)
      setError(cause instanceof Error ? cause.message : 'Unable to reach FRIDAY API')
    } finally {
      if (manual) setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
    const interval = window.setInterval(() => void refresh(), 5000)
    return () => window.clearInterval(interval)
  }, [refresh])

  const state = metrics?.state || (connected ? 'idle' : 'offline')
  const health = metrics?.health_score
  const failureCount = (metrics?.api_calls_failed || 0) + (metrics?.tool_execution_failures || 0)

  return (
    <main className="app-shell">
      <div className="ambient ambient-one" aria-hidden="true" />
      <div className="ambient ambient-two" aria-hidden="true" />
      <header className="topbar">
        <a className="brand" href="/" aria-label="FRIDAY Mission Control home">
          <span className="brand-mark"><Activity size={22} /></span>
          <span><strong>FRIDAY</strong><small>MISSION CONTROL</small></span>
        </a>
        <div className="topbar-right">
          <span className={`connection-pill ${connected ? 'is-online' : 'is-offline'}`}>
            <span className="status-dot" />{connected ? 'SYSTEM LINKED' : 'API DISCONNECTED'}
          </span>
          <button className="icon-button" onClick={() => void refresh(true)} disabled={refreshing} aria-label="Refresh system status" title="Refresh">
            <RefreshCw size={17} className={refreshing ? 'spin' : ''} />
          </button>
        </div>
      </header>

      <section className="hero">
        <div>
          <div className="eyebrow"><span className="eyebrow-line" /> REALTIME OPERATIONS</div>
          <h1>Good to see you, <span>boss.</span></h1>
          <p className="hero-copy">Your systems at a glance. Clear signals, live telemetry, no noise.</p>
        </div>
        <div className="hero-status">
          <div className={`orb ${connected ? 'orb-live' : 'orb-offline'}`}><Radio size={24} /></div>
          <div><span className="muted-label">AGENT STATUS</span><strong className="state-value">{state.toUpperCase()}</strong><small>{connected ? `Updated ${time(lastUpdated)}` : 'Waiting for backend connection'}</small></div>
        </div>
      </section>

      {error && <div className="error-banner" role="status"><AlertTriangle size={17} /><span><strong>Connection issue.</strong> {error}. Check that the FRIDAY API is running.</span></div>}

      <section className="metrics-grid" aria-label="System metrics">
        <MetricCard icon={<ShieldCheck size={18} />} label="SYSTEM HEALTH" value={health === undefined ? '—' : `${number(health)}%`} detail={health === undefined ? 'No health telemetry' : health >= 80 ? 'All core signals healthy' : health >= 60 ? 'Monitor system signals' : 'Attention recommended'} accent="cyan" progress={health} />
        <MetricCard icon={<Gauge size={18} />} label="AVG RESPONSE" value={metrics ? `${number(metrics.avg_response_time_ms, 0)} ms` : '—'} detail="Recent API response average" accent="blue" />
        <MetricCard icon={<Cpu size={18} />} label="PROCESS MEMORY" value={percent(metrics?.memory_usage_percent)} detail="Python process memory share" accent="violet" progress={metrics?.memory_usage_percent} />
        <MetricCard icon={<Signal size={18} />} label="ACTIVE SESSIONS" value={number(metrics?.active_connections)} detail="Current connected clients" accent="green" />
      </section>

      <section className="content-grid">
        <div className="panel overview-panel">
          <div className="panel-heading"><div><span className="section-kicker">LIVE TELEMETRY</span><h2>System overview</h2></div><span className="live-label"><span className="status-dot" /> LIVE</span></div>
          <div className="overview-list">
            <OverviewRow icon={<Server size={18} />} label="Agent identity" value={identity} />
            <OverviewRow icon={<Activity size={18} />} label="Runtime state" value={state} status={connected} />
            <OverviewRow icon={<Clock3 size={18} />} label="Process uptime" value={duration(metrics?.uptime_seconds)} />
            <OverviewRow icon={<Zap size={18} />} label="Tool executions" value={number(metrics?.tool_execution_count)} />
            <OverviewRow icon={<AlertTriangle size={18} />} label="Recorded failures" value={number(failureCount)} warn={failureCount > 0} />
            <OverviewRow icon={connected ? <Wifi size={18} /> : <WifiOff size={18} />} label="API connectivity" value={connected ? 'Connected' : 'Offline'} status={connected} />
          </div>
          <div className="panel-foot"><span>Last successful sync</span><strong>{time(lastUpdated)}</strong></div>
        </div>

        <div className="panel events-panel">
          <div className="panel-heading"><div><span className="section-kicker">ACTIVITY STREAM</span><h2>Recent events</h2></div><span className="event-count">{events.length} EVENTS</span></div>
          {events.length ? <div className="event-list">{events.map((event, index) => {
            const label = event.message || event.event || event.name || 'System event'
            const stamp = event.timestamp || event.time
            const isError = /error|fail|critical/i.test(`${event.level || ''} ${label}`)
            return <div className="event-row" key={`${stamp || 'event'}-${index}`}><span className={`event-icon ${isError ? 'event-error' : ''}`}>{isError ? <AlertTriangle size={15} /> : <CircleDot size={15} />}</span><div className="event-copy"><strong>{label}</strong><small>{time(stamp)}</small></div><ArrowUpRight size={14} className="event-arrow" /></div>
          })}</div> : <div className="empty-state"><Activity size={24} /><strong>No recent events</strong><span>{connected ? 'New telemetry will appear here automatically.' : 'Connect the backend to load activity.'}</span></div>}
          <div className="panel-foot"><span>Refresh interval</span><strong>5 seconds</strong></div>
        </div>
      </section>

      <footer className="footer"><span><span className="footer-spark">✳</span> FRIDAY <span className="footer-muted">/ INTELLIGENCE, AT A GLANCE</span></span><span>{metrics?.system?.python_version ? `PYTHON ${metrics.system.python_version}` : 'WEB CONSOLE'} <i /> {connected ? <><CheckCircle2 size={13} /> TELEMETRY ACTIVE</> : 'AWAITING CONNECTION'}</span></footer>
    </main>
  )
}

function MetricCard({ icon, label, value, detail, accent, progress }: { icon: ReactNode; label: string; value: string; detail: string; accent: string; progress?: number }) {
  return <article className={`metric-card accent-${accent}`}><div className="metric-top"><span className="metric-icon">{icon}</span><span className="metric-label">{label}</span></div><div className="metric-value">{value}</div><p>{detail}</p>{progress !== undefined && <div className="progress-track"><span style={{ width: `${Math.min(100, Math.max(0, progress))}%` }} /></div>}</article>
}
function OverviewRow({ icon, label, value, status, warn }: { icon: React.ReactNode; label: string; value: string; status?: boolean; warn?: boolean }) {
  return <div className="overview-row"><span className="row-icon">{icon}</span><span className="row-label">{label}</span><strong className={warn ? 'value-warn' : status === undefined ? '' : status ? 'value-good' : 'value-offline'}>{value}</strong></div>
}
export default App
