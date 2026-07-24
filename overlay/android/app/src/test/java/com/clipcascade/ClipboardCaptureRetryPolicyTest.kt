package com.clipcascade

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ClipboardCaptureRetryPolicyTest {
    @Test
    fun retriesOnlyAfterTheFirstTransientFailure() {
        assertTrue(ClipboardCaptureRetryPolicy.canRetry(1))
        assertFalse(ClipboardCaptureRetryPolicy.canRetry(2))
        assertFalse(ClipboardCaptureRetryPolicy.canRetry(0))
        assertFalse(ClipboardCaptureRetryPolicy.canRetry(3))
    }
}
