package aido.walletwatcher

import android.app.NotificationManager
import android.content.Context
import android.provider.Settings.Secure
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.core.graphics.toColorInt
import com.google.firebase.Timestamp
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.ktx.auth
import com.google.firebase.firestore.FirebaseFirestore
import com.google.firebase.ktx.Firebase
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage

class FirebaseMessagingService : FirebaseMessagingService() {

    companion object {
        private const val TAG = "FirebaseMessagingService"
        private val DEFAULT_COLOUR = R.color.default_notification_color
        private val DEFAULT_ICON = R.drawable.ic_eye
        private var isAuthenticating = false
    }

    private val db = FirebaseFirestore.getInstance()
    private val tokensCollection = db.collection("fcm_tokens")
    private lateinit var auth: FirebaseAuth

    private var authComplete = false
    private var newToken: String? = null

    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "onCreate called")
        auth = Firebase.auth
        setupAuthStateListener()
    }

    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        Log.d(TAG, "onMessageReceived called")
        Log.d(TAG, "Notification From: ${remoteMessage.from}")
        remoteMessage.notification?.let { notification ->
            Log.d(TAG, "Notification Title: ${notification.title}")
            Log.d(TAG, "Notification Body: ${notification.body}")
        }
        if (remoteMessage.data.isNotEmpty()) {
            Log.d(TAG, "Message data payload: ${remoteMessage.data}")
        }
    }

    override fun onNewToken(token: String) {
        Log.d(TAG, "onNewToken called")
        synchronized(this) {
            if (authComplete) {
                saveTokenToFirestore(token)
                sendNotification(
                    getString(R.string.notification_title_fcm_token),
                    token,
                    "#FFA500",
                    R.drawable.ic_token
                )
            } else {
                newToken = token // Store the latest token
            }
        }
    }

    private fun setupAuthStateListener() {
        Log.d(TAG, "setupAuthStateListener called")
        auth.addAuthStateListener { firebaseAuth ->
            if (firebaseAuth.currentUser != null) {
                Log.d(TAG, "AuthStateListener: User signed in")
                authComplete = true
                synchronized(this) {
                    newToken?.let {
                        saveTokenToFirestore(it)
                        sendNotification(
                            getString(R.string.notification_title_fcm_token),
                            it,
                            "#FFA500",
                            R.drawable.ic_token
                        )
                        newToken = null
                    }
                }
            } else {
                Log.d(TAG, "AuthStateListener: User signed out")
                authComplete = false
                if (!isAuthenticating) {
                    signInAnonymously()
                }
            }
        }
        if (auth.currentUser == null) {
            signInAnonymously()
        }
    }

    private fun signInAnonymously() {
        Log.d(TAG, "signInAnonymously called")
        isAuthenticating = true
        auth.signInAnonymously()
            .addOnCompleteListener { task ->
                if (task.isSuccessful) {
                    Log.d(TAG, "signInAnonymously:success")
                } else {
                    Log.w(TAG, "signInAnonymously:failure", task.exception)
                }
                isAuthenticating = false
            }
    }

    private fun sendNotification(
        messageTitle: String,
        messageBody: String,
        messageColour: String,
        messageIcon: Int = DEFAULT_ICON
    ) {
        Log.d(TAG, "sendNotification called")
        val accentColour = try {
            messageColour.toColorInt()
        } catch (e: IllegalArgumentException) {
            Log.e(TAG, "Invalid colour format: $messageColour")
            getColor(DEFAULT_COLOUR)
        }
        val notificationManager =
            getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val notificationBuilder =
            NotificationCompat.Builder(this, getString(aido.walletwatcher.Application.CHANNEL_ID))
                .setContentTitle(messageTitle)
                .setContentText(messageBody)
                .setSmallIcon(messageIcon)
                .setPriority(NotificationCompat.PRIORITY_HIGH)
                .setDefaults(NotificationCompat.DEFAULT_ALL)
                .setAutoCancel(true)
                .setColor(accentColour)
        notificationManager.notify(
            aido.walletwatcher.Application.NOTIFICATIONID_DEFAULT,
            notificationBuilder.build()
        )
    }

    private fun saveTokenToFirestore(token: String) {
        Log.d(TAG, "saveTokenToFirestore called")
        val deviceId = Secure.getString(contentResolver, Secure.ANDROID_ID)
        val fcmTokenData = hashMapOf(
            "timestamp" to Timestamp.now(),
            "token" to token
        )
        tokensCollection.document(deviceId).set(fcmTokenData)
            .addOnSuccessListener {
                Log.d(TAG, "FCM token successfully written to Firestore")
            }
            .addOnFailureListener { e ->
                Log.w(TAG, "Error writing FCM token to Firestore.", e)
            }
    }
}
