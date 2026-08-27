# FRIDAY UI Demo

This is a **static review concept**, not a production dashboard. It documents the visual direction for a future FRIDAY web/desktop operator console.

## Design goals

- Dark mission-control workspace
- Clear realtime connection state
- Voice activity indicator
- Current mission and task status
- Tool activity timeline
- Compact system telemetry
- Responsive layout suitable for desktop and mobile clients
- No dependency on the core LiveKit worker UI

## Snapshot

![FRIDAY UI demo](assets/friday-ui-demo.svg)

## Planned UI areas

1. **Header:** FRIDAY identity, connection state, environment, and session controls.
2. **Voice panel:** listening/speaking state, waveform placeholder, and transcript.
3. **Mission panel:** active goal, progress, and next action.
4. **Tool timeline:** MCP calls and results with timestamps.
5. **System panel:** LiveKit, STT, LLM, TTS, MCP, and runtime health.
6. **Command bar:** future operator command and voice controls.

## Review status

The snapshot is intentionally a design reference. Production UI implementation should be treated as a separate client project and connected to the worker through authenticated LiveKit/MCP interfaces.
