package com.g27xleo.friday;

import java.text.Normalizer;
import java.util.Locale;

/**
 * Conservative offline command parser for English, Hindi and Marathi.
 * Exact allowlisted utterances and a small set of polite variants only.
 * This is not a general-purpose NLP model or arbitrary device executor.
 */
public final class CommandRouter {
    public enum Action {
        WAKE, HELP, STATUS, TIME, DATE, BATTERY,
        OPEN_SETTINGS, OPEN_WIFI, OPEN_BLUETOOTH, OPEN_DISPLAY,
        OPEN_BROWSER, UNKNOWN
    }

    private CommandRouter() { }

    public static Action parse(String spoken) {
        if (spoken == null) return Action.UNKNOWN;
        String text = Normalizer.normalize(spoken, Normalizer.Form.NFC)
                .trim().toLowerCase(Locale.ROOT)
                .replaceAll("[!?.,।॥]+$", "")
                .replaceAll("\\s+", " ");
        for (String wake : new String[] {
                "hey friday", "ok friday", "friday",
                "हे फ्रायडे", "फ्रायडे", "हे फ्राइडे", "फ्राइडे",
        }) {
            if (text.equals(wake) || text.startsWith(wake + " ")
                    || text.startsWith(wake + ",")) {
                text = text.substring(wake.length()).trim();
                text = text.replaceFirst("^[,.:!?।॥;\\s]+", "");
                break;
            }
        }
        if (text.isEmpty()) return Action.WAKE;

        if (matches(text, "help", "what can you do", "show commands", "commands",
                "मदद", "क्या कर सकते हो", "कमांड दिखाओ",
                "मदत", "काय करू शकतेस", "कमांड दाखवा"))
            return Action.HELP;

        if (matches(text, "check systems", "system check", "check status", "status",
                "are you operational", "system status",
                "सिस्टम चेक करो", "सिस्टम की स्थिति बताओ", "सिस्टम की जांच करो",
                "सिस्टम तपासा", "सिस्टमची स्थिती सांगा", "सिस्टीम तपासा"))
            return Action.STATUS;

        if (matches(text, "time", "what time is it", "what's the time",
                "tell me the time", "current time",
                "समय बताओ", "अभी कितने बजे हैं", "क्या समय हुआ है",
                "वेळ सांगा", "आता किती वाजले", "किती वाजले"))
            return Action.TIME;

        if (matches(text, "date", "what is the date", "what's the date",
                "what day is it", "today's date",
                "आज की तारीख बताओ", "आज कौन सा दिन है", "तारीख बताओ",
                "आजची तारीख सांगा", "आज कोणता वार आहे", "तारीख सांगा"))
            return Action.DATE;

        if (matches(text, "battery", "check battery", "battery level", "battery status",
                "what is my battery", "how much battery",
                "बैटरी कितनी है", "बैटरी स्तर बताओ", "बैटरी चेक करो",
                "बॅटरी किती आहे", "बॅटरी तपासा", "बॅटरीची स्थिती सांगा"))
            return Action.BATTERY;

        if (matches(text, "open wifi", "open wi fi", "open wifi settings",
                "open wi fi settings", "wifi settings", "wi fi settings",
                "वाईफाई खोलो", "वाई फाई सेटिंग खोलो", "वाईफाई सेटिंग खोलो",
                "वायफाय उघडा", "वायफाय सेटिंग उघडा", "वायफाय सेटिंग्ज उघडा"))
            return Action.OPEN_WIFI;

        if (matches(text, "open bluetooth", "open bluetooth settings",
                "bluetooth settings", "ब्लूटूथ खोलो", "ब्लूटूथ सेटिंग खोलो",
                "ब्लूटूथ उघडा", "ब्लूटूथ सेटिंग्ज उघडा"))
            return Action.OPEN_BLUETOOTH;

        if (matches(text, "open display settings", "display settings",
                "डिस्प्ले सेटिंग खोलो", "डिस्प्ले सेटिंग्ज उघडा"))
            return Action.OPEN_DISPLAY;

        if (matches(text, "open settings", "show settings", "phone settings",
                "सेटिंग खोलो", "फोन की सेटिंग खोलो",
                "सेटिंग्ज उघडा", "फोन सेटिंग्ज उघडा"))
            return Action.OPEN_SETTINGS;

        if (matches(text, "open browser", "open the browser", "browse the web",
                "ब्राउज़र खोलो", "ब्राउझर उघडा"))
            return Action.OPEN_BROWSER;

        return Action.UNKNOWN;
    }

    private static boolean matches(String value, String... utterances) {
        for (String item : utterances) {
            if (item.equals(value)) return true;
        }
        return false;
    }
}
