package com.clipcascade

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import com.facebook.react.HeadlessJsTaskService

/** Restarts requested synchronization after boot or a same-signer package update. */
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.action ?: return
        if (action != Intent.ACTION_BOOT_COMPLETED && action != Intent.ACTION_MY_PACKAGE_REPLACED) {
            return
        }

        val app = context.applicationContext
        try {
            AsyncStorageBridge(app).setValue("restart_receiver_status", "received:$action")
            HeadlessJsTaskService.acquireWakeLockNow(app)
            app.startService(
                Intent(app, HeadlessTaskService::class.java).apply {
                    putExtra("event", action)
                }
            )
            AsyncStorageBridge(app).setValue("restart_receiver_status", "headless-started:$action")
        } catch (error: Throwable) {
            Log.e("ClipCascade", "Unable to start restart headless task", error)
            runCatching {
                AsyncStorageBridge(app).setValue(
                    "restart_receiver_status",
                    "headless-start-failed:${error.javaClass.simpleName}"
                )
            }
        }
    }
}
