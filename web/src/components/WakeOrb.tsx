import { useEffect, useRef } from 'react'
import { BrainCircuit, Headphones, Mic, Moon, ShieldCheck, Volume2, X } from 'lucide-react'
import './WakeOrb.css'

export type WakeMode = 'standby' | 'listening' | 'thinking' | 'speaking'

type WakeOrbProps = {
  mode: WakeMode
  onModeChange: (mode: WakeMode) => void
  onClose: () => void
}

const stages: { id: WakeMode; label: string; description: string; icon: typeof Mic }[] = [
  { id: 'standby', label: 'Standby', description: 'Waiting for the next activation', icon: Moon },
  { id: 'listening', label: 'Listening', description: 'Ready for your request — visual simulation', icon: Mic },
  { id: 'thinking', label: 'Thinking', description: 'Processing animation — no model running', icon: BrainCircuit },
  { id: 'speaking', label: 'Speaking', description: 'Response animation — audio is muted', icon: Volume2 },
]

/**
 * A visual preview of a future system assistant wake experience.
 *
 * This component deliberately never requests microphone permissions, starts
 * speech recognition, makes network calls, or pretends to hear a wake word.
 * Stages are driven exclusively by deliberate operator interactions.
 */
export function WakeOrb({ mode, onModeChange, onClose }: WakeOrbProps) {
  const closeRef = useRef<HTMLButtonElement>(null)
  const details = stages.find(stage => stage.id === mode) ?? stages[0]

  useEffect(() => {
    const priorOverflow = document.body.style.overflow
    const priorFocus = document.activeElement instanceof HTMLElement
      ? document.activeElement : null
    document.body.style.overflow = 'hidden'
    closeRef.current?.focus()

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        event.preventDefault()
        onClose()
      }
      if (event.key === 'Tab') {
        const dialog = document.getElementById('friday-wake-dialog')
        const focusables = dialog?.querySelectorAll<HTMLButtonElement>('button:not([disabled])')
        if (!focusables?.length) return
        const first = focusables[0]
        const last = focusables[focusables.length - 1]
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault()
          last.focus()
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault()
          first.focus()
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = priorOverflow
      priorFocus?.focus()
    }
  }, [onClose])

  return (
    <div className={'wake-screen wake-mode-' + mode}
      id="friday-wake-dialog" role="dialog" aria-modal="true"
      aria-labelledby="friday-wake-title" aria-describedby="friday-wake-description">
      <div className="wake-ambient wake-ambient-one" aria-hidden="true" />
      <div className="wake-ambient wake-ambient-two" aria-hidden="true" />

      <header className="wake-header">
        <div className="wake-brand"><span className="wake-brand-dot" /> F R I D A Y <span> / WAKE INTERFACE</span></div>
        <button ref={closeRef} className="wake-dismiss" onClick={onClose}
          aria-label="Close FRIDAY wake preview"><X size={20} /> <span>Close</span></button>
      </header>

      <div className="wake-center">
        <div className="wake-kicker"><Headphones size={15} /> SYSTEM VOICE · DESIGN PREVIEW</div>
        <div className="wake-orb-visual" aria-hidden="true">
          <div className="wake-orb-aura"/>
          <div className="wake-orb-ripple wake-orb-ripple-one"/>
          <div className="wake-orb-ripple wake-orb-ripple-two"/>
          <div className="wake-orb-sphere">
            <div className="wake-orb-fluid wake-orb-fluid-a"/>
            <div className="wake-orb-fluid wake-orb-fluid-b"/>
            <div className="wake-orb-fluid wake-orb-fluid-c"/>
            <div className="wake-orb-shimmer"/>
          </div>
          <div className="wake-orb-sparkle"/>
        </div>

        <p className="wake-identity">FRIDAY OS</p>
        <h1 id="friday-wake-title">{mode === 'standby' ? 'Standing by.' :
          mode === 'listening' ? "I'm listening." :
            mode === 'thinking' ? 'Thinking.' : 'Speaking.'}</h1>
        <p id="friday-wake-description" className="wake-description">{details.description}</p>

        <div className="wake-levels" aria-hidden="true">
          {Array.from({ length: 21 }, (_, i) => <span key={i} style={{
            animationDelay: String(i * -0.082) + 's',
            height: String(12 + ((i * 13) % 29)) + 'px',
          }}/>)}
        </div>

        <div className="wake-stage-list" role="group" aria-label="Select simulated voice state">
          {stages.map(stage => {
            const Icon = stage.icon
            return <button key={stage.id}
              className={'wake-stage-button ' + (mode === stage.id ? 'selected' : '')}
              aria-pressed={mode === stage.id} onClick={() => onModeChange(stage.id)}>
              <Icon size={16} />
              <span>{stage.label}</span>
            </button>
          })}
        </div>
        <p className="wake-demo-note"><ShieldCheck size={15} /> Preview only · Microphone off · No AI or LiveKit connection</p>
      </div>

      <footer className="wake-footer">
        <span>ORIGINAL FRIDAY VISUAL SYSTEM</span>
        <span>ESC TO CLOSE · TOUCH ENABLED</span>
      </footer>
    </div>
  )
}
