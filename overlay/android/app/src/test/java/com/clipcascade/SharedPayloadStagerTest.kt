package com.clipcascade

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class SharedPayloadStagerTest {
    @Test
    fun removesPathAndPlatformUnsafeCharacters() {
        val sanitized = SharedPayloadStager.sanitize("../bad\\name:*?\"<>|.txt")
        assertFalse(sanitized.contains('/'))
        assertFalse(sanitized.contains('\\'))
        assertFalse(sanitized.contains(':'))
        assertTrue(sanitized.endsWith(".txt"))
    }

    @Test
    fun boundsLongNamesAndProvidesFallback() {
        assertEquals("shared", SharedPayloadStager.sanitize("   "))
        assertTrue(SharedPayloadStager.sanitize("a".repeat(500)).length <= 180)
    }

    @Test
    fun keepsNormalJapaneseFilename() {
        assertEquals("会議資料.pdf", SharedPayloadStager.sanitize("会議資料.pdf"))
    }
}
