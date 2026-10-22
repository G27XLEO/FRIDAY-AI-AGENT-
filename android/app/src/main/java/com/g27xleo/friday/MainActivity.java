package com.g27xleo.friday;

import android.Manifest;
import android.app.Activity;
import android.app.role.RoleManager;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.BatteryManager;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.text.DateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.Locale;

/**
 * Foreground-only voice interface and local, allow-listed system commands.
 * Microphone permission is requested just-in-time. No hidden hotword capture.
 */
public class MainActivity extends Activity {
    public static final String EXTRA_AUTO_LISTEN = "friday.auto_listen";
    private static final int AUDIO_PERMISSION_REQUEST = 1001;
    private static final int ASSISTANT_ROLE_REQUEST = 1002;

    private FridayOrbView orb;
    private TextView stateLabel;
    private TextView transcriptLabel;
    private TextView replyLabel;
    private TextView serviceLabel;
    private EditText manualInput;
    private SpeechRecognizer recognizer;
    private TextToSpeech textToSpeech;
    private boolean speakingReady;
    private boolean listening;
    private boolean autoListenPending;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(Color.rgb(5, 10, 22));
        getWindow().setNavigationBarColor(Color.rgb(5, 10, 22));
        createInterface();
        initializeSpeech();
        showStandby();

        autoListenPending = getIntent().getBooleanExtra(EXTRA_AUTO_LISTEN, false);
        if (autoListenPending) {
            getWindow().getDecorView().post(this::startVoice);
        }
    }

    private void createInterface() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        GradientDrawable page = new GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                new int[] { 0xFF060A17, 0xFF172342, 0xFF080A1A });
        scroll.setBackground(page);
        setContentView(scroll);

        LinearLayout outer = new LinearLayout(this);
        outer.setOrientation(LinearLayout.VERTICAL);
        outer.setGravity(Gravity.CENTER_HORIZONTAL);
        outer.setPadding(dp(22), dp(25), dp(22), dp(40));
        scroll.addView(outer);

        outer.addView(label("F R I D A Y   /   SYSTEM ASSISTANT", 12, 0xFF72DAEA, true));
        spacer(outer, 8);
        outer.addView(label("Voice Command Center", 27, Color.WHITE, true));
        spacer(outer, 4);
        outer.addView(label("Android companion · operator-controlled", 13, 0xFF9EBDD5, false));
        spacer(outer, 17);

        orb = new FridayOrbView(this);
        outer.addView(orb, new LinearLayout.LayoutParams(dp(295), dp(285)));
        stateLabel = label("STANDBY", 16, 0xFF88E6FF, true);
        outer.addView(stateLabel);
        spacer(outer, 12);

        Button listen = button("🎙  TAP TO LISTEN", 0xFF20577E);
        outer.addView(listen, fullButtonParams());
        listen.setOnClickListener(view -> startVoice());
        spacer(outer, 10);
        Button team = button("✦  OPEN AI AGENT TEAM", 0xFF087F9F);
        team.setOnClickListener(view -> startActivity(new Intent(this, AgentTeamActivity.class)));
        outer.addView(team, fullButtonParams());
        spacer(outer, 13);

        transcriptLabel = label("Say 'FRIDAY, check systems' or enter a command.", 13,
                0xFFCAD9E9, false);
        transcriptLabel.setGravity(Gravity.CENTER);
        outer.addView(transcriptLabel);
        spacer(outer, 10);

        replyLabel = label("Standing by. No microphone active.", 15, 0xFFE5F6FF, false);
        replyLabel.setGravity(Gravity.CENTER);
        replyLabel.setPadding(dp(12), dp(12), dp(12), dp(12));
        GradientDrawable replyBackground = new GradientDrawable();
        replyBackground.setColor(0x5517263D);
        replyBackground.setCornerRadius(dp(13));
        replyBackground.setStroke(dp(1), 0xFF36506B);
        replyLabel.setBackground(replyBackground);
        outer.addView(replyLabel, fullButtonParams());
        spacer(outer, 20);

        serviceLabel = label("Checking available local services…", 12, 0xFF9AB4C9, false);
        serviceLabel.setGravity(Gravity.CENTER);
        outer.addView(serviceLabel);
        spacer(outer, 16);

        Button systems = button("CHECK ALL AVAILABLE SYSTEMS", 0xFF273B5E);
        systems.setOnClickListener(view -> handleCommand(CommandRouter.Action.STATUS, true));
        outer.addView(systems, fullButtonParams());
        spacer(outer, 9);

        Button assistant = button("SET AS DEFAULT ASSISTANT", 0xFF303355);
        assistant.setOnClickListener(view -> requestAssistantRole());
        outer.addView(assistant, fullButtonParams());
        spacer(outer, 17);

        manualInput = new EditText(this);
        manualInput.setSingleLine(true);
        manualInput.setTextColor(Color.WHITE);
        manualInput.setHintTextColor(0xFF8CA5BB);
        manualInput.setHint("Try: open WiFi settings");
        manualInput.setTextSize(14);
        manualInput.setPadding(dp(14), dp(10), dp(14), dp(10));
        GradientDrawable inputBackground = new GradientDrawable();
        inputBackground.setColor(0xFF10192B);
        inputBackground.setStroke(dp(1), 0xFF425C72);
        inputBackground.setCornerRadius(dp(10));
        manualInput.setBackground(inputBackground);
        outer.addView(manualInput, fullButtonParams());
        spacer(outer, 9);

        Button type = button("RUN TYPED COMMAND", 0xFF304660);
        type.setOnClickListener(view -> runTranscript(manualInput.getText().toString()));
        outer.addView(type, fullButtonParams());
        spacer(outer, 18);

        TextView limits = label(
                "Only explicit local commands are available: time, date, battery, "
                + "system status, open settings, WiFi, Bluetooth, display settings, or browser.\n\n"
                + "The Android speech provider may use internet or process audio through its own service. "
                + "Agent Team is an optional interface requiring a trusted HTTPS backend and "
                + "Ollama model. No bundled model, background hotword or unrestricted automation.",
                12, 0xFF90A8C0, false);
        limits.setLineSpacing(dp(3), 1f);
        outer.addView(limits);
    }

    private void initializeSpeech() {
        speakingReady = false;
        textToSpeech = new TextToSpeech(this, status -> {
            speakingReady = status == TextToSpeech.SUCCESS;
            if (speakingReady && textToSpeech != null) {
                int language = textToSpeech.setLanguage(Locale.getDefault());
                if (language == TextToSpeech.LANG_NOT_SUPPORTED
                        || language == TextToSpeech.LANG_MISSING_DATA) {
                    speakingReady = false;
                }
            }
            runOnUiThread(this::updateServiceLabel);
        });
        textToSpeech.setOnUtteranceProgressListener(new UtteranceProgressListener() {
            @Override public void onStart(String utteranceId) {
                runOnUiThread(() -> {
                    if (orb != null) orb.setState(FridayOrbView.State.SPEAKING);
                    if (stateLabel != null) stateLabel.setText("SPEAKING");
                });
            }
            @Override public void onDone(String utteranceId) {
                runOnUiThread(() -> showStandby());
            }
            @Override public void onError(String utteranceId) {
                runOnUiThread(() -> showStandby());
            }
        });
        updateServiceLabel();
    }

    private void updateServiceLabel() {
        if (serviceLabel == null) return;
        serviceLabel.setText("Speech recognition: "
                + (SpeechRecognizer.isRecognitionAvailable(this) ? "available" : "unavailable")
                + "   ·   Speech output: " + (speakingReady ? "ready" : "not ready"));
    }

    private void startVoice() {
        if (listening) return;
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO)
                != PackageManager.PERMISSION_GRANTED) {
            stateLabel.setText("MICROPHONE PERMISSION REQUIRED");
            requestPermissions(new String[] { Manifest.permission.RECORD_AUDIO },
                    AUDIO_PERMISSION_REQUEST);
            return;
        }
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            displayReply("The Android speech recognition service is unavailable. "
                    + "Try a typed command or enable a system speech provider.", false);
            orb.setState(FridayOrbView.State.ERROR);
            stateLabel.setText("SPEECH SERVICE UNAVAILABLE");
            return;
        }

        if (recognizer != null) {
            recognizer.destroy();
            recognizer = null;
        }
        try {
            recognizer = SpeechRecognizer.createSpeechRecognizer(this);
            recognizer.setRecognitionListener(new RecognitionListener() {
                @Override public void onReadyForSpeech(Bundle params) {
                    stateLabel.setText("LISTENING · MIC ACTIVE");
                }
                @Override public void onBeginningOfSpeech() { }
                @Override public void onRmsChanged(float rmsdB) { }
                @Override public void onBufferReceived(byte[] buffer) { }
                @Override public void onEndOfSpeech() { stateLabel.setText("PROCESSING SPEECH"); }
                @Override public void onError(int error) {
                    listening = false;
                    orb.setState(FridayOrbView.State.STANDBY);
                    stateLabel.setText("STANDBY");
                    displayReply("Speech recognition ended (code " + error
                            + "). Tap to retry or type a command.", false);
                }
                @Override public void onResults(Bundle results) {
                    listening = false;
                    ArrayList<String> hypotheses =
                            results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                    if (hypotheses == null || hypotheses.isEmpty()) {
                        showStandby();
                        displayReply("No words were recognized. Please try again.", false);
                    } else {
                        runTranscript(hypotheses.get(0));
                    }
                }
                @Override public void onPartialResults(Bundle results) { }
                @Override public void onEvent(int eventType, Bundle params) { }
            });
            Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                    RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault().toLanguageTag());
            intent.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3);
            listening = true;
            orb.setState(FridayOrbView.State.LISTENING);
            stateLabel.setText("STARTING MICROPHONE");
            transcriptLabel.setText("Listening via Android speech recognition…");
            recognizer.startListening(intent);
        } catch (RuntimeException failure) {
            listening = false;
            showStandby();
            displayReply("Unable to start Android speech recognition.", false);
        }
    }

    private void runTranscript(String spoken) {
        String normalized = spoken == null ? "" : spoken.trim();
        if (normalized.isEmpty()) {
            displayReply("Enter or speak a supported command.", false);
            return;
        }
        transcriptLabel.setText("You: " + normalized);
        orb.setState(FridayOrbView.State.THINKING);
        stateLabel.setText("INTERPRETING LOCAL COMMAND");
        CommandRouter.Action action = CommandRouter.parse(normalized);
        handleCommand(action, true);
    }

    private void handleCommand(CommandRouter.Action action, boolean audible) {
        String answer;
        Intent external = null;
        switch (action) {
            case WAKE:
                showStandby();
                displayReply("I'm ready. Say your command after tapping Listen.", audible);
                return;
            case STATUS:
                showStandby();
                displayReply(systemReport(), audible);
                return;
            case HELP:
                answer = "I can check system status, time, date, battery and open "
                        + "WiFi, Bluetooth, display, settings or browser. "
                        + "Other actions require explicit new integrations.";
                break;
            case TIME:
                answer = "The time is " + DateFormat.getTimeInstance(
                        DateFormat.SHORT, Locale.getDefault()).format(new Date()) + ".";
                break;
            case DATE:
                answer = "Today is " + DateFormat.getDateInstance(
                        DateFormat.FULL, Locale.getDefault()).format(new Date()) + ".";
                break;
            case BATTERY:
                int level = getBatteryPercent();
                answer = level >= 0 ? "Battery level is " + level + " percent."
                        : "Battery percentage is unavailable.";
                break;
            case OPEN_WIFI:
                answer = "Opening WiFi settings.";
                external = new Intent(Settings.ACTION_WIFI_SETTINGS);
                break;
            case OPEN_BLUETOOTH:
                answer = "Opening Bluetooth settings.";
                external = new Intent(Settings.ACTION_BLUETOOTH_SETTINGS);
                break;
            case OPEN_DISPLAY:
                answer = "Opening display settings.";
                external = new Intent(Settings.ACTION_DISPLAY_SETTINGS);
                break;
            case OPEN_SETTINGS:
                answer = "Opening system settings.";
                external = new Intent(Settings.ACTION_SETTINGS);
                break;
            case OPEN_BROWSER:
                answer = "Opening the browser.";
                external = new Intent(Intent.ACTION_VIEW,
                        android.net.Uri.parse("https://www.google.com"));
                break;
            default:
                answer = "That command is not supported. I won't execute unrecognized "
                        + "instructions. Say help to hear available commands.";
        }

        if (external != null) {
            try {
                startActivity(external);
            } catch (ActivityNotFoundException | SecurityException error) {
                answer = "No authorized application was available for that action.";
            }
        }
        showStandby();
        displayReply(answer, audible);
    }

    private int getBatteryPercent() {
        Intent battery = registerReceiver(null, new IntentFilter(Intent.ACTION_BATTERY_CHANGED));
        if (battery == null) return -1;
        int level = battery.getIntExtra(BatteryManager.EXTRA_LEVEL, -1);
        int scale = battery.getIntExtra(BatteryManager.EXTRA_SCALE, -1);
        return level < 0 || scale <= 0 ? -1 : Math.round((level * 100f) / scale);
    }

    private String systemReport() {
        boolean speechAvailable = SpeechRecognizer.isRecognitionAvailable(this);
        boolean micGranted = checkSelfPermission(Manifest.permission.RECORD_AUDIO)
                == PackageManager.PERMISSION_GRANTED;
        String assistantRole = "not checked (Android version)";
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            RoleManager manager = (RoleManager) getSystemService(ROLE_SERVICE);
            if (manager == null || !manager.isRoleAvailable(RoleManager.ROLE_ASSISTANT)) {
                assistantRole = "unavailable on this device";
            } else {
                assistantRole = manager.isRoleHeld(RoleManager.ROLE_ASSISTANT)
                        ? "selected" : "not selected";
            }
        }
        return "FRIDAY system check:\n"
                + "Local command router: READY\n"
                + "Android speech recognition: " + (speechAvailable ? "AVAILABLE" : "UNAVAILABLE") + "\n"
                + "Microphone permission: " + (micGranted ? "GRANTED" : "NOT GRANTED") + "\n"
                + "Text to speech: " + (speakingReady ? "READY" : "UNAVAILABLE") + "\n"
                + "Default assistant role: " + assistantRole + "\n"
                + "Battery: " + (getBatteryPercent() >= 0
                     ? getBatteryPercent() + "%" : "UNAVAILABLE") + "\n"
                + "Advanced AI model: NOT CONNECTED\n"
                + "Always-on hotword detection: NOT IMPLEMENTED";
    }

    private void displayReply(String text, boolean audible) {
        replyLabel.setText(text);
        if (audible && speakingReady && textToSpeech != null) {
            orb.setState(FridayOrbView.State.SPEAKING);
            stateLabel.setText("SPEAKING");
            if (textToSpeech.speak(text, TextToSpeech.QUEUE_FLUSH, null, "friday-response")
                    == TextToSpeech.ERROR) {
                showStandby();
            }
        }
    }

    private void requestAssistantRole() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            RoleManager manager = (RoleManager) getSystemService(ROLE_SERVICE);
            if (manager != null && manager.isRoleAvailable(RoleManager.ROLE_ASSISTANT)) {
                if (manager.isRoleHeld(RoleManager.ROLE_ASSISTANT)) {
                    displayReply("FRIDAY is already selected as the default assistant.", true);
                } else {
                    startActivityForResult(manager.createRequestRoleIntent(RoleManager.ROLE_ASSISTANT),
                            ASSISTANT_ROLE_REQUEST);
                }
                return;
            }
        }
        displayReply("This device does not expose the assistant role request here. "
                + "Check Settings > Apps > Default apps > Digital assistant.", true);
    }

    private void showStandby() {
        if (orb != null) orb.setState(FridayOrbView.State.STANDBY);
        if (stateLabel != null) stateLabel.setText("STANDBY");
    }

    @Override
    public void onRequestPermissionsResult(int code, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(code, permissions, results);
        if (code == AUDIO_PERMISSION_REQUEST) {
            if (results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED) {
                startVoice();
            } else {
                autoListenPending = false;
                displayReply("Microphone access denied. Typed commands still work.", false);
                showStandby();
            }
        }
    }

    @Override
    protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request == ASSISTANT_ROLE_REQUEST) {
            displayReply(result == RESULT_OK
                    ? "Assistant role request completed. Check Systems to confirm."
                    : "Assistant selection was cancelled or unsupported.", true);
        }
    }

    @Override protected void onResume() {
        super.onResume();
        if (orb != null) orb.setRunning(true);
    }

    @Override protected void onPause() {
        if (orb != null) orb.setRunning(false);
        if (recognizer != null && listening) {
            recognizer.cancel();
            listening = false;
            showStandby();
        }
        super.onPause();
    }

    @Override protected void onDestroy() {
        if (recognizer != null) {
            recognizer.destroy();
            recognizer = null;
        }
        if (textToSpeech != null) {
            textToSpeech.stop();
            textToSpeech.shutdown();
            textToSpeech = null;
        }
        super.onDestroy();
    }

    private LinearLayout.LayoutParams fullButtonParams() {
        return new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
    }

    private TextView label(String text, int size, int color, boolean bold) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextColor(color);
        view.setTextSize(size);
        view.setGravity(Gravity.CENTER);
        if (bold) view.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        return view;
    }

    private Button button(String text, int background) {
        Button value = new Button(this);
        value.setAllCaps(false);
        value.setText(text);
        value.setTextSize(13);
        value.setTextColor(Color.WHITE);
        value.setPadding(dp(8), dp(13), dp(8), dp(13));
        GradientDrawable shape = new GradientDrawable();
        shape.setColor(background);
        shape.setCornerRadius(dp(13));
        shape.setStroke(dp(1), 0xFF467494);
        value.setBackground(shape);
        return value;
    }

    private void spacer(LinearLayout layout, int height) {
        View spacer = new View(this);
        layout.addView(spacer, new LinearLayout.LayoutParams(1, dp(height)));
    }

    private int dp(float amount) {
        return Math.round(amount * getResources().getDisplayMetrics().density);
    }
}
