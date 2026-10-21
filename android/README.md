# FRIDAY OS — Android system-assistant companion

This is an **installable Android app prototype** for Android 8.0+ (API 26+).
It is separate from the standalone React dashboard in `web/`.

This app is **not a superintelligence or an autonomous general AI**.
It provides native assistant registration, a JARVIS-inspired animated ARC reactor HUD, foreground speech
recognition via the Android speech provider, text-to-speech feedback, a
permission-gated microphone and a restricted command router.

## Get the APK (after CI succeeds)

1. Open GitHub Actions in the FRIDAY repository.
2. Select **FRIDAY Android Companion APK**.
3. Open the most recent **successful** workflow run for this branch.
4. In **Artifacts**, select `friday-os-android-debug`.
5. Download the ZIP to your Android phone and extract `app-debug.apk`.
6. Open the APK from Files and approve Android's **Install unknown apps**
   prompt only for this trusted installation.
7. Open **FRIDAY OS**, choose a speech language, then tap **SYSTEM SCAN** or **INITIALIZE VOICE LINK**.

Do not install an APK from untrusted links. GitHub's automated
artifact download may require signing in. The artifact is retained for
7 days; it is a debug build, not a Play Store release.

Alternatively build on Linux with Java 17, Android SDK 35 and Gradle 8.9:

```bash
gradle -p android :app:testDebugUnitTest
gradle -p android :app:assembleDebug
```

The APK will be at
`android/app/build/outputs/apk/debug/app-debug.apk`.

## How to test a real phone

### App and permission check

1. Launch the app and confirm the fluid orb appears without crashing.
2. Choose Device default, English (India), Hindi, or Marathi in the language selector.
3. Tap **SYSTEM SCAN** or expand diagnostics for a full report.
3. Check the reported fields individually:
   - Local command router should show READY.
   - Speech recognition depends on whether Android exposes a recognizer.
   - Microphone permission is initially NOT GRANTED, until the user allows it.
   - Text to speech requires an installed voice provider and language.
   - Default assistant selection depends on Android/OEM support.
4. Tap **INITIALIZE VOICE LINK** and grant microphone permission if you choose.
5. Try English "what time is it", Hindi "समय बताओ", or Marathi "वेळ सांगा". Confirm the screen shows the transcript
   and speaks an appropriate answer if TTS is available.
6. Try typing **"open Bluetooth settings"**. It should open Android Settings.
7. Type **"delete all my photos"**. It should refuse to execute it.
8. Return to FRIDAY and verify that the app stops recording when backgrounded.
9. To test assistant integration, expand diagnostics and tap **SET DEFAULT ASSISTANT**, then
   approve the Android system prompt if it offers FRIDAY. On some phones the
   setting is under Apps > Default apps > Digital assistant app. Try the
   phone's normal assistant gesture.

Android 10 OEM software may restrict third-party assistant selection, voice
services, and speech providers. The exact Settings path varies by vendor.

### Current capability matrix

| Capability | Included | What the check actually proves |
|---|---|---|
| Native Android installable UI | Yes | CI compiles APK, phone install needs manual check |
| Animated ARC reactor HUD | Yes | Native Canvas visualizer, not audio-level input |
| Voice commands while app foreground | Conditional | English/Hindi/Marathi allowlisted phrases; depends on Android recognizer |
| Speech output | Conditional | Short localized responses; matching TTS voice/provider required |
| Local device actions | Yes | Explicit commands only (settings/browser) |
| Battery/time/date/system status | Yes | Uses local Android APIs |
| Android default-assistant role | Experimental | User choice and OEM-specific support |
| Always-on "Hey FRIDAY" wake with screen off | **No** | Not implemented; may require privileged hotword/DSP access |
| LiveKit, cloud LLM or multimodal reasoning | **No** | Not connected to Android companion |
| Autonomous unrestricted device access | **No** | Explicitly prohibited |
| AGI / superintelligence | **No** | Not a verifiable capability |

## Security and privacy boundaries

The app declares only `RECORD_AUDIO` as a runtime permission. It does not
request accessibility access, notifications, SMS, contacts, admin rights,
location, storage, boot-start or overlays. It does not listen for a wake word
in the background. No API keys are bundled and there is no app-owned
network/LLM pipeline.

**Caution:** Android `SpeechRecognizer` delegates to the installed system
recognition provider, which may send audio to its own servers. Android TTS
is also provider dependent. The app makes this dependency visible.

For genuinely reliable system-wide hotwording, further work must determine
whether the handset grants hotword hardware or software detection to third-
party voice assistants, and must implement it with the user's explicit
permission and adequate power, lifecycle and privacy protections.

## Development status

The automated pipeline runs a pure Java command-routing test and builds
a debug APK. It does **not** prove Android system assistant invocation,
permission dialogs, background restrictions, wake-word recognition, mic
quality, TTS latency or device compatibility. Those require actual physical
device tests.

The React `web/` dashboard remains standalone and does not connect to the
Android voice companion.

## Multilingual voice and ARC design (v0.2)

The native app supports one **selected speech language** at a time:
device default, English (India), Hindi or Marathi. The Android speech
recognizer and TTS provider must support the selected language; on Android 8+
this selector is not automatic mixed-language switching. Commands remain
restricted to explicit allowlisted phrases.

The **separate** LiveKit worker uses Groq multilingual transcription with
language detection enabled by FRIDAY_MULTILINGUAL_STT=true, conservative
Unicode-aware intent/language hints and ElevenLabs multilingual TTS
(ELEVENLABS_TTS_MODEL=eleven_multilingual_v2). It is **not connected**
to the Android app.

Use a voice that is licensed for your project. The LiveKit worker can be
configured with a warm, articulate, subtle Irish-inflected female voice,
but does not include or claim the real voice of actor Kerry Condon.
The Android app relies on installed system TTS providers instead.

Libraries.dev effects (thinking-orbs, border-beam, metal-fx) power the
standalone React HUD. The native Android ARC reactor is drawn with Canvas
because those npm React packages are not compatible with a Java View.
