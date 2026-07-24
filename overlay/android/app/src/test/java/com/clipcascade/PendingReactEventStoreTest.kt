package com.clipcascade

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class PendingReactEventStoreTest {
    @Test
    fun firstRetryableFailureKeepsItselfAndEveryLaterEventQueued() {
        val attempted = mutableListOf<Int>()
        val result = PendingReactEventStore.drainInOrder(listOf(1, 2, 3, 4)) { item ->
            attempted += item
            if (item == 2) {
                PendingReactEventStore.DeliveryDecision.RETRY
            } else {
                PendingReactEventStore.DeliveryDecision.DELIVERED
            }
        }

        assertEquals(listOf(1, 2), attempted)
        assertEquals(1, result.delivered)
        assertEquals(listOf(2, 3, 4), result.remaining)
    }

    @Test
    fun invalidEventCanBeDroppedWithoutBlockingLaterEvents() {
        val result = PendingReactEventStore.drainInOrder(listOf("invalid", "valid")) { item ->
            if (item == "invalid") {
                PendingReactEventStore.DeliveryDecision.DROP
            } else {
                PendingReactEventStore.DeliveryDecision.DELIVERED
            }
        }

        assertEquals(1, result.delivered)
        assertTrue(result.remaining.isEmpty())
    }

    @Test
    fun pendingEventsForceNewEventsBehindTheQueue() {
        assertEquals(
            PendingReactEventStore.AdmissionPlan.QUEUE_AND_DRAIN,
            PendingReactEventStore.admissionPlan(
                deliveryReady = true,
                reactContextAvailable = true,
                pendingCount = 1
            )
        )
        assertEquals(
            PendingReactEventStore.AdmissionPlan.DIRECT,
            PendingReactEventStore.admissionPlan(
                deliveryReady = true,
                reactContextAvailable = true,
                pendingCount = 0
            )
        )
    }

    @Test
    fun unavailableDeliveryAlwaysQueuesWithoutDrain() {
        assertEquals(
            PendingReactEventStore.AdmissionPlan.QUEUE_ONLY,
            PendingReactEventStore.admissionPlan(
                deliveryReady = false,
                reactContextAvailable = true,
                pendingCount = 0
            )
        )
        assertEquals(
            PendingReactEventStore.AdmissionPlan.QUEUE_ONLY,
            PendingReactEventStore.admissionPlan(
                deliveryReady = true,
                reactContextAvailable = false,
                pendingCount = 0
            )
        )
    }

    @Test
    fun wallClockRollbackNeverExtendsDeduplicationWindow() {
        assertTrue(PendingReactEventStore.isWithinDedupWindow(12_000L, 10_500L))
        assertFalse(PendingReactEventStore.isWithinDedupWindow(12_501L, 10_500L))
        assertFalse(PendingReactEventStore.isWithinDedupWindow(9_000L, 10_500L))
        assertFalse(PendingReactEventStore.isWithinDedupWindow(12_000L, 0L))
    }
}
