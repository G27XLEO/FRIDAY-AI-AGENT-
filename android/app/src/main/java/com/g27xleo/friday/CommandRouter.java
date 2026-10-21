package com.g27xleo.friday;

import java.util.Locale;

/**
 * Deterministic, offline routing for a small allow-list of explicit commands.
 * This is NOT an LLM and must never claim to understand arbitrary instructions.
 */
public final class CommandRouter {
    public enum Action {
        WAKE, HELP, STATUS, TIME, DATE, BATTERY,
        OPEN_SETTINGS, OPEN_WIFI, OPEN_BLUETOOTH, OPEN_DISPLAY,
        OPEN_BROWSER, UNKNOWN
    }

    private CommandRouter() { }

    public static Action parse(String spoken) {
        if (spoken == null) {
            return Action.UNKNOWN;
        }
        String text = spoken.trim().toLowerCase(Locale.ROOT)
                .replaceAll("[!?.,]+$", "")
                .replaceAll("\\s+", " ");
        if (text.startsWith("hey friday")) {
            text = text.substring("hey friday".length()).trim();
        } else if (text.startsWith("ok friday")) {
            text = text.substring("ok friday".length()).trim();
        } else if (text.startsWith("friday")) {
            text = text.substring("friday".length()).trim();
        }
        // Recognizers often add punctuation after a wake phrase.
        text = text.replaceFirst("^[,.:!?;\\s]+", "");
        if (text.isEmpty()) {
            return Action.WAKE;
        }
        if (matches(text, "help", "what can you do", "show commands", "commands")) {
            return Action.HELP;
        }
        if (matches(text, "check systems", "system check", "check status", "status",
                "are you operational", "system status")) {
            return Action.STATUS;
        }
        if (matches(text, "time", "what time is it", "what's the time",
                "tell me the time", "current time")) {
            return Action.TIME;
        }
        if (matches(text, "date", "what is the date", "what's the date",
                "what day is it", "today's date")) {
            return Action.DATE;
        }
        if (matches(text, "battery", "check battery", "battery level", "battery status",
                "what is my battery", "how much battery")) {
            return Action.BATTERY;
        }
        if (matches(text, "open wifi", "open wi fi", "open wifi settings",
                "open wi fi settings", "wifi settings", "wi fi settings")) {
            return Action.OPEN_WIFI;
        }
        if (matches(text, "open bluetooth", "open bluetooth settings",
                "bluetooth settings")) {
            return Action.OPEN_BLUETOOTH;
        }
        if (matches(text, "open display settings", "display settings")) {
            return Action.OPEN_DISPLAY;
        }
        if (matches(text, "open settings", "show settings", "phone settings")) {
            return Action.OPEN_SETTINGS;
        }
        if (matches(text, "open browser", "open the browser", "browse the web")) {
            return Action.OPEN_BROWSER;
        }
        return Action.UNKNOWN;
    }

    private static boolean matches(String value, String... candidates) {
        for (String candidate : candidates) {
            if (candidate.equals(value)) {
                return true;
            }
        }
        return false;
    }
}
