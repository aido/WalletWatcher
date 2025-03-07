package aido.walletwatcher

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.os.Build
import android.util.Log

class Application : Application() {

    companion object {
        private const val TAG = "Applicaton"
        val CHANNEL_ID = R.string.default_notification_channel_id
        private val CHANNEL_NAME = R.string.default_notification_channel_name
        private val CHANNEL_DESCRIPTION = R.string.default_notification_channel_description
        const val NOTIFICATIONID_DEFAULT = 1
        const val NOTIFICATIONID_PERSISTENT = 2
    }

    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "onCreate called")
        createNotificationChannel()
    }

    private fun createNotificationChannel() {
        Log.d(TAG, "createNotificationChannel called")
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val notificationManager =
                getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

            if (notificationManager.getNotificationChannel(getString(CHANNEL_ID)) == null) {
                val importance = NotificationManager.IMPORTANCE_LOW
                val channel = NotificationChannel(
                    getString(CHANNEL_ID), getString(
                        CHANNEL_NAME
                    ), importance
                ).apply {
                    description = getString(CHANNEL_DESCRIPTION)
                }
                notificationManager.createNotificationChannel(channel)
            }
        }
    }
}
