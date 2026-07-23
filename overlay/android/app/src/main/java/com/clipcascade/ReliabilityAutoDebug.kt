package com.clipcascade

import android.content.ClipboardManager
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.provider.Settings
import androidx.core.content.ContextCompat
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

/** Read-only, one-tap diagnostic snapshot. It does not require ADB or logcat. */
object ReliabilityAutoDebug {
    private val STORAGE_KEYS = listOf(
        "wsIsRunning",
        "wsStatusMessage",
        "p2pStatusMessage",
        "js_listener_status",
        "outbound_queue_status",
        "shared_payload_status",
        "shared_payload_pending",
        "foreground_service_error",
        "foreground_service_state",
        "foreground_service_heartbeat_at",
        "foreground_service_last_started_at",
        "foreground_service_last_stopped_at",
        "p2p_candidate_peers",
        "p2p_compatible_peers",
        "p2p_incompatible_peers",
        "p2p_last_compatibility_error",
        "accessibility_service_status",
        "accessibility_capture_status",
        "clipboard_fallback_status"
    )

    fun run(context: Context): String {
        val app = context.applicationContext
        val bridge = AsyncStorageBridge(app)
        val clipboard = app.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        val clipboardResult = JSONObject()
        try {
            val clip = clipboard.primaryClip
            val uriCount = if (clip == null) 0 else (0 until clip.itemCount).count {
                clip.getItemAt(it).uri != null
            }
            val mimeTypes = JSONArray()
            clip?.description?.let { description ->
                for (index in 0 until description.mimeTypeCount) {
                    mimeTypes.put(description.getMimeType(index).orEmpty())
                }
            }
            val payload = ClipboardPayloadReader.read(app, clipboard)
            clipboardResult.put("clipboardRead", true)
            clipboardResult.put("payloadPresent", payload != null || uriCount > 0)
            clipboardResult.put(
                "type",
                payload?.get("type") ?: if (uriCount > 0) "uri" else "empty"
            )
            clipboardResult.put("contentLength", payload?.get("content")?.length ?: 0)
            clipboardResult.put("uriCount", uriCount)
            clipboardResult.put("mimeTypes", mimeTypes)
        } catch (security: SecurityException) {
            clipboardResult.put("clipboardRead", false)
            clipboardResult.put("error", "SecurityException:${security.message}")
        } catch (error: Throwable) {
            clipboardResult.put("clipboardRead", false)
            clipboardResult.put("error", "${error.javaClass.simpleName}:${error.message}")
        }

        val storage = JSONObject()
        STORAGE_KEYS.forEach { key -> storage.put(key, bridge.getValue(key) ?: JSONObject.NULL) }

        val sharedRoot = File(app.cacheDir, "shared_outbound")
        val sharedFiles = sharedRoot.walkTopDown().filter { it.isFile }.toList()
        val shizuku = runCatching { JSONObject(ShizukuSetup.status(app)) }
            .getOrElse { JSONObject().put("error", "${it.javaClass.simpleName}:${it.message}") }

        return JSONObject().apply {
            put("generatedAt", System.currentTimeMillis())
            put("sdk", Build.VERSION.SDK_INT)
            put("manufacturer", Build.MANUFACTURER)
            put("model", Build.MODEL)
            put("packageName", app.packageName)
            put("versionName", BuildConfig.VERSION_NAME)
            put("versionCode", BuildConfig.VERSION_CODE)
            put("clipboard", clipboardResult)
            put("accessibilityEnabled", isAccessibilityEnabled(app))
            put("overlay", Settings.canDrawOverlays(app))
            put(
                "readLogs",
                ContextCompat.checkSelfPermission(app, android.Manifest.permission.READ_LOGS) ==
                    PackageManager.PERMISSION_GRANTED
            )
            put("pendingNativeEvents", PendingReactEventStore.pendingCount(app))
            put("nativeDeliveryReady", PendingReactEventStore.isDeliveryReady())
            put("captureCoordinator", ClipboardCaptureCoordinator.status(app))
            put("sharedCacheFiles", sharedFiles.size)
            put("sharedCacheBytes", sharedFiles.sumOf { it.length().coerceAtLeast(0L) })
            put("storage", storage)
            put("shizuku", shizuku)
        }.toString()
    }

    private fun isAccessibilityEnabled(context: Context): Boolean {
        val component = android.content.ComponentName(
            context,
            ClipCascadeAccessibilityService::class.java
        ).flattenToString()
        return Settings.Secure.getString(
            context.contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
        ).orEmpty().split(':').any { it.equals(component, ignoreCase = true) }
    }
}
