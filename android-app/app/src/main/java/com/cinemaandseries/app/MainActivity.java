package com.cinemaandseries.app;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.CookieManager;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

public class MainActivity extends Activity {
    private static final String APP_HOST = "cinema-and-series.rayadinaveen98.workers.dev";
    private static final String HOME_URL = "https://" + APP_HOST + "/#/";
    // A cancelable event lets the React detail dialog or filter panel handle Back
    // synchronously before WebView walks the hash-router history stack.
    // No exposed JavascriptInterface: external pages cannot invoke native APIs.
    private static final String WEB_BACK_EVENT =
        "(function(){var e=new Event('cinema-android-back',{cancelable:true});"
            + "document.dispatchEvent(e);return e.defaultPrevented;})()";

    private WebView webView;
    private ProgressBar loadProgress;
    private View retryScreen;
    private boolean mainFrameFailed;
    private boolean backPending;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        getWindow().setStatusBarColor(Color.BLACK);
        getWindow().setNavigationBarColor(Color.BLACK);
        getWindow().getDecorView().setSystemUiVisibility(0);

        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.BLACK);
        webView = new WebView(this);
        webView.setBackgroundColor(Color.BLACK);
        root.addView(webView, new FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        loadProgress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        loadProgress.setMax(100);
        loadProgress.setProgressTintList(ColorStateList.valueOf(Color.WHITE));
        loadProgress.setProgressBackgroundTintList(ColorStateList.valueOf(Color.TRANSPARENT));
        FrameLayout.LayoutParams bar = new FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, dp(2), Gravity.TOP);
        root.addView(loadProgress, bar);
        loadProgress.setVisibility(View.GONE);

        LinearLayout offline = new LinearLayout(this);
        offline.setOrientation(LinearLayout.VERTICAL);
        offline.setGravity(Gravity.CENTER);
        offline.setBackgroundColor(Color.BLACK);
        TextView message = new TextView(this);
        message.setText("Couldn't connect");
        message.setTextColor(Color.WHITE);
        message.setTextSize(18);
        offline.addView(message);
        Button retry = new Button(this);
        retry.setText("Retry");
        LinearLayout.LayoutParams retryParams = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        retryParams.topMargin = dp(12);
        offline.addView(retry, retryParams);
        retryScreen = offline;
        root.addView(retryScreen, new FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        retryScreen.setVisibility(View.GONE);
        retry.setOnClickListener(view -> {
            mainFrameFailed = false;
            retryScreen.setVisibility(View.GONE);
            loadProgress.setVisibility(View.VISIBLE);
            webView.reload();
        });
        setContentView(root);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setUserAgentString(settings.getUserAgentString() + " CinemaAndSeriesAndroid/1.2");

        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, false);

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onProgressChanged(WebView view, int progress) {
                loadProgress.setProgress(progress);
            }
        });
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                if (!request.isForMainFrame()) return false;
                Uri uri = request.getUrl();
                if (isAppUrl(uri)) return false;
                if (uri != null && ("https".equalsIgnoreCase(uri.getScheme())
                        || "http".equalsIgnoreCase(uri.getScheme()))) {
                    try {
                        startActivity(new Intent(Intent.ACTION_VIEW, uri));
                    } catch (ActivityNotFoundException error) {
                        // Nothing installed to handle the link: keep the current page.
                    }
                }
                // Never navigate external/untrusted schemes inside the privileged WebView.
                return true;
            }

            @Override
            public void onPageStarted(WebView view, String url, Bitmap favicon) {
                mainFrameFailed = false;
                retryScreen.setVisibility(View.GONE);
                loadProgress.setProgress(0);
                loadProgress.setVisibility(View.VISIBLE);
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                loadProgress.setVisibility(View.GONE);
                if (mainFrameFailed) retryScreen.setVisibility(View.VISIBLE);
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) showLoadFailure();
            }

            @Override
            public void onReceivedHttpError(WebView view, WebResourceRequest request, WebResourceResponse response) {
                if (request.isForMainFrame() && response.getStatusCode() >= 400) showLoadFailure();
            }
        });

        if (savedInstanceState == null || webView.restoreState(savedInstanceState) == null) {
            webView.loadUrl(HOME_URL);
        }
    }

    private int dp(int pixels) {
        return Math.round(pixels * getResources().getDisplayMetrics().density);
    }

    private static boolean isAppUrl(Uri uri) {
        return uri != null && "https".equalsIgnoreCase(uri.getScheme())
            && APP_HOST.equalsIgnoreCase(uri.getHost());
    }

    private void showLoadFailure() {
        mainFrameFailed = true;
        loadProgress.setVisibility(View.GONE);
        retryScreen.setVisibility(View.VISIBLE);
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        if (webView != null) webView.saveState(outState);
        super.onSaveInstanceState(outState);
    }

    private void backThroughHistoryOrFinish() {
        if (webView != null && webView.canGoBack()) webView.goBack();
        else finish();
    }

    @Override
    public void onBackPressed() {
        if (backPending) return;
        if (webView == null || retryScreen.getVisibility() == View.VISIBLE
                || !isAppUrl(Uri.parse(webView.getUrl() == null ? "" : webView.getUrl()))) {
            backThroughHistoryOrFinish();
            return;
        }
        backPending = true;
        webView.evaluateJavascript(WEB_BACK_EVENT, result -> {
            backPending = false;
            if (isFinishing() || webView == null) return;
            if (!"true".equals(result)) backThroughHistoryOrFinish();
        });
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.stopLoading();
            webView.setWebViewClient(null);
            webView.setWebChromeClient(null);
            ((ViewGroup) webView.getParent()).removeView(webView);
            webView.destroy();
            webView = null;
        }
        super.onDestroy();
    }
}
