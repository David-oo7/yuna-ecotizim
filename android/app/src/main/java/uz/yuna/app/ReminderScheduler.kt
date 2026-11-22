package uz.yuna.app

import android.Manifest
import android.app.AlarmManager
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import kotlinx.coroutines.runBlocking
import java.time.Instant
import java.time.OffsetDateTime

/**
 * Eslatmalarni qurilmaning o'zida rejalashtiradi.
 *
 * Backenddagi `remind_at` vaqtiga exact alarm qo'yiladi; vaqt kelganda
 * [ReminderReceiver] ishga tushadi va [ReminderSpeechService] matnni ovoz bilan o'qiydi.
 * Shu sababli ilova yopiq bo'lsa ham eslatma ishlaydi.
 */
object ReminderScheduler {
    const val ACTION_REMINDER = "uz.yuna.app.action.REMINDER"
    const val EXTRA_TEXT = "text"

    private const val PREFS = "yuna_alarms"
    private const val KEY_IDS = "ids"
    private const val CHANNEL = "eslatma"
    private const val NOTIFICATION_ID = 4101

    /** Exact alarm ruxsati bor-yo'qligi (Android 12+ da "Alarms & reminders" ruxsati). */
    fun canUseExactAlarms(context: Context): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) return true
        val manager = context.getSystemService(AlarmManager::class.java) ?: return false
        return manager.canScheduleExactAlarms()
    }

    fun canNotify(context: Context): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) return true
        return ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) ==
            PackageManager.PERMISSION_GRANTED
    }

    /** Backenddan faol eslatmalarni olib, alarmlarni qayta qo'yadi (bloklovchi, fon oqimida chaqiriladi). */
    fun sync(context: Context) {
        val session = Session(context)
        if (session.accessToken == null) {
            cancelAll(context)
            return
        }
        Api.setBaseUrl(session.serverUrl ?: BuildConfig.API_URL)
        val items = runCatching {
            runBlocking { Api.service.reminders(session.bearer, "pending") }
        }.getOrNull()?.items ?: return
        schedule(context, items)
    }

    fun syncAsync(context: Context) {
        Thread { runCatching { sync(context.applicationContext) } }.start()
    }

    fun schedule(context: Context, items: List<ReminderDto>) {
        val manager = context.getSystemService(AlarmManager::class.java) ?: return
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val now = Instant.now()

        val upcoming = items.mapNotNull { reminder ->
            val moment = runCatching {
                OffsetDateTime.parse(reminder.remindAt).toInstant()
            }.getOrNull()
            if (moment == null || moment.isBefore(now.minusSeconds(120))) null else reminder to moment
        }

        // Eski alarmlarni bekor qilamiz, keyin yangilarini qo'yamiz.
        prefs.getStringSet(KEY_IDS, emptySet()).orEmpty().forEach { raw ->
            raw.toIntOrNull()?.let { manager.cancel(pendingIntent(context, it, null)) }
        }

        val ids = mutableSetOf<String>()
        upcoming.forEach { (reminder, moment) ->
            val whenMs = maxOf(moment.toEpochMilli(), System.currentTimeMillis() + 2_000)
            val intent = pendingIntent(context, reminder.id, reminder.text)
            runCatching {
                if (canUseExactAlarms(context)) {
                    manager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, whenMs, intent)
                } else {
                    // Ruxsat bo'lmasa ham uyg'onib eslatishga harakat qilamiz (bir oz kechikishi mumkin).
                    manager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, whenMs, intent)
                }
            }
            ids.add(reminder.id.toString())
        }
        prefs.edit().putStringSet(KEY_IDS, ids).apply()
    }

    fun cancelAll(context: Context) {
        val manager = context.getSystemService(AlarmManager::class.java) ?: return
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        prefs.getStringSet(KEY_IDS, emptySet()).orEmpty().forEach { raw ->
            raw.toIntOrNull()?.let { manager.cancel(pendingIntent(context, it, null)) }
        }
        prefs.edit().remove(KEY_IDS).apply()
    }

    /** Ovoz chiqarib bo'lmay qolgan holatda (masalan xizmat taqiqlangan) bildirishnoma ko'rsatadi. */
    fun notify(context: Context, text: String) {
        if (!canNotify(context)) return
        val manager = context.getSystemService(NotificationManager::class.java) ?: return
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            manager.createNotificationChannel(
                NotificationChannel(CHANNEL, "Eslatmalar", NotificationManager.IMPORTANCE_HIGH).apply {
                    description = "Eslatma vaqti kelganda ovozli eslatma"
                    enableVibration(true)
                }
            )
        }
        val open = PendingIntent.getActivity(
            context,
            0,
            Intent(context, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        val notification = NotificationCompat.Builder(context, CHANNEL)
            .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
            .setContentTitle("Eslatma")
            .setContentText(text)
            .setStyle(NotificationCompat.BigTextStyle().bigText(text))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setContentIntent(open)
            .setAutoCancel(true)
            .build()
        runCatching { manager.notify(NOTIFICATION_ID, notification) }
    }

    private fun pendingIntent(context: Context, id: Int, text: String?): PendingIntent {
        val intent = Intent(context, ReminderReceiver::class.java)
            .setAction(ACTION_REMINDER)
            .putExtra("id", id)
            .putExtra(EXTRA_TEXT, text)
        return PendingIntent.getBroadcast(
            context,
            id,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
    }
}
