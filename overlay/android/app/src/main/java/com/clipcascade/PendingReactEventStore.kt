package com.clipcascade

import android.content.Context
import com.facebook.react.bridge.Arguments
import com.facebook.react.bridge.ReactContext
import com.facebook.react.modules.core.DeviceEventManagerModule
import org.json.JSONArray
import org.json.JSONObject
import java.security.MessageDigest
import java.util.concurrent.atomic.AtomicBoolean

/**
 * Native entry points can run before React Native has registered its event listeners.
 * ReactContext existence alone is not a delivery guarantee, so events remain durable
 * until ClipboardListener.startListening() atomically activates and drains the queue.
 */
object PendingReactEventStore {
    private const val PREFS = "clipcascade_native_events"
    private const val QUEUE = "queue"
    private const val LAST_FINGERPRINT = "last_fingerprint"
    private const val LAST_FINGERPRINT_TIME = "last_fingerprint_time"
    private const val MAX_EVENTS = 64
    private const val DEDUP_WINDOW_MS = 2_000L
    private val deliveryReady = AtomicBoolean(false)

    internal enum class DeliveryDecision {
        DELIVERED,
        DROP,
        RETRY
    }

    internal data class DrainResult<T>(
        val delivered: Int,
        val remaining: List<T>
    )

    @Synchronized
    fun emitOrQueue(
        context: Context,
        reactContext: ReactContext?,
        eventName: String,
        payload: Map<String, String>
    ): Boolean {
        if (deliveryReady.get() && reactContext != null && emitNow(reactContext, eventName, payload)) {
            return true
        }
        enqueue(context.applicationContext, eventName, payload)
        return false
    }

    /** Activates direct delivery and drains older events without allowing overtaking. */
    @Synchronized
    fun activateAndDrain(context: Context, reactContext: ReactContext): Int {
        deliveryReady.set(true)
        return drainLocked(context.applicationContext, reactContext)
    }

    @Synchronized
    fun deactivate() {
        deliveryReady.set(false)
    }

    @Synchronized
    fun drain(context: Context, reactContext: ReactContext): Int {
        if (!deliveryReady.get()) return 0
        return drainLocked(context.applicationContext, reactContext)
    }

    @Synchronized
    fun pendingCount(context: Context): Int {
        val prefs = context.applicationContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        return parseQueue(prefs.getString(QUEUE, null)).length()
    }

    fun isDeliveryReady(): Boolean = deliveryReady.get()

    private fun drainLocked(appContext: Context, reactContext: ReactContext): Int {
        val prefs = appContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val source = parseQueue(prefs.getString(QUEUE, null))
        if (source.length() == 0) return 0

        val queued = buildList {
            for (index in 0 until source.length()) {
                source.optJSONObject(index)?.let(::add)
            }
        }
        val result = drainInOrder(queued) { item ->
            val eventName = item.optString("event")
            if (eventName.isBlank()) {
                return@drainInOrder DeliveryDecision.DROP
            }
            val payloadObject = item.optJSONObject("payload") ?: JSONObject()
            val payload = mutableMapOf<String, String>()
            val keys = payloadObject.keys()
            while (keys.hasNext()) {
                val key = keys.next()
                payload[key] = payloadObject.optString(key)
            }
            if (emitNow(reactContext, eventName, payload)) {
                DeliveryDecision.DELIVERED
            } else {
                DeliveryDecision.RETRY
            }
        }

        val remaining = JSONArray()
        result.remaining.forEach(remaining::put)
        prefs.edit().putString(QUEUE, remaining.toString()).apply()
        return result.delivered
    }

    /**
     * Delivers a prefix only. The first retryable failure and every item behind it remain
     * queued so a transient React failure can never reorder clipboard events.
     */
    internal fun <T> drainInOrder(
        items: List<T>,
        deliver: (T) -> DeliveryDecision
    ): DrainResult<T> {
        val remaining = mutableListOf<T>()
        var delivered = 0
        var blocked = false
        items.forEach { item ->
            if (blocked) {
                remaining += item
                return@forEach
            }
            when (deliver(item)) {
                DeliveryDecision.DELIVERED -> delivered += 1
                DeliveryDecision.DROP -> Unit
                DeliveryDecision.RETRY -> {
                    blocked = true
                    remaining += item
                }
            }
        }
        return DrainResult(delivered, remaining)
    }

    private fun emitNow(
        reactContext: ReactContext,
        eventName: String,
        payload: Map<String, String>
    ): Boolean = try {
        val params = Arguments.createMap()
        payload.forEach { (key, value) -> params.putString(key, value) }
        reactContext
            .getJSModule(DeviceEventManagerModule.RCTDeviceEventEmitter::class.java)
            .emit(eventName, params)
        true
    } catch (_: Throwable) {
        false
    }

    private fun enqueue(context: Context, eventName: String, payload: Map<String, String>) {
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val now = System.currentTimeMillis()
        val fingerprint = fingerprint(eventName, payload)
        val previousTime = prefs.getLong(LAST_FINGERPRINT_TIME, 0L)
        val duplicate = prefs.getString(LAST_FINGERPRINT, null) == fingerprint &&
            isWithinDedupWindow(now, previousTime)
        if (duplicate) return

        val source = parseQueue(prefs.getString(QUEUE, null))
        val bounded = JSONArray()
        val first = maxOf(0, source.length() - (MAX_EVENTS - 1))
        for (index in first until source.length()) {
            bounded.put(source.opt(index))
        }
        bounded.put(
            JSONObject().apply {
                put("event", eventName)
                put("payload", JSONObject(payload))
                put("createdAt", now)
            }
        )
        prefs.edit()
            .putString(QUEUE, bounded.toString())
            .putString(LAST_FINGERPRINT, fingerprint)
            .putLong(LAST_FINGERPRINT_TIME, now)
            .apply()
    }

    internal fun isWithinDedupWindow(nowMs: Long, previousMs: Long): Boolean =
        previousMs > 0L &&
            nowMs >= previousMs &&
            nowMs - previousMs <= DEDUP_WINDOW_MS

    private fun parseQueue(raw: String?): JSONArray = try {
        if (raw.isNullOrBlank()) JSONArray() else JSONArray(raw)
    } catch (_: Exception) {
        JSONArray()
    }

    private fun fingerprint(eventName: String, payload: Map<String, String>): String {
        val canonical = buildString {
            append(eventName)
            payload.toSortedMap().forEach { (key, value) ->
                append('\u0000').append(key).append('\u0000').append(value)
            }
        }
        return MessageDigest.getInstance("SHA-256")
            .digest(canonical.toByteArray(Charsets.UTF_8))
            .joinToString("") { "%02x".format(it) }
    }
}
