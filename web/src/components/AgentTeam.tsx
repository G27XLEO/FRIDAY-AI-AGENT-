import { useEffect, useState, type FormEvent } from 'react'
import {
  Bot, BrainCircuit, Check, ChevronRight, PlusCircle, KeyRound,
  Loader2, LockKeyhole, MessageSquare, Send, ShieldCheck, Users, X,
} from 'lucide-react'
import { BotAvatar } from 'bot-avatars'
import { VoiceBeam } from 'voice-glow'
import './AgentTeam.css'

type Agent = {
  id: string
  name: string
  specialty: string
  instructions: string
}
type Thread = { id: string; title: string; created_at: string }
type Message = {
  id: string
  speaker: 'user' | 'agent' | 'coordinator'
  agent_id: string | null
  content: string
  created_at: string
}
type Conversation = { thread: Thread; messages: Message[] }
type TeamResponse = Conversation & { agents_used: string[]; warnings: string[] }
type Health = { ready: boolean; provider: string; model: string }

const TOKEN_KEY = 'friday-team-token'
const HOST_KEY = 'friday-team-api-host'
const avatarTypes = ['mech','hexagon','droid','star','cloud','cat','alien','clover','ghost','square','circle','flower'] as const

function readHost() {
  try { return window.localStorage.getItem(HOST_KEY) || '' }
  catch { return '' }
}

function readToken() {
  try { return window.sessionStorage.getItem(TOKEN_KEY) || '' }
  catch { return '' }
}

export default function AgentTeam() {
  const [token, setToken] = useState(readToken)
  const [enteredToken, setEnteredToken] = useState('')
  const [apiHost, setApiHost] = useState(readHost)
  const [hostInput, setHostInput] = useState(readHost)
  const [agents, setAgents] = useState<Agent[]>([])
  const [threads, setThreads] = useState<Thread[]>([])
  const [activeId, setActiveId] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [health, setHealth] = useState<Health | null>(null)
  const [selected, setSelected] = useState<string[]>([])
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [showCreator, setShowCreator] = useState(false)
  const [newName, setNewName] = useState('')
  const [newSpecialty, setNewSpecialty] = useState('')
  const [newInstructions, setNewInstructions] = useState('')
  const [connected, setConnected] = useState(false)

  async function request<T>(path: string, method = 'GET', body?: object,
                            credential = token): Promise<T> {
    const response = await fetch((apiHost || '') + '/api/team' + path, {
      method,
      headers: {
        Authorization: 'Bearer ' + credential,
        ...(body ? { 'Content-Type': 'application/json' } : {}),
      },
      ...(body ? { body: JSON.stringify(body) } : {}),
    })
    const data: unknown = await response.json()
    if (!response.ok) {
      const reason = (typeof data === 'object' && data !== null && 'detail' in data)
        ? String((data as { detail: unknown }).detail) : 'Request failed'
      throw new Error(reason)
    }
    return data as T
  }

  useEffect(() => {
    fetch((apiHost || '') + '/api/team/health')
      .then(response => response.ok ? response.json() as Promise<Health> : null)
      .then(data => setHealth(data))
      .catch(() => setHealth(null))
  }, [apiHost])

  useEffect(() => {
    if (!token) { setConnected(false); return }
    let cancelled = false
    async function load() {
      try {
        const [roster, conversations] = await Promise.all([
          request<Agent[]>('/agents'),
          request<Thread[]>('/threads'),
        ])
        if (cancelled) return
        setAgents(roster)
        setThreads(conversations)
        setConnected(true)
        setError('')
        if (conversations.length) {
          const result = await request<Conversation>('/threads/' + conversations[0].id)
          if (!cancelled) {
            setActiveId(result.thread.id)
            setMessages(result.messages)
          }
        } else {
          setActiveId('')
          setMessages([])
        }
      } catch (exc) {
        if (!cancelled) { setConnected(false); setError(String(exc)) }
      }
    }
    void load()
    return () => { cancelled = true }
    // The token is the only input needed to start a new authenticated session.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, apiHost])

  function connect(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const value = enteredToken.trim()
    if (!value) return
    const origin = hostInput.trim().replace(/\/+$/, '')
    if (origin && !/^https:\/\/[a-z0-9][^\s]*$/i.test(origin)) {
      setError('Use a trusted HTTPS server origin, such as https://friday.example.com')
      return
    }
    if (location.hostname === 'appassets.androidplatform.net' && !origin) {
      setError('Enter the HTTPS address of your FRIDAY backend to use Agent Team in the APK.')
      return
    }
    if (origin) {
      try {
        const url = new URL(origin)
        if (url.pathname !== '/' || url.username || url.password || url.search || url.hash) throw new Error('invalid')
      } catch {
        setError('Enter only the trusted HTTPS server origin, without a path or credentials.')
        return
      }
    }
    try { window.localStorage.setItem(HOST_KEY, origin) } catch { /* private mode */ }
    try { window.sessionStorage.setItem(TOKEN_KEY, value) } catch { /* private mode */ }
    setApiHost(origin)
    setToken(value)
    setEnteredToken('')
  }

  function disconnect() {
    try { window.sessionStorage.removeItem(TOKEN_KEY) } catch { /* private mode */ }
    setToken('')
    setAgents([])
    setThreads([])
    setActiveId('')
    setMessages([])
    setSelected([])
    setConnected(false)
    setError('')
  }

  async function changeThread(id: string) {
    if (busy) return
    setError('')
    try {
      const data = await request<Conversation>('/threads/' + id)
      setActiveId(data.thread.id)
      setMessages(data.messages)
    } catch (exc) { setError(String(exc)) }
  }

  async function newThread(title = 'New collaboration') {
    const thread = await request<Thread>('/threads', 'POST', { title })
    setThreads(previous => [thread, ...previous])
    setActiveId(thread.id)
    setMessages([])
    return thread
  }

  async function addAgent(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (busy) return
    setBusy(true)
    setError('')
    try {
      const agent = await request<Agent>('/agents', 'POST', {
        name: newName.trim(), specialty: newSpecialty.trim(),
        instructions: newInstructions.trim(),
      })
      setAgents(previous => [...previous, agent])
      setNewName('')
      setNewSpecialty('')
      setNewInstructions('')
      setShowCreator(false)
    } catch (exc) { setError(String(exc)) }
    finally { setBusy(false) }
  }

  function selectAgent(id: string) {
    setSelected(previous => previous.includes(id)
      ? previous.filter(value => value !== id)
      : previous.length >= 3 ? previous : [...previous, id])
  }

  async function send(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const text = draft.trim()
    if (!text || busy || !connected) return
    setBusy(true)
    setError('')
    setDraft('')
    try {
      let id = activeId
      if (!id) {
        const thread = await newThread(text.slice(0, 72))
        id = thread.id
      }
      // Optimistic user bubble; replace it with server-confirmed messages.
      setMessages(previous => [...previous, {
        id: 'pending', speaker: 'user', agent_id: null,
        content: text, created_at: new Date().toISOString(),
      }])
      const response = await request<TeamResponse>(
        '/threads/' + id + '/messages',
        'POST',
        { content: text, agent_ids: selected },
      )
      setMessages(response.messages)
      if (response.warnings.length) {
        setError('Some specialists were unavailable: ' + response.warnings.join('; '))
      }
    } catch (exc) {
      setError(String(exc))
      setDraft(text)
      if (activeId) {
        try {
          const response = await request<Conversation>('/threads/' + activeId)
          setMessages(response.messages)
        } catch { /* keep the server error */ }
      }
    } finally { setBusy(false) }
  }

  const agentAvatar = (id: string) => avatarTypes[Math.max(0, agents.findIndex(agent => agent.id === id)) % avatarTypes.length]

  const agentName = (id: string | null) =>
    agents.find(agent => agent.id === id)?.name || 'Specialist'

  return (
    <div className="team-workspace">
      <div className="team-heading">
        <div>
          <span className="eyebrow">MULTI-AGENT WORKSPACE / LOCAL OLLAMA</span>
          <h1>Agent Team<span className="aqua">.</span></h1>
          <p>Delegate a goal. Specialists collaborate; FRIDAY synthesizes the result.</p>
        </div>
        <div className="team-heading-status">
          <span className={connected ? 'team-ready' : 'team-offline'}>
            {connected ? <Check size={15} /> : <LockKeyhole size={15} />}
            {connected ? 'PRIVATE SESSION' : 'NOT CONNECTED'}
          </span>
          <small>{health?.model || 'Local model'} · No LiveKit needed</small>
        </div>
      </div>

      {!connected ? (
        <section className="team-connect panel">
          <div className="team-connect-icon"><KeyRound size={26} /></div>
          <h2>Connect to your own agent team</h2>
          <p>Run FRIDAY FastAPI and Ollama on your computer. Enter the private
            FRIDAY_TEAM_API_TOKEN configured on the backend. The Android app needs a trusted HTTPS backend address.</p>
          <form onSubmit={connect}>
            <input type="url" aria-label="FRIDAY backend HTTPS origin" placeholder="Backend HTTPS origin (optional in web development)"
              value={hostInput} onChange={event => setHostInput(event.target.value)} />
            <input type="password" aria-label="Agent Team API token" required
              value={enteredToken} onChange={event => setEnteredToken(event.target.value)}
              placeholder="Private Agent Team token" autoComplete="off" />
            <button type="submit">Connect <ChevronRight size={16} /></button>
          </form>
          <small>{health?.ready === false
            ? 'Backend detected, but FRIDAY_TEAM_API_TOKEN is not configured.'
            : 'No paid model API key needed. Local Ollama must be running.'}</small>
          {error && <p className="team-error" role="alert">{error}</p>}
          <a href="https://github.com/G27XLEO/FRIDAY-AI-AGENT-/blob/feature/friday-agent-team/docs/AGENT_TEAM.md"
            target="_blank" rel="noreferrer">Local setup instructions</a>
        </section>
      ) : (
        <div className="team-layout">
          <aside className="team-side">
            <div className="team-panel panel">
              <div className="team-section-title"><Users size={17} /><b>Specialist roster</b>
                <span>{agents.length}</span></div>
              <p className="team-caption">Select up to 3 or leave all unselected for auto-routing.</p>
              <button className={'team-auto ' + (!selected.length ? 'active' : '')}
                onClick={() => setSelected([])}>
                <BrainCircuit size={18} /> FRIDAY auto-route
                {!selected.length && <Check size={15} />}
              </button>
              <div className="team-agents">
                {agents.map(agent => (
                  <button className={'team-agent ' + (selected.includes(agent.id) ? 'active' : '')}
                    onClick={() => selectAgent(agent.id)} aria-pressed={selected.includes(agent.id)}
                    key={agent.id} title={agent.instructions}>
                    <span className="team-avatar team-character"><BotAvatar type={agentAvatar(agent.id)} size={32}
                      state={busy && (selected.length === 0 || selected.includes(agent.id)) ? 'working' : 'default'}
                      shading="plastic" theme="dark" /></span>
                    <span><b>{agent.name}</b><small>{agent.specialty}</small></span>
                    {selected.includes(agent.id) && <Check size={15} />}
                  </button>
                ))}
              </div>
              {showCreator ? (
                <form className="team-create-agent" onSubmit={addAgent}>
                  <input required minLength={2} maxLength={50} aria-label="New agent name"
                    placeholder="Name" value={newName}
                    onChange={event => setNewName(event.target.value)} />
                  <input required minLength={3} maxLength={100} aria-label="New agent specialty"
                    placeholder="Specialty" value={newSpecialty}
                    onChange={event => setNewSpecialty(event.target.value)} />
                  <textarea required minLength={10} maxLength={1500}
                    aria-label="New agent instructions" placeholder="What should this agent do?"
                    value={newInstructions} onChange={event => setNewInstructions(event.target.value)} />
                  <div className="team-actions">
                    <button type="button" onClick={() => setShowCreator(false)}>Cancel</button>
                    <button type="submit" disabled={busy}>Save agent</button>
                  </div>
                </form>
              ) : (
                <button className="team-add" disabled={agents.length >= 12}
                  onClick={() => setShowCreator(true)}><PlusCircle size={16} />
                  Add specialist</button>
              )}
            </div>
            <div className="team-panel panel">
              <div className="team-section-title"><MessageSquare size={17}/><b>Conversations</b></div>
              <button className="team-new-thread" disabled={busy}
                onClick={() => { void newThread().catch(exc => setError(String(exc))) }}>
                <PlusCircle size={16}/> New conversation
              </button>
              <div className="team-threads">
                {threads.map(thread => (
                  <button key={thread.id}
                    className={'team-thread ' + (activeId === thread.id ? 'active' : '')}
                    onClick={() => { void changeThread(thread.id) }}>
                    <MessageSquare size={15}/><span>{thread.title}</span>
                  </button>
                ))}
              </div>
            </div>
            <button className="team-disconnect" onClick={disconnect}><X size={15}/> Disconnect session</button>
          </aside>

          <section className="team-chat panel" aria-label="Agent Team collaboration">
            <header className="team-chat-head">
              <div><span className="team-avatar lead"><BrainCircuit size={21}/></span>
                <div><b>FRIDAY · Team Coordinator</b>
                  <small>{selected.length
                    ? selected.map(agentName).join(', ')
                    : 'Automatic specialist delegation'}</small></div>
              </div>
              <span className="team-safe"><ShieldCheck size={14}/> Advisory only</span>
            </header>
            <div className="team-message-scroll" aria-live="polite">
              {!messages.length && (
                <div className="team-empty">
                  <BrainCircuit size={42}/>
                  <h2>One request. A whole team.</h2>
                  <p>Ask FRIDAY to plan a product, review code, compare options,
                    or design a workflow. Your specialists will collaborate.</p>
                  <div>Example: “Plan a secure, fast multilingual voice assistant.”</div>
                </div>
              )}
              {messages.map(message => (
                <article key={message.id}
                  className={'team-message team-' + message.speaker}>
                  <div className="team-message-by">
                    {message.speaker === 'user' ? 'YOU'
                      : message.speaker === 'coordinator' ? 'FRIDAY · COORDINATOR'
                      : agentName(message.agent_id).toUpperCase()}
                  </div>
                  <div className="team-message-content">{message.content}</div>
                </article>
              ))}
              {busy && (
                <div className="team-thinking"><Loader2 size={18}/>
                  Specialists are collaborating through your local model…</div>
              )}
            </div>
            {error && <p className="team-error" role="alert">{error}</p>}
            <form onSubmit={send} className="team-composer">
              <VoiceBeam level={0} processing={busy} colorVariant="ocean" strength={0.65} theme="dark">
              <textarea value={draft} rows={3} maxLength={4000}
                onChange={event => setDraft(event.target.value)}
                onKeyDown={event => {
                  if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
                    event.preventDefault()
                    event.currentTarget.form?.requestSubmit()
                  }
                }}
                placeholder="Assign a task to your AI team…" aria-label="Team task" />
              </VoiceBeam>
              <div>
                <small><LockKeyhole size={13}/> Local backend · Ctrl+Enter to send</small>
                <button type="submit" disabled={busy || !draft.trim()}>
                  {busy ? <Loader2 size={17}/> : <Send size={17}/>}
                  {busy ? 'Working' : 'Delegate'}
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
      <p className="team-disclaimer">Responses are AI-generated proposals. Agents do not
        access accounts, browse websites, run commands, or execute background tasks.</p>
    </div>
  )
}
