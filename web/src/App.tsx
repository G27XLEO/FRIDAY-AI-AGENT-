import { useEffect, useMemo, useState, type FormEvent } from 'react'
import {
  Activity, ArrowRight, ArrowUpRight, Bot, Check, CheckCircle2,
  ClipboardList, Clock3, Cpu, Info, Layers3, ListChecks,
  Plus, RotateCcw, ShieldCheck, Sparkles, Trash2, Zap,
} from 'lucide-react'
import { ThinkingOrb } from 'thinking-orbs'
import { BorderBeam } from 'border-beam'
import { MetalFx, MetalText } from 'metal-fx'
import { WakeOrb, type WakeMode } from './components/WakeOrb'
import './styles.css'

type View = 'overview' | 'missions' | 'activity'
type VisualState = 'breathing' | 'working' | 'solving'
type MissionStep = { id: string; label: string; done: boolean }
type Mission = {
  id: string
  title: string
  criteria: string
  steps: MissionStep[]
  createdAt: string
}
type LocalEvent = { id: string; message: string; createdAt: string }
type Workspace = { missions: Mission[]; events: LocalEvent[] }

const STORAGE_KEY = 'friday-standalone-workspace-v1'
const DEFAULT_STEPS = 'Define the objective\nPrepare the execution plan\nReview the result'

function uniqueId() {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : String(Date.now()) + '-' + Math.random().toString(36).slice(2)
}

const previews: { state: VisualState; label: string; description: string }[] = [
  { state: 'breathing', label: 'Standby', description: 'Ambient visual state' },
  { state: 'working', label: 'Active', description: 'Active visual state' },
  { state: 'solving', label: 'Thinking', description: 'Processing visual state' },
]

function readWorkspace(): Workspace {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY)
    if (!stored) return { missions: [], events: [] }
    const value: unknown = JSON.parse(stored)
    if (!value || typeof value !== 'object') return { missions: [], events: [] }
    const data = value as Partial<Workspace>
    if (!Array.isArray(data.missions) || !Array.isArray(data.events)) {
      return { missions: [], events: [] }
    }
    const missions = data.missions.filter((m): m is Mission =>
      Boolean(m && typeof m.id === 'string' && typeof m.title === 'string' &&
        typeof m.criteria === 'string' && Array.isArray(m.steps) &&
        m.steps.every(s => s && typeof s.id === 'string' &&
          typeof s.label === 'string' && typeof s.done === 'boolean'))
    ).slice(0, 30)
    const events = data.events.filter((e): e is LocalEvent =>
      Boolean(e && typeof e.id === 'string' &&
        typeof e.message === 'string' && typeof e.createdAt === 'string')
    ).slice(0, 40)
    return { missions, events }
  } catch {
    // Browser storage may be blocked. The interface still works in memory.
    return { missions: [], events: [] }
  }
}

function shortTime(iso: string) {
  const date = new Date(iso)
  return Number.isNaN(date.valueOf()) ? 'Local' : date.toLocaleString()
}

function Stat({ title, value, detail, icon: Icon }: {
  title: string
  value: string
  detail: string
  icon: typeof Activity
}) {
  return (
    <article className="stat panel">
      <div className="stat-label"><span>{title}</span><Icon size={18} aria-hidden="true" /></div>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  )
}

export default function App() {
  const [view, setView] = useState<View>('overview')
  const [orbState, setOrbState] = useState<VisualState>('breathing')
  const [wakeOpen, setWakeOpen] = useState(false)
  const [wakeMode, setWakeMode] = useState<WakeMode>('standby')
  const [workspace, setWorkspace] = useState<Workspace>(readWorkspace)
  const [goal, setGoal] = useState('')
  const [criteria, setCriteria] = useState('')
  const [stepsText, setStepsText] = useState(DEFAULT_STEPS)
  const [help, setHelp] = useState(false)
  const [storageAvailable, setStorageAvailable] = useState(true)

  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(workspace))
      setStorageAvailable(true)
    } catch {
      setStorageAvailable(false)
    }
  }, [workspace])

  const completed = useMemo(
    () => workspace.missions.reduce((count, mission) =>
      count + mission.steps.filter(step => step.done).length, 0),
    [workspace.missions]
  )
  const totalSteps = useMemo(
    () => workspace.missions.reduce((count, mission) => count + mission.steps.length, 0),
    [workspace.missions]
  )

  function createMission(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const title = goal.trim()
    const lines = stepsText.split('\n').map(line => line.trim()).filter(Boolean)
    if (!title || !criteria.trim() || lines.length === 0) return
    const mission: Mission = {
      id: uniqueId(),
      title: title.slice(0, 160),
      criteria: criteria.trim().slice(0, 400),
      steps: lines.slice(0, 8).map(label => ({
        id: uniqueId(),
        label: label.slice(0, 160),
        done: false,
      })),
      createdAt: new Date().toISOString(),
    }
    setWorkspace(previous => ({
      missions: [mission, ...previous.missions].slice(0, 30),
      events: [{
        id: uniqueId(),
        message: 'Created local mission: ' + mission.title,
        createdAt: new Date().toISOString(),
      }, ...previous.events].slice(0, 40),
    }))
    setGoal('')
    setCriteria('')
    setStepsText(DEFAULT_STEPS)
  }

  function toggleStep(missionId: string, stepId: string) {
    const mission = workspace.missions.find(item => item.id === missionId)
    const step = mission?.steps.find(item => item.id === stepId)
    if (!mission || !step) return
    setWorkspace(previous => ({
      missions: previous.missions.map(item => item.id === missionId ? {
        ...item,
        steps: item.steps.map(entry => entry.id === stepId
          ? { ...entry, done: !entry.done } : entry),
      } : item),
      events: [{
        id: uniqueId(),
        message: (step.done ? 'Reopened: ' : 'Manually checked: ') + step.label,
        createdAt: new Date().toISOString(),
      }, ...previous.events].slice(0, 40),
    }))
  }

  function deleteMission(missionId: string) {
    const mission = workspace.missions.find(item => item.id === missionId)
    if (!mission) return
    setWorkspace(previous => ({
      missions: previous.missions.filter(item => item.id !== missionId),
      events: [{
        id: uniqueId(),
        message: 'Removed local mission: ' + mission.title,
        createdAt: new Date().toISOString(),
      }, ...previous.events].slice(0, 40),
    }))
  }

  function resetWorkspace() {
    if (!window.confirm('Delete all missions and activity stored in this browser?')) return
    setWorkspace({ missions: [], events: [] })
    setGoal('')
    setCriteria('')
    setStepsText(DEFAULT_STEPS)
    setOrbState('breathing')
    setView('overview')
  }

  function openWake() {
    setWakeMode('listening')
    setWakeOpen(true)
  }

  function closeWake() {
    setWakeOpen(false)
    setWakeMode('standby')
  }

  useEffect(() => {
    function handleShortcut(event: KeyboardEvent) {
      if (event.altKey && event.key.toLowerCase() === 'f' &&
        !event.ctrlKey && !event.metaKey && !event.repeat) {
        event.preventDefault()
        setWakeMode('listening')
        setWakeOpen(true)
      }
    }
    window.addEventListener('keydown', handleShortcut)
    return () => window.removeEventListener('keydown', handleShortcut)
  }, [])

  const nav: { id: View; title: string; icon: typeof Activity }[] = [
    { id: 'overview', title: 'Overview', icon: Activity },
    { id: 'missions', title: 'Mission planner', icon: ClipboardList },
    { id: 'activity', title: 'Activity log', icon: Clock3 },
  ]
  const orbDescription = previews.find(item => item.state === orbState)?.description || 'Visual preview'

  return (
    <div className="shell">
      <aside className="sidebar">
        <button className="brand brand-button" onClick={() => setView('overview')} aria-label="FRIDAY home">
          <span className="brand-icon"><Bot size={25} /></span> FRIDAY <em>OS</em>
        </button>
        <p className="nav-label">MISSION CONTROL</p>
        <nav aria-label="Primary navigation">
          {nav.map(item => (
            <button key={item.id} onClick={() => setView(item.id)}
              aria-current={view === item.id ? 'page' : undefined}
              className={'nav-item ' + (view === item.id ? 'selected' : '')}>
              <item.icon size={18} /> {item.title}
            </button>
          ))}
        </nav>
        <div className="side-foot">
          <div><ShieldCheck size={17} /> LOCAL / INTERFACE ONLY</div>
          <p>Nothing here connects to LiveKit, an AI model, or a backend service.</p>
          <p>{storageAvailable ? 'Your missions are saved in this browser.' : 'Browser storage unavailable: changes are temporary.'}</p>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="breadcrumb">FRIDAY <span>/</span> Mission Control <span>/</span> {view === 'overview' ? 'Overview' : view === 'missions' ? 'Missions' : 'Activity'}</div>
          <div className="top-actions">
            <button className="wake-top-launch" onClick={openWake} aria-label="Open FRIDAY wake orb demo"><Sparkles size={16} /> Wake orb</button>
            <span className="connect online"><span className="dot" /> STANDALONE PREVIEW</span>
            <button className="icon-button" onClick={() => setHelp(value => !value)}
              aria-label="About standalone mode" aria-expanded={help}><Info size={18} /></button>
          </div>
        </header>

        {help && (
          <div className="help-banner" role="status">
            This is an interactive frontend prototype. The orb states are manually selected
            visual previews, mission checkboxes are local notes, and no AI inference or
            audio processing occurs. No network requests are made by the application.
          </div>
        )}

        {view === 'overview' && (
          <>
            <div className="intro">
              <span className="eyebrow">INTERFACE SANDBOX / FRIDAY OS 2</span>
              <h1>Mission Control<span className="aqua">.</span></h1>
              <p>A command center designed for an intelligent future. Explore the interface offline.</p>
            </div>
            <section className="hero" aria-label="FRIDAY design preview">
              <BorderBeam size="md" colorVariant="ocean" strength={0.65} active={orbState !== 'breathing'}>
                <div className="core panel">
                  <div className="overline"><span className="dot" /> CORE VISUALIZER / PREVIEW ONLY</div>
                  <div className="orb-stage"><ThinkingOrb state={orbState} size={64} /></div>
                  <MetalText font="600 26px/1.2 Inter" color="#E7F8FF">FRIDAY</MetalText>
                  <h2>{orbState === 'breathing' ? 'STANDBY' : orbState === 'working' ? 'ACTIVE PREVIEW' : 'THINKING PREVIEW'}</h2>
                  <p>{orbDescription} · No microphone or AI connected</p>
                  <button className="wake-main-launch" onClick={openWake}>
                    <Sparkles size={17} /> Simulate "Hey FRIDAY" <ArrowUpRight size={16} />
                  </button>
                  <div className="wake-hint">Siri-inspired full-screen wake experience · Touch or Alt+F</div>
                  <div className="preview-switch" role="group" aria-label="Visualizer preview state">
                    {previews.map(item => <button key={item.state}
                      aria-pressed={orbState === item.state}
                      className={'preview-button ' + (orbState === item.state ? 'active' : '')}
                      onClick={() => setOrbState(item.state)}>{item.label}</button>)}
                  </div>
                  <div className="core-bottom">
                    <span>ENGINE <b>NOT CONNECTED</b></span>
                    <span>MODE <b>LOCAL INTERFACE</b></span>
                  </div>
                </div>
              </BorderBeam>
              <article className="mission panel">
                <div className="panel-title"><span><Zap size={17} /> MISSION DESIGN</span><span className="tag">OFFLINE</span></div>
                <h2>Prepare before you execute.</h2>
                <p>Shape your next task into clear steps, define what success looks like,
                  and track your progress manually. AI automation remains disconnected.</p>
                <div className="steps">
                  <div><span>01</span><section><b>DEFINE</b><small>Set a precise outcome</small></section></div>
                  <div><span>02</span><section><b>PLAN</b><small>Write actionable steps</small></section></div>
                  <div><span>03</span><section><b>REVIEW</b><small>Tick off steps yourself</small></section></div>
                </div>
                <MetalFx preset="silver" strength={0.6}>
                  <button className="metal-action" onClick={() => setView('missions')}>
                    Open mission planner <ArrowRight size={17}/>
                  </button>
                </MetalFx>
              </article>
            </section>
            <section className="stats" aria-label="Local workspace summary">
              <Stat title="LOCAL MISSIONS" value={String(workspace.missions.length)} detail="Saved in this browser" icon={Layers3}/>
              <Stat title="STEPS CHECKED" value={String(completed)} detail="Manually completed" icon={CheckCircle2}/>
              <Stat title="STEPS REMAINING" value={String(totalSteps - completed)} detail="Not yet checked" icon={ListChecks}/>
              <Stat title="AI / API CALLS" value="0" detail="No model or service attached" icon={Cpu}/>
            </section>
            <section className="activity panel">
              <header className="activity-heading">
                <div><span className="eyebrow">YOUR WORKSPACE</span><h2>Recent actions</h2></div>
                <button className="quiet-action" onClick={() => setView('activity')}>View all <ArrowUpRight size={15}/></button>
              </header>
              <ActivityFeed entries={workspace.events.slice(0, 4)} />
            </section>
          </>
        )}

        {view === 'missions' && (
          <>
            <div className="intro">
              <span className="eyebrow">WORKSPACE / MANUAL PLANNING</span>
              <h1>Mission planner<span className="aqua">.</span></h1>
              <p>Create and organize tasks locally. FRIDAY will not run or verify them.</p>
            </div>
            <section className="planner-layout">
              <form className="planner-form panel" onSubmit={createMission}>
                <div className="panel-title"><span><Plus size={17}/> NEW MISSION</span><span className="tag">LOCAL</span></div>
                <label htmlFor="goal">Objective</label>
                <input id="goal" value={goal} maxLength={160} required
                  onChange={event => setGoal(event.target.value)}
                  placeholder="e.g. Design a faster FRIDAY interface"/>
                <label htmlFor="criteria">Success criteria</label>
                <textarea id="criteria" value={criteria} maxLength={400} required rows={3}
                  onChange={event => setCriteria(event.target.value)}
                  placeholder="What must be true when this mission is complete?"/>
                <label htmlFor="steps">Steps <small>(one per line, max 8)</small></label>
                <textarea id="steps" value={stepsText} rows={6} required
                  onChange={event => setStepsText(event.target.value)}
                  placeholder="Write one task per line"/>
                <p className="form-note">These are your own notes—not AI-generated instructions.</p>
                <MetalFx preset="silver" strength={0.6}>
                  <button className="metal-action" type="submit"><Plus size={17}/> Create local mission</button>
                </MetalFx>
              </form>
              <div className="mission-list">
                <div className="list-head"><h2>My missions</h2><span>{workspace.missions.length} saved</span></div>
                {workspace.missions.length === 0 ? (
                  <div className="empty-card panel">
                    <ClipboardList size={30}/>
                    <h3>Start with a goal.</h3>
                    <p>Use the form to create your first mission and track its steps.</p>
                  </div>
                ) : workspace.missions.map(mission => {
                  const done = mission.steps.filter(step => step.done).length
                  return (
                    <article className="mission-card panel" key={mission.id}>
                      <div className="mission-card-top">
                        <div><span className="eyebrow">LOCAL MISSION</span><h3>{mission.title}</h3></div>
                        <button className="icon-button danger-button"
                          title="Remove mission" aria-label={'Remove ' + mission.title}
                          onClick={() => deleteMission(mission.id)}><Trash2 size={17}/></button>
                      </div>
                      <div className="mission-criteria"><ShieldCheck size={16}/> {mission.criteria}</div>
                      <div className="progress-top"><span>Manually checked steps</span><strong>{done} / {mission.steps.length}</strong></div>
                      <div className="progress-track"><span style={{ width: String(done / mission.steps.length * 100) + '%' }}/></div>
                      <div className="mission-tasks">
                        {mission.steps.map(step => (
                          <label key={step.id} className={'task-row ' + (step.done ? 'checked' : '')}>
                            <input type="checkbox" checked={step.done}
                              onChange={() => toggleStep(mission.id, step.id)}/>
                            <span>{step.done ? <Check size={15} /> : null}</span>
                            <span>{step.label}</span>
                          </label>
                        ))}
                      </div>
                      <small>Created {shortTime(mission.createdAt)} · Manual checkmarks are not automated verification.</small>
                    </article>
                  )
                })}
              </div>
            </section>
          </>
        )}

        {view === 'activity' && (
          <>
            <div className="intro">
              <span className="eyebrow">WORKSPACE / LOCAL HISTORY</span>
              <h1>Activity log<span className="aqua">.</span></h1>
              <p>Only actions you perform in this interface appear here.</p>
            </div>
            <section className="activity panel">
              <header className="activity-heading">
                <div><span className="eyebrow">BROWSER HISTORY</span><h2>Recent local changes</h2></div>
                <button className="quiet-action" disabled={!workspace.events.length}
                  onClick={() => setWorkspace(previous => ({ ...previous, events: [] }))}>Clear log <Trash2 size={15}/></button>
              </header>
              <ActivityFeed entries={workspace.events}/>
            </section>
            <div className="reset-row">
              <span><Info size={16}/> All data stays in this browser. There is no backend sync.</span>
              <button className="reset-button" onClick={resetWorkspace}><RotateCcw size={16}/> Reset workspace</button>
            </div>
          </>
        )}

        <footer>
          <span>FRIDAY / STANDALONE INTERFACE · NO LIVEKIT / NO AI CONNECTION</span>
          <a href="https://libraries.dev/" target="_blank" rel="noreferrer">
            Visual effects by Libraries.dev <ArrowUpRight size={14}/>
          </a>
        </footer>
      </main>
      {wakeOpen && <WakeOrb mode={wakeMode} onModeChange={setWakeMode} onClose={closeWake} />}
    </div>
  )
}

function ActivityFeed({ entries }: { entries: LocalEvent[] }) {
  if (!entries.length) {
    return <div className="empty"><Sparkles size={19}/> No actions yet. Create a mission to begin.</div>
  }
  return (
    <ul className="event-list">
      {entries.map(event => (
        <li key={event.id}>
          <span className="mark" aria-hidden="true"/>
          <div><b>{event.message}</b><small>Local interaction</small></div>
          <time>{shortTime(event.createdAt)}</time>
        </li>
      ))}
    </ul>
  )
}
