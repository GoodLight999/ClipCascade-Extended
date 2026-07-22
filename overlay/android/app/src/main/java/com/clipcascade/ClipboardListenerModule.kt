package com.clipcascade

import android.Manifest
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.provider.Settings
import androidx.core.content.ContextCompat
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod
import java.io.BufferedReader
import java.io.InputStreamReader
import java.util.concurrent.atomic.AtomicBoolean

class ClipboardListenerModule(
    reactContext: ReactApplicationContext
) : ReactContextBaseJavaModule(reactContext) {
    private val clipboardManager =
        reactContext.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
    private val bridge = AsyncStorageBridge(reactContext)
    private val stopLogcat = AtomicBoolean(false)
    private var clipboardListener: ClipboardManager.OnPrimaryClipChangedListener? = null
    private var logcatThread: Thread? = null
    private var logcatProcess: Process? = null
    private var lastOverlayLaunch = 0L

    @Volatile
    private var listening = false

    override fun getName(): String = "ClipboardListener"

    @ReactMethod
    @Synchronized
    fun startListening() {
        if (listening) {
            PendingReactEventStore.drain(reactApplicationContext, reactApplicationContext)
            return
        }

        clipboardListener = ClipboardManager.OnPrimaryClipChangedListener {
            try {
                readClipboardPayload()?.let { payload ->
                    PendingReactEventStore.emitOrQueue(
                        reactApplicationContext,
                        reactApplicationContext,
                        "onClipboardChange",
                        payload
                    )
                }
            } catch (security: SecurityException) {
                bridge.setValue("clipboard_fallback_status", "native-listener-denied")
            } catch (error: Exception) {
                bridge.setValue(
                    "clipboard_fallback_status",
                    "native-listener-error:${error.javaClass.simpleName}"
                )
            }
        }
        clipboardManager.addPrimaryClipChangedListener(clipboardListener)
        listening = true

        val delivered = PendingReactEventStore.drain(
            reactApplicationContext,
            reactApplicationContext
        )
        if (delivered > 0) {
            bridge.setValue("clipboard_fallback_status", "delivered-pending:$delivered")
        }

        if (Build.VERSION.SDK_INT <= Build.VERSION_CODES.P) {
            bridge.setValue("clipboard_fallback_status", "native-listener-active")
            return
        }

        val readLogsGranted = ContextCompat.checkSelfPermission(
            reactApplicationContext,
            Manifest.permission.READ_LOGS
        ) == PackageManager.PERMISSION_GRANTED
        val overlayGranted = Settings.canDrawOverlays(reactApplicationContext)

        when {
            !readLogsGranted -> bridge.setValue(
                "clipboard_fallback_status",
                "manual-share-or-notification;READ_LOGS-missing"
            )
            !overlayGranted -> bridge.setValue(
                "clipboard_fallback_status",
                "manual-share-or-notification;overlay-missing"
            )
            else -> startLogcatFallback()
        }
    }

    private fun startLogcatFallback() {
        stopLogcat.set(false)
        logcatThread = Thread({
            try {
                val process = ProcessBuilder(ClipboardAccessPolicy.logcatCommand())
                    .redirectErrorStream(true)
                    .start()
                logcatProcess = process
                bridge.setValue("clipboard_fallback_status", "logcat-overlay-active")
                BufferedReader(InputStreamReader(process.inputStream)).use { reader ->
                    while (!stopLogcat.get()) {
                        val line = reader.readLine() ?: break
                        if (ClipboardAccessPolicy.isClipboardDenialLine(line, BuildConfig.APPLICATION_ID)) {
                            launchClipboardCapture()
                        }
                    }
                }
            } catch (error: Exception) {
                if (!stopLogcat.get()) {
                    bridge.setValue(
                        "clipboard_fallback_status",
                        "logcat-error:${error.javaClass.simpleName}"
                    )
                }
            } finally {
                logcatProcess = null
                if (!stopLogcat.get()) {
                    bridge.setValue("clipboard_fallback_status", "logcat-stopped")
                }
            }
        }, "ClipCascade-ClipboardLogcat").apply {
            isDaemon = true
            start()
        }
    }

    @Synchronized
    private fun launchClipboardCapture() {
        val now = System.currentTimeMillis()
        if (now - lastOverlayLaunch < 750L) return
        lastOverlayLaunch = now
        try {
            val intent: Intent = ClipboardFloatingActivity.getIntent(reactApplicationContext)
            reactApplicationContext.startActivity(intent)
            bridge.setValue("clipboard_fallback_status", "capture-requested")
        } catch (error: Exception) {
            bridge.setValue(
                "clipboard_fallback_status",
                "capture-launch-error:${error.javaClass.simpleName}"
            )
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

    @ReactMethod
    @Synchronized
    fun stopListening() {
        clipboardListener?.let { clipboardManager.removePrimaryClipChangedListener(it) }
        clipboardListener = null
        listening = false

        stopLogcat.set(true)
        try {
            logcatProcess?.destroy()
        } catch (_: Exception) {
        }
        try {
            logcatThread?.interrupt()
        } catch (_: Exception) {
        }
        logcatProcess = null
        logcatThread = null
        bridge.setValue("clipboard_fallback_status", "stopped")
    }

    @ReactMethod
    fun addListener(type: String?) = Unit

    @ReactMethod
    fun removeListeners(count: Int?) = Unit
}
