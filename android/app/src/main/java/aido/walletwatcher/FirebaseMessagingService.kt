package aido.walletwatcher

import android.app.NotificationManager
import android.content.Context
import android.util.Log
import androidx.core.app.NotificationCompat
import com.google.firebase.messaging.FirebaseMessaging
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import androidx.core.graphics.toColorInt

class FirebaseMessagingService : FirebaseMessagingService() {

    companion object {
        private const val TAG = "FirebaseMessagingService"
        private val DEFAULT_COLOUR = R.color.default_notification_color
        private const val FCM_PREFS = "FCM_PREFS"
        private const val FCM_TOKEN_KEY = "FCM_TOKEN"
        private val DEFAULT_ICON = R.drawable.ic_eye
    }

    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        Log.d(TAG, "onMessageReceived called")
        Log.d(TAG, "Notification From: ${remoteMessage.from}")

        remoteMessage.notification?.let { notification ->
            Log.d(TAG, "Notification Title: $notification.title")
            Log.d(TAG, "Notification Body: $notification.body")
        }

        // Check if the message has a data payload
        if (remoteMessage.data.isNotEmpty()) {
            Log.d(TAG, "Message data payload: ${remoteMessage.data}")
            // Handle data payload here if needed
        }
    }

    override fun onNewToken(token: String) {
        Log.d(TAG, "onNewToken called")
        // Get the token here
        FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
            if (task.isSuccessful) {
                val newToken = task.result
                Log.d(TAG, "FCM Token: $newToken")
                // Save the token to SharedPreferences
                saveTokenToSharedPreferences(newToken)
                sendNotification(getString(R.string.notification_title_fcm_token), newToken, "#FFA500", R.drawable.ic_token)
            } else {
                Log.e(TAG, "FCM Token failed", task.exception)
            }
        }
    }

    private fun sendNotification(messageTitle: String, messageBody: String, messageColour: String, messageIcon: Int = DEFAULT_ICON) {
        Log.d(TAG, "sendNotification called")

        // Determine the accent colour
        val accentColour = try {
            messageColour.toColorInt()
        } catch (e: IllegalArgumentException) {
            Log.e(TAG, "Invalid colour format: $messageColour")
            getColor(DEFAULT_COLOUR)
        }

        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        val notificationBuilder = NotificationCompat.Builder(this, getString(aido.walletwatcher.Application.CHANNEL_ID))
            .setContentTitle(messageTitle)
            .setContentText(messageBody)
            .setSmallIcon(messageIcon)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setDefaults(NotificationCompat.DEFAULT_ALL)
            .setAutoCancel(true)
            .setColor(accentColour)

        notificationManager.notify(aido.walletwatcher.Application.  NOTIFICATIONID_DEFAULT, notificationBuilder.build())
    }

    private fun saveTokenToSharedPreferences(token: String) {
        Log.d(TAG, "saveTokenToSharedPreferences called")
        val sharedPreferences = getSharedPreferences(FCM_PREFS, Context.MODE_PRIVATE)
        with(sharedPreferences.edit()) {
            putString(FCM_TOKEN_KEY, token)
            apply() // Use apply() for asynchronous saving
        }
    }
}