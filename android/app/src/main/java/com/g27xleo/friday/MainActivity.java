package com.g27xleo.friday;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
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
import java.util.List;

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

    /**
     * FRIDAY home adopts Libraries.dev's visual language (black, oversized
     * typography, pill navigation, effect showcase cards) without copying
     * its brand assets or claiming that React npm effects run in native Java.
     * All actions below retain their real device handlers.
     */
    private void createInterface() {
        final int white = 0xFFF4F4F4;
        final int muted = 0xFFAAAAAA;
        final int cyan = 0xFFB5F7FF;
        final int border = 0xFF393939;

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(0xFF050505);
        setContentView(scroll);
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(20), dp(18), dp(20), dp(30));
        scroll.addView(page);

        // Clean product navigation rather than a diagnostic header.
        LinearLayout navigation = new LinearLayout(this);
        navigation.setOrientation(LinearLayout.HORIZONTAL);
        navigation.setGravity(Gravity.CENTER_VERTICAL);
        page.addView(navigation, fullButtonParams());
        TextView brand = label("◈  FRIDAY", 19, white, true);
        brand.setGravity(Gravity.START | Gravity.CENTER_VERTICAL);
        brand.setLetterSpacing(-0.02f);
        navigation.addView(brand, new LinearLayout.LayoutParams(0, dp(45), 1f));
        TextView navLabel = label("ASSISTANT  •  LOCAL", 10, 0xFFCBCBCB, true);
        navLabel.setPadding(dp(13), dp(11), dp(13), dp(11));
        navLabel.setBackground(panelShape(0xFF171717, border, 25));
        navigation.addView(navLabel);
        spacer(page, 32);

        TextView micro = label("◉  YOUR PERSONAL AI INTERFACE", 11, muted, true);
        micro.setGravity(Gravity.START);
        micro.setLetterSpacing(.13f);
        page.addView(micro, fullButtonParams());
        spacer(page, 15);
        TextView headline = label("An assistant\nthat feels alive.", 36, white, true);
        headline.setGravity(Gravity.START);
        headline.setLetterSpacing(-.047f);
        headline.setLineSpacing(dp(3), 1f);
        page.addView(headline, fullButtonParams());
        spacer(page, 13);
        TextView description = label(
                "Talk naturally, open installed apps, and control supported "
                + "phone features from one beautifully simple space.",
                14, muted, false);
        description.setGravity(Gravity.START);
        description.setLineSpacing(dp(5), 1f);
        page.addView(description, fullButtonParams());
        spacer(page, 25);

        Button listen = button("●   Start listening   ↗", white);
        listen.setTextColor(0xFF080808);
        listen.setTextSize(15);
        listen.setPadding(dp(17), dp(18), dp(17), dp(18));
        listen.setBackground(panelShape(white, white, 24));
        listen.setContentDescription("Start one foreground speech recognition session");
        page.addView(listen, fullButtonParams());
        listen.setOnClickListener(v -> startVoice());
        spacer(page, 10);
        Button browse = button("Browse installed apps   →", 0xFF171717);
        browse.setTextSize(14);
        browse.setBackground(panelShape(0xFF171717, border, 24));
        browse.setOnClickListener(v -> showInstalledApps());
        page.addView(browse, fullButtonParams());
        spacer(page, 25);

        // One large featured effect card, like the examples at Libraries.dev.
        LinearLayout featured = new LinearLayout(this);
        featured.setOrientation(LinearLayout.VERTICAL);
        featured.setGravity(Gravity.CENTER_HORIZONTAL);
        featured.setPadding(dp(14), dp(19), dp(14), dp(21));
        featured.setBackground(panelShape(0xFF101113, 0xFF353638, 25));
        page.addView(featured, fullButtonParams());
        LinearLayout featuredHeader = new LinearLayout(this);
        featuredHeader.setGravity(Gravity.CENTER_VERTICAL);
        featured.addView(featuredHeader, fullButtonParams());
        TextView featureName = label("VOICE / REACTOR", 11, 0xFFF1F1F1, true);
        featureName.setGravity(Gravity.START);
        featuredHeader.addView(featureName, new LinearLayout.LayoutParams(0, -2, 1f));
        TextView featurePill = label("NATIVE EFFECT", 9, 0xFFB6DDDF, true);
        featurePill.setPadding(dp(9), dp(7), dp(9), dp(7));
        featurePill.setBackground(panelShape(0xFF1B282A, 0xFF375158, 17));
        featuredHeader.addView(featurePill);

        orb = new FridayOrbView(this);
        int screenDp = (int) (getResources().getDisplayMetrics().widthPixels
                / getResources().getDisplayMetrics().density);
        int coreSize = Math.max(218, Math.min(302, screenDp - 95));
        featured.addView(orb, new LinearLayout.LayoutParams(dp(coreSize), dp(coreSize)));
        stateLabel = label("STANDBY", 15, cyan, true);
        stateLabel.setLetterSpacing(.14f);
        featured.addView(stateLabel);
        spacer(featured, 8);
        TextView privacy = label("Microphone off until you tap Start listening", 11, muted, false);
        featured.addView(privacy);
        spacer(page, 25);

        TextView section = label("Made for the things you do.", 24, white, true);
        section.setGravity(Gravity.START);
        page.addView(section, fullButtonParams());
        spacer(page, 5);
        TextView sectionSubtitle = label("One tap, one action. No hidden automation.", 12, muted, false);
        sectionSubtitle.setGravity(Gravity.START);
        page.addView(sectionSubtitle, fullButtonParams());
        spacer(page, 16);

        LinearLayout tiles1 = new LinearLayout(this);
        tiles1.setOrientation(LinearLayout.HORIZONTAL);
        page.addView(tiles1, fullButtonParams());
        Button appTile = effectTile("↗\n\nInstalled apps\nOpen WhatsApp, YouTube and more");
        Button scanTile = effectTile("◉\n\nSystem scan\nRead your device status");
        LinearLayout.LayoutParams tileLeft = new LinearLayout.LayoutParams(0, dp(142), 1f);
        tileLeft.rightMargin = dp(9);
        tiles1.addView(appTile, tileLeft);
        tiles1.addView(scanTile, new LinearLayout.LayoutParams(0, dp(142), 1f));
        appTile.setOnClickListener(v -> showInstalledApps());
        scanTile.setOnClickListener(v -> handleCommand(CommandRouter.Action.STATUS, true));
        spacer(page, 9);

        LinearLayout tiles2 = new LinearLayout(this);
        tiles2.setOrientation(LinearLayout.HORIZONTAL);
        page.addView(tiles2, fullButtonParams());
        Button wifiTile = effectTile("⌘\n\nWi-Fi settings\nOpen Android controls");
        Button batteryTile = effectTile("◫\n\nBattery check\nInspect power level");
        LinearLayout.LayoutParams tileLeft2 = new LinearLayout.LayoutParams(0, dp(142), 1f);
        tileLeft2.rightMargin = dp(9);
        tiles2.addView(wifiTile, tileLeft2);
        tiles2.addView(batteryTile, new LinearLayout.LayoutParams(0, dp(142), 1f));
        wifiTile.setOnClickListener(v -> handleCommand(CommandRouter.Action.OPEN_WIFI, true));
        batteryTile.setOnClickListener(v -> handleCommand(CommandRouter.Action.BATTERY, true));
        spacer(page, 28);

        TextView languageLabel = label("Speak your language", 23, white, true);
        languageLabel.setGravity(Gravity.START);
        page.addView(languageLabel, fullButtonParams());
        spacer(page, 5);
        TextView languageHelp = label("English, Hindi and Marathi, based on your phone's speech provider.",
                12, muted, false);
        languageHelp.setGravity(Gravity.START);
        page.addView(languageHelp, fullButtonParams());
        spacer(page, 13);
        Spinner languages = new Spinner(this);
        ArrayAdapter<String> languageAdapter = new ArrayAdapter<>(this,
                android.R.layout.simple_spinner_item, new String[] {
                "Device default", "English (India)", "हिन्दी · Hindi",
                "मराठी · Marathi" });
        languageAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        languages.setAdapter(languageAdapter);
        languages.setBackground(panelShape(0xFF191919, 0xFF464646, 15));
        languages.setPadding(dp(15), dp(9), dp(10), dp(9));
        languages.setContentDescription("Select voice input and response language");
        page.addView(languages, new LinearLayout.LayoutParams(-1, dp(53)));
        languages.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override public void onItemSelected(AdapterView<?> parent, View view,
                    int position, long id) {
                speechLocale = position == 1 ? new Locale("en", "IN")
                        : position == 2 ? new Locale("hi", "IN")
                        : position == 3 ? new Locale("mr", "IN") : Locale.getDefault();
                if (textToSpeech != null) {
                    int result = textToSpeech.setLanguage(speechLocale);
                    speakingReady = result != TextToSpeech.LANG_MISSING_DATA
                            && result != TextToSpeech.LANG_NOT_SUPPORTED;
                }
                updateServiceLabel();
            }
            @Override public void onNothingSelected(AdapterView<?> parent) { }
        });
        spacer(page, 27);

        TextView transcriptTitle = label("Your conversation", 24, white, true);
        transcriptTitle.setGravity(Gravity.START);
        page.addView(transcriptTitle, fullButtonParams());
        spacer(page, 12);
        transcriptLabel = label("Say “open WhatsApp” or “what time is it?”", 13, muted, false);
        transcriptLabel.setGravity(Gravity.START);
        transcriptLabel.setPadding(dp(16), dp(14), dp(16), dp(14));
        transcriptLabel.setBackground(panelShape(0xFF161616, border, 16));
        page.addView(transcriptLabel, fullButtonParams());
        spacer(page, 9);
        replyLabel = label("FRIDAY is ready. Microphone off.", 14, white, false);
        replyLabel.setLineSpacing(dp(4), 1f);
        replyLabel.setGravity(Gravity.START);
        replyLabel.setPadding(dp(17), dp(19), dp(17), dp(19));
        replyLabel.setBackground(panelShape(0xFF1D2022, 0xFF424749, 16));
        page.addView(replyLabel, fullButtonParams());
        spacer(page, 12);
        manualInput = new EditText(this);
        manualInput.setSingleLine(true);
        manualInput.setTextColor(white);
        manualInput.setHintTextColor(muted);
        manualInput.setHint("Type a command or an app name…");
        manualInput.setTextSize(14);
        manualInput.setPadding(dp(16), dp(14), dp(16), dp(14));
        manualInput.setBackground(panelShape(0xFF141414, 0xFF464646, 14));
        page.addView(manualInput, fullButtonParams());
        spacer(page, 10);
        Button execute = button("Run command   ↗", white);
        execute.setTextColor(0xFF090909);
        execute.setBackground(panelShape(white, white, 25));
        execute.setOnClickListener(v -> runTranscript(manualInput.getText().toString()));
        page.addView(execute, fullButtonParams());
        spacer(page, 26);

        Button diagnosticsToggle = button("Assistant settings & diagnostics   ▾", 0xFF171717);
        diagnosticsToggle.setBackground(panelShape(0xFF171717, border, 20));
        page.addView(diagnosticsToggle, fullButtonParams());
        spacer(page, 10);
        LinearLayout diagnostics = new LinearLayout(this);
        diagnostics.setOrientation(LinearLayout.VERTICAL);
        diagnostics.setPadding(dp(16), dp(16), dp(16), dp(16));
        diagnostics.setBackground(panelShape(0xFF111111, border, 19));
        diagnostics.setVisibility(View.GONE);
        page.addView(diagnostics, fullButtonParams());
        diagnosticsToggle.setOnClickListener(v -> {
            boolean expand = diagnostics.getVisibility() != View.VISIBLE;
            diagnostics.setVisibility(expand ? View.VISIBLE : View.GONE);
            diagnosticsToggle.setText(expand
                    ? "Hide assistant settings   ▴" : "Assistant settings & diagnostics   ▾");
        });
        serviceLabel = label("Checking local speech services…", 12, muted, false);
        serviceLabel.setGravity(Gravity.START);
        diagnostics.addView(serviceLabel, fullButtonParams());
        spacer(diagnostics, 12);
        Button status = button("Check all systems", 0xFF272727);
        status.setBackground(panelShape(0xFF272727, border, 15));
        status.setOnClickListener(v -> handleCommand(CommandRouter.Action.STATUS, false));
        diagnostics.addView(status, fullButtonParams());
        spacer(diagnostics, 9);
        Button assistant = button("Set as default assistant", 0xFF272727);
        assistant.setBackground(panelShape(0xFF272727, border, 15));
        assistant.setOnClickListener(v -> requestAssistantRole());
        diagnostics.addView(assistant, fullButtonParams());
        spacer(diagnostics, 13);
        TextView disclosure = label(
                "This Android companion supports foreground speech and local commands only. "
                + "It is not connected to a cloud AI model, and it does not listen in the background. "
                + "Your phone's speech/TTS provider may use network services.",
                11, muted, false);
        disclosure.setGravity(Gravity.START);
        disclosure.setLineSpacing(dp(3), 1f);
        diagnostics.addView(disclosure, fullButtonParams());
        spacer(page, 23);
        TextView foot = label("FRIDAY OS  ·  INSPIRED BY MODERN UI EFFECT GALLERIES", 10,
                0xFF848484, false);
        foot.setGravity(Gravity.CENTER);
        page.addView(foot, fullButtonParams());
    }

    private Button effectTile(String text) {
        Button tile = new Button(this);
        tile.setAllCaps(false);
        tile.setGravity(Gravity.TOP | Gravity.START);
        tile.setText(text);
        tile.setTextSize(12);
        tile.setTextColor(0xFFEDEDED);
        tile.setPadding(dp(14), dp(14), dp(11), dp(9));
        tile.setBackground(panelShape(0xFF171717, 0xFF333333, 20));
        return tile;
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
        if (action == CommandRouter.Action.UNKNOWN) {
            String requested = AppCommandParser.requestedApp(normalized);
            if (requested != null) {
                openAppByVoice(requested);
                return;
            }
        }
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
                        + "WiFi, Bluetooth, display, settings, browser, or an installed app. "
                        + "For example, say open WhatsApp or open YouTube. "
                        + "Unsupported device actions are not executed.";
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

    private void openAppByVoice(String appName) {
        List<AppLauncher.Entry> matches = AppLauncher.exactMatches(
                appName, AppLauncher.visibleApps(this));
        if (matches.isEmpty()) {
            showStandby();
            displayReply("I cannot find a launchable app named " + appName
                    + ". Try the installed-app picker or check the name.", true);
            return;
        }
        if (matches.size() > 1) {
            showAppChoice("Choose the application named " + appName, matches);
            return;
        }
        launchSelectedApp(matches.get(0));
    }

    private void launchSelectedApp(AppLauncher.Entry app) {
        try {
            // The resolved, explicit launcher activity is the only destination.
            startActivity(AppLauncher.intentFor(app));
            showStandby();
            displayReply("Opening " + app.label + ".", false);
        } catch (ActivityNotFoundException | SecurityException error) {
            showStandby();
            displayReply("Android could not open " + app.label
                    + ". It may be disabled or blocked by your phone.", true);
        }
    }

    private void showAppChoice(String title, List<AppLauncher.Entry> entries) {
        showStandby();
        String[] names = new String[entries.size()];
        for (int i = 0; i < entries.size(); i++) {
            names[i] = entries.get(i).label + " · " + entries.get(i).packageName;
        }
        new AlertDialog.Builder(this)
                .setTitle(title)
                .setItems(names, (dialog, which) -> launchSelectedApp(entries.get(which)))
                .setNegativeButton("Cancel", null)
                .show();
    }

    private void showInstalledApps() {
        List<AppLauncher.Entry> apps = AppLauncher.visibleApps(this);
        if (apps.isEmpty()) {
            displayReply("Android did not expose any launchable applications.", false);
            return;
        }
        showAppChoice("Select installed application", apps);
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
