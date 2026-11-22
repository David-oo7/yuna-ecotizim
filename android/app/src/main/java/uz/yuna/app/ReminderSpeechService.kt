package uz.yuna.app

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import androidx.core.app.NotificationCompat
import java.util.Locale

/**
 * Eslatma matnini ovoz chiqarib o'qiydigan foreground xizmat.
 *
 * Ilova yopiq bo'lsa ham exact alarm orqali ishga tushadi: bildirishnoma ko'rsatadi
 * va matnni TextToSpeech bilan o'qiydi.
 */
class ReminderSpeechService : Service(), TextToSpeech.OnInitListener {

    private var speaker: TextToSpeech? = null
    private var ready = false
    private var text = ""
    private var finished = false
    private val handler = Handler(Looper.getMainLooper())
    private val safetyStop = Runnable { stopSafely() }

    override fun onCreate() {
        super.onCreate()
        speaker = TextToSpeech(this, this)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        text = intent?.getStringExtra(ReminderScheduler.EXTRA_TEXT).orEmpty().trim()
        finished = false
        val notification = buildNotification()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(
                NOTIFICATION_ID,
                notification,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK,
            )
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }
        if (text.isNotBlank() && ready) speak()
        return START_NOT_STICKY
    }

    override fun onInit(status: Int) {
        val engine = speaker ?: return
        if (status != TextToSpeech.SUCCESS) {
            ReminderScheduler.notify(this, text)
            stopSafely()
            return
        }
        if (engine.setLanguage(Locale.forLanguageTag("uz-UZ")) >= TextToSpeech.LANG_MISSING_DATA) {
            engine.setLanguage(Locale.getDefault())
        }
        engine.setSpeechRate(0.95f)
        engine.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
            override fun onStart(utteranceId: String?) = Unit
            override fun onDone(utteranceId: String?) = stopSafely()
            @Deprecated("Deprecated in Java")
            override fun onError(utteranceId: String?) = stopSafely()
        })
        ready = true
        if (text.isNotBlank()) speak()
    }

    private fun speak() {
        val engine = speaker ?: return
        val result = engine.speak(text, TextToSpeech.QUEUE_FLUSH, null, UTTERANCE_ID)
        if (result == TextToSpeech.ERROR) {
            ReminderScheduler.notify(this, text)
            stopSafely()
            return
        }
        handler.removeCallbacks(safetyStop)
        handler.postDelayed(safetyStop, SAFETY_TIMEOUT_MS)
    }

    private fun stopSafely() {
        if (finished) return
        finished = true
        handler.removeCallbacks(safetyStop)
        stopForegroundCompat()
        stopSelf()
    }

    @Suppress("DEPRECATION")
    private fun stopForegroundCompat() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            stopForeground(STOP_FOREGROUND_DETACH)
        } else {
            stopForeground(false)
        }
    }

    private fun buildNotification(): android.app.Notification {
        val manager = getSystemService(NotificationManager::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            manager.createNotificationChannel(
                NotificationChannel(CHANNEL, "Eslatmalar", NotificationManager.IMPORTANCE_HIGH).apply {
                    description = "Eslatma vaqti kelganda ovozli eslatma"
                }
            )
        }
        val open = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        return NotificationCompat.Builder(this, CHANNEL)
            .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
            .setContentTitle("Eslatma")
            .setContentText(text)
            .setStyle(NotificationCompat.BigTextStyle().bigText(text))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setContentIntent(open)
            .setOngoing(true)
            .build()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        handler.removeCallbacks(safetyStop)
        speaker?.stop()
        speaker?.shutdown()
        speaker = null
        super.onDestroy()
    }

    private companion object {
        const val CHANNEL = "eslatma"
        const val NOTIFICATION_ID = 4102
        const val UTTERANCE_ID = "yuna-eslatma"
        const val SAFETY_TIMEOUT_MS = 45_000L
    }
}
