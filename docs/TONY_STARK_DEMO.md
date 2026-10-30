# Tony Stark FRIDAY Demo — upstream submodule

This repository includes [SAGAR-TAMANG/friday-tony-stark-demo](https://github.com/SAGAR-TAMANG/friday-tony-stark-demo) as a **Git submodule**, pinned to upstream commit `4d85750ae4c60c88850a6c69107e91bf02300673` (as inspected on 2026-10-30).

The upstream demo is kept at `integrations/friday-tony-stark-demo/`. It is **not** merged into the root Python package, web UI, Android app, or default CI runtime. No existing FRIDAY entry points or dependencies are replaced.

## Check out the complete upstream code

Clone everything:

```sh
git clone --recurse-submodules https://github.com/G27XLEO/FRIDAY-AI-AGENT-.git
cd FRIDAY-AI-AGENT-
```

Or, within an existing checkout:

```sh
git submodule update --init --recursive
```

The submodule checkout contains the upstream `uv.lock` and all other tracked files. A plain `git clone` without `--recurse-submodules` does **not** download the submodule contents.

## Run the demo independently (optional)

In `integrations/friday-tony-stark-demo/`, follow the upstream README: install Python 3.11+ and `uv`, run `uv sync`, copy `.env.example` to `.env`, add credentials, then start its MCP server with `uv run friday` and its voice agent with `uv run friday_voice` in separate terminals. Never commit `.env` or service API keys.

### Compatibility and integration notes

- The original FRIDAY AI AGENT favors **Groq** (LLM/STT) and **ElevenLabs** (TTS). The upstream demo defaults to **Gemini**, **Sarvam**, and **OpenAI TTS**; it is **not** automatically reconfigured to your providers.
- The demo uses its own FastMCP SSE server and may listen on port 8000. Avoid running it on the same port as the existing FRIDAY server.
- The demo is a separate Python project and is not a native Android application. Running its voice worker on Android/Termux may require a compatible Linux environment.
- Review upstream source, license claims, dependencies, and required secrets before deployment. No live service credentials are included by this import.
- Updating the submodule to a new upstream commit is an explicit future change and should be independently reviewed.

Source: https://github.com/SAGAR-TAMANG/friday-tony-stark-demo
