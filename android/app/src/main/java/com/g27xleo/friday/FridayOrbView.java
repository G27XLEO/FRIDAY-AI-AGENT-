package com.g27xleo.friday;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RadialGradient;
import android.graphics.Shader;
import android.graphics.SweepGradient;
import android.os.SystemClock;
import android.view.View;

/**
 * Native, dependency-free fluid orb for Android devices.
 * Waveform/ripples indicate UI state, not actual audio amplitude.
 */
public final class FridayOrbView extends View {
    public enum State { STANDBY, LISTENING, THINKING, SPEAKING, ERROR }

    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private State state = State.STANDBY;
    private boolean running;

    public FridayOrbView(Context context) {
        super(context);
        setContentDescription("FRIDAY voice orb");
    }

    public void setState(State newState) {
        state = newState;
        setContentDescription("FRIDAY orb: " + newState.name().toLowerCase());
        invalidate();
    }

    public void setRunning(boolean value) {
        running = value;
        if (running) invalidate();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        float cx = getWidth() * 0.5f;
        float cy = getHeight() * 0.5f;
        float radius = Math.min(getWidth(), getHeight()) * 0.35f;
        float seconds = (SystemClock.uptimeMillis() % 240000L) / 1000f;
        float speed;
        switch (state) {
            case LISTENING: speed = 1.8f; break;
            case THINKING: speed = 2.8f; break;
            case SPEAKING: speed = 3.6f; break;
            case ERROR: speed = 0.4f; break;
            default: speed = 0.55f;
        }
        float breathe = 1f + 0.035f * (float) Math.sin(seconds * speed * 2f);
        float r = radius * breathe;

        // Light, transparent aura. Does not need hardware microphone.
        paint.setStyle(Paint.Style.FILL);
        paint.setAlpha(170);
        paint.setShader(new RadialGradient(cx, cy, r * 1.7f,
                new int[] { 0x6659D8FF, 0x33774FFF, 0x00734FFF },
                new float[] { 0f, 0.48f, 1f }, Shader.TileMode.CLAMP));
        canvas.drawCircle(cx, cy, r * 1.7f, paint);
        paint.setShader(null);
        paint.setAlpha(255);

        if (state == State.LISTENING || state == State.SPEAKING) {
            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeWidth(dp(1.3f));
            for (int i = 0; i < 2; i++) {
                float fraction = (seconds * 0.55f + i * 0.5f) % 1f;
                paint.setColor(Color.argb((int) (125 * (1f - fraction)), 88, 207, 252));
                canvas.drawCircle(cx, cy, r * (1f + 0.65f * fraction), paint);
            }
            paint.setStyle(Paint.Style.FILL);
        }

        int[] colors = state == State.ERROR
                ? new int[] { 0xFFFF8F8F, 0xFF852B87, 0xFF551164, 0xFFFF8F8F }
                : new int[] {
                    0xFF89F8FF, 0xFF2C83F0, 0xFFB855E8,
                    0xFFEF83E4, 0xFF5271F5, 0xFF89F8FF
                };
        canvas.save();
        canvas.rotate(seconds * speed * 11f, cx, cy);
        paint.setShader(new SweepGradient(cx, cy, colors, null));
        canvas.drawCircle(cx, cy, r, paint);
        paint.setShader(null);
        canvas.restore();

        paint.setShader(new RadialGradient(cx - r * 0.38f, cy - r * 0.46f,
                r * 1.52f,
                new int[] { 0xDDFFFFFF, 0x5577DBFF, 0x00443DF6 },
                new float[] { 0f, 0.38f, 1f }, Shader.TileMode.CLAMP));
        canvas.drawCircle(cx, cy, r, paint);
        paint.setShader(null);

        paint.setStyle(Paint.Style.STROKE);
        paint.setColor(0x7AA0EEFF);
        paint.setStrokeWidth(dp(1f));
        canvas.drawCircle(cx, cy, r, paint);
        paint.setStyle(Paint.Style.FILL);

        if (running && isAttachedToWindow()) {
            postInvalidateDelayed(42);
        }
    }

    private float dp(float size) {
        return size * getResources().getDisplayMetrics().density;
    }
}
