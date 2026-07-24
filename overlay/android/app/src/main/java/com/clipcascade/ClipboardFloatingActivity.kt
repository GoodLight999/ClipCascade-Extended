package com.clipcascade

import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.graphics.PixelFormat
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import androidx.appcompat.app.AppCompatActivity
import com.facebook.react.ReactInstanceManager
import com.facebook.react.bridge.ReactContext
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger

/**
 * One-shot focus bridge for Android 10+ clipboard restrictions.
 * URI bytes are copied into app-owned cache before the bridge loses focus.
 */
class ClipboardFloatingActivity : AppCompatActivity() {
    private val captureInProgress = AtomicBoolean(false)
    private val captureAttempts = AtomicInteger(0)
    private val completed = AtomicBoolean(false)
    private val handler = Handler(Looper.getMainLooper())
    private lateinit var windowManager: WindowManager
    private lateinit var clipboardManager: ClipboardManager
    private var floatingView: View? = null
    private var requestSequence: Long = 0L
    private val bridge by lazy { AsyncStorageBridge(applicationContext) }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        overridePendingTransition(0, 0)
        requestSequence = intent.getLongExtra(EXTRA_REQUEST_SEQUENCE, 0L)
        clipboardManager = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        windowManager = getSystemService(Context.WINDOW_SERVICE) as WindowManager

        if (!Settings.canDrawOverlays(this)) {
            bridge.setValue("clipboard_fallback_status", "capture-blocked;overlay-missing")
            finishCapture("capture-blocked;overlay-missing")
            return
        }

        try {
            val view = View(this)
            val params = WindowManager.LayoutParams(
                1,
                1,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE or
                    WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT
            ).apply {
                gravity = Gravity.TOP or Gravity.START
                x = 0
                y = 0
            }
            floatingView = view
            windowManager.addView(view, params)
            // The Activity/overlay is user-visible at this point, so a requested dead
            // foreground runtime can be recovered without an arbitrary background launch.
            ForegroundRuntimeRecovery.startIfRequested(this, "clipboard-overlay")
            view.postDelayed(::captureClipboard, INITIAL_CAPTURE_DELAY_MS)
            // OEMs can attach the overlay view late. This backup only starts a read when
            // no earlier read is running; a transient empty/denied first read is retried below.
            handler.postDelayed(::captureClipboard, START_FALLBACK_DELAY_MS)
        } catch (error: Exception) {
            val outcome = "overlay-error:${error.javaClass.simpleName}"
            bridge.setValue("clipboard_fallback_status", outcome)
            finishCapture(outcome)
        }
    }

    private fun captureClipboard() {
        if (completed.get() || !captureInProgress.compareAndSet(false, true)) return
        val attempt = captureAttempts.incrementAndGet()
        try {
            ClipboardPayloadReader.readOrStage(
                applicationContext,
                clipboardManager,
                onUriStagingStarted = {
                    if (requestSequence > 0L) {
                        ClipboardCaptureCoordinator.extendForUriStaging(
                            applicationContext,
                            requestSequence
                        )
                    }
                }
            ) { result ->
                handler.post { finishPayload(result, attempt) }
            }
        } catch (security: SecurityException) {
            retryOrFinishCapture(attempt, "capture-denied")
        } catch (error: Throwable) {
            finishCapture("capture-error:${error.javaClass.simpleName}:${error.message}".take(300))
        }
    }

    private fun finishPayload(result: Result<Map<String, String>?>, attempt: Int) {
        if (completed.get()) return
        result.onSuccess { payload ->
            if (payload == null) {
                retryOrFinishCapture(attempt, "capture-empty")
                return
            }
            val delivered = PendingReactEventStore.emitOrQueue(
                applicationContext,
                currentReactContext(),
                "onClipboardChange",
                payload
            )
            val type = payload["type"].orEmpty()
            finishCapture(
                if (delivered) "capture-delivered:$type" else "capture-queued:$type"
            )
        }.onFailure { error ->
            val outcome =
                "capture-staging-error:${error.javaClass.simpleName}:${error.message}".take(300)
            if (error is SecurityException) {
                retryOrFinishCapture(attempt, "capture-denied")
            } else {
                finishCapture(outcome)
            }
        }
    }

    private fun retryOrFinishCapture(attempt: Int, outcome: String) {
        if (completed.get()) return
        if (ClipboardCaptureRetryPolicy.canRetry(attempt)) {
            bridge.setValue(
                "clipboard_fallback_status",
                "$outcome;retry-scheduled:${attempt + 1}"
            )
            captureInProgress.set(false)
            handler.postDelayed(
                ::captureClipboard,
                ClipboardCaptureRetryPolicy.RETRY_DELAY_MS
            )
        } else {
            finishCapture("$outcome;attempts:$attempt")
        }
    }

    private fun currentReactContext(): ReactContext? {
        val manager: ReactInstanceManager =
            (applicationContext as MainApplication).reactNativeHost.reactInstanceManager
        return manager.currentReactContext
    }

    private fun cleanupOverlay() {
        handler.removeCallbacksAndMessages(null)
        if (::windowManager.isInitialized) {
            floatingView?.let { view ->
                try {
                    if (view.isAttachedToWindow) windowManager.removeViewImmediate(view)
                } catch (_: Exception) {
                }
            }
        }
        floatingView = null
    }

    private fun finishCapture(outcome: String) {
        if (!completed.compareAndSet(false, true)) return
        bridge.setValue("clipboard_fallback_status", outcome)
        if (requestSequence > 0L) {
            ClipboardCaptureCoordinator.complete(applicationContext, requestSequence, outcome)
        }
        cleanupOverlay()
        finish()
        overridePendingTransition(0, 0)
    }

    override fun onDestroy() {
        if (completed.compareAndSet(false, true) && requestSequence > 0L) {
            ClipboardCaptureCoordinator.fail(
                applicationContext,
                requestSequence,
                "activity-destroyed-before-capture"
            )
        }
        cleanupOverlay()
        super.onDestroy()
    }

    companion object {
        private const val EXTRA_REQUEST_SEQUENCE = "capture_request_sequence"
        private const val INITIAL_CAPTURE_DELAY_MS = 120L
        private const val START_FALLBACK_DELAY_MS = 700L

        fun getIntent(context: Context, requestSequence: Long = 0L): Intent =
            Intent(context.applicationContext, ClipboardFloatingActivity::class.java).apply {
                putExtra(EXTRA_REQUEST_SEQUENCE, requestSequence)
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or
                    Intent.FLAG_ACTIVITY_NO_HISTORY or
                    Intent.FLAG_ACTIVITY_EXCLUDE_FROM_RECENTS or
                    Intent.FLAG_ACTIVITY_NO_ANIMATION
            }
    }
}
