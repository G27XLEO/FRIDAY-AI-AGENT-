package com.g27xleo.friday;

import java.text.Normalizer;
import java.util.Locale;

/**
 * Extracts only explicit, single-app launch requests in en/hi/mr.
 * The target is NOT a package name or an Intent. Callers must resolve it
 * against user-visible launchable apps on the device by exact label/alias.
 */
public final class AppCommandParser {
    private AppCommandParser() { }

    public static String requestedApp(String utterance) {
        if (utterance == null || utterance.indexOf('\n') >= 0 || utterance.indexOf('\r') >= 0) return null;
        String text = Normalizer.normalize(utterance, Normalizer.Form.NFC)
                .trim().toLowerCase(Locale.ROOT)
                .replaceAll("[!?.,।॥]+$", "")
                .replaceAll("\\s+", " ");
        if (text.length() > 90 || text.indexOf('\n') >= 0) return null;

        for (String wake : new String[] {
                "hey friday", "ok friday", "friday", "हे फ्रायडे",
                "फ्रायडे", "हे फ्राइडे", "फ्राइडे",
        }) {
            if (text.equals(wake) || text.startsWith(wake + " ")
                    || text.startsWith(wake + ",")) {
                text = text.substring(wake.length()).trim()
                        .replaceFirst("^[,.:!?।॥;\\s]+", "");
                break;
            }
        }

        String app = null;
        for (String prefix : new String[] {
                "open the app ", "launch the app ", "start the app ",
                "open app ", "launch app ", "start app ",
                "open ", "launch ", "start ",
                "खोलो ", "खोलिए ", "ओपन ", "चालू करो ",
                "उघडा ", "उघड ", "सुरू करा ", "चालू करा ",
        }) {
            if (text.startsWith(prefix)) {
                app = text.substring(prefix.length()).trim();
                break;
            }
        }
        if (app == null) {
            for (String suffix : new String[] {
                    " ऐप खोलो", " एप खोलो", " खोलो", " खोलिए",
                    " अॅप उघडा", " ॲप उघडा", " उघडा", " उघड", " सुरू करा",
            }) {
                if (text.endsWith(suffix)) {
                    app = text.substring(0, text.length() - suffix.length()).trim();
                    break;
                }
            }
        }
        if (app == null || app.isEmpty() || app.length() > 56
                || !app.matches("[\\p{L}\\p{M}\\p{N}][\\p{L}\\p{M}\\p{N} ._'-]*")) {
            return null;
        }

        // Do not interpret compound sentences or instructions as app names.
        for (String forbidden : new String[] {
                " and ", " then ", " after ", " while ", " or ",
                " और ", " फिर ", " तथा ", " आणि ", " मग ", " किंवा ",
        }) {
            if ((" " + app + " ").contains(forbidden)) return null;
        }
        return app.equals("app") || app.equals("application") ? null : app;
    }
}
