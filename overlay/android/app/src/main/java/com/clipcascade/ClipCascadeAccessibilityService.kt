package com.clipcascade

import android.accessibilityservice.AccessibilityService
import android.view.accessibility.AccessibilityEvent

/** ADB-free copy-signal detector modeled on, then hardened beyond, ClipCascade Go. */
class ClipCascadeAccessibilityService : AccessibilityService() {
    private val bridge by lazy { AsyncStorageBridge(applicationContext) }

    override fun onServiceConnected() {
        super.onServiceConnected()
        bridge.setValue("accessibility_service_status", "enabled")
        ClipboardCaptureCoordinator.resumePending(this)
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (event == null) return
        if (bridge.getValue("wsIsRunning")?.toBoolean() != true) {
            bridge.setValue("accessibility_service_status", "enabled;sync-stopped")
            return
        }

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

        val source = "${event.packageName}:${decision.reason}"
        bridge.setValue("accessibility_service_status", "trigger:$source")
        ClipboardCaptureCoordinator.request(this, source, decision.delayMs)
    }

    override fun onInterrupt() {
        bridge.setValue("accessibility_service_status", "interrupted")
    }

    override fun onUnbind(intent: android.content.Intent?): Boolean {
        bridge.setValue("accessibility_service_status", "disabled-or-unbound")
        return super.onUnbind(intent)
    }
}
