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
import android.widget.ArrayAdapter;
import android.widget.AdapterView;
import android.widget.Spinner;
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
    private Locale speechLocale = Locale.getDefault();

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
        final int cyan = 0xFF67E9F9;
        final int muted = 0xFF8AAABE;
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setClipToPadding(false);
        GradientDrawable background = new GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                new int[] { 0xFF030912, 0xFF0A1C2A, 0xFF020710 });
        scroll.setBackground(background);
        setContentView(scroll);

        LinearLayout outer = new LinearLayout(this);
        outer.setOrientation(LinearLayout.VERTICAL);
        outer.setGravity(Gravity.CENTER_HORIZONTAL);
        outer.setPadding(dp(18), dp(20), dp(18), dp(32));
        scroll.addView(outer);

        // Minimal telemetry rail; no fake network connectivity indicators.
        LinearLayout top = new LinearLayout(this);
        top.setGravity(Gravity.CENTER_VERTICAL);
        top.setOrientation(LinearLayout.HORIZONTAL);
        outer.addView(top, fullButtonParams());
        TextView mark = label("◈  F R I D A Y", 17, 0xFFE4FDFF, true);
        mark.setGravity(Gravity.START | Gravity.CENTER_VERTICAL);
        mark.setTypeface(Typeface.create("monospace", Typeface.BOLD));
        top.addView(mark, new LinearLayout.LayoutParams(0, dp(44), 1f));
        TextView edition = label("O S  /  0 3", 10, cyan, true);
        edition.setTypeface(Typeface.MONOSPACE);
        edition.setGravity(Gravity.END | Gravity.CENTER_VERTICAL);
        top.addView(edition);
        spacer(outer, 6);
        TextView subtitle = label("PERSONAL ASSISTANT   //   TACTICAL INTERFACE", 10, muted, false);
        subtitle.setGravity(Gravity.START);
        subtitle.setLetterSpacing(0.12f);
        outer.addView(subtitle, fullButtonParams());
        spacer(outer, 18);

        LinearLayout rail = new LinearLayout(this);
        rail.setOrientation(LinearLayout.HORIZONTAL);
        rail.setGravity(Gravity.CENTER_VERTICAL);
        rail.setPadding(dp(12), dp(10), dp(12), dp(10));
        rail.setBackground(panelShape(0xCC071522, 0xFF1B576B, 9));
        outer.addView(rail, fullButtonParams());
        TextView local = label("●  LOCAL CORE", 10, cyan, true);
        local.setGravity(Gravity.START);
        local.setTypeface(Typeface.MONOSPACE);
        rail.addView(local, new LinearLayout.LayoutParams(0, -2, 1f));
        TextView battery = label("POWER  " + (getBatteryPercent() < 0
                ? "--" : getBatteryPercent() + "%"), 10, 0xFFFFC77D, true);
        battery.setTypeface(Typeface.MONOSPACE);
        rail.addView(battery);
        spacer(outer, 15);

        TextView orbKicker = label("◌    A R C   I N T E L L I G E N C E   C O R E    ◌",
                10, muted, true);
        orbKicker.setTypeface(Typeface.MONOSPACE);
        outer.addView(orbKicker);
        spacer(outer, 6);

        orb = new FridayOrbView(this);
        int widthDp = (int) (getResources().getDisplayMetrics().widthPixels
                / getResources().getDisplayMetrics().density);
        int orbSize = Math.max(248, Math.min(340, widthDp - 44));
        outer.addView(orb, new LinearLayout.LayoutParams(dp(orbSize), dp(orbSize)));

        stateLabel = label("STANDBY", 17, cyan, true);
        stateLabel.setTypeface(Typeface.create("monospace", Typeface.BOLD));
        stateLabel.setLetterSpacing(0.21f);
        outer.addView(stateLabel);
        spacer(outer, 5);
        TextView context = label("SYSTEM AWAITING DIRECT COMMAND", 10, muted, false);
        context.setLetterSpacing(0.1f);
        outer.addView(context);
        spacer(outer, 21);

        // Speech providers may not have Hindi/Marathi voices installed.
        TextView languageLabel = label("SPEECH LANGUAGE  /  DEVICE PROVIDER", 10, muted, true);
        languageLabel.setGravity(Gravity.START);
        languageLabel.setTypeface(Typeface.MONOSPACE);
        outer.addView(languageLabel, fullButtonParams());
        spacer(outer, 7);
        Spinner languages = new Spinner(this);
        ArrayAdapter<String> languageAdapter = new ArrayAdapter<>(this,
                android.R.layout.simple_spinner_item, new String[] {
                "Device language (default)", "English (India)", "हिन्दी · Hindi",
                "मराठी · Marathi" });
        languageAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        languages.setAdapter(languageAdapter);
        languages.setBackground(panelShape(0xFF102C3A, 0xFF347D91, 9));
        languages.setPadding(dp(12), dp(6), dp(8), dp(6));
        languages.setContentDescription("Select speech recognition and voice language");
        outer.addView(languages, new LinearLayout.LayoutParams(-1, dp(49)));
        languages.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override public void onItemSelected(AdapterView<?> parent, View selected,
                    int position, long id) {
                speechLocale = position == 1 ? new Locale("en", "IN")
                        : position == 2 ? new Locale("hi", "IN")
                        : position == 3 ? new Locale("mr", "IN")
                        : Locale.getDefault();
                if (textToSpeech != null && speakingReady) {
                    int result = textToSpeech.setLanguage(speechLocale);
                    speakingReady = result != TextToSpeech.LANG_MISSING_DATA
                            && result != TextToSpeech.LANG_NOT_SUPPORTED;
                }
                updateServiceLabel();
            }
            @Override public void onNothingSelected(AdapterView<?> parent) { }
        });
        spacer(outer, 14);

        Button listen = button("◉   INITIALIZE VOICE LINK", 0xFF09485A);
        listen.setContentDescription("Tap to start Android speech recognition");
        listen.setTextSize(14);
        listen.setPadding(dp(12), dp(17), dp(12), dp(17));
        outer.addView(listen, fullButtonParams());
        listen.setOnClickListener(view -> startVoice());
        spacer(outer, 21);

        TextView inTitle = label("01  /  INPUT TRANSCRIPT", 10, cyan, true);
        inTitle.setGravity(Gravity.START);
        inTitle.setTypeface(Typeface.MONOSPACE);
        outer.addView(inTitle, fullButtonParams());
        spacer(outer, 7);
        transcriptLabel = label("Awaiting voice or typed input…", 13,
                0xFFCFEBF6, false);
        transcriptLabel.setGravity(Gravity.START | Gravity.CENTER_VERTICAL);
        transcriptLabel.setPadding(dp(14), dp(13), dp(14), dp(13));
        transcriptLabel.setBackground(panelShape(0xCF081924, 0xFF25566A, 11));
        outer.addView(transcriptLabel, fullButtonParams());
        spacer(outer, 14);

        TextView outTitle = label("02  /  FRIDAY RESPONSE", 10, cyan, true);
        outTitle.setGravity(Gravity.START);
        outTitle.setTypeface(Typeface.MONOSPACE);
        outer.addView(outTitle, fullButtonParams());
        spacer(outer, 7);
        replyLabel = label("All local systems standing by. Microphone is off.", 14,
                0xFFF0FBFF, false);
        replyLabel.setGravity(Gravity.START | Gravity.CENTER_VERTICAL);
        replyLabel.setLineSpacing(dp(4), 1.05f);
        replyLabel.setPadding(dp(16), dp(17), dp(16), dp(17));
        replyLabel.setBackground(panelShape(0xF0092031, 0xFF327C8F, 12));
        outer.addView(replyLabel, fullButtonParams());
        spacer(outer, 20);

        TextView quickTitle = label("QUICK EXECUTION  /  ALLOWLISTED", 10, muted, true);
        quickTitle.setTypeface(Typeface.MONOSPACE);
        quickTitle.setGravity(Gravity.START);
        outer.addView(quickTitle, fullButtonParams());
        spacer(outer, 9);
        LinearLayout quick = new LinearLayout(this);
        quick.setOrientation(LinearLayout.HORIZONTAL);
        outer.addView(quick, fullButtonParams());
        Button status = button("SYSTEM SCAN", 0xFF102B3A);
        Button wifi = button("WIFI", 0xFF102B3A);
        Button time = button("TIME", 0xFF102B3A);
        LinearLayout.LayoutParams cell = new LinearLayout.LayoutParams(0, dp(49), 1f);
        cell.setMargins(0, 0, dp(7), 0);
        quick.addView(status, cell);
        LinearLayout.LayoutParams cell2 = new LinearLayout.LayoutParams(0, dp(49), 1f);
        cell2.setMargins(0, 0, dp(7), 0);
        quick.addView(wifi, cell2);
        quick.addView(time, new LinearLayout.LayoutParams(0, dp(49), 1f));
        status.setOnClickListener(view -> handleCommand(CommandRouter.Action.STATUS, true));
        wifi.setOnClickListener(view -> handleCommand(CommandRouter.Action.OPEN_WIFI, true));
        time.setOnClickListener(view -> handleCommand(CommandRouter.Action.TIME, true));
        spacer(outer, 22);

        TextView consoleTitle = label("03  /  COMMAND TERMINAL", 10, cyan, true);
        consoleTitle.setTypeface(Typeface.MONOSPACE);
        consoleTitle.setGravity(Gravity.START);
        outer.addView(consoleTitle, fullButtonParams());
        spacer(outer, 8);
        manualInput = new EditText(this);
        manualInput.setSingleLine(true);
        manualInput.setTextColor(Color.WHITE);
        manualInput.setHintTextColor(0xFF7F9AAC);
        manualInput.setHint("Enter an allowed command...");
        manualInput.setTextSize(13);
        manualInput.setPadding(dp(15), dp(13), dp(15), dp(13));
        manualInput.setBackground(panelShape(0xFF061623, 0xFF245568, 9));
        outer.addView(manualInput, fullButtonParams());
        spacer(outer, 8);
        Button execute = button("EXECUTE COMMAND   →", 0xFF164258);
        outer.addView(execute, fullButtonParams());
        execute.setOnClickListener(view -> runTranscript(manualInput.getText().toString()));
        spacer(outer, 26);

        // Technical controls are real and accessible, but not the focal point.
        Button diagnosticsToggle = button("▤   DIAGNOSTICS & ASSISTANT SETTINGS   ▾", 0xFF132437);
        outer.addView(diagnosticsToggle, fullButtonParams());
        spacer(outer, 10);
        LinearLayout diagnostics = new LinearLayout(this);
        diagnostics.setOrientation(LinearLayout.VERTICAL);
        diagnostics.setPadding(dp(13), dp(15), dp(13), dp(15));
        diagnostics.setBackground(panelShape(0xFF071521, 0xFF25516A, 10));
        diagnostics.setVisibility(View.GONE);
        outer.addView(diagnostics, fullButtonParams());
        diagnosticsToggle.setOnClickListener(v -> {
            boolean expand = diagnostics.getVisibility() != View.VISIBLE;
            diagnostics.setVisibility(expand ? View.VISIBLE : View.GONE);
            diagnosticsToggle.setText(expand
                    ? "▤   HIDE DIAGNOSTICS   ▴"
                    : "▤   DIAGNOSTICS & ASSISTANT SETTINGS   ▾");
        });
        serviceLabel = label("Checking speech services…", 12, muted, false);
        serviceLabel.setGravity(Gravity.START);
        serviceLabel.setLineSpacing(dp(3), 1f);
        diagnostics.addView(serviceLabel);
        spacer(diagnostics, 12);
        Button systems = button("RUN ALL SYSTEM CHECKS", 0xFF18394B);
        diagnostics.addView(systems, fullButtonParams());
        systems.setOnClickListener(v -> handleCommand(CommandRouter.Action.STATUS, false));
        spacer(diagnostics, 9);
        Button assistant = button("SET DEFAULT ASSISTANT", 0xFF1D344A);
        diagnostics.addView(assistant, fullButtonParams());
        assistant.setOnClickListener(v -> requestAssistantRole());
        spacer(diagnostics, 12);
        TextView limits = label("DEVICE MODE / LOCAL COMMANDS ONLY\n"
                + "No background hotword, LiveKit connection, or AI reasoning in this APK. "
                + "Android speech recognition and TTS depend on installed system providers. "
                + "Microphone access is requested only when you tap Voice Link.", 11, muted, false);
        limits.setGravity(Gravity.START);
        limits.setLineSpacing(dp(4), 1f);
        diagnostics.addView(limits);

        spacer(outer, 19);
        TextView footer = label("FRIDAY // LOCAL DEVICE INTERFACE  •  v0.2 HUD", 10,
                0xFF5F879A, false);
        footer.setTypeface(Typeface.MONOSPACE);
        outer.addView(footer);
    }

    private GradientDrawable panelShape(int fill, int stroke, int radiusDp) {
        GradientDrawable shape = new GradientDrawable();
        shape.setColor(fill);
        shape.setCornerRadius(dp(radiusDp));
        shape.setStroke(dp(1), stroke);
        return shape;
    }

    private void initializeSpeech() {
        speakingReady = false;
        textToSpeech = new TextToSpeech(this, status -> {
            speakingReady = status == TextToSpeech.SUCCESS;
            if (speakingReady && textToSpeech != null) {
                int language = textToSpeech.setLanguage(speechLocale);
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
                + "   ·   Speech output: " + (speakingReady ? "ready" : "not ready")
                + "   ·   Language: " + speechLocale.toLanguageTag());
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
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, speechLocale.toLanguageTag());
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
                String localTime = DateFormat.getTimeInstance(
                        DateFormat.SHORT, speechLocale).format(new Date());
                answer = languageText("The time is ", "अभी समय है ", "आता वेळ आहे ")
                        + localTime + ".";
                break;
            case DATE:
                String localDate = DateFormat.getDateInstance(
                        DateFormat.FULL, speechLocale).format(new Date());
                answer = languageText("Today is ", "आज तारीख है ", "आज तारीख आहे ")
                        + localDate + ".";
                break;
            case BATTERY:
                int level = getBatteryPercent();
                answer = level >= 0
                        ? languageText("Battery level is ", "बैटरी ", "बॅटरी ")
                            + level + languageText(" percent.", " प्रतिशत है।", " टक्के आहे.")
                        : languageText("Battery percentage is unavailable.",
                            "बैटरी स्तर उपलब्ध नहीं है।", "बॅटरी पातळी उपलब्ध नाही.");
                break;
            case OPEN_WIFI:
                answer = languageText("Opening WiFi settings.",
                        "वाईफाई सेटिंग खोल रही हूँ।", "वायफाय सेटिंग्ज उघडत आहे.");
                external = new Intent(Settings.ACTION_WIFI_SETTINGS);
                break;
            case OPEN_BLUETOOTH:
                answer = languageText("Opening Bluetooth settings.",
                        "ब्लूटूथ सेटिंग खोल रही हूँ।", "ब्लूटूथ सेटिंग्ज उघडत आहे.");
                external = new Intent(Settings.ACTION_BLUETOOTH_SETTINGS);
                break;
            case OPEN_DISPLAY:
                answer = languageText("Opening display settings.",
                        "डिस्प्ले सेटिंग खोल रही हूँ।", "डिस्प्ले सेटिंग्ज उघडत आहे.");
                external = new Intent(Settings.ACTION_DISPLAY_SETTINGS);
                break;
            case OPEN_SETTINGS:
                answer = languageText("Opening system settings.",
                        "सिस्टम सेटिंग खोल रही हूँ।", "सिस्टम सेटिंग्ज उघडत आहे.");
                external = new Intent(Settings.ACTION_SETTINGS);
                break;
            case OPEN_BROWSER:
                answer = languageText("Opening the browser.",
                        "ब्राउज़र खोल रही हूँ।", "ब्राउझर उघडत आहे.");
                external = new Intent(Intent.ACTION_VIEW,
                        android.net.Uri.parse("https://www.google.com"));
                break;
            default:
                answer = languageText(
                        "Unsupported command. Say help for available local commands.",
                        "यह आदेश समर्थित नहीं है। उपलब्ध आदेश जानने के लिए मदद कहें।",
                        "ही आज्ञा समर्थित नाही. उपलब्ध आज्ञांसाठी मदत म्हणा.");
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

    private String languageText(String english, String hindi, String marathi) {
        String code = speechLocale.getLanguage();
        if ("hi".equals(code)) return hindi;
        if ("mr".equals(code)) return marathi;
        return english;
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
                + "Speech language: " + speechLocale.toLanguageTag() + "\n"
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
