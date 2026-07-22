package com.clipcascade

import android.app.Notification
import android.content.Context
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import com.facebook.react.bridge.ReactContext

/**
 * Optional ADB-free path for OTP notifications from Gmail, Beeper, messaging,
 * and authenticator-adjacent applications. Android exposes notification text
 * only after the user grants Notification Access in system settings.
 */
class NotificationCaptureService : NotificationListenerService() {
    private val bridge by lazy { AsyncStorageBridge(applicationContext) }

    override fun onListenerConnected() {
        super.onListenerConnected()
        bridge.setValue("notification_capture_status", "listener-connected")
    }

    override fun onListenerDisconnected() {
        bridge.setValue("notification_capture_status", "listener-disconnected")
        super.onListenerDisconnected()
    }

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        if (sbn == null || sbn.packageName == packageName) return
        if (sbn.notification.flags and Notification.FLAG_GROUP_SUMMARY != 0) return
        if (bridge.getValue("wsIsRunning") != "true") return

        try {
            val extras = sbn.notification.extras
            val parts = buildList<CharSequence?> {
                add(extras.getCharSequence(Notification.EXTRA_TITLE))
                add(extras.getCharSequence(Notification.EXTRA_TITLE_BIG))
                add(extras.getCharSequence(Notification.EXTRA_TEXT))
                add(extras.getCharSequence(Notification.EXTRA_BIG_TEXT))
                add(extras.getCharSequence(Notification.EXTRA_SUB_TEXT))
                add(extras.getCharSequence(Notification.EXTRA_SUMMARY_TEXT))
                extras.getCharSequenceArray(Notification.EXTRA_TEXT_LINES)?.forEach(::add)
            }
            val code = OtpExtractor.extract(parts) ?: return
            if (isDuplicate(sbn.packageName, code)) return

            val delivered = PendingReactEventStore.emitOrQueue(
                applicationContext,
                currentReactContext(),
                "SHARED_TEXT",
                mapOf("text" to code)
            )
            bridge.setValue(
                "notification_capture_status",
                "${if (delivered) "delivered" else "queued"}:${sbn.packageName}:${code.length}-digit"
            )
        } catch (error: Exception) {
            bridge.setValue(
                "notification_capture_status",
                "capture-error:${error.javaClass.simpleName}"
            )
        }
    }

    private fun currentReactContext(): ReactContext? =
        (applicationContext as? MainApplication)
            ?.reactNativeHost
            ?.reactInstanceManager
            ?.currentReactContext

    private fun isDuplicate(sourcePackage: String, code: String): Boolean {
        val prefs = getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val fingerprint = "$sourcePackage\u0000$code"
        val now = System.currentTimeMillis()
        val duplicate = prefs.getString(LAST, null) == fingerprint &&
            now - prefs.getLong(LAST_TIME, 0L) <= DEDUP_WINDOW_MS
        if (!duplicate) {
            prefs.edit()
                .putString(LAST, fingerprint)
                .putLong(LAST_TIME, now)
                .apply()
        }
        return duplicate
    }

    companion object {
        private const val PREFS = "clipcascade_notification_capture"
        private const val LAST = "last_fingerprint"
        private const val LAST_TIME = "last_time"
        private const val DEDUP_WINDOW_MS = 120_000L
    }
}
