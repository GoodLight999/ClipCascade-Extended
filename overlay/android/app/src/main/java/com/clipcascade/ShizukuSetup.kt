package com.clipcascade

import android.content.ComponentName
import android.content.Context
import android.content.ServiceConnection
import android.content.pm.PackageManager
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import androidx.core.content.ContextCompat
import com.facebook.react.bridge.Promise
import org.json.JSONObject
import rikka.shizuku.Shizuku
import java.util.concurrent.Executors

/** One-shot setup helper. ClipCascade runtime must never depend on Shizuku staying alive. */
object ShizukuSetup {
    private const val REQUEST_CODE = 7342
    private const val PERMISSION_TIMEOUT_MS = 30_000L
    private const val SETUP_TIMEOUT_MS = 30_000L
    private val handler = Handler(Looper.getMainLooper())
    private val setupExecutor = Executors.newSingleThreadExecutor { runnable ->
        Thread(runnable, "ClipCascade-ShizukuSetup").apply { isDaemon = true }
    }
    private var permissionPromise: Promise? = null
    private var permissionTimeout: Runnable? = null
    private var setupPromise: Promise? = null
    private var activeConnection: ServiceConnection? = null
    private var setupTimeout: Runnable? = null

    private val permissionListener = Shizuku.OnRequestPermissionResultListener { requestCode, result ->
        if (requestCode != REQUEST_CODE) return@OnRequestPermissionResultListener
        finishPermissionRequest(result)
    }

    init {
        Shizuku.addRequestPermissionResultListener(permissionListener)
    }

    fun status(context: Context): String = JSONObject().apply {
        val running = binderAlive()
        put("running", running)
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
        if (!binderAlive()) {
            promise.reject("SHIZUKU_NOT_RUNNING", "Start Shizuku once, then return to ClipCascade")
            return
        }
        val alreadyGranted = runCatching {
            Shizuku.checkSelfPermission() == PackageManager.PERMISSION_GRANTED
        }.getOrElse { error ->
            promise.reject("SHIZUKU_PERMISSION_ERROR", error.message, error)
            return
        }
        if (alreadyGranted) {
            promise.resolve(true)
            return
        }
        if (permissionPromise != null) {
            promise.reject("SHIZUKU_BUSY", "A Shizuku permission request is already open")
            return
        }

        permissionPromise = promise
        val timeout = Runnable {
            synchronized(this@ShizukuSetup) {
                val pending = permissionPromise ?: return@synchronized
                permissionPromise = null
                permissionTimeout = null
                pending.reject(
                    "SHIZUKU_PERMISSION_TIMEOUT",
                    "Shizuku permission request timed out; restart Shizuku and try again"
                )
            }
        }
        permissionTimeout = timeout
        handler.postDelayed(timeout, PERMISSION_TIMEOUT_MS)
        try {
            Shizuku.requestPermission(REQUEST_CODE)
        } catch (error: Throwable) {
            handler.removeCallbacks(timeout)
            permissionTimeout = null
            permissionPromise = null
            promise.reject("SHIZUKU_PERMISSION_ERROR", error.message, error)
        }
    }

    @Synchronized
    fun apply(context: Context, promise: Promise) {
        if (!binderAlive()) {
            promise.reject("SHIZUKU_NOT_RUNNING", "Start Shizuku once, then return to ClipCascade")
            return
        }
        val permissionGranted = runCatching {
            Shizuku.checkSelfPermission() == PackageManager.PERMISSION_GRANTED
        }.getOrElse { error ->
            promise.reject("SHIZUKU_PERMISSION_ERROR", error.message, error)
            return
        }
        if (!permissionGranted) {
            promise.reject("SHIZUKU_PERMISSION_REQUIRED", "Authorize ClipCascade in Shizuku first")
            return
        }
        if (setupPromise != null) {
            promise.reject("SHIZUKU_BUSY", "Setup is already running")
            return
        }

        val app = context.applicationContext
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
                                "Shizuku commands returned but Android did not retain the required grants: $verified"
                            )
                        }
                        handler.post {
                            finishSetup(args, connection, result = remote.toString())
                        }
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
            if (error == null) promise.resolve(result) else promise.reject(
                "SHIZUKU_SETUP_ERROR",
                error.message,
                error
            )
        }
    }

    private fun waitForVerification(context: Context, connection: ServiceConnection): JSONObject {
        val deadline = System.currentTimeMillis() + 5_000L
        var latest = JSONObject(status(context))
        while (System.currentTimeMillis() < deadline) {
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

    private fun binderAlive(): Boolean = runCatching { Shizuku.pingBinder() }.getOrDefault(false)
}
