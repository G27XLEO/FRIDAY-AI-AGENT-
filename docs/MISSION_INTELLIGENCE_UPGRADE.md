# FRIDAY Mission Intelligence + Libraries.dev UI (proposed upgrade)

This branch upgrades FRIDAY from a conversation-only voice worker into an
**operator-controlled mission assistant** with an explicit planning and
verification state machine. It also adds a working, mobile-friendly React
mission-control dashboard using the **free Libraries.dev React effects**.

## Honest capability boundary

This is **not AGI or superintelligence**. Groq remains the reasoning model
and LiveKit remains the realtime voice transport. The mission controller adds
state and evidence discipline, not a new foundation model or autonomous
guarantee of correctness.

The React dashboard is a **standalone interface** that requires no Python
server, LiveKit client, AI account or API keys. Its mission workspace lives in
browser local storage. The manual preview states are animations, not evidence
that an AI or voice worker is online. The separate voice worker and MCP
services remain available in the repository for future integration.

## Design (standalone)

- `thinking-orbs`: manually selected idle, active and thinking previews.
- `metal-fx`: metallic UI button.
- `border-beam`: animated frame for the visualizer in active preview states.
- Responsive dark glass panels, local mission/task management, progress totals
  and real history of the user's own local interface actions.
- No fake uptime, fabricated AI metrics, backend requests, microphone usage
  or model invocation.
- Reduced-motion CSS, text labels and keyboard-operable controls.

Free package API reference: https://libraries.dev/

## Intelligence layer

`friday_agent/mission_control.py` implements:

1. Create up to five missions, each with up to eight ordered steps.
2. Require a goal and measurable success criteria.
3. Keep exactly one active step for progress updates.
4. Record `reported` progress separately from `verified` status.
5. Verify text evidence by reading a public workspace file.
6. Mark the whole mission verified only when **every** step was checked.
7. Block on a reported failure and allow a retry.

`friday_agent/livekit_agent.py` exposes these controls as LiveKit function
tools: `create_mission`, `mission_status`, `report_mission_step`,
`verify_document_step`, `read_project_document`, `runtime_status`.
Each voice-agent instance gets separate ephemeral mission state.

Important: a model can fabricate its own `report_mission_step` evidence,
so the reported state is **not considered proof**. Only deterministic
`verify_document_step` checks can change status to `verified`; those checks
verify a file contains specified text, not that arbitrary code is correct.
Other kinds of task verification require future, scoped verifiers and tests.

This worker does **not** offer the model shell execution, file writes,
credential access, GitHub pushing, purchases, deployment, or self-modification.
The separate MCP server still has more powerful tools: keep it on a trusted,
authenticated private network until it is independently hardened. Do not
expose its streamable HTTP endpoint publicly.

## Local web preview (no LiveKit)

From the repository root:

```bash
cd web
npm install --no-audit --no-fund
npm run test:standalone
npm run type-check
npm run build
npm run dev
```

Visit http://localhost:3000. Vite does **not** proxy `/api` or `/ws`.
No `python`, Docker, FastAPI, Groq, ElevenLabs or LiveKit process needs to
be started to view and interact with the interface.

To deploy only the UI, host the generated `web/dist` folder statically.
The independent voice backend still exists elsewhere in the repository,
but it is not attached to these preview controls. See `web/README.md`.

## Validation

- CI builds the Docker worker and dashboard, syntax-checks Python, runs
  the unit tests, verifies no frontend backend/audio connections, type-checks
  TypeScript and builds Vite.
- Mission tests cover planning limits, progress, failures, retries, and
  verified versus unverified outcomes.
- LiveKit audio, Groq calls, real ElevenLabs audio, cross-process telemetry
  and mobile WebGL performance require integration tests with real accounts.
  The GitHub Actions job does not attest to those external runtime services.

No hardware/IoT integration, no standalone Android application and no
unreviewed deployment changes are included in this branch.
