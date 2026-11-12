# LiveKit + Groq + ElevenLabs

FRIDAY uses LiveKit for realtime audio, Groq Whisper for speech recognition,
Groq's LLM for reasoning, and ElevenLabs for speech. Silero VAD and LiveKit's
local `v1-mini` turn detector handle turn boundaries without a separate inference
gateway key. This setup targets Python 3.12 and LiveKit Agents 1.8.11.

## Install

On Linux, macOS or WSL2, run from the repository:

```bash
bash scripts/setup_voice.sh
```

This creates `.venv`, installs dependencies and model assets, and copies
`.env.example` to `.env` only if `.env` does not already exist. The final check
exits with status 1 until credentials are configured; dependency installation
has still completed. Existing `.env` values are preserved.

For Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m livekit.agents download-files
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

## Configure the services

1. Create or select a project in [LiveKit Cloud](https://cloud.livekit.io/).
   In project settings, obtain its WebSocket URL, API key and API secret. Set
   `LIVEKIT_URL`, `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` from the same project.
2. Create a key in [Groq Console](https://console.groq.com/keys) and set
   `GROQ_API_KEY`. Defaults are `whisper-large-v3-turbo` for transcription and
   `llama-3.3-70b-versatile` for reasoning. Change `GROQ_STT_MODEL` or
   `GROQ_LLM_MODEL` if your account requires different supported models.
3. Create an [ElevenLabs API key](https://elevenlabs.io/app/settings/api-keys)
   with access to text-to-speech and set `ELEVENLABS_API_KEY`. FRIDAY passes this
   key explicitly to the LiveKit plugin; you do not need `ELEVEN_API_KEY`.
   Leave `ELEVENLABS_VOICE_ID` blank for the plugin default, or select a voice
   your account can use. `ELEVENLABS_VOICE_LINK` also accepts a share URL with
   `voiceId=...` or `/voices/<id>` and takes precedence when nonempty.
   `ELEVENLABS_TTS_MODEL` defaults to `eleven_flash_v2_5` for low latency.

Store the values in the repository's ignored `.env`, or in your deployment's
secret/environment settings. Existing environment variables take precedence
over `.env`. Do not paste credentials into chat, browser code or GitHub files.
For Codespaces, use Codespaces secrets; Actions secrets only apply to CI.

## Verify and start

```bash
source .venv/bin/activate
python -m friday_agent.doctor
./start-friday.sh
```

The doctor is an **offline configuration check**, not an authentication or
connectivity test. It rejects missing values, template placeholders and malformed
LiveKit URLs without printing keys. The worker also validates settings before
starting. Production uses `python -m friday_agent.livekit_agent start`.

## First voice conversation

For an immediate local microphone/speaker test (Groq + ElevenLabs only):

```bash
python -m friday_agent.doctor --console
python -m friday_agent.livekit_agent console
```

Use a machine with microphone/audio devices; a cloud container typically has
none. On Linux, the console may also require the system PortAudio runtime.

For LiveKit end to end:

1. Start the worker in `dev` mode and wait for successful worker registration.
2. Open the [LiveKit Agents Playground](https://agents-playground.livekit.io/)
   and connect it to the same project. Use a microphone-enabled HTTPS browser.
3. Select/dispatch the named agent `friday-ai-agent` (or your `FRIDAY_IDENTITY`)
   into the playground room. Because this worker has an explicit agent name,
   joining a room alone does not guarantee that it will be dispatched. If your
   client does not support agent selection, use the authenticated LiveKit CLI:

   ```bash
   lk dispatch create --agent-name friday-ai-agent --room YOUR_ROOM_NAME
   ```

4. Confirm the worker joins that room, hear its greeting, ask a question, and
   check that it responds aloud and can handle interruptions.

This uses provider quota. An actual call is the acceptance check for service
authentication, model/voice access, network connectivity and audio quality.
The repository dashboard remains a standalone visual demo; it is not a LiveKit
audio client. Use console mode or the playground for this setup.

## Containers

```bash
docker build -t friday-ai-agent .
docker run --rm --env-file .env friday-ai-agent
```

The image installs model assets at build time. Hugging Face cache files live in
`/app/.cache/huggingface`, which the non-root `friday` runtime user can read and
write. Never add credentials to the Dockerfile or build arguments.

## Troubleshooting

- **Doctor reports placeholders:** replace every `your_...` value. The example
  file intentionally cannot start a real worker.
- **No agent in the room:** check successful worker registration, matching
  project credentials and explicit dispatch using `FRIDAY_IDENTITY`.
- **Groq authorization/model error:** confirm key access and the two model names
  in Groq Console. An offline doctor pass does not verify account permissions.
- **ElevenLabs authorization/voice error:** confirm TTS permissions, available
  credits, voice access and the TTS model. Try a blank voice ID to use the default.
- **Audio absent:** allow the browser microphone, check the selected input/output
  devices and use HTTPS/localhost. Console mode needs local audio hardware.
- **Missing models after upgrading:** reactivate `.venv`, reinstall requirements
  and run `python -m livekit.agents download-files` again.
