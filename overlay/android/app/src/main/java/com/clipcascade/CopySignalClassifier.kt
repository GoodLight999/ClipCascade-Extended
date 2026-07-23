package com.clipcascade

import android.view.accessibility.AccessibilityEvent

/** Pure copy-signal policy separated from AccessibilityService lifecycle. */
object CopySignalClassifier {
    data class Decision(
        val capture: Boolean,
        val delayMs: Long = 0L,
        val reason: String = "ignored"
    )

    private val strongCopyPhrases = listOf(
        Regex("\\bcopied(?:\\s+to\\s+(?:the\\s+)?clipboard)?\\b", RegexOption.IGNORE_CASE),
        Regex("\\bcopy(?:ied)?\\s+to\\s+(?:the\\s+)?clipboard\\b", RegexOption.IGNORE_CASE),
        Regex("クリップボードにコピー(?:しました|済み)?"),
        Regex("コピー(?:しました|済み)"),
        Regex("已复制(?:到剪贴板)?"),
        Regex("已複製(?:到剪貼簿)?"),
        Regex("复制到剪贴板"),
        Regex("複製到剪貼簿"),
        Regex("클립보드에 복사(?:됨|했습니다)?"),
        Regex("복사(?:됨|했습니다)")
    )

    private val explicitCopyLabels = setOf(
        "copy", "copy text", "copy link", "copy image",
        "コピー", "テキストをコピー", "リンクをコピー", "画像をコピー",
        "复制", "复制文本", "复制链接", "复制图片",
        "複製", "複製文字", "複製連結", "複製圖片",
        "복사", "텍스트 복사", "링크 복사", "이미지 복사"
    )

    fun classify(
        eventType: Int,
        sourcePackage: String?,
        texts: List<String>,
        ownPackage: String
    ): Decision {
        if (sourcePackage.isNullOrBlank() || sourcePackage == ownPackage) {
            return Decision(false, reason = "self-or-unknown-package")
        }

        val normalized = texts
            .asSequence()
            .map { it.trim() }
            .filter { it.isNotEmpty() }
            .toList()
        val joined = normalized.joinToString(" ")
        val strongPhrase = strongCopyPhrases.any { it.containsMatchIn(joined) }
        val explicitLabel = normalized.any { it.lowercase() in explicitCopyLabels }

        return when (eventType) {
            AccessibilityEvent.TYPE_NOTIFICATION_STATE_CHANGED,
            AccessibilityEvent.TYPE_ANNOUNCEMENT -> if (strongPhrase) {
                Decision(true, delayMs = 140L, reason = "localized-copy-announcement")
            } else {
                Decision(false, reason = "unrelated-announcement")
            }

            AccessibilityEvent.TYPE_VIEW_CLICKED -> if (explicitLabel || strongPhrase) {
                Decision(true, delayMs = 180L, reason = "explicit-copy-action")
            } else {
                Decision(false, reason = "generic-click")
            }

            AccessibilityEvent.TYPE_VIEW_TEXT_SELECTION_CHANGED ->
                Decision(true, delayMs = 420L, reason = "selection-change-probe")

            AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED -> if (strongPhrase) {
                Decision(true, delayMs = 220L, reason = "copy-feedback-content-change")
            } else {
                Decision(false, reason = "unrelated-content-change")
            }

            else -> Decision(false, reason = "unsupported-event")
        }
    }
}
