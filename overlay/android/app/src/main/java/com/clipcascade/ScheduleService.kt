package com.clipcascade

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import kotlinx.coroutines.delay

class ScheduleService(
    context: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(context, workerParams) {
    companion object {
        private const val TAG = "ScheduleService"
        private const val CHANNEL_ID = "clipcascade_foreground_service_stopped_running"
        private const val NOTIFICATION_ID = 1

        fun removeNotificationIfPresent(context: Context) {
            val manager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            manager.cancel(NOTIFICATION_ID)
        }

        fun hasNotificationPermission(context: Context): Boolean =
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                ContextCompat.checkSelfPermission(
                    context,
                    android.Manifest.permission.POST_NOTIFICATIONS
                ) == PackageManager.PERMISSION_GRANTED
            } else {
                true
            }
    }

    override suspend fun doWork(): Result = try {
        if (hasNotificationPermission(applicationContext)) {
            val bridge = AsyncStorageBridge(applicationContext)
            if (bridge.getValue("wsIsRunning")?.toBoolean() == true) {
                if (foregroundServiceIsActive(bridge)) {
                    removeNotificationIfPresent(applicationContext)
                } else {
                    showNotificationIfMissing()
                }
            } else {
                removeNotificationIfPresent(applicationContext)
            }
        }
        Result.success()
    } catch (error: Exception) {
        Log.e(TAG, "Foreground-service health check failed", error)
        Result.retry()
    }

    private suspend fun foregroundServiceIsActive(bridge: AsyncStorageBridge): Boolean {
        bridge.setValue("echo", "ping")
        repeat(35) {
            delay(100)
            if (bridge.getValue("echo") == "pong") return true
        }
        return false
    }

    private fun showNotificationIfMissing() {
        val manager = applicationContext
            .getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            manager.createNotificationChannel(
                NotificationChannel(
                    CHANNEL_ID,
                    applicationContext.getString(R.string.clipcascade_service_alert_channel),
                    NotificationManager.IMPORTANCE_DEFAULT
                )
            )
        }
        if (manager.activeNotifications.any { it.id == NOTIFICATION_ID }) return

        val intent = Intent(applicationContext, MainActivity::class.java).apply {
            action = "com.clipcascade.NOTIFICATION_ACTION"
            putExtra("action", "foreground_service_stopped_running")
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or
                Intent.FLAG_ACTIVITY_SINGLE_TOP or
                Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            applicationContext,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val notification = NotificationCompat.Builder(applicationContext, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_notification_failure)
            .setContentTitle(
                applicationContext.getString(R.string.clipcascade_service_inactive_title)
            )
            .setContentText(
                applicationContext.getString(R.string.clipcascade_service_inactive_text)
            )
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()
        manager.notify(NOTIFICATION_ID, notification)
    }
}
