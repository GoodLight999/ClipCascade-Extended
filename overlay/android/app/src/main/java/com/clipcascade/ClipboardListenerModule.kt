package com.clipcascade

import android.Manifest
import android.content.ClipboardManager
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.os.SystemClock
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
    private var lastLogcatTrigger = 0L

    @Volatile
    private var listening = false

    override fun getName(): String = "ClipboardListener"

    @ReactMethod
    @Synchronized
    fun startListening() {
        if (listening) {
            PendingReactEventStore.drain(reactApplicationContext, reactApplicationContext)
            ClipboardCaptureCoordinator.resumePending(reactApplicationContext)
            return
        }

        clipboardListener = ClipboardManager.OnPrimaryClipChangedListener {
            try {
                ClipboardPayloadReader.readOrStage(
                    reactApplicationContext,
                    clipboardManager
                ) { result ->
                    result.onSuccess { payload ->
                        payload?.let {
                            PendingReactEventStore.emitOrQueue(
                                reactApplicationContext,
                                reactApplicationContext,
                                "onClipboardChange",
                                it
                            )
                        }
                    }.onFailure { error ->
                        bridge.setValue(
                            "clipboard_fallback_status",
                            "native-listener-error:${error.javaClass.simpleName}:${error.message}"
                                .take(300)
                        )
                    }
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
        ClipboardCaptureCoordinator.resumePending(reactApplicationContext)

        val delivered = PendingReactEventStore.activateAndDrain(
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
                "accessibility-primary;READ_LOGS-fallback-missing"
            )
            !overlayGranted -> bridge.setValue(
                "clipboard_fallback_status",
                "accessibility-primary;overlay-missing"
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
                            requestSerializedCapture()
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
    private fun requestSerializedCapture() {
        val now = SystemClock.elapsedRealtime()
        if (now - lastLogcatTrigger < 180L) return
        lastLogcatTrigger = now
        ClipboardCaptureCoordinator.request(
            reactApplicationContext,
            "read-logs-denial",
            100L
        )
        bridge.setValue("clipboard_fallback_status", "capture-queued-from-logcat")
    }

    @ReactMethod
    @Synchronized
    fun stopListening() {
        PendingReactEventStore.deactivate()
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
