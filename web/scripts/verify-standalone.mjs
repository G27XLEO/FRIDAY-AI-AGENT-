import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const app = readFileSync(new URL('../src/App.tsx', import.meta.url), 'utf8')
const vite = readFileSync(new URL('../vite.config.ts', import.meta.url), 'utf8')
const wake = readFileSync(new URL('../src/components/WakeOrb.tsx', import.meta.url), 'utf8')

const forbidden = [
  [/\bfetch\s*\(/, 'HTTP fetch'],
  [/\bnew\s+WebSocket\s*\(/, 'WebSocket connection'],
  [/\bEventSource\s*\(/, 'SSE connection'],
  [/\bnavigator\.mediaDevices\b/, 'microphone or camera'],
  [/from\s*['"][^'"]*livekit/i, 'LiveKit import'],
  [/from\s*['"]axios['"]/, 'HTTP client'],
  [/['"]\/api\//, 'API endpoint'],
  [/['"]\/ws\//, 'WebSocket endpoint'],
]

for (const [pattern, label] of forbidden) {
  assert.doesNotMatch(app, pattern, 'Standalone UI must not use ' + label)
  assert.doesNotMatch(wake, pattern, 'Wake orb must not use ' + label)
}
assert.doesNotMatch(vite, /proxy\s*:/, 'Standalone Vite must not proxy to a backend')
assert.match(app, /<ThinkingOrb /, 'Thinking Orbs visualizer must exist')
assert.match(app, /<BorderBeam /, 'Border Beam effect must exist')
assert.match(app, /<MetalFx /, 'Metal FX controls must exist')
assert.match(app, /localStorage/, 'Local workspace must be saved without a server')
assert.match(app, /createMission/, 'Manual local mission creation must exist')
assert.match(app, /toggleStep/, 'Manual step tracking must exist')
assert.match(app, /<WakeOrb /, 'Wake orb must be wired into dashboard')
assert.match(wake, /id: 'listening'/, 'Wake orb must have a listening preview')
assert.match(wake, /id: 'thinking'/, 'Wake orb must have a thinking preview')
assert.match(wake, /id: 'speaking'/, 'Wake orb must have a speaking preview')
assert.match(wake, /Escape/, 'Wake overlay must support keyboard dismiss')
assert.match(wake, /Microphone off/, 'Wake overlay must disclose demo-only operation')

process.stdout.write('Standalone UI contract verified: no AI, voice, or backend connection.\\n')
