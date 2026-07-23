package com.clipcascade

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class SyncRequestCacheTest {
    @Test
    fun firstReadAlwaysLoadsThenCachesWithinInterval() {
        val cache = SyncRequestCache(250L)
        var loads = 0
        assertTrue(cache.get(10L) { loads += 1; true })
        assertTrue(cache.get(100L) { loads += 1; false })
        assertTrue(loads == 1)
    }

    @Test
    fun refreshesAfterInterval() {
        val cache = SyncRequestCache(250L)
        assertFalse(cache.get(10L) { false })
        assertTrue(cache.get(260L) { true })
    }

    @Test
    fun refreshesWhenClockMovesBackwards() {
        val cache = SyncRequestCache(250L)
        assertFalse(cache.get(500L) { false })
        assertTrue(cache.get(5L) { true })
    }

    @Test
    fun invalidateForcesNextRead() {
        val cache = SyncRequestCache(250L)
        assertFalse(cache.get(1L) { false })
        cache.invalidate()
        assertTrue(cache.get(2L) { true })
    }
}
