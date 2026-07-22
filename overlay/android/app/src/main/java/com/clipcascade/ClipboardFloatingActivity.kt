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
 * A one-shot focus bridge for Android 10+ clipboard restrictions.
 *
 * Unlike the upstream activity, this never uses FLAG_ACTIVITY_CLEAR_TASK and
 * never assumes React Native is already alive. Captured data is queued when
 * necessary and delivered when the foreground service becomes ready.
 */
class ClipboardFloatingActivity : AppCompatActivity() {
    private val completed = AtomicBoolean(false)
    private val handler = Handler(Looper.getMainLooper())
    private lateinit var windowManager: WindowManager
    private lateinit var clipboardManager: ClipboardManager
    private var floatingView: View? = null
    private val bridge by lazy { AsyncStorageBridge(applicationContext) }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        overridePendingTransition(0, 0)
        clipboardManager = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        windowManager = getSystemService(Context.WINDOW_SERVICE) as WindowManager

        if (!Settings.canDrawOverlays(this)) {
            bridge.setValue("clipboard_fallback_status", "capture-blocked;overlay-missing")
            finishCapture()
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
            view.postDelayed(::captureClipboard, 60L)
            handler.postDelayed(::captureClipboard, 500L)
        } catch (error: Exception) {
            bridge.setValue(
                "clipboard_fallback_status",
                "overlay-error:${error.javaClass.simpleName}"
            )
            finishCapture()
        }
    }

    private fun captureClipboard() {
        if (!completed.compareAndSet(false, true)) return
        try {
            val payload = readClipboardPayload()
            if (payload == null) {
                bridge.setValue("clipboard_fallback_status", "capture-empty")
            } else {
                val delivered = PendingReactEventStore.emitOrQueue(
                    applicationContext,
                    currentReactContext(),
                    "onClipboardChange",
                    payload
                )
                bridge.setValue(
                    "clipboard_fallback_status",
                    if (delivered) "capture-delivered" else "capture-queued"
                )
            }
        } catch (security: SecurityException) {
            bridge.setValue("clipboard_fallback_status", "capture-denied")
        } catch (error: Exception) {
            bridge.setValue(
                "clipboard_fallback_status",
                "capture-error:${error.javaClass.simpleName}"
            )
        } finally {
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
                if (view.isAttachedToWindow) {
                    windowManager.removeViewImmediate(view)
                }
            } catch (_: Exception) {
            }
        }
        floatingView = null
    }

    private fun finishCapture() {
        completed.set(true)
        cleanupOverlay()
        finish()
        overridePendingTransition(0, 0)
    }

    override fun onDestroy() {
        cleanupOverlay()
        super.onDestroy()
    }

    companion object {
        fun getIntent(context: Context): Intent =
            Intent(context.applicationContext, ClipboardFloatingActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or
                    Intent.FLAG_ACTIVITY_NO_HISTORY or
                    Intent.FLAG_ACTIVITY_EXCLUDE_FROM_RECENTS or
                    Intent.FLAG_ACTIVITY_NO_ANIMATION
            }
    }
}
