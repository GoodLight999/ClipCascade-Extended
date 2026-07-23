package com.clipcascade

/** Small monotonic-time cache used to avoid SQLite reads on repeated copy feedback events. */
internal class SyncRequestCache(private val intervalMs: Long) {
    private var lastCheckAt: Long? = null
    private var cachedValue = false

    init {
        require(intervalMs >= 0L) { "Cache interval must be non-negative" }
    }

    fun get(now: Long, loader: () -> Boolean): Boolean {
        val previous = lastCheckAt
        if (previous == null || now < previous || now - previous >= intervalMs) {
            cachedValue = loader()
            lastCheckAt = now
        }
        return cachedValue
    }

    fun invalidate() {
        lastCheckAt = null
    }
}
