package com.clipcascade

import android.content.Context
import android.os.Handler
import android.os.Looper
import java.util.concurrent.atomic.AtomicBoolean

/**
 * Serializes Android 10+ focus-bridge captures and persists the newest request.
 * A newer request arriving during a capture is never dropped; it runs next.
 */
object ClipboardCaptureCoordinator {
    private const val PREFS = "clipcascade_capture_coordinator"
    private const val KEY_PENDING = "pending"
    private const val KEY_SEQUENCE = "sequence"
    private const val KEY_DUE_AT = "due_at"
    private const val KEY_SOURCE = "source"
    private const val KEY_ATTEMPTS = "attempts"
    private const val MAX_ATTEMPTS = 3
    private val mainHandler = Handler(Looper.getMainLooper())
    private val inFlight = AtomicBoolean(false)
    private val scheduleLock = Any()
    private var scheduledRunnable: Runnable? = null

    fun request(context: Context, source: String, delayMs: Long) {
        val app = context.applicationContext
        val prefs = app.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val sequence = prefs.getLong(KEY_SEQUENCE, 0L) + 1L
        val dueAt = System.currentTimeMillis() + delayMs.coerceIn(80L, 1500L)
        prefs.edit()
            .putBoolean(KEY_PENDING, true)
            .putLong(KEY_SEQUENCE, sequence)
            .putLong(KEY_DUE_AT, dueAt)
            .putString(KEY_SOURCE, source.take(160))
            .putInt(KEY_ATTEMPTS, 0)
            .apply()
        AsyncStorageBridge(app).setValue("accessibility_capture_status", "queued:$source")
        schedulePending(app)
    }

    fun resumePending(context: Context) {
        val app = context.applicationContext
        val prefs = app.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        if (prefs.getBoolean(KEY_PENDING, false)) {
            inFlight.set(false)
            schedulePending(app)
        }
    }

    fun complete(context: Context, completedSequence: Long, outcome: String) {
        val app = context.applicationContext
        val prefs = app.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        inFlight.set(false)
        val newestSequence = prefs.getLong(KEY_SEQUENCE, 0L)
        if (newestSequence <= completedSequence) {
            prefs.edit()
                .putBoolean(KEY_PENDING, false)
                .putInt(KEY_ATTEMPTS, 0)
                .apply()
            AsyncStorageBridge(app).setValue("accessibility_capture_status", outcome)
        } else {
            AsyncStorageBridge(app).setValue(
                "accessibility_capture_status",
                "$outcome;newer-request-pending"
            )
            schedulePending(app)
        }
    }

    fun status(context: Context): String {
        val prefs = context.applicationContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        return buildString {
            append(if (prefs.getBoolean(KEY_PENDING, false)) "pending" else "idle")
            append(";inFlight=").append(inFlight.get())
            append(";seq=").append(prefs.getLong(KEY_SEQUENCE, 0L))
            prefs.getString(KEY_SOURCE, null)?.let { append(";source=").append(it) }
        }
    }

    private fun schedulePending(context: Context) {
        synchronized(scheduleLock) {
            scheduledRunnable?.let(mainHandler::removeCallbacks)
            val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            val delay = (prefs.getLong(KEY_DUE_AT, 0L) - System.currentTimeMillis())
                .coerceAtLeast(0L)
            val runnable = Runnable { launchPending(context) }
            scheduledRunnable = runnable
            mainHandler.postDelayed(runnable, delay)
        }
    }

    private fun launchPending(context: Context) {
        synchronized(scheduleLock) { scheduledRunnable = null }
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        if (!prefs.getBoolean(KEY_PENDING, false)) return
        if (!inFlight.compareAndSet(false, true)) {
            prefs.edit().putLong(KEY_DUE_AT, System.currentTimeMillis() + 180L).apply()
            schedulePending(context)
            return
        }

        val sequence = prefs.getLong(KEY_SEQUENCE, 0L)
        try {
            context.startActivity(ClipboardFloatingActivity.getIntent(context, sequence))
            AsyncStorageBridge(context).setValue(
                "accessibility_capture_status",
                "capture-launched:$sequence"
            )
        } catch (error: Exception) {
            inFlight.set(false)
            val attempts = prefs.getInt(KEY_ATTEMPTS, 0) + 1
            if (attempts >= MAX_ATTEMPTS) {
                prefs.edit().putBoolean(KEY_PENDING, false).putInt(KEY_ATTEMPTS, attempts).apply()
                AsyncStorageBridge(context).setValue(
                    "accessibility_capture_status",
                    "capture-launch-failed:${error.javaClass.simpleName}"
                )
            } else {
                prefs.edit()
                    .putInt(KEY_ATTEMPTS, attempts)
                    .putLong(KEY_DUE_AT, System.currentTimeMillis() + attempts * 350L)
                    .apply()
                schedulePending(context)
            }
        }
    }
}
