package com.clipcascade

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ClipboardAccessPolicyTest {
    private val packageName = "com.clipcascade.extended"

    @Test
    fun detectsAospClipboardServiceDenial() {
        assertTrue(
            ClipboardAccessPolicy.isClipboardDenialLine(
                "W/ClipboardService: Denying clipboard access to com.clipcascade.extended, application is not in focus nor is it a system service",
                packageName
            )
        )
    }

    @Test
    fun detectsOemClipboardManagerDenial() {
        assertTrue(
            ClipboardAccessPolicy.isClipboardDenialLine(
                "E/ClipboardManager: Clipboard access not allowed for com.clipcascade.extended",
                packageName
            )
        )
    }

    @Test
    fun ignoresOtherApplicationsAndNormalClipboardLogs() {
        assertFalse(
            ClipboardAccessPolicy.isClipboardDenialLine(
                "W/ClipboardService: Denying clipboard access to com.example.other, application is not in focus",
                packageName
            )
        )
        assertFalse(
            ClipboardAccessPolicy.isClipboardDenialLine(
                "V/ClipboardService: clipboard listener registered for com.clipcascade.extended",
                packageName
            )
        )
    }

    @Test
    fun logcatStartsFromRecentEntriesAndUsesBothKnownTags() {
        val command = ClipboardAccessPolicy.logcatCommand()
        assertTrue(command.windowed(2).any { it == listOf("-T", "1") })
        assertTrue(command.contains("ClipboardService:V"))
        assertTrue(command.contains("ClipboardManager:V"))
    }
}
