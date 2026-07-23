package com.clipcascade

import android.view.accessibility.AccessibilityEvent
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
    fun acceptsEnglishJapaneseAndChineseCopyFeedback() {
        val samples = listOf("Copied to clipboard", "クリップボードにコピーしました", "已复制到剪贴板")
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
    fun ignoresGenericClicksButAcceptsExplicitCopyButton() {
        val generic = CopySignalClassifier.classify(
            AccessibilityEvent.TYPE_VIEW_CLICKED,
            "example.app",
            listOf("Open"),
            ownPackage
        )
        val copy = CopySignalClassifier.classify(
            AccessibilityEvent.TYPE_VIEW_CLICKED,
            "example.app",
            listOf("コピー"),
            ownPackage
        )
        assertFalse(generic.capture)
        assertTrue(copy.capture)
    }

    @Test
    fun selectionChangeCreatesDelayedProbe() {
        val result = CopySignalClassifier.classify(
            AccessibilityEvent.TYPE_VIEW_TEXT_SELECTION_CHANGED,
            "example.app",
            emptyList(),
            ownPackage
        )
        assertTrue(result.capture)
        assertTrue(result.delayMs >= 300L)
    }
}
