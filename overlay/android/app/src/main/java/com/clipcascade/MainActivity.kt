package com.clipcascade

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.widget.Toast
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import com.facebook.react.ReactActivity
import com.facebook.react.ReactActivityDelegate
import com.facebook.react.ReactInstanceManager
import com.facebook.react.defaults.DefaultNewArchitectureEntryPoint.fabricEnabled
import com.facebook.react.defaults.DefaultReactActivityDelegate
import com.facebook.react.devsupport.interfaces.DevSupportManager
import org.json.JSONArray
import java.util.concurrent.TimeUnit

class MainActivity : ReactActivity() {
    companion object {
        const val TAG = "ClipCascade"
        const val WORK_NAME = "schedule_work"
    }

    private val mainHandler = Handler(Looper.getMainLooper())

    override fun getMainComponentName(): String = "ClipCascade"

    override fun createReactActivityDelegate(): ReactActivityDelegate =
        DefaultReactActivityDelegate(this, mainComponentName, fabricEnabled)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        SharedPayloadStager.cleanup(applicationContext)
        intent?.let(::handleIntent)

        try {
            val bridge = AsyncStorageBridge(applicationContext)
            val enabled = bridge.getValue("enable_periodic_checks")?.toBoolean() ?: true
            if (enabled) {
                scheduleJob()
                if (ScheduleService.hasNotificationPermission(applicationContext)) {
                    ScheduleService.removeNotificationIfPresent(applicationContext)
                }
            } else {
                WorkManager.getInstance(applicationContext).cancelUniqueWork(WORK_NAME)
            }
        } catch (error: Exception) {
            Log.e(TAG, "Error scheduling periodic health check", error)
        }
    }

    private fun scheduleJob() {
        val request = PeriodicWorkRequestBuilder<ScheduleService>(15, TimeUnit.MINUTES)
            .addTag(WORK_NAME)
            .build()
        WorkManager.getInstance(applicationContext).enqueueUniquePeriodicWork(
            WORK_NAME,
            ExistingPeriodicWorkPolicy.KEEP,
            request
        )
    }

    override fun onPause() {
        super.onPause()
        val manager: ReactInstanceManager = reactNativeHost.reactInstanceManager
        val devSupport: DevSupportManager = manager.devSupportManager
        if (devSupport.devSupportEnabled) {
            devSupport.hideRedboxDialog()
        }
    }

    override fun onNewIntent(intent: Intent?) {
        super.onNewIntent(intent)
        setIntent(intent)
        intent?.let(::handleIntent)
    }

    @Suppress("DEPRECATION")
    private fun handleIntent(intent: Intent) {
        when {
            Intent.ACTION_SEND == intent.action && intent.type == "text/plain" -> {
                intent.getStringExtra(Intent.EXTRA_TEXT)?.let {
                    dispatch("SHARED_TEXT", "text", it)
                }
            }

            Intent.ACTION_PROCESS_TEXT == intent.action && intent.type == "text/plain" -> {
                intent.getCharSequenceExtra(Intent.EXTRA_PROCESS_TEXT)?.let {
                    dispatch("SHARED_TEXT", "text", it.toString())
                }
            }

            Intent.ACTION_SEND == intent.action && intent.type?.startsWith("image/") == true -> {
                intent.getParcelableExtra<Uri>(Intent.EXTRA_STREAM)?.let { uri ->
                    stageAndDispatch(listOf(uri), "SHARED_IMAGE", "image")
                }
            }

            Intent.ACTION_SEND == intent.action && intent.type != null -> {
                intent.getParcelableExtra<Uri>(Intent.EXTRA_STREAM)?.let { uri ->
                    stageAndDispatch(listOf(uri), "SHARED_FILES", "files")
                }
            }

            Intent.ACTION_SEND_MULTIPLE == intent.action && intent.type != null -> {
                intent.getParcelableArrayListExtra<Uri>(Intent.EXTRA_STREAM)?.let { uris ->
                    stageAndDispatch(uris, "SHARED_FILES", "files")
                }
            }
        }

        if (intent.action == "com.clipcascade.NOTIFICATION_ACTION" &&
            intent.getStringExtra("action") == "foreground_service_stopped_running"
        ) {
            try {
                AsyncStorageBridge(applicationContext)
                    .setValue("foreground_service_stopped_running", "true")
            } catch (error: Exception) {
                Log.e(TAG, "Unable to persist foreground-service state", error)
            }
        }
    }

    private fun stageAndDispatch(
        uris: List<Uri>,
        eventName: String,
        key: String
    ) {
        val app = applicationContext
        AsyncStorageBridge(app).setValue("shared_payload_status", "staging:${uris.size}")
        SharedPayloadStager.stage(app, uris) { result ->
            mainHandler.post {
                result.onSuccess { staged ->
                    val value = if (key == "files") {
                        JSONArray(staged.map(Uri::toString)).toString()
                    } else {
                        staged.single().toString()
                    }
                    AsyncStorageBridge(app).setValue(
                        "shared_payload_status",
                        "staged:${staged.size}"
                    )
                    dispatch(eventName, key, value)
                }.onFailure { error ->
                    val outcome = "staging-error:${error.javaClass.simpleName}:${error.message}"
                    AsyncStorageBridge(app).setValue("shared_payload_status", outcome.take(300))
                    Log.e(TAG, "Unable to stage shared payload", error)
                    if (!isFinishing && !isDestroyed) {
                        Toast.makeText(
                            this,
                            "ClipCascade could not prepare the shared file.",
                            Toast.LENGTH_LONG
                        ).show()
                    }
                }
            }
        }
    }

    private fun dispatch(eventName: String, key: String, value: String) {
        PendingReactEventStore.emitOrQueue(
            applicationContext,
            reactInstanceManager.currentReactContext,
            eventName,
            mapOf(key to value)
        )
    }
}
