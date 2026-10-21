package com.g27xleo.friday;

import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RadialGradient;
import android.graphics.RectF;
import android.graphics.Shader;
import android.os.SystemClock;
import android.view.View;

/**
 * Dependency-free JARVIS-inspired ARC HUD. Visual state represents the
 * speech recognizer/TTS lifecycle, not measured audio or AI processing.
 * Nothing here captures microphone data or requests extra permissions.
 */
public final class FridayOrbView extends View {
    public enum State { STANDBY, LISTENING, THINKING, SPEAKING, ERROR }

    private final Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
    private State state = State.STANDBY;
    private boolean running;
    private final RectF arc = new RectF();

    public FridayOrbView(Context context) {
        super(context);
        setLayerType(View.LAYER_TYPE_SOFTWARE, null);
        setContentDescription("FRIDAY holographic reactor interface, standby");
    }

    public void setState(State next) {
        state = next;
        setContentDescription("FRIDAY reactor: " + next.name().toLowerCase());
        invalidate();
    }

    public void setRunning(boolean value) {
        running = value;
        if (running) invalidate();
    }

    @Override protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        float cx = getWidth() / 2f;
        float cy = getHeight() / 2f;
        float u = Math.min(getWidth(), getHeight()) / 2f;
        float sec = SystemClock.uptimeMillis() / 1000f;
        float speed = state == State.THINKING ? 1.65f
                : state == State.LISTENING ? 1.3f
                : state == State.SPEAKING ? 2.0f
                : state == State.ERROR ? 0.2f : 0.45f;
        int cyan = state == State.ERROR ? 0xFFFF856E : 0xFF5BEBFF;
        int accent = state == State.ERROR ? 0xFFEF7159
                : state == State.SPEAKING ? 0xFFFFCB82 : 0xFF3EA8E1;
        float pulse = 1f + 0.016f * (float) Math.sin(sec * speed * 2.8);

        p.setStyle(Paint.Style.FILL);
        p.setShader(new RadialGradient(cx, cy, u * 0.92f,
                new int[] {0x2221D4F5, 0x0920BFE4, 0x00000000},
                new float[] {0f, 0.49f, 1f}, Shader.TileMode.CLAMP));
        canvas.drawCircle(cx, cy, u * .95f, p);
        p.setShader(null);

        // Concentric dashboard circles and orbital ruler.
        stroke(0x263A8AA4, dp(1));
        canvas.drawCircle(cx, cy, u * .91f, p);
        stroke(0x284AB3D1, dp(.7f));
        canvas.drawCircle(cx, cy, u * .78f, p);
        stroke(0x8046B9D9, dp(.9f));
        canvas.drawCircle(cx, cy, u * .65f, p);
        stroke(0x5552D3EF, dp(1));
        canvas.drawCircle(cx, cy, u * .48f, p);

        // 72 measured angular ticks. Four cardinals carry longer markers.
        for (int i = 0; i < 72; i++) {
            double angle = Math.PI * (i / 36.0 - 0.5);
            float x = (float) Math.cos(angle), y = (float) Math.sin(angle);
            boolean major = i % 9 == 0;
            float start = u * (major ? .84f : .865f);
            float end = u * (major ? .93f : .90f);
            stroke(major ? cyan : 0x66539AB9, dp(major ? 1.5f : .8f));
            canvas.drawLine(cx + x * start, cy + y * start,
                    cx + x * end, cy + y * end, p);
        }

        // Slow counter-rotating segmented scanning rings.
        arc.set(cx - u * .74f, cy - u * .74f, cx + u * .74f, cy + u * .74f);
        stroke(cyan, dp(2.5f));
        canvas.save();
        canvas.rotate(sec * speed * 17f, cx, cy);
        canvas.drawArc(arc, -86, 67, false, p);
        canvas.drawArc(arc, 39, 38, false, p);
        canvas.drawArc(arc, 151, 77, false, p);
        canvas.drawArc(arc, 259, 17, false, p);
        canvas.restore();

        arc.set(cx - u * .57f, cy - u * .57f, cx + u * .57f, cy + u * .57f);
        stroke(accent, dp(3.2f));
        canvas.save();
        canvas.rotate(-sec * speed * 29f, cx, cy);
        canvas.drawArc(arc, 4, 86, false, p);
        canvas.drawArc(arc, 136, 35, false, p);
        canvas.drawArc(arc, 239, 65, false, p);
        canvas.restore();

        // Inner breathing reactor core.
        p.setStyle(Paint.Style.FILL);
        p.setShader(new RadialGradient(cx - u * .05f, cy - u * .07f, u * .41f,
                state == State.ERROR
                        ? new int[] {0xF99A6252, 0xBB562728, 0x170A1E28}
                        : new int[] {0xDD9CF7FF, 0xBD1C8BAE, 0x15124465},
                new float[] {0f, .37f, 1f}, Shader.TileMode.CLAMP));
        canvas.drawCircle(cx, cy, u * .395f * pulse, p);
        p.setShader(null);
        stroke(cyan, dp(1.9f));
        canvas.drawCircle(cx, cy, u * .39f * pulse, p);

        stroke(0x885DEDF8, dp(1));
        canvas.drawCircle(cx, cy, u * .295f, p);
        p.setStyle(Paint.Style.FILL);
        p.setColor(0xFFF4FFFF);
        p.setTypeface(android.graphics.Typeface.create(
                "sans-serif-light", android.graphics.Typeface.NORMAL));
        p.setTextAlign(Paint.Align.CENTER);
        p.setTextSize(u * .36f);
        canvas.drawText("F", cx, cy + u * .13f, p);

        // HUD azimuth guides.
        stroke(0x754AA5BE, dp(1f));
        canvas.drawLine(cx - u*.94f, cy, cx - u*.8f, cy, p);
        canvas.drawLine(cx + u*.8f, cy, cx + u*.94f, cy, p);
        canvas.drawLine(cx, cy - u*.94f, cx, cy - u*.8f, p);
        canvas.drawLine(cx, cy + u*.8f, cx, cy + u*.94f, p);
        p.setStyle(Paint.Style.FILL);
        p.setColor(accent);
        canvas.drawCircle(cx + u*.78f, cy, dp(2.4f), p);
        canvas.drawCircle(cx - u*.78f, cy, dp(2.4f), p);

        if (state == State.LISTENING || state == State.SPEAKING) {
            float wave = (sec * .6f) % 1f;
            stroke(Color.argb((int)(115*(1f-wave)), 90, 227, 255), dp(1.25f));
            canvas.drawCircle(cx, cy, u * (.47f + wave * .32f), p);
        }
        if (running && isAttachedToWindow() && ValueAnimator.areAnimatorsEnabled()) {
            postInvalidateDelayed(33);
        }
    }

    private void stroke(int color, float width) {
        p.setShader(null);
        p.setColor(color);
        p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(width);
        p.setStrokeCap(Paint.Cap.ROUND);
    }

    private float dp(float value) {
        return value * getResources().getDisplayMetrics().density;
    }
}
