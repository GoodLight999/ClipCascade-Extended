package com.clipcascade

/** Bounded retry policy for transient focus/clipboard-access races. */
object ClipboardCaptureRetryPolicy {
    internal const val MAX_ATTEMPTS = 2
    internal const val RETRY_DELAY_MS = 450L

    internal fun canRetry(completedAttempts: Int): Boolean =
        completedAttempts in 1 until MAX_ATTEMPTS
}
