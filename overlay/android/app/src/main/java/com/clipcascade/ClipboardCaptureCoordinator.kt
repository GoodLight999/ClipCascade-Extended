package com.clipcascade

import android.content.Context
import android.os.Handler
import android.os.Looper
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicLong

/**
 * Serializes Android 10+ focus-bridge captures and persists the newest request.
 * A newer request arriving during a capture runs next. A launch that Android accepts
 * but never creates is recovered by a watchdog instead of wedging all future copies.
 */
object ClipboardCaptureCoordinator {
    private const val PREFS = "clipcascade_capture_coordinator"
    private const val KEY_PENDING = "pending"
    private const val KEY_SEQUENCE = "sequence"
    private const val KEY_DUE_AT = "due_at"
    private const val KEY_SOURCE = "source"
    private const val KEY_ATTEMPTS = "attempts"
    private const val MAX_ATTEMPTS = 3
    private const val CAPTURE_TIMEOUT_MS = 3_500L
    private val mainHandler = Handler(Looper.getMainLooper())
    private val inFlight = AtomicBoolean(false)
    private val activeSequence = AtomicLong(0L)
    private val scheduleLock = Any()
    private var scheduledRunnable: Runnable? = null
    private var watchdogRunnable: Runnable? = null

    @Synchronized
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
        if (!inFlight.get()) schedulePending(app)
    }

    @Synchronized
    fun resumePending(context: Context) {
        // In-memory inFlight state is already reset after process death. Within the
        // same process, clearing it here can launch a duplicate Activity while the
        // original capture is still running.
        if (inFlight.get()) return
        val app = context.applicationContext
        val prefs = app.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        if (prefs.getBoolean(KEY_PENDING, false)) schedulePending(app)
    }

    @Synchronized
    fun complete(context: Context, completedSequence: Long, outcome: String) {
        val app = context.applicationContext
        if (activeSequence.get() != completedSequence) {
            AsyncStorageBridge(app).setValue(
                "accessibility_capture_status",
                "$outcome;stale-completion:$completedSequence"
            )
            return
        }

        clearActiveCapture()
        val prefs = app.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
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

    @Synchronized
    fun fail(context: Context, failedSequence: Long, outcome: String) {
        val app = context.applicationContext
        if (activeSequence.get() != failedSequence) return
        clearActiveCapture()
        retryOrStop(app, failedSequence, outcome)
    }

    fun status(context: Context): String {
        val prefs = context.applicationContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        return buildString {
            append(if (prefs.getBoolean(KEY_PENDING, false)) "pending" else "idle")
            append(";inFlight=").append(inFlight.get())
            append(";activeSeq=").append(activeSequence.get())
            append(";seq=").append(prefs.getLong(KEY_SEQUENCE, 0L))
            append(";attempts=").append(prefs.getInt(KEY_ATTEMPTS, 0))
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

    @Synchronized
    private fun launchPending(context: Context) {
        synchronized(scheduleLock) { scheduledRunnable = null }
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        if (!prefs.getBoolean(KEY_PENDING, false) || inFlight.get()) return

        val sequence = prefs.getLong(KEY_SEQUENCE, 0L)
        inFlight.set(true)
        activeSequence.set(sequence)
        try {
            context.startActivity(ClipboardFloatingActivity.getIntent(context, sequence))
            AsyncStorageBridge(context).setValue(
                "accessibility_capture_status",
                "capture-launched:$sequence"
            )
            scheduleWatchdog(context.applicationContext, sequence)
        } catch (error: Exception) {
            clearActiveCapture()
            retryOrStop(
                context.applicationContext,
                sequence,
                "capture-launch-failed:${error.javaClass.simpleName}"
            )
        }
    }

    private fun scheduleWatchdog(context: Context, sequence: Long) {
        synchronized(scheduleLock) {
            watchdogRunnable?.let(mainHandler::removeCallbacks)
            val runnable = Runnable {
                synchronized(this@ClipboardCaptureCoordinator) {
                    if (inFlight.get() && activeSequence.get() == sequence) {
                        clearActiveCapture()
                        retryOrStop(context, sequence, "capture-timeout")
                    }
                }
            }
            watchdogRunnable = runnable
            mainHandler.postDelayed(runnable, CAPTURE_TIMEOUT_MS)
        }
    }

    private fun retryOrStop(context: Context, failedSequence: Long, outcome: String) {
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val newestSequence = prefs.getLong(KEY_SEQUENCE, 0L)
        if (newestSequence > failedSequence) {
            AsyncStorageBridge(context).setValue(
                "accessibility_capture_status",
                "$outcome;newer-request-pending"
            )
            schedulePending(context)
            return
        }

        val attempts = prefs.getInt(KEY_ATTEMPTS, 0) + 1
        if (attempts >= MAX_ATTEMPTS) {
            prefs.edit()
                .putBoolean(KEY_PENDING, false)
                .putInt(KEY_ATTEMPTS, attempts)
                .apply()
            AsyncStorageBridge(context).setValue(
                "accessibility_capture_status",
                "$outcome;abandoned-after:$attempts"
            )
        } else {
            prefs.edit()
                .putInt(KEY_ATTEMPTS, attempts)
                .putLong(KEY_DUE_AT, System.currentTimeMillis() + attempts * 350L)
                .apply()
            AsyncStorageBridge(context).setValue(
                "accessibility_capture_status",
                "$outcome;retry:$attempts"
            )
            schedulePending(context)
        }
    }

    private fun clearActiveCapture() {
        inFlight.set(false)
        activeSequence.set(0L)
        synchronized(scheduleLock) {
            watchdogRunnable?.let(mainHandler::removeCallbacks)
            watchdogRunnable = null
        }
    }
}
