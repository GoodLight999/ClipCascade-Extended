package com.clipcascade

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.net.Uri
import org.json.JSONArray

/** Shared clipboard parsing and immediate URI staging for foreground/overlay reads. */
object ClipboardPayloadReader {
    /** Synchronous text-only probe used by automatic diagnostics. */
    fun read(context: Context, clipboardManager: ClipboardManager): Map<String, String>? {
        val clip = clipboardManager.primaryClip ?: return null
        if (clip.itemCount <= 0) return null
        if ((0 until clip.itemCount).any { clip.getItemAt(it).uri != null }) return null
        return firstText(context, clip)?.let { mapOf("content" to it, "type" to "text") }
    }

    /**
     * Reads text immediately or copies URI bytes into app-owned cache before returning.
     * The callback can run on a SharedPayloadStager worker thread.
     */
    fun readOrStage(
        context: Context,
        clipboardManager: ClipboardManager,
        callback: (Result<Map<String, String>?>) -> Unit
    ) {
        val app = context.applicationContext
        val clip = runCatching { clipboardManager.primaryClip }.getOrElse {
            callback(Result.failure(it))
            return
        }
        if (clip == null || clip.itemCount <= 0) {
            callback(Result.success(null))
            return
        }

        val uris = buildList<Uri> {
            for (index in 0 until clip.itemCount) {
                clip.getItemAt(index).uri?.let(::add)
            }
        }
        if (uris.isNotEmpty()) {
            val mimeTypes = buildList {
                for (index in 0 until clip.description.mimeTypeCount) {
                    add(clip.description.getMimeType(index).orEmpty())
                }
            }
            val isSingleImage = uris.size == 1 && mimeTypes.any { it.startsWith("image/") }
            AsyncStorageBridge(app).setValue(
                "clipboard_fallback_status",
                "clipboard-uri-staging:${uris.size}"
            )
            SharedPayloadStager.stage(app, uris) { result ->
                result.onSuccess { staged ->
                    val payload = if (isSingleImage) {
                        mapOf("content" to staged.single().toString(), "type" to "image")
                    } else {
                        mapOf(
                            "content" to JSONArray(staged.map(Uri::toString)).toString(),
                            "type" to "files"
                        )
                    }
                    AsyncStorageBridge(app).setValue(
                        "clipboard_fallback_status",
                        "clipboard-uri-staged:${staged.size}"
                    )
                    callback(Result.success(payload))
                }.onFailure { error ->
                    AsyncStorageBridge(app).setValue(
                        "clipboard_fallback_status",
                        "clipboard-uri-staging-error:${error.javaClass.simpleName}:${error.message}"
                            .take(300)
                    )
                    callback(Result.failure(error))
                }
            }
            return
        }

        callback(
            Result.success(
                firstText(context, clip)?.let { mapOf("content" to it, "type" to "text") }
            )
        )
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
