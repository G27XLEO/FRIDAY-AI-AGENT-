import { useCallback, useEffect, useState } from 'react'
import { Activity, ArrowUpRight, Bot, Clock3, Cpu, RefreshCw, ShieldCheck, Terminal, Wifi, WifiOff, Zap } from 'lucide-react'
import { ThinkingOrb } from 'thinking-orbs'
import { BorderBeam } from 'border-beam'
import { MetalFx, MetalText } from 'metal-fx'
import './styles.css'

type Metrics = {
  timestamp: string
  state: string
  uptime_seconds: number
  active_connections: number
  api_calls_total: number
  avg_response_time_ms: number
  tool_execution_count: number
  tool_execution_failures: number
}
type Event = { timestamp: string; event_type: string; severity: string; message: string }

function uptime(seconds: number) {
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  return hours ? String(hours) + 'h ' + String(minutes % 60) + 'm' : String(minutes) + 'm'
}

function Stat({ title, value, detail }: { title: string; value: string; detail: string }) {
  return <article className="stat panel"><span>{title}</span><strong>{value}</strong><small>{detail}</small></article>
}

export default function App() {
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [events, setEvents] = useState<Event[]>([])
  const [error, setError] = useState('')
  const [updated, setUpdated] = useState('')
  const [socketLive, setSocketLive] = useState(false)
  const [help, setHelp] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const [m, e] = await Promise.all([
        fetch('/api/metrics', { cache: 'no-store' }),
        fetch('/api/events?limit=8', { cache: 'no-store' }),
      ])
      if (!m.ok || !e.ok) throw new Error('FRIDAY API unavailable')
      const next = await m.json() as Metrics
      const activity = await e.json() as Event[]
      setMetrics(next)
      setEvents(Array.isArray(activity) ? activity : [])
      setError('')
      setUpdated(new Date().toLocaleTimeString())
    } catch (cause) {
      setMetrics(null)
      setError(cause instanceof Error ? cause.message : 'Network error')
    }
  }, [])

  useEffect(() => {
    void refresh()
    const interval = window.setInterval(() => void refresh(), 15000)
    return () => window.clearInterval(interval)
  }, [refresh])

  useEffect(() => {
    let socket: WebSocket | undefined
    let retry: number | undefined
    let ended = false
    const connect = () => {
      if (ended) return
      const scheme = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      socket = new WebSocket(scheme + '//' + window.location.host + '/ws/metrics')
      socket.onopen = () => setSocketLive(true)
      socket.onmessage = (message) => {
        try {
          const packet = JSON.parse(message.data) as { type: string; data?: Metrics }
          if (packet.type === 'metrics_update' && packet.data) {
            setMetrics(previous => ({ ...(previous ?? {}), ...packet.data } as Metrics))
          }
        } catch { /* Ignore malformed telemetry. */ }
      }
      socket.onclose = () => {
        setSocketLive(false)
        if (!ended) retry = window.setTimeout(connect, 5000)
      }
      socket.onerror = () => socket?.close()
    }
    connect()
    return () => {
      ended = true
      if (retry !== undefined) window.clearTimeout(retry)
      socket?.close()
    }
  }, [])

  const orbState = metrics === null ? 'connecting'
    : metrics.state === 'processing' ? 'solving'
    : metrics.state === 'active' ? 'working' : 'breathing'

  return (
    <div className="shell">
      <aside className="sidebar">
        <a href="/" className="brand"><span className="brand-icon"><Bot size={25}/></span>FRIDAY <em>OS</em></a>
        <p className="nav-label">MISSION CONTROL</p>
        <nav aria-label="Mission control">
          <a className="nav-item selected" href="#overview"><Activity size={18}/> Overview</a>
          <a className="nav-item" href="#intelligence"><Cpu size={18}/> Intelligence</a>
          <a className="nav-item" href="#activity"><Clock3 size={18}/> Activity</a>
        </nav>
        <div className="side-foot">
          <div><ShieldCheck size={17}/> OPERATOR-LED</div>
          <p>Software only. No destructive actions from this console.</p>
        </div>
      </aside>
      <main id="overview" className="main">
        <header className="topbar">
          <div className="breadcrumb">FRIDAY <span>/</span> Mission Control <span>/</span> Overview</div>
          <div className="top-actions">
            <span className={socketLive ? 'connect online' : 'connect'}>
              {socketLive ? <Wifi size={15}/> : <WifiOff size={15}/>}
              {socketLive ? 'Live telemetry' : 'Reconnecting'}
            </span>
            <button className="icon-button" aria-label="Refresh metrics" onClick={() => void refresh()}><RefreshCw size={17}/></button>
          </div>
        </header>
        <div className="intro">
          <span className="eyebrow">INTELLIGENCE SYSTEM / VERSION 2</span>
          <h1>Mission Control<span className="aqua">.</span></h1>
          <p>Observe the runtime. Plan with evidence. Keep the operator in command.</p>
        </div>
        <section id="intelligence" className="hero">
          <BorderBeam size="md" colorVariant="ocean" strength={0.65} active={socketLive}>
            <div className="core panel">
              <div className="overline"><span className="dot"/> FRIDAY CORE / API STATUS</div>
              <div className="orb-stage"><ThinkingOrb state={orbState} size={64} dark/></div>
              <MetalText font="600 26px/1.2 Inter" color="#E7F8FF">FRIDAY</MetalText>
              <h2>{metrics ? metrics.state.toUpperCase() : 'DISCONNECTED'}</h2>
              <p>{metrics ? 'Dashboard telemetry is available.' : 'Waiting for the FRIDAY API server.'}</p>
              <div className="core-bottom"><span>ENGINE <b>GROQ + LIVEKIT</b></span><span>POLICY <b>HUMAN CONTROL</b></span></div>
            </div>
          </BorderBeam>
          <div className="mission panel">
            <div className="panel-title"><span><Zap size={17}/> MISSION INTELLIGENCE</span><span className="tag">UPGRADE</span></div>
            <h2>A more capable FRIDAY.</h2>
            <p>Mission planning adds observable success criteria, step-by-step progress reports and independent verification instead of unsupported completion claims.</p>
            <div className="steps">
              <div><span>01</span><section><b>UNDERSTAND</b><small>Goal, context, constraints</small></section></div>
              <div><span>02</span><section><b>EXECUTE SAFELY</b><small>Bounded actions with permissions</small></section></div>
              <div><span>03</span><section><b>VERIFY</b><small>Evidence before success claims</small></section></div>
            </div>
            <MetalFx preset="silver" strength={0.6}><button className="metal-action" onClick={() => setHelp(!help)}>How the system works <ArrowUpRight size={16}/></button></MetalFx>
            {help && <p className="help-note" role="status">This read-only UI shows FastAPI telemetry, not LiveKit microphone activity. Connect a separate LiveKit client to speak with the agent.</p>}
          </div>
        </section>
        <section className="stats" aria-label="Runtime metrics">
          <Stat title="UPTIME" value={metrics ? uptime(metrics.uptime_seconds) : '—'} detail="API process"/>
          <Stat title="CONNECTIONS" value={metrics ? String(metrics.active_connections) : '—'} detail="Dashboard viewers"/>
          <Stat title="TOOL EXECUTIONS" value={metrics ? String(metrics.tool_execution_count) : '—'} detail={metrics ? String(metrics.tool_execution_failures) + ' failures' : 'Awaiting data'}/>
          <Stat title="AVG RESPONSE" value={metrics ? String(metrics.avg_response_time_ms.toFixed(0)) + 'ms' : '—'} detail="0 means no samples"/>
        </section>
        <section id="activity" className="activity panel">
          <header><div><span className="eyebrow">OBSERVABILITY</span><h2>Event stream</h2></div><small>{updated ? 'Last sync ' + updated : 'Not yet synchronized'}</small></header>
          {error ? <div className="empty" role="alert"><WifiOff size={19}/> {error}. Run the FastAPI dashboard on port 8001.</div>
            : events.length === 0 ? <div className="empty"><Terminal size={19}/> No recorded events yet.</div>
            : <ul>{events.map((event, i) => <li key={event.timestamp + String(i)}><span className={event.severity === 'error' ? 'mark error' : 'mark'}/><div><b>{event.message}</b><small>{event.event_type}</small></div><time>{new Date(event.timestamp).toLocaleTimeString()}</time></li>)}</ul>}
        </section>
        <footer>FRIDAY / RESEARCH-GRADE MISSION CONTROL <a href="https://libraries.dev/" target="_blank" rel="noreferrer">UI effects by Libraries.dev <ArrowUpRight size={14}/></a></footer>
      </main>
    </div>
  )
}
