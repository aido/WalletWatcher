package aido.walletwatcher

import android.Manifest
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.util.Log
import android.os.Build
import androidx.core.content.ContextCompat

class BroadcastReceiver : BroadcastReceiver() {
    companion object {
        private const val TAG = "BroadcastReceiver"
    }

    override fun onReceive(context: Context, intent: Intent) {
        Log.d(TAG, "onReceive called, action: ${intent.action}")

        when (intent.action) {
            Intent.ACTION_BOOT_COMPLETED, Intent.ACTION_MY_PACKAGE_REPLACED -> {
                if (ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) ==
                    PackageManager.PERMISSION_GRANTED) {
                    val serviceIntent = Intent(context, Service::class.java)
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                        context.startForegroundService(serviceIntent)
                    } else {
                        context.startService(serviceIntent)
                    }
                } else {
                     Log.w(TAG, "POST_NOTIFICATIONS permission not granted, not starting service!")
                }
            }
            else -> {
                Log.d(TAG, "Unknown action: ${intent.action}")
            }
        }
    }
}