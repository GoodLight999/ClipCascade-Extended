package com.clipcascade

import android.accessibilityservice.AccessibilityService
import android.os.SystemClock
import android.view.accessibility.AccessibilityEvent

/** ADB-free copy-signal detector modeled on, then hardened beyond, ClipCascade Go. */
class ClipCascadeAccessibilityService : AccessibilityService() {
    private val bridge by lazy { AsyncStorageBridge(applicationContext) }
    private val syncRequestCache = SyncRequestCache(SYNC_CHECK_CACHE_MS)

    override fun onServiceConnected() {
        super.onServiceConnected()
        syncRequestCache.invalidate()
        bridge.setValue("accessibility_service_status", "enabled")
        ClipboardCaptureCoordinator.resumePending(this)
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (event == null) return

        // Classify first. Window/content/click events are frequent; ignored events must not
        // touch AsyncStorage/SQLite or they can increase typing latency and battery use.
        val texts = buildList {
            event.text?.forEach { add(it?.toString().orEmpty()) }
            event.contentDescription?.toString()?.let(::add)
        }
        val decision = CopySignalClassifier.classify(
            eventType = event.eventType,
            sourcePackage = event.packageName?.toString(),
            texts = texts,
            ownPackage = packageName
        )
        if (!decision.capture) return

        if (!isSyncRequested()) {
            bridge.setValue("accessibility_service_status", "enabled;sync-stopped")
            return
        }

        val source = "${event.packageName}:${decision.reason}"
        bridge.setValue("accessibility_service_status", "trigger:$source")
        ClipboardCaptureCoordinator.request(this, source, decision.delayMs)
    }

    private fun isSyncRequested(): Boolean = syncRequestCache.get(SystemClock.elapsedRealtime()) {
        bridge.getValue("wsIsRunning")?.toBoolean() == true
    }

    override fun onInterrupt() {
        bridge.setValue("accessibility_service_status", "interrupted")
    }

    override fun onUnbind(intent: android.content.Intent?): Boolean {
        syncRequestCache.invalidate()
        bridge.setValue("accessibility_service_status", "disabled-or-unbound")
        return super.onUnbind(intent)
    }

    companion object {
        private const val SYNC_CHECK_CACHE_MS = 250L
    }
}
