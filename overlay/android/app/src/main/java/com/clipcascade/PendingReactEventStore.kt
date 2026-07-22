package com.clipcascade

import android.content.Context
import com.facebook.react.bridge.Arguments
import com.facebook.react.bridge.ReactContext
import com.facebook.react.modules.core.DeviceEventManagerModule
import org.json.JSONArray
import org.json.JSONObject
import java.security.MessageDigest

/**
 * Native entry points can run before React Native has created a ReactContext.
 * Upstream silently drops those events. This store persists a small FIFO queue
 * and drains it as soon as the foreground service starts its native listener.
 */
object PendingReactEventStore {
    private const val PREFS = "clipcascade_native_events"
    private const val QUEUE = "queue"
    private const val LAST_FINGERPRINT = "last_fingerprint"
    private const val LAST_FINGERPRINT_TIME = "last_fingerprint_time"
    private const val MAX_EVENTS = 64
    private const val DEDUP_WINDOW_MS = 2_000L

    @Synchronized
    fun emitOrQueue(
        context: Context,
        reactContext: ReactContext?,
        eventName: String,
        payload: Map<String, String>
    ): Boolean {
        if (reactContext != null && emitNow(reactContext, eventName, payload)) {
            return true
        }
        enqueue(context.applicationContext, eventName, payload)
        return false
    }

    @Synchronized
    fun drain(context: Context, reactContext: ReactContext): Int {
        val appContext = context.applicationContext
        val prefs = appContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val source = parseQueue(prefs.getString(QUEUE, null))
        if (source.length() == 0) return 0

        val remaining = JSONArray()
        var delivered = 0
        for (index in 0 until source.length()) {
            val item = source.optJSONObject(index) ?: continue
            val eventName = item.optString("event")
            val payloadObject = item.optJSONObject("payload") ?: JSONObject()
            val payload = mutableMapOf<String, String>()
            val keys = payloadObject.keys()
            while (keys.hasNext()) {
                val key = keys.next()
                payload[key] = payloadObject.optString(key)
            }
            if (eventName.isNotBlank() && emitNow(reactContext, eventName, payload)) {
                delivered += 1
            } else {
                remaining.put(item)
            }
        }
        prefs.edit().putString(QUEUE, remaining.toString()).apply()
        return delivered
    }

    @Synchronized
    fun pendingCount(context: Context): Int {
        val prefs = context.applicationContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        return parseQueue(prefs.getString(QUEUE, null)).length()
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
        val duplicate = prefs.getString(LAST_FINGERPRINT, null) == fingerprint &&
            now - prefs.getLong(LAST_FINGERPRINT_TIME, 0L) <= DEDUP_WINDOW_MS
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
