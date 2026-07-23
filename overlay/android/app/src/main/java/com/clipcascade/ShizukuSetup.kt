package com.clipcascade

import android.content.ComponentName
import android.content.Context
import android.content.ServiceConnection
import android.content.pm.PackageManager
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.SystemClock
import androidx.core.content.ContextCompat
import com.facebook.react.bridge.Promise
import org.json.JSONObject
import rikka.shizuku.Shizuku
import java.util.concurrent.Executors

/** One-shot setup helper. ClipCascade runtime must never depend on Shizuku staying alive. */
object ShizukuSetup {
    private const val REQUEST_CODE = 7342
    private const val BINDER_TIMEOUT_MS = 8_000L
    private const val PERMISSION_TIMEOUT_MS = 30_000L
    private const val SETUP_TIMEOUT_MS = 30_000L
    private const val SHIZUKU_PACKAGE = "moe.shizuku.privileged.api"

    private val handler = Handler(Looper.getMainLooper())
    private val setupExecutor = Executors.newSingleThreadExecutor { runnable ->
        Thread(runnable, "ClipCascade-ShizukuSetup").apply { isDaemon = true }
    }
    private val binderMonitor = Object()

    @Volatile
    private var binderLastEvent = "not-observed"

    private var permissionPromise: Promise? = null
    private var permissionTimeout: Runnable? = null
    private var setupPromise: Promise? = null
    private var applyWaitingForBinder = false
    private var activeConnection: ServiceConnection? = null
    private var setupTimeout: Runnable? = null

    private val binderReceivedListener = Shizuku.OnBinderReceivedListener {
        binderLastEvent = "received:${SystemClock.elapsedRealtime()}"
        synchronized(binderMonitor) { binderMonitor.notifyAll() }
    }

    private val binderDeadListener = Shizuku.OnBinderDeadListener {
        binderLastEvent = "dead:${SystemClock.elapsedRealtime()}"
        synchronized(binderMonitor) { binderMonitor.notifyAll() }
    }

    private val permissionListener = Shizuku.OnRequestPermissionResultListener { requestCode, result ->
        if (requestCode != REQUEST_CODE) return@OnRequestPermissionResultListener
        finishPermissionRequest(result)
    }

    init {
        // The provider delivers its Binder asynchronously. A one-shot ping performed
        // before this callback is not proof that Shizuku is stopped.
        Shizuku.addBinderReceivedListenerSticky(binderReceivedListener)
        Shizuku.addBinderDeadListener(binderDeadListener)
        Shizuku.addRequestPermissionResultListener(permissionListener)
    }

    fun status(context: Context): String = JSONObject().apply {
        val running = binderAlive()
        val packageInstalled = runCatching {
            context.packageManager.getPackageInfo(SHIZUKU_PACKAGE, 0)
            true
        }.getOrDefault(false)
        put("installed", packageInstalled)
        put("running", running)
        put("binderEvent", binderLastEvent)
        put("permissionGranted", running && runCatching {
            Shizuku.checkSelfPermission() == PackageManager.PERMISSION_GRANTED
        }.getOrDefault(false))
        put("serverUid", if (running) runCatching { Shizuku.getUid() }.getOrDefault(-1) else -1)
        put("apiVersion", if (running) runCatching { Shizuku.getVersion() }.getOrDefault(-1) else -1)
        put(
            "readLogs",
            ContextCompat.checkSelfPermission(context, android.Manifest.permission.READ_LOGS) ==
                PackageManager.PERMISSION_GRANTED
        )
        put("overlay", android.provider.Settings.canDrawOverlays(context))
        put("runtimeDependency", false)
        put("usage", "one-time-setup-only")
    }.toString()

    @Synchronized
    fun requestPermission(promise: Promise) {
        if (permissionPromise != null) {
            promise.reject("SHIZUKU_BUSY", "A Shizuku permission request is already open")
            return
        }
        permissionPromise = promise
        setupExecutor.execute {
            val ready = awaitBinder(BINDER_TIMEOUT_MS)
            handler.post {
                if (!ready) {
                    failPermissionRequest(
                        "SHIZUKU_NOT_RUNNING",
                        "Shizuku Binder was not delivered. Open Shizuku, confirm that its service is running, then try again."
                    )
                } else {
                    beginPermissionRequest()
                }
            }
        }
    }

    @Synchronized
    private fun beginPermissionRequest() {
        val promise = permissionPromise ?: return
        val alreadyGranted = runCatching {
            Shizuku.checkSelfPermission() == PackageManager.PERMISSION_GRANTED
        }.getOrElse { error ->
            failPermissionRequest("SHIZUKU_PERMISSION_ERROR", error.message ?: "Permission check failed", error)
            return
        }
        if (alreadyGranted) {
            permissionPromise = null
            promise.resolve(true)
            return
        }

        val timeout = Runnable {
            synchronized(this@ShizukuSetup) {
                if (permissionPromise != null) {
                    failPermissionRequest(
                        "SHIZUKU_PERMISSION_TIMEOUT",
                        "Shizuku permission request timed out"
                    )
                }
            }
        }
        permissionTimeout = timeout
        handler.postDelayed(timeout, PERMISSION_TIMEOUT_MS)
        try {
            Shizuku.requestPermission(REQUEST_CODE)
        } catch (error: Throwable) {
            failPermissionRequest(
                "SHIZUKU_PERMISSION_ERROR",
                error.message ?: "Unable to request Shizuku permission",
                error
            )
        }
    }

    @Synchronized
    fun apply(context: Context, promise: Promise) {
        if (setupPromise != null || applyWaitingForBinder) {
            promise.reject("SHIZUKU_BUSY", "Setup is already running")
            return
        }
        applyWaitingForBinder = true
        val app = context.applicationContext
        setupExecutor.execute {
            val ready = awaitBinder(BINDER_TIMEOUT_MS)
            handler.post {
                synchronized(this@ShizukuSetup) { applyWaitingForBinder = false }
                if (!ready) {
                    promise.reject(
                        "SHIZUKU_NOT_RUNNING",
                        "Shizuku Binder was not delivered. Open Shizuku, confirm that its service is running, then try again."
                    )
                } else {
                    beginApply(app, promise)
                }
            }
        }
    }

    @Synchronized
    private fun beginApply(app: Context, promise: Promise) {
        val permissionGranted = runCatching {
            Shizuku.checkSelfPermission() == PackageManager.PERMISSION_GRANTED
        }.getOrElse { error ->
            promise.reject("SHIZUKU_PERMISSION_ERROR", error.message, error)
            return
        }
        if (!permissionGranted) {
            promise.reject("SHIZUKU_PERMISSION_REQUIRED", "Authorize ClipCascade Extended in Shizuku first")
            return
        }
        if (setupPromise != null) {
            promise.reject("SHIZUKU_BUSY", "Setup is already running")
            return
        }

        val args = Shizuku.UserServiceArgs(
            ComponentName(BuildConfig.APPLICATION_ID, ClipCascadeSetupUserService::class.java.name)
        )
            .daemon(false)
            .processNameSuffix("setup")
            .debuggable(BuildConfig.DEBUG)
            .version(BuildConfig.VERSION_CODE)

        val connection = object : ServiceConnection {
            override fun onServiceConnected(name: ComponentName, binder: IBinder) {
                val connection = this
                synchronized(this@ShizukuSetup) {
                    if (setupPromise == null || activeConnection !== connection) return
                }
                setupExecutor.execute {
                    synchronized(this@ShizukuSetup) {
                        if (setupPromise == null || activeConnection !== connection) return@execute
                    }
                    try {
                        val service = IClipCascadeSetupService.Stub.asInterface(binder)
                        val remote = JSONObject(service.applySetup(app.packageName))
                        val verified = waitForVerification(app, connection)
                        remote.put("verified", verified)
                        if (!verified.getBoolean("readLogs") || !verified.getBoolean("overlay")) {
                            throw IllegalStateException(
                                "Android did not retain the required grants: $verified"
                            )
                        }
                        handler.post { finishSetup(args, connection, result = remote.toString()) }
                    } catch (error: Throwable) {
                        handler.post { finishSetup(args, connection, error = error) }
                    }
                }
            }

            override fun onServiceDisconnected(name: ComponentName) {
                handler.post {
                    finishSetup(
                        args,
                        this,
                        error = IllegalStateException("Shizuku setup service disconnected")
                    )
                }
            }
        }

        setupPromise = promise
        activeConnection = connection
        val timeout = Runnable {
            synchronized(this@ShizukuSetup) {
                if (setupPromise != null && activeConnection === connection) {
                    finishSetup(
                        args,
                        connection,
                        error = IllegalStateException("Shizuku setup timed out")
                    )
                }
            }
        }
        setupTimeout = timeout
        handler.postDelayed(timeout, SETUP_TIMEOUT_MS)
        try {
            Shizuku.bindUserService(args, connection)
        } catch (error: Throwable) {
            finishSetup(args, connection, error = error)
        }
    }

    @Synchronized
    private fun finishPermissionRequest(result: Int) {
        val promise = permissionPromise ?: return
        permissionPromise = null
        permissionTimeout?.let(handler::removeCallbacks)
        permissionTimeout = null
        if (result == PackageManager.PERMISSION_GRANTED) {
            promise.resolve(true)
        } else {
            promise.reject("SHIZUKU_DENIED", "Shizuku permission was denied")
        }
    }

    @Synchronized
    private fun failPermissionRequest(code: String, message: String, error: Throwable? = null) {
        val promise = permissionPromise ?: return
        permissionPromise = null
        permissionTimeout?.let(handler::removeCallbacks)
        permissionTimeout = null
        promise.reject(code, message, error)
    }

    @Synchronized
    private fun finishSetup(
        args: Shizuku.UserServiceArgs,
        connection: ServiceConnection,
        result: String? = null,
        error: Throwable? = null
    ) {
        if (activeConnection !== connection) return
        val promise = setupPromise
        setupPromise = null
        activeConnection = null
        setupTimeout?.let(handler::removeCallbacks)
        setupTimeout = null
        try {
            if (binderAlive()) Shizuku.unbindUserService(args, connection, true)
        } catch (_: Throwable) {
        }
        if (promise != null) {
            if (error == null) {
                promise.resolve(result)
            } else {
                promise.reject("SHIZUKU_SETUP_ERROR", error.message, error)
            }
        }
    }

    private fun waitForVerification(context: Context, connection: ServiceConnection): JSONObject {
        val deadline = SystemClock.elapsedRealtime() + 5_000L
        var latest = JSONObject(status(context))
        while (SystemClock.elapsedRealtime() < deadline) {
            synchronized(this@ShizukuSetup) {
                if (setupPromise == null || activeConnection !== connection) {
                    throw IllegalStateException("Shizuku setup was cancelled before verification")
                }
            }
            if (latest.optBoolean("readLogs") && latest.optBoolean("overlay")) return latest
            Thread.sleep(150L)
            latest = JSONObject(status(context))
        }
        return latest
    }

    private fun awaitBinder(timeoutMs: Long): Boolean {
        if (binderAlive()) return true
        val deadline = SystemClock.elapsedRealtime() + timeoutMs
        synchronized(binderMonitor) {
            while (!binderAlive()) {
                val remaining = deadline - SystemClock.elapsedRealtime()
                if (remaining <= 0L) break
                try {
                    binderMonitor.wait(minOf(remaining, 500L))
                } catch (_: InterruptedException) {
                    Thread.currentThread().interrupt()
                    break
                }
            }
        }
        return binderAlive()
    }

    private fun binderAlive(): Boolean = runCatching { Shizuku.pingBinder() }.getOrDefault(false)
}
