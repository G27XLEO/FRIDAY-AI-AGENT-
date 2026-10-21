package com.g27xleo.friday;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;

import java.text.Normalizer;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/**
 * Discovers only foreground launchable activities visible to the requesting
 * Android application. No QUERY_ALL_PACKAGES, shell, accessibility, or
 * privileged APIs. An app is launched only after an exact name/alias match
 * or an explicit user selection from the list.
 */
public final class AppLauncher {
    public static final class Entry {
        public final String label;
        public final String packageName;
        public final String activityName;

        Entry(String label, String packageName, String activityName) {
            this.label = label;
            this.packageName = packageName;
            this.activityName = activityName;
        }
    }

    private AppLauncher() { }

    public static List<Entry> visibleApps(Context context) {
        PackageManager pm = context.getPackageManager();
        Intent query = new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER);
        List<ResolveInfo> handlers = pm.queryIntentActivities(query, 0);
        List<Entry> result = new ArrayList<>();
        Set<String> seen = new HashSet<>();
        for (ResolveInfo info : handlers) {
            if (info.activityInfo == null || !info.activityInfo.exported) continue;
            String pkg = info.activityInfo.packageName;
            String activity = info.activityInfo.name;
            if (pkg == null || activity == null || pkg.equals(context.getPackageName())) continue;
            CharSequence loaded = info.loadLabel(pm);
            String label = loaded == null ? "" : loaded.toString().trim();
            if (label.isEmpty()) continue;
            if (seen.add(pkg + "/" + activity)) result.add(new Entry(label, pkg, activity));
        }
        Collections.sort(result, (a, b) -> {
            int byLabel = a.label.compareToIgnoreCase(b.label);
            return byLabel != 0 ? byLabel : a.packageName.compareTo(b.packageName);
        });
        return result;
    }

    private static String normalizeName(String name) {
        return Normalizer.normalize(name, Normalizer.Form.NFC)
                .trim().toLowerCase(Locale.ROOT).replaceAll("\\s+", " ")
                .replaceFirst(" (app|application)$", "");
    }

    public static List<Entry> exactMatches(String requested, List<Entry> apps) {
        String key = normalizeName(requested);
        String knownPkg = knownPackage(key);
        List<Entry> matched = new ArrayList<>();
        for (Entry entry : apps) {
            if (normalizeName(entry.label).equals(key)
                    || (knownPkg != null && entry.packageName.equals(knownPkg))) {
                matched.add(entry);
            }
        }
        return matched;
    }

    private static String knownPackage(String name) {
        switch (name) {
            case "whatsapp":
            case "व्हाट्सएप":
            case "व्हॉट्सअॅप":
                return "com.whatsapp";
            case "youtube":
            case "you tube":
            case "यूट्यूब":
                return "com.google.android.youtube";
            case "chrome":
            case "क्रोम":
                return "com.android.chrome";
            case "instagram":
            case "इंस्टाग्राम":
                return "com.instagram.android";
            case "telegram":
            case "टेलीग्राम":
            case "टेलिग्राम":
                return "org.telegram.messenger";
            case "gmail":
            case "जीमेल":
                return "com.google.android.gm";
            case "google maps":
            case "maps":
            case "गूगल मैप्स":
                return "com.google.android.apps.maps";
            case "spotify":
            case "स्पॉटिफाई":
                return "com.spotify.music";
            default:
                return null;
        }
    }

    public static Intent intentFor(Entry entry) {
        return new Intent(Intent.ACTION_MAIN)
                .addCategory(Intent.CATEGORY_LAUNCHER)
                .setComponent(new ComponentName(entry.packageName, entry.activityName))
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
    }
}
