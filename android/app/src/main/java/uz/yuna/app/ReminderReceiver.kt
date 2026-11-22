package uz.yuna.app

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import androidx.core.content.ContextCompat

/**
 * Alarm qo'ng'irog'i va tizim hodisalarini qabul qiladi.
 *
 * - eslatma vaqti kelganda: ovozli xizmatni ishga tushiradi
 * - qayta yuklash / yangilanish / vaqt o'zgarishi: alarmlarni qaytadan qo'yadi
 */
class ReminderReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        when (intent.action) {
            Intent.ACTION_BOOT_COMPLETED,
            Intent.ACTION_MY_PACKAGE_REPLACED,
            Intent.ACTION_TIME_CHANGED,
            Intent.ACTION_TIMEZONE_CHANGED,
            -> {
                val pending = goAsync()
                Thread {
                    runCatching { ReminderScheduler.sync(context.applicationContext) }
                    runCatching { pending.finish() }
                }.start()
            }

            else -> {
                val text = intent.getStringExtra(ReminderScheduler.EXTRA_TEXT).orEmpty()
                if (text.isBlank()) return
                val service = Intent(context, ReminderSpeechService::class.java)
                    .putExtra(ReminderScheduler.EXTRA_TEXT, text)
                try {
                    ContextCompat.startForegroundService(context, service)
                } catch (_: Exception) {
                    // Xizmatni fondan boshlash taqiqlangan bo'lsa — ovozli bildirishnoma.
                    ReminderScheduler.notify(context, text)
                }
            }
        }
    }
}
