package com.clipcascade

import android.content.Context
import androidx.annotation.Keep
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/** Runs only during the one-time Shizuku setup and exits immediately afterwards. */
class ClipCascadeSetupUserService() : IClipCascadeSetupService.Stub() {
    @Keep
    constructor(@Suppress("UNUSED_PARAMETER") context: Context) : this()

    override fun applySetup(packageName: String): String {
        require(packageName == BuildConfig.APPLICATION_ID) { "Unexpected package: $packageName" }
        val commands = listOf(
            listOf("cmd", "package", "grant", packageName, android.Manifest.permission.READ_LOGS),
            listOf("cmd", "appops", "set", packageName, "android:system_alert_window", "allow")
        )
        val results = commands.map(::runCommand)
        val failed = results.filter { it.optInt("exitCode", -1) != 0 }
        if (failed.isNotEmpty()) {
            throw IllegalStateException(
                "One-time Shizuku setup command failed: ${JSONArray(failed)}"
            )
        }
        return JSONObject().apply {
            put("mode", "one-time-shizuku")
            put("commands", JSONArray(results))
            put("inspection", JSONObject(inspectSetup(packageName)))
        }.toString()
    }

    override fun inspectSetup(packageName: String): String {
        require(packageName == BuildConfig.APPLICATION_ID) { "Unexpected package: $packageName" }
        return JSONObject().apply {
            put(
                "readLogs",
                runCommand(
                    listOf(
                        "cmd", "package", "check-permission",
                        android.Manifest.permission.READ_LOGS, packageName, "0"
                    )
                )
            )
            put(
                "overlayAppOp",
                runCommand(listOf("cmd", "appops", "get", packageName, "android:system_alert_window"))
            )
        }.toString()
    }

    override fun destroy() {
        kotlin.system.exitProcess(0)
    }

    private fun runCommand(command: List<String>): JSONObject {
        val process = ProcessBuilder(command).redirectErrorStream(true).start()
        val finished = process.waitFor(12, TimeUnit.SECONDS)
        if (!finished) process.destroyForcibly()
        val output = process.inputStream.bufferedReader().use { it.readText().trim() }
        return JSONObject().apply {
            put("command", command.joinToString(" "))
            put("finished", finished)
            put("exitCode", if (finished) process.exitValue() else -1)
            put("output", output)
        }
    }
}
