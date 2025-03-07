package aido.walletwatcher

import android.Manifest
import android.app.Service
import android.app.Notification
import android.app.PendingIntent
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.IBinder
import android.provider.Settings
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat

class Service : Service() {
    companion object {
        private const val TAG = "Service"
        const val ACTION_SERVICE_STARTED = "aido.walletwatcher.ACTION_SERVICE_STARTED"
        const val ACTION_SERVICE_ALREADY_RUNNING = "aido.walletwatcher.ACTION_SERVICE_ALREADY_RUNNING"
        const val ACTION_SERVICE_STOPPED = "aido.walletwatcher.ACTION_SERVICE_STOPPED"
    }

    private var isRunning = false

    override fun onCreate() {
        super.onCreate()

    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.d(TAG, "onStartCommand called")

        val action = if (isRunning) {
            ACTION_SERVICE_ALREADY_RUNNING
        } else {
            isRunning = true
            ACTION_SERVICE_STARTED
        }

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) ==
            PackageManager.PERMISSION_GRANTED) {
            sendBroadcast(Intent(action))
            startForeground(aido.walletwatcher.Application.NOTIFICATIONID_PERSISTENT, createPersistentNotification())
            return START_STICKY
        } else {
            Log.e(TAG, "POST_NOTIFICATIONS permission not granted, stopping service!")
            isRunning = false
            sendBroadcast(Intent(ACTION_SERVICE_STOPPED))
            stopSelf()
            return START_NOT_STICKY
        }
    }

    private fun createPersistentNotification(): Notification {
        Log.d(TAG, "createPersistentNotification called")

        // Create an intent to open the LauncherActivity
        val launcherIntent = Intent(this, LauncherActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }

        // Create a PendingIntent from the launcher intent
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            launcherIntent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        val notificationBuilder = NotificationCompat.Builder(this, getString(aido.walletwatcher.Application.CHANNEL_ID))
            .setContentTitle("Wallet Watcher Client")
            .setContentText("Running")
            .setSmallIcon(R.drawable.ic_eye)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setContentIntent(pendingIntent)
        return notificationBuilder.build()
    }

    override fun onDestroy() {
        super.onDestroy()

        isRunning = false
        sendBroadcast(Intent(ACTION_SERVICE_STOPPED))

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            // Android 13 (Tiramisu) and higher
            stopForeground(Service.STOP_FOREGROUND_REMOVE)
        } else {
            // Android 12L (Snow Cone) and lower
            @Suppress("DEPRECATION")
            stopForeground(true)
        }
        stopSelf()
    }

    override fun onBind(intent: Intent?): IBinder? {
        return null
    }
}