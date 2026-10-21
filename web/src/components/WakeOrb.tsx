import { useEffect, useRef } from 'react'
import { Activity, BrainCircuit, Cpu, Mic, Radio, ShieldCheck, Volume2, X } from 'lucide-react'
import { ThinkingOrb } from 'thinking-orbs'
import { BorderBeam } from 'border-beam'
import { MetalFx } from 'metal-fx'
import './WakeOrb.css'

export type WakeMode = 'standby' | 'listening' | 'thinking' | 'speaking'

type WakeOrbProps = {
  mode: WakeMode
  onModeChange: (mode: WakeMode) => void
  onClose: () => void
}

const modes: { mode: WakeMode; title: string; icon: typeof Mic; orb: 'breathing' | 'listening' | 'solving' | 'working' }[] = [
  { mode: 'standby', title: 'Standby', icon: Radio, orb: 'breathing' },
  { mode: 'listening', title: 'Listening', icon: Mic, orb: 'listening' },
  { mode: 'thinking', title: 'Thinking', icon: BrainCircuit, orb: 'solving' },
  { mode: 'speaking', title: 'Speaking', icon: Volume2, orb: 'working' },
]

/** A manual, offline JARVIS-inspired visual simulation, never a live microphone. */
export function WakeOrb({ mode, onModeChange, onClose }: WakeOrbProps) {
  const closeRef = useRef<HTMLButtonElement>(null)
  const active = modes.find(item => item.mode === mode) ?? modes[0]

  useEffect(() => {
    const priorOverflow = document.body.style.overflow
    const priorFocus = document.activeElement instanceof HTMLElement
      ? document.activeElement : null
    document.body.style.overflow = 'hidden'
    closeRef.current?.focus()

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        event.preventDefault()
        onClose()
      }
      if (event.key === 'Tab') {
        const dialog = document.getElementById('friday-wake-dialog')
        const controls = dialog?.querySelectorAll<HTMLButtonElement>('button:not([disabled])')
        if (!controls?.length) return
        if (event.shiftKey && document.activeElement === controls[0]) {
          event.preventDefault()
          controls[controls.length - 1].focus()
        } else if (!event.shiftKey && document.activeElement === controls[controls.length - 1]) {
          event.preventDefault()
          controls[0].focus()
        }
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = priorOverflow
      priorFocus?.focus()
    }
  }, [onClose])

  return (
    <div id="friday-wake-dialog" className={'wake-screen wake-mode-' + mode}
      role="dialog" aria-modal="true" aria-labelledby="friday-wake-title"
      aria-describedby="friday-wake-description">
      <header className="wake-header">
        <div className="wake-logo"><span className="wake-logo-mark">◈</span>
          <span>F R I D A Y <small> / A.R.C. INTERFACE</small></span>
        </div>
        <div className="wake-header-end">
          <span className="wake-system-pill"><span className="wake-status-dot" /> LOCAL VISUAL DEMO</span>
          <button ref={closeRef} className="wake-dismiss" onClick={onClose}
            aria-label="Close JARVIS preview"><X size={18} /> <span>Exit HUD</span></button>
        </div>
      </header>

      <div className="wake-hud-main">
        <div className="wake-hud-side wake-side-left" aria-hidden="true">
          <div className="wake-panel-number">01 / CORE DATA</div>
          <div className="wake-data-line"><Cpu size={16} /> REACTOR <strong>SIMULATED</strong></div>
          <div className="wake-data-line"><Activity size={16} /> TELEMETRY <strong>DISPLAY</strong></div>
          <div className="wake-data-line"><ShieldCheck size={16} /> PRIVACY <strong>MIC OFF</strong></div>
          <div className="wake-hud-bars">{Array.from({ length: 18 }, (_, i) =>
            <span key={i} style={{ height: 12 + ((i * 13) % 35) + 'px' }} />)}</div>
          <p>Original JARVIS-inspired command display. System signals are design indicators, not live diagnostic readings.</p>
        </div>

        <div className="wake-core-column">
          <div className="wake-kicker">◌ &nbsp; A R C &nbsp; / &nbsp; V O I C E &nbsp; C O R E &nbsp; ◌</div>
          <div className="wake-reactor" aria-label="Animated holographic reactor core">
            <div className="wake-reactor-aura" />
            <div className="wake-reactor-dial" />
            <div className="wake-reactor-ticks" />
            <div className="wake-reactor-ring wake-ring-a" />
            <div className="wake-reactor-ring wake-ring-b" />
            <div className="wake-reactor-ring wake-ring-c" />
            <div className="wake-reactor-inner">
              <span className="wake-core-letter">F</span>
            </div>
            <span className="wake-reactor-cross wake-cross-top" />
            <span className="wake-reactor-cross wake-cross-bottom" />
            <span className="wake-reactor-cross wake-cross-left" />
            <span className="wake-reactor-cross wake-cross-right" />
          </div>

          <span className="wake-mode-overline">FRIDAY / LOCAL SYSTEM INTERFACE</span>
          <h1 id="friday-wake-title">{mode === 'standby' ? 'SYSTEM STANDBY'
            : mode === 'listening' ? 'LISTENING PREVIEW'
            : mode === 'thinking' ? 'PROCESSING PREVIEW' : 'SPEAKING PREVIEW'}</h1>
          <p id="friday-wake-description">
            Manual visual state · No microphone, live agent or cloud model connected
          </p>

          <div className="wake-mini-orb"><ThinkingOrb state={active.orb} size={64} />
            <span>VISUAL STATE / {mode.toUpperCase()}</span></div>

          <div className="wake-stage-list" role="group" aria-label="Choose visual simulator state">
            {modes.map(item => {
              const Icon = item.icon
              return <button key={item.mode}
                className={'wake-stage-button ' + (mode === item.mode ? 'selected' : '')}
                aria-pressed={mode === item.mode} onClick={() => onModeChange(item.mode)}>
                <Icon size={15} /> {item.title}
              </button>
            })}
          </div>
        </div>

        <div className="wake-hud-side wake-side-right" aria-hidden="true">
          <div className="wake-panel-number">02 / STATUS</div>
          <BorderBeam size="md" colorVariant="ocean" strength={0.65} active={mode !== 'standby'}>
            <div className="wake-side-status">
              <span>SIMULATION MODE</span>
              <strong>{mode.toUpperCase()}</strong>
              <span>INPUT PIPELINE</span>
              <strong>DISCONNECTED</strong>
              <span>MODEL LINK</span>
              <strong>NOT CONFIGURED</strong>
            </div>
          </BorderBeam>
          <p>Animation only. Install the Android companion for foreground device commands.</p>
        </div>
      </div>

      <footer className="wake-footer">
        <span>JARVIS-INSPIRED HUD / ORIGINAL FRIDAY DESIGN</span>
        <div className="wake-footer-center"><MetalFx preset="silver" strength={0.45}>
          <span className="wake-metal-chip">FRIDAY · ARC ONLINE AS PREVIEW</span>
        </MetalFx></div>
        <span>ESC TO CLOSE · NO LIVE AUDIO</span>
      </footer>
    </div>
  )
}
