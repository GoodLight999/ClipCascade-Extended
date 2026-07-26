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
    private const val MAX_FILES = 64

    // The current mobile transport is deliberately non-streaming: each decoded
    // file is copied into a native byte array, Base64, JSON and possibly an
    // encrypted/fragmented copy. A 512 MiB staging allowance therefore caused
    // predictable OOM risk before protocol delivery. Keep these decoded limits
    // conservative until both outbound and inbound paths stream end-to-end.
    internal const val MAX_SINGLE_FILE_BYTES = 32L * 1024L * 1024L
    internal const val MAX_BATCH_BYTES = 32L * 1024L * 1024L
    internal const val MAX_CACHE_BYTES = 96L * 1024L * 1024L

    private val executor = Executors.newSingleThreadExecutor { runnable ->
        Thread(runnable, "ClipCascade-ShareStager").apply { isDaemon = true }
    }

    fun cleanup(context: Context) {
        val app = context.applicationContext
        executor.execute { cleanupExpired(app) }
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
        require(uris.size <= MAX_FILES) { "Too many shared files: ${uris.size} > $MAX_FILES" }
        cleanupExpired(context)

        val root = File(context.cacheDir, ROOT)
        val existingBytes = directorySize(root)
        check(existingBytes <= MAX_CACHE_BYTES) {
            "Shared-payload cache already exceeds ${MAX_CACHE_BYTES} bytes"
        }

        val knownSizes = uris.map { knownSize(context, it) }
        knownSizes.forEachIndexed { index, size ->
            if (size >= 0L) {
                check(size <= MAX_SINGLE_FILE_BYTES) {
                    "Shared file ${index + 1} exceeds the 32 MiB mobile safety limit"
                }
            }
        }
        val knownBatchBytes = knownSizes.filter { it >= 0L }.sum()
        check(knownBatchBytes <= MAX_BATCH_BYTES) {
            "Shared batch exceeds the 32 MiB mobile safety limit"
        }
        check(existingBytes + knownBatchBytes <= MAX_CACHE_BYTES) {
            "Shared-payload cache would exceed ${MAX_CACHE_BYTES} bytes"
        }

        val batch = File(root, UUID.randomUUID().toString())
        check(batch.mkdirs()) { "Unable to create shared-payload cache" }
        val staged = mutableListOf<Uri>()
        var batchBytes = 0L
        try {
            uris.forEachIndexed { index, source ->
                val displayName = safeDisplayName(context, source, index)
                val target = uniqueTarget(batch, displayName)
                context.contentResolver.openInputStream(source)?.use { input ->
                    target.outputStream().buffered().use { output ->
                        val buffer = ByteArray(DEFAULT_BUFFER_SIZE)
                        var fileBytes = 0L
                        while (true) {
                            val read = input.read(buffer)
                            if (read < 0) break
                            fileBytes += read
                            batchBytes += read
                            check(fileBytes <= MAX_SINGLE_FILE_BYTES) {
                                "Shared file exceeds the 32 MiB mobile safety limit"
                            }
                            check(batchBytes <= MAX_BATCH_BYTES) {
                                "Shared batch exceeds the 32 MiB mobile safety limit"
                            }
                            check(existingBytes + batchBytes <= MAX_CACHE_BYTES) {
                                "Shared-payload cache exceeds ${MAX_CACHE_BYTES} bytes"
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

    private fun knownSize(context: Context, uri: Uri): Long = runCatching {
        context.contentResolver.query(
            uri,
            arrayOf(OpenableColumns.SIZE),
            null,
            null,
            null
        )?.use { cursor ->
            val column = cursor.getColumnIndex(OpenableColumns.SIZE)
            if (column >= 0 && cursor.moveToFirst() && !cursor.isNull(column)) {
                cursor.getLong(column)
            } else {
                -1L
            }
        } ?: -1L
    }.getOrDefault(-1L)

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

    private fun directorySize(file: File): Long {
        if (!file.exists()) return 0L
        if (file.isFile) return file.length().coerceAtLeast(0L)
        return file.listFiles()?.sumOf(::directorySize) ?: 0L
    }
}
