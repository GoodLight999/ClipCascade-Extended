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
        val isShareIntent = intent.action == Intent.ACTION_SEND ||
            intent.action == Intent.ACTION_SEND_MULTIPLE ||
            intent.action == Intent.ACTION_PROCESS_TEXT
        val bridge = AsyncStorageBridge(applicationContext)
        if (isShareIntent) {
            bridge.apply {
                setValue("shared_payload_pending", "true")
                setValue("shared_payload_status", "intent-received:${intent.action}:${intent.type}")
            }
        }

        var shareHandled = false
        when (intent.action) {
            Intent.ACTION_PROCESS_TEXT -> {
                intent.getCharSequenceExtra(Intent.EXTRA_PROCESS_TEXT)?.toString()?.let { text ->
                    shareHandled = true
                    dispatch("SHARED_TEXT", "text", text)
                }
            }

            Intent.ACTION_SEND -> {
                val stream = intent.getParcelableExtra<Uri>(Intent.EXTRA_STREAM)
                val text = intent.getCharSequenceExtra(Intent.EXTRA_TEXT)?.toString()
                when {
                    stream != null && intent.type?.startsWith("image/") == true -> {
                        shareHandled = true
                        stageAndDispatch(listOf(stream), "SHARED_IMAGE", "image")
                    }

                    stream != null -> {
                        shareHandled = true
                        stageAndDispatch(listOf(stream), "SHARED_FILES", "files")
                    }

                    text != null -> {
                        // EXTRA_TEXT is a CharSequence in Android's contract. Restricting
                        // it to String/text/plain loses Spanned, text/html and MIME-less shares.
                        shareHandled = true
                        dispatch("SHARED_TEXT", "text", text)
                    }
                }
            }

            Intent.ACTION_SEND_MULTIPLE -> {
                val uris = intent.getParcelableArrayListExtra<Uri>(Intent.EXTRA_STREAM)
                if (!uris.isNullOrEmpty()) {
                    shareHandled = true
                    stageAndDispatch(uris, "SHARED_FILES", "files")
                }
            }
        }

        if (isShareIntent && !shareHandled) {
            bridge.apply {
                setValue("shared_payload_pending", "false")
                setValue("shared_payload_status", "unsupported-share:${intent.action}:${intent.type}")
            }
        }

        if (intent.action == "com.clipcascade.NOTIFICATION_ACTION" &&
            intent.getStringExtra("action") == "foreground_service_stopped_running"
        ) {
            try {
                bridge.setValue("foreground_service_stopped_running", "true")
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
                    AsyncStorageBridge(app).apply {
                        setValue("shared_payload_status", outcome.take(300))
                        setValue("shared_payload_pending", "false")
                    }
                    Log.e(TAG, "Unable to stage shared payload", error)
                    if (!isFinishing && !isDestroyed) {
                        Toast.makeText(
                            this,
                            getString(R.string.clipcascade_share_prepare_failed),
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
