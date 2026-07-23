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

/**
 * One-shot focus bridge for Android 10+ clipboard restrictions.
 * URI bytes are copied into app-owned cache before the bridge loses focus.
 */
class ClipboardFloatingActivity : AppCompatActivity() {
    private val captureStarted = AtomicBoolean(false)
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
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT
            ).apply {
                gravity = Gravity.TOP or Gravity.START
                x = 0
                y = 0
            }
            floatingView = view
            windowManager.addView(view, params)
            view.postDelayed(::captureClipboard, 80L)
            handler.postDelayed(::captureClipboard, 650L)
        } catch (error: Exception) {
            val outcome = "overlay-error:${error.javaClass.simpleName}"
            bridge.setValue("clipboard_fallback_status", outcome)
            finishCapture(outcome)
        }
    }

    private fun captureClipboard() {
        if (!captureStarted.compareAndSet(false, true) || completed.get()) return
        try {
            val containsUri = runCatching {
                val clip = clipboardManager.primaryClip
                clip != null && (0 until clip.itemCount).any { clip.getItemAt(it).uri != null }
            }.getOrDefault(false)
            if (containsUri && requestSequence > 0L) {
                ClipboardCaptureCoordinator.extendForUriStaging(
                    applicationContext,
                    requestSequence
                )
            }

            ClipboardPayloadReader.readOrStage(
                applicationContext,
                clipboardManager
            ) { result ->
                handler.post { finishPayload(result) }
            }
        } catch (security: SecurityException) {
            finishCapture("capture-denied")
        } catch (error: Throwable) {
            finishCapture("capture-error:${error.javaClass.simpleName}:${error.message}".take(300))
        }
    }

    private fun finishPayload(result: Result<Map<String, String>?>) {
        if (completed.get()) return
        result.onSuccess { payload ->
            if (payload == null) {
                finishCapture("capture-empty")
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
            finishCapture(
                "capture-staging-error:${error.javaClass.simpleName}:${error.message}".take(300)
            )
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
