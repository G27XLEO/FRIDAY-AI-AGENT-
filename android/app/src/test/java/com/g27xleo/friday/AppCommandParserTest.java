package com.g27xleo.friday;

import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;

public final class AppCommandParserTest {
    @Test public void acceptsExactEnglishAppRequest() {
        assertEquals("whatsapp", AppCommandParser.requestedApp("Open WhatsApp"));
        assertEquals("youtube", AppCommandParser.requestedApp("Hey Friday, launch YouTube!"));
        assertEquals("instagram", AppCommandParser.requestedApp("open app Instagram"));
        assertEquals("google maps", AppCommandParser.requestedApp("start Google Maps"));
        assertEquals("calculator", AppCommandParser.requestedApp("launch calculator"));
    }

    @Test public void acceptsExplicitHindiMarathiCommands() {
        assertEquals("व्हाट्सएप", AppCommandParser.requestedApp("व्हाट्सएप खोलो"));
        assertEquals("यूट्यूब", AppCommandParser.requestedApp("हे फ्रायडे, यूट्यूब खोलो"));
        assertEquals("व्हॉट्सअॅप", AppCommandParser.requestedApp("व्हॉट्सअॅप उघडा"));
        assertEquals("इंस्टाग्राम", AppCommandParser.requestedApp("इंस्टाग्राम उघडा"));
        assertEquals("स्पॉटिफाई", AppCommandParser.requestedApp("स्पॉटिफाई सुरू करा"));
    }

    @Test public void rejectsCompoundOrUnsafeInstructions() {
        assertNull(AppCommandParser.requestedApp("open whatsapp and send a message"));
        assertNull(AppCommandParser.requestedApp("open youtube then erase data"));
        assertNull(AppCommandParser.requestedApp("व्हाट्सएप खोलो और पैसे भेजो"));
        assertNull(AppCommandParser.requestedApp("यूट्यूब उघडा आणि फोटो काढा"));
        assertNull(AppCommandParser.requestedApp("how can I open whatsapp"));
        assertNull(AppCommandParser.requestedApp("please open my apps"));
        assertNull(AppCommandParser.requestedApp("open"));
        assertNull(AppCommandParser.requestedApp("launch app"));
        assertNull(AppCommandParser.requestedApp(null));
    }

    @Test public void rejectsInjectionLikePackageAndUrls() {
        assertNull(AppCommandParser.requestedApp("open com.example.app;rm -rf"));
        assertNull(AppCommandParser.requestedApp("open https://example.com"));
        assertNull(AppCommandParser.requestedApp("open youtube\nopen banking"));
        assertNull(AppCommandParser.requestedApp("open app"));
    }
}
