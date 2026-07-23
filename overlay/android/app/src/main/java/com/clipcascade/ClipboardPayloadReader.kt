package com.clipcascade

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context

/** Shared clipboard parsing for foreground listeners and one-shot overlay capture. */
object ClipboardPayloadReader {
    fun read(context: Context, clipboardManager: ClipboardManager): Map<String, String>? {
        val clip = clipboardManager.primaryClip ?: return null
        if (clip.itemCount <= 0) return null

        val mimeTypes = buildList {
            for (index in 0 until clip.description.mimeTypeCount) {
                add(clip.description.getMimeType(index).orEmpty())
            }
        }

        if (mimeTypes.any { it.startsWith("text/") }) {
            firstText(context, clip)?.let { text ->
                return mapOf("content" to text, "type" to "text")
            }
        }

        val uris = buildList {
            for (index in 0 until clip.itemCount) {
                clip.getItemAt(index).uri?.toString()?.let(::add)
            }
        }
        if (uris.isEmpty()) return null

        return if (mimeTypes.any { it.startsWith("image/") } && uris.size == 1) {
            mapOf("content" to uris.first(), "type" to "image")
        } else {
            mapOf("content" to uris.joinToString(","), "type" to "files")
        }
    }

    private fun firstText(context: Context, clip: ClipData): String? {
        for (index in 0 until clip.itemCount) {
            val item = clip.getItemAt(index)
            val text = item.text?.toString()
                ?: item.htmlText
                ?: runCatching { item.coerceToText(context)?.toString() }.getOrNull()
            if (!text.isNullOrEmpty()) return text
        }
        return null
    }
}
