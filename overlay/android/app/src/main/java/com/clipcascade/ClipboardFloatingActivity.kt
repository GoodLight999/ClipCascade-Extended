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
 * Capture launches are serialized by ClipboardCaptureCoordinator.
 */
class ClipboardFloatingActivity : AppCompatActivity() {
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
        if (!completed.compareAndSet(false, true)) return
        var outcome = "capture-empty"
        try {
            val payload = readClipboardPayload()
            if (payload == null) {
                bridge.setValue("clipboard_fallback_status", outcome)
            } else {
                val delivered = PendingReactEventStore.emitOrQueue(
                    applicationContext,
                    currentReactContext(),
                    "onClipboardChange",
                    payload
                )
                outcome = if (delivered) "capture-delivered" else "capture-queued"
                bridge.setValue("clipboard_fallback_status", outcome)
            }
        } catch (security: SecurityException) {
            outcome = "capture-denied"
            bridge.setValue("clipboard_fallback_status", outcome)
        } catch (error: Exception) {
            outcome = "capture-error:${error.javaClass.simpleName}"
            bridge.setValue("clipboard_fallback_status", outcome)
        } finally {
            ClipboardCaptureCoordinator.complete(applicationContext, requestSequence, outcome)
            cleanupOverlay()
            finish()
            overridePendingTransition(0, 0)
        }
    }

    private fun readClipboardPayload(): Map<String, String>? {
        val clip = clipboardManager.primaryClip ?: return null
        if (clip.itemCount <= 0 || clip.description.mimeTypeCount <= 0) return null
        val item = clip.getItemAt(0)
        val mimeType = clip.description.getMimeType(0).orEmpty()
        return when {
            mimeType.startsWith("text/") && item.text != null -> mapOf(
                "content" to item.text.toString(),
                "type" to "text"
            )
            mimeType.startsWith("image/") && item.uri != null -> mapOf(
                "content" to item.uri.toString(),
                "type" to "image"
            )
            item.uri != null -> mapOf(
                "content" to item.uri.toString(),
                "type" to "files"
            )
            else -> null
        }
    }

    private fun currentReactContext(): ReactContext? {
        val manager: ReactInstanceManager =
            (applicationContext as MainApplication).reactNativeHost.reactInstanceManager
        return manager.currentReactContext
    }

    private fun cleanupOverlay() {
        handler.removeCallbacksAndMessages(null)
        floatingView?.let { view ->
            try {
                if (view.isAttachedToWindow) windowManager.removeViewImmediate(view)
            } catch (_: Exception) {
            }
        }
        floatingView = null
    }

    private fun finishCapture(outcome: String) {
        if (completed.compareAndSet(false, true)) {
            ClipboardCaptureCoordinator.complete(applicationContext, requestSequence, outcome)
        }
        cleanupOverlay()
        finish()
        overridePendingTransition(0, 0)
    }

    override fun onDestroy() {
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
