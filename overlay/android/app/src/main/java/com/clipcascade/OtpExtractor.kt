package com.clipcascade

import kotlin.math.abs

/**
 * Extracts a 4-8 digit one-time code only when an authentication keyword is
 * nearby. The conservative keyword requirement avoids copying arbitrary order,
 * tracking, phone, and payment numbers from notifications.
 */
object OtpExtractor {
    private val candidatePattern = Regex("""(?<!\d)(?:\d{3}[\s-]?\d{3}|\d{4,8})(?!\d)""")
    private val keywordPattern = Regex(
        """\b(?:otp|one[- ]time(?: password| passcode)?|verification(?: code)?|security code|auth(?:entication)? code|passcode|login code|your code|code is|2fa|two[- ]factor)\b|認証(?:コード|番号)?|確認コード|ワンタイム(?:パスワード|コード)?|验证码|校验码|动态码|인증번호""",
        setOf(RegexOption.IGNORE_CASE)
    )

    fun extract(parts: Iterable<CharSequence?>): String? {
        val text = parts
            .mapNotNull { it?.toString()?.trim()?.takeIf(String::isNotEmpty) }
            .joinToString("\n")
        if (text.isBlank()) return null

        val keywords = keywordPattern.findAll(text).toList()
        if (keywords.isEmpty()) return null

        return candidatePattern.findAll(text)
            .mapNotNull { candidate ->
                val digits = candidate.value.filter(Char::isDigit)
                if (digits.length !in 4..8) return@mapNotNull null
                val center = (candidate.range.first + candidate.range.last) / 2
                val distance = keywords.minOf { keyword ->
                    abs(center - (keyword.range.first + keyword.range.last) / 2)
                }
                if (distance > 96) return@mapNotNull null
                val lengthPenalty = when (digits.length) {
                    6 -> 0
                    5, 7, 8 -> 2
                    else -> 4
                }
                val yearPenalty = if (
                    digits.length == 4 && digits.toIntOrNull() in 1900..2099
                ) 40 else 0
                ScoredCode(digits, distance + lengthPenalty + yearPenalty, candidate.range.first)
            }
            .minWithOrNull(compareBy<ScoredCode> { it.score }.thenBy { it.position })
            ?.code
    }

    private data class ScoredCode(
        val code: String,
        val score: Int,
        val position: Int
    )
}
