package com.clipcascade

import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import androidx.core.content.FileProvider
import java.io.File
import java.util.UUID
import java.util.concurrent.Executors

/**
 * ACTION_SEND URI grants may expire before React Native drains a durable event.
 * Copy shared payloads into app-owned cache first, then expose stable FileProvider URIs.
 */
object SharedPayloadStager {
    private const val ROOT = "shared_outbound"
    private const val RETENTION_MS = 24L * 60L * 60L * 1000L
    private const val MAX_SINGLE_FILE_BYTES = 512L * 1024L * 1024L
    private val executor = Executors.newSingleThreadExecutor { runnable ->
        Thread(runnable, "ClipCascade-ShareStager").apply { isDaemon = true }
    }

    fun stage(
        context: Context,
        uris: List<Uri>,
        callback: (Result<List<Uri>>) -> Unit
    ) {
        val app = context.applicationContext
        executor.execute {
            callback(runCatching { stageBlocking(app, uris) })
        }
    }

    private fun stageBlocking(context: Context, uris: List<Uri>): List<Uri> {
        require(uris.isNotEmpty()) { "No shared URI supplied" }
        cleanupExpired(context)

        val batch = File(context.cacheDir, "$ROOT/${UUID.randomUUID()}")
        check(batch.mkdirs()) { "Unable to create shared-payload cache" }
        val staged = mutableListOf<Uri>()
        try {
            uris.forEachIndexed { index, source ->
                val displayName = safeDisplayName(context, source, index)
                val target = uniqueTarget(batch, displayName)
                context.contentResolver.openInputStream(source)?.use { input ->
                    target.outputStream().buffered().use { output ->
                        val buffer = ByteArray(DEFAULT_BUFFER_SIZE)
                        var total = 0L
                        while (true) {
                            val read = input.read(buffer)
                            if (read < 0) break
                            total += read
                            check(total <= MAX_SINGLE_FILE_BYTES) {
                                "Shared file exceeds ${MAX_SINGLE_FILE_BYTES} bytes"
                            }
                            output.write(buffer, 0, read)
                        }
                    }
                } ?: error("Unable to open shared URI: $source")

                staged += FileProvider.getUriForFile(
                    context,
                    "${context.packageName}.fileprovider",
                    target
                )
            }
            return staged
        } catch (error: Throwable) {
            batch.deleteRecursively()
            throw error
        }
    }

    private fun safeDisplayName(context: Context, uri: Uri, index: Int): String {
        val queried = runCatching {
            context.contentResolver.query(
                uri,
                arrayOf(OpenableColumns.DISPLAY_NAME),
                null,
                null,
                null
            )?.use { cursor ->
                val column = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                if (column >= 0 && cursor.moveToFirst()) cursor.getString(column) else null
            }
        }.getOrNull()
        val fallback = uri.lastPathSegment?.substringAfterLast('/') ?: "shared_$index"
        return sanitize(queried ?: fallback).ifBlank { "shared_$index" }
    }

    internal fun sanitize(name: String): String = name
        .replace(Regex("[\\u0000-\\u001f\\u007f/\\\\:*?\"<>|]"), "_")
        .trim()
        .take(180)
        .ifBlank { "shared" }

    private fun uniqueTarget(directory: File, originalName: String): File {
        var candidate = File(directory, originalName)
        if (!candidate.exists()) return candidate
        val dot = originalName.lastIndexOf('.')
        val stem = if (dot > 0) originalName.substring(0, dot) else originalName
        val extension = if (dot > 0) originalName.substring(dot) else ""
        var suffix = 1
        while (candidate.exists()) {
            candidate = File(directory, "$stem ($suffix)$extension")
            suffix += 1
        }
        return candidate
    }

    private fun cleanupExpired(context: Context) {
        val root = File(context.cacheDir, ROOT)
        val cutoff = System.currentTimeMillis() - RETENTION_MS
        root.listFiles()?.forEach { batch ->
            if (batch.lastModified() < cutoff) batch.deleteRecursively()
        }
    }
}
