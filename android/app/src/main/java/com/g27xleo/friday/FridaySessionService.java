package com.g27xleo.friday;

import android.content.Intent;
import android.os.Bundle;
import android.service.voice.VoiceInteractionSession;
import android.service.voice.VoiceInteractionSessionService;
import android.view.View;
import android.widget.Button;

/**
 * When Android invokes FRIDAY as the selected assistant, launch the visible
 * voice-control activity. Do not start invisible background recordings.
 */
public class FridaySessionService extends VoiceInteractionSessionService {
    @Override
    public VoiceInteractionSession onNewSession(Bundle args) {
        return new FridaySession();
    }

    private final class FridaySession extends VoiceInteractionSession {
        FridaySession() {
            super(FridaySessionService.this);
        }

        @Override
        public View onCreateContentView() {
            Button open = new Button(FridaySessionService.this);
            open.setText("Open FRIDAY voice controls");
            open.setOnClickListener(view -> openVisibleActivity());
            return open;
        }

        @Override
        public void onShow(Bundle args, int showFlags) {
            super.onShow(args, showFlags);
            // Keep a clickable fallback for OEMs that reject assistant activity starts.
            openVisibleActivity();
        }

        private void openVisibleActivity() {
            try {
                Intent intent = new Intent(FridaySessionService.this, MainActivity.class);
                intent.putExtra(MainActivity.EXTRA_AUTO_LISTEN, true);
                startAssistantActivity(intent);
                finish();
            } catch (SecurityException | IllegalStateException ignored) {
                // Keep the fallback button visible. No background actions.
            }
        }
    }
}
