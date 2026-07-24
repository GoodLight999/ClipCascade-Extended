package com.clipcascade

import org.junit.Assert.assertEquals
import org.junit.Test

class CaptureSchedulePolicyTest {
    @Test
    fun preservesOrdinaryShortDelay() {
        assertEquals(450L, CaptureSchedulePolicy.remainingDelayMs(10_450L, 10_000L))
    }

    @Test
    fun overdueOrMissingRequestRunsImmediately() {
        assertEquals(0L, CaptureSchedulePolicy.remainingDelayMs(0L, 10_000L))
        assertEquals(0L, CaptureSchedulePolicy.remainingDelayMs(9_000L, 10_000L))
    }

    @Test
    fun wallClockRollbackCannotSuspendCaptureBeyondTheBound() {
        assertEquals(
            CaptureSchedulePolicy.MAX_DELAY_MS,
            CaptureSchedulePolicy.remainingDelayMs(100_000L, 1_000L)
        )
    }

    @Test
    fun subtractionOverflowAlsoFallsBackToTheBound() {
        assertEquals(
            CaptureSchedulePolicy.MAX_DELAY_MS,
            CaptureSchedulePolicy.remainingDelayMs(Long.MAX_VALUE, Long.MIN_VALUE)
        )
    }
}
