package com.g27xleo.friday;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.TextView;
import androidx.webkit.WebViewAssetLoader;

/** Bundled React interface, without a JavaScript-to-Android bridge. */
public final class AgentTeamActivity extends Activity {
    private static final String HOST = "appassets.androidplatform.net";
    private static final String URL = "https://" + HOST + "/assets/friday/index.html";
    private WebView web;
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(0xFF071427);
        try {
            getAssets().open("friday/index.html").close();
        } catch (java.io.IOException missing) {
            TextView label = new TextView(this);
            label.setText("FRIDAY workspace is not bundled. Build using the GitHub Android APK workflow.");
            label.setGravity(Gravity.CENTER);
            label.setTextColor(Color.WHITE);
            label.setTextSize(18);
            setContentView(label);
            return;
        }
        WebViewAssetLoader loader = new WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
            .build();
        web = new WebView(this);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        s.setJavaScriptCanOpenWindowsAutomatically(false);
        web.setBackgroundColor(0xFF061324);
        web.setWebViewClient(new WebViewClient() {
            @Override public WebResourceResponse shouldInterceptRequest(
                    WebView view, WebResourceRequest request) {
                return loader.shouldInterceptRequest(request.getUrl());
            }
            @Override public boolean shouldOverrideUrlLoading(
                    WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if ("https".equals(uri.getScheme()) && HOST.equals(uri.getHost())) return false;
                if ("https".equals(uri.getScheme())) {
                    try { startActivity(new Intent(Intent.ACTION_VIEW, uri)); }
                    catch (ActivityNotFoundException ignored) { }
                }
                return true;
            }
        });
        setContentView(web);
        web.loadUrl(URL);
    }
    @Override public void onBackPressed() {
        if (web != null && web.canGoBack()) web.goBack();
        else super.onBackPressed();
    }
    @Override protected void onDestroy() {
        if (web != null) { web.loadUrl("about:blank"); web.destroy(); web = null; }
        super.onDestroy();
    }
}
