package com.clipcascade

import java.util.Locale

/** Pure policy kept separate from Android APIs so OEM log variants are unit-testable. */
object ClipboardAccessPolicy {
    private val denialMarkers = listOf(
        "denying clipboard access",
        "clipboard access denied",
        "clipboard access not allowed",
        "not allowed to access clipboard",
        "does not have focus",
        "not in focus",
        "background clipboard access"
    )

    fun isClipboardDenialLine(line: String, applicationId: String): Boolean {
        if (line.isBlank() || applicationId.isBlank()) return false
        val normalized = line.lowercase(Locale.ROOT)
        if (!normalized.contains("clipboard")) return false
        if (!normalized.contains(applicationId.lowercase(Locale.ROOT))) return false
        return denialMarkers.any(normalized::contains)
    }

    fun logcatCommand(): List<String> = listOf(
        "logcat",
        "-T",
        "1",
        "ClipboardService:V",
        "ClipboardManager:V",
        "*:S"
    )
}
