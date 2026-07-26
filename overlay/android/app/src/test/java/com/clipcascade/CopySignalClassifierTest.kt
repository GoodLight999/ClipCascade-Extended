package com.clipcascade

import android.view.accessibility.AccessibilityEvent
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class CopySignalClassifierTest {
    private val ownPackage = "com.clipcascade.extended"

    @Test
    fun ignoresOwnPackage() {
        val result = CopySignalClassifier.classify(
            AccessibilityEvent.TYPE_ANNOUNCEMENT,
            ownPackage,
            listOf("Copied to clipboard"),
            ownPackage
        )
        assertFalse(result.capture)
    }

    @Test
    fun acceptsLocalizedCopyFeedback() {
        val samples = listOf(
            "Copied to clipboard",
            "クリップボードにコピーしました",
            "已复制到剪贴板",
            "已複製到剪貼簿",
            "클립보드에 복사했습니다"
        )
        samples.forEach { text ->
            val result = CopySignalClassifier.classify(
                AccessibilityEvent.TYPE_NOTIFICATION_STATE_CHANGED,
                "example.app",
                listOf(text),
                ownPackage
            )
            assertTrue(text, result.capture)
        }
    }

    @Test
    fun rejectsUnrelatedNotificationNumbers() {
        val result = CopySignalClassifier.classify(
            AccessibilityEvent.TYPE_NOTIFICATION_STATE_CHANGED,
            "example.app",
            listOf("Order 123456 has shipped"),
            ownPackage
        )
        assertFalse(result.capture)
    }

    @Test
    fun ignoresGenericClicksButAcceptsExplicitCopyButtons() {
        val generic = CopySignalClassifier.classify(
            AccessibilityEvent.TYPE_VIEW_CLICKED,
            "example.app",
            listOf("Open"),
            ownPackage
        )
        val labels = listOf("Copy", "アドレスをコピー", "复制地址", "주소 복사")
        assertFalse(generic.capture)
        labels.forEach { label ->
            val copy = CopySignalClassifier.classify(
                AccessibilityEvent.TYPE_VIEW_CLICKED,
                "example.app",
                listOf(label),
                ownPackage
            )
            assertTrue(label, copy.capture)
        }
    }

    @Test
    fun selectionWithoutCopyNeverTriggersCapture() {
        val result = CopySignalClassifier.classify(
            AccessibilityEvent.TYPE_VIEW_TEXT_SELECTION_CHANGED,
            "example.app",
            listOf("selected text"),
            ownPackage
        )
        assertFalse(result.capture)
        assertEquals("selection-without-copy", result.reason)
    }

    @Test
    fun rejectsUnknownPackageEvenWithCopyText() {
        val result = CopySignalClassifier.classify(
            AccessibilityEvent.TYPE_ANNOUNCEMENT,
            null,
            listOf("Copied"),
            ownPackage
        )
        assertFalse(result.capture)
    }
}
