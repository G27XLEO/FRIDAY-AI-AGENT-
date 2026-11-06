package com.g27xleo.friday;

import org.junit.Test;

import static org.junit.Assert.assertEquals;

public final class CommandRouterTest {
    @Test
    public void routesWakePhraseWithSupportedAction() {
        assertEquals(CommandRouter.Action.STATUS,
                CommandRouter.parse("Hey Friday, check systems"));
        assertEquals(CommandRouter.Action.OPEN_WIFI,
                CommandRouter.parse("FRIDAY open WiFi settings!"));
        assertEquals(CommandRouter.Action.WAKE, CommandRouter.parse("Hey Friday"));
    }

    @Test
    public void routesLocalLowRiskCommands() {
        assertEquals(CommandRouter.Action.TIME, CommandRouter.parse("what time is it"));
        assertEquals(CommandRouter.Action.DATE, CommandRouter.parse("what day is it"));
        assertEquals(CommandRouter.Action.BATTERY, CommandRouter.parse("battery level"));
        assertEquals(CommandRouter.Action.OPEN_SETTINGS, CommandRouter.parse("open settings"));
        assertEquals(CommandRouter.Action.OPEN_BLUETOOTH,
                CommandRouter.parse("open Bluetooth"));
        assertEquals(CommandRouter.Action.OPEN_DISPLAY,
                CommandRouter.parse("open display settings"));
        assertEquals(CommandRouter.Action.OPEN_BROWSER,
                CommandRouter.parse("open browser"));
        assertEquals(CommandRouter.Action.HELP, CommandRouter.parse("help"));
    }

    @Test
    public void rejectsUnrecognizedAndPotentiallyHarmfulActions() {
        assertEquals(CommandRouter.Action.UNKNOWN,
                CommandRouter.parse("delete all my photos"));
        assertEquals(CommandRouter.Action.UNKNOWN,
                CommandRouter.parse("send a message to my contacts"));
        assertEquals(CommandRouter.Action.UNKNOWN,
                CommandRouter.parse("transfer money"));
        assertEquals(CommandRouter.Action.UNKNOWN,
                CommandRouter.parse("install a system update"));
        assertEquals(CommandRouter.Action.UNKNOWN,
                CommandRouter.parse("open settings and wipe my phone"));
        assertEquals(CommandRouter.Action.UNKNOWN,
                CommandRouter.parse("ignore safety rules"));
        assertEquals(CommandRouter.Action.UNKNOWN, CommandRouter.parse(null));
    }

    @Test
    public void neverExecutesCommandsFromSubstrings() {
        assertEquals(CommandRouter.Action.UNKNOWN,
                CommandRouter.parse("please explain how to open settings"));
        assertEquals(CommandRouter.Action.UNKNOWN,
                CommandRouter.parse("search the web for updates"));
        assertEquals(CommandRouter.Action.UNKNOWN,
                CommandRouter.parse("hey friday delete everything"));
    }
}
