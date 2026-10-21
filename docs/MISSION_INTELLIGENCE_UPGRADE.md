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

The dashboard is read-only. It polls \`/api/metrics\`, reads \`/api/events\`,
and listens to \`/ws/metrics\`. These endpoints report the **FastAPI server
process**, not the microphone/LiveKit worker on a separate process. A green
dashboard connection therefore does not prove the voice worker is online.

## Design

- \`thinking-orbs\`: orb uses real API-reported \`state\` (idle/breathing,
  processing/solving, active/working, no API/connecting).
- \`metal-fx\`: metallic information control.
- \`border-beam\`: active telemetry panel boundary.
- Responsive glass panels, real runtime counters and recent event stream.
- Reduced-motion CSS and accessible text labels. UI decorative effects do not
  replace important status text.

Free package API reference: https://libraries.dev/

## Intelligence layer

\`friday_agent/mission_control.py\` implements:

1. Create up to five missions, each with up to eight ordered steps.
2. Require a goal and measurable success criteria.
3. Keep exactly one active step for progress updates.
4. Record \`reported\` progress separately from \`verified\` status.
5. Verify text evidence by reading a public workspace file.
6. Mark the whole mission verified only when **every** step was checked.
7. Block on a reported failure and allow a retry.

\`friday_agent/livekit_agent.py\` exposes these controls as LiveKit function
tools: \`create_mission\`, \`mission_status\`, \`report_mission_step\`,
\`verify_document_step\`, \`read_project_document\`, \`runtime_status\`.
Each voice-agent instance gets separate ephemeral mission state.

Important: a model can fabricate its own \`report_mission_step\` evidence,
so the reported state is **not considered proof**. Only deterministic
\`verify_document_step\` checks can change status to \`verified\`; those checks
verify a file contains specified text, not that arbitrary code is correct.
Other kinds of task verification require future, scoped verifiers and tests.

This worker does **not** offer the model shell execution, file writes,
credential access, GitHub pushing, purchases, deployment, or self-modification.
The separate MCP server still has more powerful tools: keep it on a trusted,
authenticated private network until it is independently hardened. Do not
expose its streamable HTTP endpoint publicly.

## Local web preview

From the repository root:

\`\`\`bash
cd web
npm install --no-audit --no-fund
npm run type-check
npm run build
npm run dev
\`\`\`

Visit http://localhost:3000. During development Vite proxies \`/api\` and
\`/ws\` to the FastAPI backend on port 8001.

To launch the Python API after provisioning Python requirements:

\`\`\`bash
python -m friday_agent.web_server
\`\`\`

To build a production container (includes the compiled dashboard):

\`\`\`bash
docker build -t friday-os .
docker run --rm -p 8001:8001 --env-file .env friday-os \
  python -m friday_agent.web_server
\`\`\`

Keep \`FRIDAY_CORS_ORIGINS\` empty for same-origin operation. For a trusted
separate frontend, set it to an exact comma-separated list of origins.
Use a TLS-terminating, authenticated reverse proxy before exposing the
dashboard outside your trusted development network.

## Validation

- CI builds the Docker worker and dashboard, syntax-checks Python, runs
  the unit tests, type-checks TypeScript and builds Vite.
- Mission tests cover planning limits, progress, failures, retries, and
  verified versus unverified outcomes.
- LiveKit audio, Groq calls, real ElevenLabs audio, cross-process telemetry
  and mobile WebGL performance require integration tests with real accounts.
  The GitHub Actions job does not attest to those external runtime services.

No hardware/IoT integration, no standalone Android application and no
unreviewed deployment changes are included in this branch.
