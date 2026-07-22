package com.clipcascade

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class OtpExtractorTest {
    @Test
    fun extractsEnglishCodeFromMultilineNotification() {
        assertEquals(
            "713642",
            OtpExtractor.extract(listOf("DAWN", "Your code is", "713642", "Expires in 10 minutes"))
        )
    }

    @Test
    fun extractsJapaneseAndChineseCodes() {
        assertEquals("4821", OtpExtractor.extract(listOf("ログイン認証コード: 4821")))
        assertEquals("938204", OtpExtractor.extract(listOf("您的验证码是 938-204")))
    }

    @Test
    fun prefersCodeNearestAuthenticationKeyword() {
        assertEquals(
            "654321",
            OtpExtractor.extract(listOf("Order 12345678", "Verification code: 654321"))
        )
    }

    @Test
    fun ignoresNumbersWithoutAuthenticationContext() {
        assertNull(OtpExtractor.extract(listOf("Order shipped", "Tracking number 713642")))
        assertNull(OtpExtractor.extract(listOf("Meeting starts at 2026-07-23 10:30")))
    }
}
