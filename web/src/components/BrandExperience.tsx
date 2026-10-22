import { useState } from 'react'
import { ArrowRight, Mic2, Users, Layers3 } from 'lucide-react'
import { ImageGeneration } from 'img-fx'
import { Liquid } from 'liquid-gooey'
import { BorderBeam } from 'border-beam'
import './BrandExperience.css'

/** Preview a bundled brand asset; this does not generate an AI image. */
export default function BrandExperience({ onTeam, onWake }: {
  onTeam: () => void
  onWake: () => void
}) {
  const [expanded, setExpanded] = useState(false)
  const mark = import.meta.env.BASE_URL + 'friday-mark.svg'
  return (
    <section className="brand-experience" aria-label="FRIDAY visual command dock">
      <BorderBeam colorVariant="ocean" size="line" strength={0.35}>
        <div className="brand-panel panel">
          <div className="brand-render" aria-label="FRIDAY emblem reveal">
            <ImageGeneration preset="pixels-mechanic" images={[mark]} autoReveal>
              <div className="brand-render-frame"><img src={mark} alt="FRIDAY OS glowing cyan emblem" /></div>
            </ImageGeneration>
          </div>
          <div className="brand-info">
            <span className="eyebrow">FRIDAY OS / VISUAL IDENTITY</span>
            <h2>One intelligence. Your entire team.</h2>
            <p>Fluid interactions, animated teammates, and an orbiting intelligence core.
              Effects are visual enhancements; AI collaboration runs only when your model is connected.</p>
            <div className="brand-tags">
              <span><Layers3 size={13} /> Libraries.dev</span>
              <span><Users size={13}/> Multi-agent UI</span>
            </div>
            <div className="brand-liquid-shell">
              <Liquid blur={6} contrast={18} fill="#0e829c" shadow="0 1px 6px rgba(5,226,247,.24)">
                <Liquid.Item x={expanded ? -67 : 0} y={expanded ? -9 : 0} transition="bouncy">
                  <button onClick={onTeam} className="brand-liquid-action" aria-label="Open AI Agent Team" tabIndex={expanded ? 0 : -1}>
                    <Users size={18} />
                  </button>
                </Liquid.Item>
                <Liquid.Item x={expanded ? 67 : 0} y={expanded ? -9 : 0} transition="bouncy">
                  <button onClick={onWake} className="brand-liquid-action" aria-label="Open voice orb" tabIndex={expanded ? 0 : -1}>
                    <Mic2 size={18} />
                  </button>
                </Liquid.Item>
                <Liquid.Item x={0} y={0} transition="bouncy">
                  <button className="brand-liquid-action brand-liquid-main"
                    aria-label={expanded ? 'Collapse quick actions' : 'Expand quick actions'}
                    aria-expanded={expanded} onClick={() => setExpanded(value => !value)}>
                    <ArrowRight size={19} />
                  </button>
                </Liquid.Item>
              </Liquid>
              <span className="brand-dock-caption">{expanded ? 'Team · Quick actions · Voice' : 'Open quick actions'}</span>
            </div>
          </div>
        </div>
      </BorderBeam>
    </section>
  )
}
