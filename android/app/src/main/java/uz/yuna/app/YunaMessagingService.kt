package uz.yuna.app

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.os.Build
import androidx.core.app.NotificationCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/**
 * Push xabarlar:
 *  - {command: "open_app", package: "..."}  -> ilovani ochadi
 *  - oddiy notification -> ko'rsatiladi
 *  - yangi token -> /devices/register orqali backendga yuboriladi
 */
class YunaMessagingService : FirebaseMessagingService() {

    override fun onMessageReceived(message: RemoteMessage) {
        val data = message.data
        if (data["command"] == "open_app") {
            AppsSync.openPackage(this, data["package"])
                .let { opened ->
                    if (!opened) AppsSync.openByName(this, data["app_name"])
                }
            return
        }

        val title = message.notification?.title ?: data["title"] ?: "Yuna"
        val body = message.notification?.body ?: data["body"] ?: "Yangi xabar"
        showNotification(title, body)
    }

    override fun onNewToken(token: String) {
        val session = Session(this)
        if (session.accessToken == null) return
        CoroutineScope(Dispatchers.IO).launch {
            runCatching {
                Api.service.registerDevice(
                    session.bearer,
                    DeviceRegister(deviceUid = session.deviceUid, fcmToken = token),
                )
            }
        }
    }

    private fun showNotification(title: String, body: String) {
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            manager.createNotificationChannel(
                NotificationChannel("yuna", "Yuna", NotificationManager.IMPORTANCE_DEFAULT)
            )
        }
        val notification = NotificationCompat.Builder(this, "yuna")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(title)
            .setContentText(body)
            .setAutoCancel(true)
            .build()
        manager.notify(System.currentTimeMillis().toInt(), notification)
    }
}
