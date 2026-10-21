# FRIDAY OS — Standalone Interface

This React + Vite app is an **independent, interactive UI preview**.
You do not need LiveKit, Python, Groq, ElevenLabs, an MCP server, API
credentials, a microphone, or any backend process to use it.

## Start

From the repository root:

```bash
cd web
npm install --no-audit --no-fund
npm run test:standalone
npm run type-check
npm run dev
```

Then open **http://localhost:3000**. The development server defaults to
port 3000 and does not proxy requests to a backend.

For a static build:

```bash
npm run build
npm run preview
```

The generated `web/dist` directory can be deployed on a static web host.

## What works without AI

- Manual preview buttons change the Thinking Orbs animation between
  standby, active and thinking. These are **visual demos**, not voice states.
- **JARVIS-inspired FRIDAY ARC HUD:** press "Wake orb" in the header or
  "Simulate Hey FRIDAY" on the overview to open an immersive, animated
  cyan holographic reactor command HUD. Touch the Standby, Listening, Thinking and
  Speaking controls to preview the visual states. Press Escape or Close
  to dismiss. **Alt+F** opens the preview from the keyboard.
- Wake is **button/shortcut simulated only**: it does not detect "Hey FRIDAY",
  record sound or run Android system-wide background services.
- Create missions by entering a goal, success criteria and up to 8 tasks.
- Manually check tasks, view local completion counts and activity history.
- Delete individual missions or reset all browser data with confirmation.
- Local storage restores the workspace in the same browser when available.
- Mobile layouts, keyboard-friendly modal controls and reduced-motion CSS are included.
- Metal FX and Border Beam from https://libraries.dev/ are bundled as
  npm packages during the build.

## Scope and privacy

No API polling, `/api` proxy, WebSocket, LiveKit media connection,
microphone access, speech processing or model calls are made from this UI.
No activity is sent to a server by its application code.

Workspace data is stored in the browser's `localStorage`, so clearing
browser data or using another browser removes the history. Browser extensions,
hosting platforms and third-party link clicks have separate privacy rules.

This prototype **does not perform any AI tasks** and manual checkmarks
are not independent verification of real-world work.

Run `npm run test:standalone` to check the source for common accidental
backend/audio connections.

## ARC interface v3

The new React preview combines Libraries.dev **Thinking Orbs** for visual
states, **Border Beam** for an active telemetry panel, and **Metal FX** for
metallic interface accents. It also updates the overview reactor design.

Everything remains a **standalone local-only UI preview**. It has no
microphone, no model calls, no telemetry connection, and does not control
the separate Android companion. Hindi and Marathi NLP reside in the
Android command router and the separately deployed LiveKit worker.
