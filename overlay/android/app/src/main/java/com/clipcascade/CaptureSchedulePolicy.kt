package com.clipcascade

/** Pure, rollback-safe delay calculation for persisted clipboard capture requests. */
object CaptureSchedulePolicy {
    internal const val MAX_DELAY_MS = 1_500L

    internal fun remainingDelayMs(dueAtMs: Long, nowMs: Long): Long {
        if (dueAtMs <= 0L || dueAtMs <= nowMs) return 0L
        val delta = try {
            Math.subtractExact(dueAtMs, nowMs)
        } catch (_: ArithmeticException) {
            MAX_DELAY_MS
        }
        return delta.coerceIn(0L, MAX_DELAY_MS)
    }
}
