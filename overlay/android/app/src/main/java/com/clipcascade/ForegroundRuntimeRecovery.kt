package com.clipcascade

import android.content.Context
import android.content.Intent
import com.facebook.react.HeadlessJsTaskService
import java.util.concurrent.atomic.AtomicLong

/**
 * Restarts a requested clipboard/network runtime only while the one-shot capture Activity
 * is visible. This avoids forbidden arbitrary background FGS launches while recovering from
 * OEM/process death at the next explicit user copy action.
 */
object ForegroundRuntimeRecovery {
    const val EVENT = "com.clipcascade.CAPTURE_RECOVERY"
    private const val HEARTBEAT_STALE_MS = 15_000L
    private const val MIN_RETRY_INTERVAL_MS = 10_000L
    private val lastAttemptAt = AtomicLong(0L)

    fun startIfRequested(context: Context, source: String): Boolean {
        val app = context.applicationContext
        val bridge = AsyncStorageBridge(app)
        if (bridge.getValue("wsIsRunning") != "true") {
            bridge.setValue("foreground_service_recovery_status", "not-requested:$source")
            return false
        }

        val now = System.currentTimeMillis()
        val heartbeatAt = bridge.getValue("foreground_service_heartbeat_at")?.toLongOrNull() ?: 0L
        if (heartbeatAt > 0L && now >= heartbeatAt && now - heartbeatAt <= HEARTBEAT_STALE_MS) {
            bridge.setValue("foreground_service_recovery_status", "heartbeat-healthy:$source")
            return false
        }

        while (true) {
            val previous = lastAttemptAt.get()
            if (previous > 0L && now >= previous && now - previous < MIN_RETRY_INTERVAL_MS) {
                bridge.setValue(
                    "foreground_service_recovery_status",
                    "recovery-throttled:$source:${now - previous}"
                )
                return false
            }
            if (lastAttemptAt.compareAndSet(previous, now)) break
        }

        return try {
            bridge.setValue("foreground_service_recovery_status", "recovery-requested:$source")
            HeadlessJsTaskService.acquireWakeLockNow(app)
            app.startService(
                Intent(app, HeadlessTaskService::class.java).apply {
                    putExtra("event", EVENT)
                    putExtra("source", source.take(120))
                }
            )
            bridge.setValue("foreground_service_recovery_status", "headless-started:$source")
            true
        } catch (error: Throwable) {
            bridge.setValue(
                "foreground_service_recovery_status",
                "recovery-failed:${error.javaClass.simpleName}:${error.message}".take(300)
            )
            false
        }
    }
}
