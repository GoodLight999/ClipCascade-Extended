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

/** One-shot setup helper. ClipCascade runtime must never depend on Shizuku staying alive. */
object ShizukuSetup {
    private const val REQUEST_CODE = 7342
    private val handler = Handler(Looper.getMainLooper())
    private var permissionPromise: Promise? = null
    private var setupPromise: Promise? = null
    private var activeConnection: ServiceConnection? = null
    private var activeArgs: Shizuku.UserServiceArgs? = null

    private val permissionListener = Shizuku.OnRequestPermissionResultListener { requestCode, result ->
        if (requestCode != REQUEST_CODE) return@OnRequestPermissionResultListener
        val promise = synchronized(this) {
            permissionPromise.also { permissionPromise = null }
        } ?: return@OnRequestPermissionResultListener
        if (result == PackageManager.PERMISSION_GRANTED) {
            promise.resolve(true)
        } else {
            promise.reject("SHIZUKU_DENIED", "Shizuku permission was denied")
        }
    }

    init {
        Shizuku.addRequestPermissionResultListener(permissionListener)
    }

    fun status(context: Context): String = JSONObject().apply {
        val running = try { Shizuku.pingBinder() } catch (_: Throwable) { false }
        put("running", running)
        put("permissionGranted", running && try {
            Shizuku.checkSelfPermission() == PackageManager.PERMISSION_GRANTED
        } catch (_: Throwable) { false })
        put("serverUid", if (running) try { Shizuku.getUid() } catch (_: Throwable) { -1 } else -1)
        put("apiVersion", if (running) try { Shizuku.getVersion() } catch (_: Throwable) { -1 } else -1)
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
        if (Shizuku.checkSelfPermission() == PackageManager.PERMISSION_GRANTED) {
            promise.resolve(true)
            return
        }
        if (permissionPromise != null) {
            promise.reject("SHIZUKU_BUSY", "A Shizuku permission request is already open")
            return
        }
        permissionPromise = promise
        try {
            Shizuku.requestPermission(REQUEST_CODE)
        } catch (error: Throwable) {
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
        if (Shizuku.checkSelfPermission() != PackageManager.PERMISSION_GRANTED) {
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
                try {
                    val service = IClipCascadeSetupService.Stub.asInterface(binder)
                    val remote = JSONObject(service.applySetup(app.packageName))
                    val verified = waitForVerification(app)
                    remote.put("verified", verified)
                    if (!verified.getBoolean("readLogs") || !verified.getBoolean("overlay")) {
                        throw IllegalStateException(
                            "Shizuku commands returned but Android did not retain the required grants: $verified"
                        )
                    }
                    finishSetup(args, this, result = remote.toString())
                } catch (error: Throwable) {
                    finishSetup(args, this, error = error)
                }
            }

            override fun onServiceDisconnected(name: ComponentName) {
                finishSetup(
                    args,
                    this,
                    error = IllegalStateException("Shizuku setup service disconnected")
                )
            }
        }

        setupPromise = promise
        activeArgs = args
        activeConnection = connection
        try {
            Shizuku.bindUserService(args, connection)
            handler.postDelayed({
                synchronized(this@ShizukuSetup) {
                    if (setupPromise != null && activeConnection === connection) {
                        finishSetup(
                            args,
                            connection,
                            error = IllegalStateException("Shizuku setup timed out")
                        )
                    }
                }
            }, 20_000L)
        } catch (error: Throwable) {
            finishSetup(args, connection, error = error)
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
        activeArgs = null
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

    private fun waitForVerification(context: Context): JSONObject {
        val deadline = System.currentTimeMillis() + 5_000L
        var latest = JSONObject(status(context))
        while (System.currentTimeMillis() < deadline) {
            if (latest.optBoolean("readLogs") && latest.optBoolean("overlay")) return latest
            Thread.sleep(150L)
            latest = JSONObject(status(context))
        }
        return latest
    }

    private fun binderAlive(): Boolean = try { Shizuku.pingBinder() } catch (_: Throwable) { false }
}
