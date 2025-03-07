package aido.walletwatcher

import android.Manifest
import android.annotation.SuppressLint
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.graphics.Rect
import android.graphics.Color
import android.widget.TextView
import android.widget.Button
import android.view.Window
import android.view.WindowManager
import androidx.appcompat.app.AppCompatActivity
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat

class LauncherActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "LauncherActivity"
    }

    private lateinit var launcherMessageTextView: TextView
    private lateinit var launcherStatusTextView: TextView
    private lateinit var launcherButton: Button
    private lateinit var serviceStateReceiver: BroadcastReceiver

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { isGranted: Boolean ->
        if (isGranted) {
            // Start the service
            val serviceIntent = Intent(this, Service::class.java)
            startService(serviceIntent)

            launcherMessageTextView.text = getString(R.string.launcher_message_granted_notifications)
            Log.d(TAG, "Wallet Watcher has notification permission. Service has started.")
        } else {
            launcherMessageTextView.text = getString(R.string.launcher_message_cannot_display_notifications)
            launcherStatusTextView.text = getString(R.string.launcher_status_service_not_started)
            launcherStatusTextView.setTextColor(Color.RED)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Log.d(TAG, "onCreate called")
        setContentView(R.layout.launcher_layout)

        // Adjust window size
        val window: Window = window
        val windowMetrics = windowManager.currentWindowMetrics
        val bounds: Rect = windowMetrics.bounds
        val layoutParams = WindowManager.LayoutParams()
        layoutParams.copyFrom(window.attributes)
        layoutParams.width = (bounds.width() * 0.8).toInt()
        layoutParams.height = (bounds.height() * 0.4).toInt()
        layoutParams.flags = layoutParams.flags or WindowManager.LayoutParams.FLAG_DIM_BEHIND
        layoutParams.type = WindowManager.LayoutParams.TYPE_APPLICATION_PANEL
        window.attributes = layoutParams

        launcherMessageTextView = findViewById(R.id.launcherMessageTextView)
        launcherStatusTextView = findViewById(R.id.launcherStatusTextView)
        launcherButton = findViewById(R.id.launcherButton)

        launcherButton.setOnClickListener {
            finish()
        }

        // Set up the broadcast receiver
        serviceStateReceiver = object : BroadcastReceiver() {
            override fun onReceive(context: Context?, intent: Intent?) {
                when (intent?.action) {
                    Service.ACTION_SERVICE_STARTED -> {
                        Log.d(TAG, "Service started broadcast received")
                        launcherStatusTextView.text = getString(R.string.launcher_status_service_started)
                        launcherStatusTextView.setTextColor(Color.GREEN)
                    }
                    Service.ACTION_SERVICE_ALREADY_RUNNING -> {
                        Log.d(TAG, "Service already running broadcast received")
                        launcherStatusTextView.text = getString(R.string.launcher_status_service_running)
                        launcherStatusTextView.setTextColor(Color.GREEN)
                    }
                    Service.ACTION_SERVICE_STOPPED -> {
                        Log.d(TAG, "Service stopped broadcast received")
                        launcherStatusTextView.text = getString(R.string.launcher_status_service_stopped)
                        launcherStatusTextView.setTextColor(Color.RED)
                    }
                }
            }
        }

        // Register the broadcast receiver
        val filter = IntentFilter().apply {
            addAction(Service.ACTION_SERVICE_STARTED)
            addAction(Service.ACTION_SERVICE_ALREADY_RUNNING)
            addAction(Service.ACTION_SERVICE_STOPPED)
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE){
            registerReceiver(serviceStateReceiver, filter, Context.RECEIVER_EXPORTED)
        } else {
            @Suppress("UnspecifiedRegisterReceiverFlag", "RECEIVER_EXPORTED NOT REQUIRED FOR API LEVEL < 34")
            registerReceiver(serviceStateReceiver, filter)
        }

        val serviceIntent = Intent(this, Service::class.java)

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            // Check if the permission is already granted
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) ==
                PackageManager.PERMISSION_GRANTED
            ) {
                // Start the service
                startService(serviceIntent)
                Log.d(
                    TAG,
                    "Wallet Watcher has notification permission. Service has started."
                )
                launcherMessageTextView.text = getString(R.string.launcher_message_has_notifications)
            } else {
                // Permission is not granted. Request it.
                Log.d(TAG, "Requesting notification permissions")
                requestPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        } else {
            startService(serviceIntent)
            launcherMessageTextView.text = getString(R.string.launcher_message_requires_notifications)
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        // Unregister the broadcast receiver
        unregisterReceiver(serviceStateReceiver)
    }
}