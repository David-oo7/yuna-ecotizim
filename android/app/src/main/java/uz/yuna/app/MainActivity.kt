package uz.yuna.app

import android.Manifest
import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.media.MediaRecorder
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.MediaStore
import android.provider.OpenableColumns
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AdminPanelSettings
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Chat
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Download
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Logout
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Notifications
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Restaurant
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File
import java.time.OffsetDateTime
import java.time.format.DateTimeFormatter

private val ACCENT = Color(0xFF8B6CFF)
private val ACCENT_DEEP = Color(0xFF6A45E8)
private val SOFT = Color(0xFF2A2840)
private val INK = Color(0xFFEDEDF5)
private val MUTED = Color(0xFF8E8EA8)
private val SURFACE = Color(0xFF1F1F2C)
private val SURFACE_HI = Color(0xFF262636)
private val BG_DARK = Color(0xFF14141C)
private val TEAL = Color(0xFF3FD7C4)
private val GREEN = Color(0xFF6BE39B)

private val MEAL_LABELS = mapOf(
    "breakfast" to "Nonushta",
    "lunch" to "Tushlik",
    "dinner" to "Kechki ovqat",
    "snack" to "Gazak",
)

private enum class Tabs(val title: String, val icon: ImageVector) {
    HOME("Bugun", Icons.Filled.Home),
    CHAT("Chat", Icons.Filled.Chat),
    REMINDERS("Eslatmalar", Icons.Filled.Notifications),
    FOOD("Ovqat", Icons.Filled.Restaurant),
    PROFILE("Profil", Icons.Filled.Person),
}

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) !=
            PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1001)
        }
        setContent {
            MaterialTheme(
                colorScheme = darkColorScheme(
                    primary = ACCENT,
                    onPrimary = Color.White,
                    secondary = TEAL,
                    background = BG_DARK,
                    onBackground = INK,
                    surface = SURFACE,
                    onSurface = INK,
                    surfaceVariant = SURFACE_HI,
                    onSurfaceVariant = MUTED,
                    outline = Color(0xFF34344A),
                ),
            ) {
                YunaApp()
            }
        }
    }
}

@Composable
private fun YunaApp() {
    val context = LocalContext.current
    val session = remember { Session(context) }
    var loggedIn by remember { mutableStateOf(session.accessToken != null) }
    var user by remember { mutableStateOf<UserDto?>(null) }

    LaunchedEffect(loggedIn) {
        if (loggedIn) {
            Api.setBaseUrl(session.serverUrl ?: BuildConfig.API_URL)
            runCatching { Api.service.me(session.bearer) }.onSuccess { user = it }
            ReminderScheduler.syncAsync(context)
        }
    }

    if (loggedIn) {
        MainShell(
            session = session,
            user = user,
            onUser = { user = it },
            onLogout = {
                session.clear()
                user = null
                loggedIn = false
            },
        )
    } else {
        LoginScreen(session) {
            loggedIn = true
            AppsSync.sync(context, session)
        }
    }
}

// --------------------------- LOGIN ---------------------------
@Composable
private fun LoginScreen(session: Session, onDone: () -> Unit) {
    val scope = rememberCoroutineScope()
    var isRegister by remember { mutableStateOf(false) }
    var name by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var error by remember { mutableStateOf<String?>(null) }
    var loading by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier.fillMaxSize().padding(28.dp),
        verticalArrangement = Arrangement.Center,
    ) {
        Text("Y.U.N.A", fontSize = 36.sp, fontWeight = FontWeight.Bold, color = ACCENT)
        Text("Sizning shaxsiy yordamchingiz", color = MUTED)
        Spacer(Modifier.height(28.dp))

        if (isRegister) {
            OutlinedTextField(
                value = name,
                onValueChange = { name = it },
                label = { Text("Ismingiz") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            Spacer(Modifier.height(10.dp))
        }

        OutlinedTextField(
            value = email,
            onValueChange = { email = it },
            label = { Text("Email") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )
        Spacer(Modifier.height(10.dp))
        OutlinedTextField(
            value = password,
            onValueChange = { password = it },
            label = { Text("Parol") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )

        error?.let {
            Spacer(Modifier.height(8.dp))
            Text(it, color = MaterialTheme.colorScheme.error)
        }

        Spacer(Modifier.height(20.dp))
        Button(
            onClick = {
                scope.launch {
                    loading = true
                    error = null
                    runCatching {
                        val tokens = if (isRegister) {
                            Api.service.register(RegisterRequest(name, email, password))
                        } else {
                            Api.service.login(LoginRequest(email, password))
                        }
                        session.save(tokens)
                    }.onSuccess { onDone() }
                        .onFailure { error = it.message ?: "Aloqa xatosi" }
                    loading = false
                }
            },
            modifier = Modifier.fillMaxWidth().height(52.dp),
            enabled = !loading,
        ) {
            Text(if (loading) "Kuting..." else if (isRegister) "Ro'yxatdan o'tish" else "Kirish")
        }

        TextButton(onClick = { isRegister = !isRegister }) {
            Text(if (isRegister) "Hisobim bor" else "Yangi hisob yaratish")
        }
    }
}

// --------------------------- ASOSIY QOBIQ ---------------------------
@Composable
private fun MainShell(
    session: Session,
    user: UserDto?,
    onUser: (UserDto) -> Unit,
    onLogout: () -> Unit,
) {
    var tab by remember { mutableStateOf(Tabs.HOME) }
    var overlay by remember { mutableStateOf<String?>(null) }
    var startVoice by remember { mutableStateOf(false) }

    Scaffold(
        containerColor = BG_DARK,
        bottomBar = {
            NavigationBar(containerColor = SURFACE, tonalElevation = 0.dp) {
                Tabs.entries.forEach { item ->
                    NavigationBarItem(
                        selected = tab == item && overlay == null,
                        onClick = {
                            overlay = null
                            tab = item
                        },
                        icon = {
                            Icon(
                                item.icon,
                                contentDescription = item.title,
                                modifier = Modifier.size(22.dp),
                            )
                        },
                        label = { Text(item.title, fontSize = 9.sp, maxLines = 1) },
                        colors = NavigationBarItemDefaults.colors(
                            selectedIconColor = TEAL,
                            selectedTextColor = TEAL,
                            unselectedIconColor = MUTED,
                            unselectedTextColor = MUTED,
                            indicatorColor = Color.Transparent,
                        ),
                    )
                }
            }
        },
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding).background(BG_DARK)) {
            when {
                overlay == "admin" -> AdminScreen(session) { overlay = null }
                overlay == "docs" -> DocumentsScreen(session) { overlay = null }
                tab == Tabs.HOME -> HomeScreen(
                    session = session,
                    user = user,
                    onOpenDocs = { overlay = "docs" },
                    onOpenReminders = { tab = Tabs.REMINDERS },
                    onOpenFood = { tab = Tabs.FOOD },
                    onOpenChat = { tab = Tabs.CHAT },
                    onVoice = {
                        startVoice = true
                        tab = Tabs.CHAT
                    },
                )
                tab == Tabs.CHAT -> ChatScreen(
                    session = session,
                    user = user,
                    startVoice = startVoice,
                    onVoiceHandled = { startVoice = false },
                )
                tab == Tabs.REMINDERS -> RemindersScreen(session)
                tab == Tabs.FOOD -> FoodScreen(session)
                else -> SettingsScreen(
                    session = session,
                    user = user,
                    onUser = onUser,
                    onLogout = onLogout,
                    onOpenAdmin = { overlay = "admin" },
                )
            }
        }
    }
}

@Composable
private fun sectionCard(title: String, content: @Composable ColumnScope.() -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(SURFACE, RoundedCornerShape(20.dp))
            .padding(16.dp),
    ) {
        Text(title, fontWeight = FontWeight.SemiBold, color = INK)
        Spacer(Modifier.height(10.dp))
        content()
    }
}

// --------------------------- BUGUN (UY) ---------------------------
private val MONTHS_UZ = listOf(
    "yanvar", "fevral", "mart", "aprel", "may", "iyun",
    "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr",
)

private fun todayUz(): String {
    val now = java.time.LocalDate.now()
    return "Bugun ${now.dayOfMonth}-${MONTHS_UZ[now.monthValue - 1]}, ${now.year}-yil"
}

private fun friendlyMoment(value: String): String {
    val moment = runCatching {
        OffsetDateTime.parse(value).atZoneSameInstant(java.time.ZoneId.systemDefault())
    }.getOrNull() ?: return value
    val days = java.time.temporal.ChronoUnit.DAYS.between(
        java.time.LocalDate.now(),
        moment.toLocalDate(),
    )
    val prefix = when (days) {
        0L -> "Bugun"
        1L -> "Ertaga"
        -1L -> "Kecha"
        else -> moment.format(DateTimeFormatter.ofPattern("dd.MM"))
    }
    return "$prefix ${moment.format(DateTimeFormatter.ofPattern("HH:mm"))}"
}

@Composable
private fun YunaLogo() {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(
            Modifier
                .size(34.dp)
                .background(Brush.linearGradient(listOf(TEAL, GREEN)), RoundedCornerShape(10.dp)),
            contentAlignment = Alignment.Center,
        ) {
            Text("Y", color = Color(0xFF06231F), fontWeight = FontWeight.Bold, fontSize = 18.sp)
        }
        Spacer(Modifier.width(10.dp))
        Text("Yuna", fontSize = 22.sp, fontWeight = FontWeight.Bold, color = TEAL)
    }
}

@Composable
private fun AvatarBadge(name: String?) {
    Box(
        Modifier.size(38.dp).background(ACCENT, CircleShape),
        contentAlignment = Alignment.Center,
    ) {
        Text(
            name?.trim()?.take(1)?.uppercase() ?: "Y",
            color = Color.White,
            fontWeight = FontWeight.Bold,
        )
    }
}

@Composable
private fun HomeScreen(
    session: Session,
    user: UserDto?,
    onOpenDocs: () -> Unit,
    onOpenReminders: () -> Unit,
    onOpenFood: () -> Unit,
    onOpenChat: () -> Unit,
    onVoice: () -> Unit,
) {
    val scope = rememberCoroutineScope()
    var advice by remember { mutableStateOf<AdviceDto?>(null) }
    var summary by remember { mutableStateOf<FoodSummaryDto?>(null) }
    var nextReminder by remember { mutableStateOf<ReminderDto?>(null) }
    var busy by remember { mutableStateOf(false) }

    suspend fun load() {
        busy = true
        runCatching { Api.service.advice(session.bearer) }.onSuccess { advice = it }
        runCatching { Api.service.foodSummary(session.bearer) }.onSuccess { summary = it }
        runCatching { Api.service.reminders(session.bearer, "pending") }
            .onSuccess { list -> nextReminder = list.items.minByOrNull { it.remindAt } }
        busy = false
    }

    LaunchedEffect(Unit) { load() }

    Box(Modifier.fillMaxSize()) {
        Column(
            Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(start = 16.dp, end = 16.dp, bottom = 88.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Spacer(Modifier.height(6.dp))
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                YunaLogo()
                Spacer(Modifier.weight(1f))
                AvatarBadge(user?.name)
                Spacer(Modifier.width(10.dp))
                Box(
                    Modifier.size(38.dp).background(SURFACE, RoundedCornerShape(12.dp)),
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(
                        Icons.Filled.Notifications,
                        contentDescription = "Bildirishnomalar",
                        tint = MUTED,
                        modifier = Modifier.size(20.dp),
                    )
                }
            }

            Column {
                Text("Xush kelibsiz!", fontSize = 24.sp, fontWeight = FontWeight.Bold, color = INK)
                Text(todayUz(), color = MUTED, fontSize = 13.sp)
            }

            AdviceCard(advice, busy) { scope.launch { load() } }

            FoodBalanceCard(summary)

            ReminderStrip(nextReminder, onOpenReminders)

            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                QuickChip("\uD83D\uDCC4 Hujjatlar", onOpenDocs)
                QuickChip("\uD83C\uDF7D Ovqat", onOpenFood)
                QuickChip("\uD83D\uDCAC Chat", onOpenChat)
            }

            QuickMicCard(onVoice)
            Spacer(Modifier.height(6.dp))
        }

        Box(
            Modifier
                .align(Alignment.BottomCenter)
                .padding(bottom = 10.dp)
                .size(72.dp)
                .background(Brush.linearGradient(listOf(TEAL, GREEN)), CircleShape)
                .clickable { onVoice() },
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                Icons.Filled.Mic,
                contentDescription = "Mikrofon",
                tint = Color(0xFF06231F),
                modifier = Modifier.size(32.dp),
            )
        }
    }
}

@Composable
private fun AdviceCard(advice: AdviceDto?, busy: Boolean, onRefresh: () -> Unit) {
    Column(
        Modifier
            .fillMaxWidth()
            .background(Brush.linearGradient(listOf(ACCENT, ACCENT_DEEP)), RoundedCornerShape(20.dp))
            .padding(16.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                Modifier.size(30.dp).background(Color(0x33FFFFFF), RoundedCornerShape(9.dp)),
                contentAlignment = Alignment.Center,
            ) { Text("\u2726", color = Color.White, fontSize = 16.sp) }
            Spacer(Modifier.width(10.dp))
            Text(
                "Bugungi Maslahat",
                color = Color.White,
                fontWeight = FontWeight.Bold,
                fontSize = 16.sp,
                modifier = Modifier.weight(1f),
            )
            Box(
                Modifier
                    .size(30.dp)
                    .background(Color(0x33FFFFFF), RoundedCornerShape(9.dp))
                    .clickable(enabled = !busy) { onRefresh() },
                contentAlignment = Alignment.Center,
            ) {
                Icon(
                    Icons.Filled.Refresh,
                    contentDescription = "Yangilash",
                    tint = Color.White,
                    modifier = Modifier.size(17.dp),
                )
            }
        }
        Spacer(Modifier.height(10.dp))
        Text(
            when {
                busy && advice == null -> "Yuklanmoqda..."
                else -> advice?.text ?: "Maslahat hozircha yo'q."
            },
            color = Color(0xFFF3F0FF),
            fontSize = 14.sp,
            lineHeight = 20.sp,
        )
    }
}

@Composable
private fun FoodBalanceCard(summary: FoodSummaryDto?) {
    val totals = summary?.totals ?: emptyMap()
    val kcal = (totals["kcal"] ?: 0.0).toFloat()
    val goal = (summary?.goalKcal ?: 2200).toFloat()
    Column(
        Modifier.fillMaxWidth().background(SURFACE, RoundedCornerShape(20.dp)).padding(16.dp),
    ) {
        Text("Ovqat balansi", fontWeight = FontWeight.SemiBold, color = INK, fontSize = 15.sp)
        Spacer(Modifier.height(12.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            KcalDonut(kcal, goal, Modifier.size(142.dp))
            Spacer(Modifier.width(14.dp))
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                MacroBar("Oqsil", (totals["protein"] ?: 0.0).toFloat(), 120f, TEAL)
                MacroBar("Yog'", (totals["fat"] ?: 0.0).toFloat(), 80f, GREEN)
                MacroBar("Uglevod", (totals["carbs"] ?: 0.0).toFloat(), 250f, ACCENT)
            }
        }
        Spacer(Modifier.height(10.dp))
        Text("Raqamlar taxminiy.", color = MUTED, fontSize = 11.sp)
    }
}

@Composable
private fun KcalDonut(consumed: Float, goal: Float, modifier: Modifier = Modifier) {
    val ratio = if (goal > 0f) (consumed / goal).coerceIn(0f, 1f) else 0f
    Box(modifier, contentAlignment = Alignment.Center) {
        Canvas(Modifier.fillMaxSize()) {
            val stroke = size.minDimension * 0.075f
            val inset = stroke / 2f + 2f
            val arcSize = Size(size.width - inset * 2, size.height - inset * 2)
            drawArc(
                color = SURFACE_HI,
                startAngle = 90f,
                sweepAngle = 360f,
                useCenter = false,
                topLeft = Offset(inset, inset),
                size = arcSize,
                style = Stroke(width = stroke, cap = StrokeCap.Round),
            )
            if (ratio > 0f) {
                drawArc(
                    brush = Brush.linearGradient(listOf(TEAL, GREEN)),
                    startAngle = 90f,
                    sweepAngle = -360f * ratio,
                    useCenter = false,
                    topLeft = Offset(inset, inset),
                    size = arcSize,
                    style = Stroke(width = stroke, cap = StrokeCap.Round),
                )
            }
        }
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text("Kkal", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = INK)
            Text("(${consumed.toInt()} / ${goal.toInt()} kcal)", fontSize = 9.sp, color = MUTED)
        }
    }
}

@Composable
private fun MacroBar(label: String, value: Float, target: Float, color: Color) {
    val ratio = if (target > 0f) (value / target).coerceIn(0f, 1f) else 0f
    Column(Modifier.fillMaxWidth()) {
        Row {
            Text(label, color = INK, fontSize = 13.sp)
            Spacer(Modifier.weight(1f))
            Text("${value.toInt()} g", color = MUTED, fontSize = 12.sp)
        }
        Spacer(Modifier.height(5.dp))
        Box(
            Modifier.fillMaxWidth().height(8.dp).background(SURFACE_HI, RoundedCornerShape(4.dp)),
        ) {
            if (ratio > 0f) {
                Box(
                    Modifier
                        .fillMaxWidth(ratio.coerceAtLeast(0.04f))
                        .fillMaxHeight()
                        .background(
                            Brush.horizontalGradient(listOf(TEAL, color)),
                            RoundedCornerShape(4.dp),
                        ),
                )
            }
        }
    }
}

@Composable
private fun ReminderStrip(reminder: ReminderDto?, onOpen: () -> Unit) {
    Column(
        Modifier
            .fillMaxWidth()
            .background(SURFACE, RoundedCornerShape(20.dp))
            .clickable { onOpen() }
            .padding(16.dp),
    ) {
        Text("Eng yaqin eslatma", fontWeight = FontWeight.SemiBold, color = INK, fontSize = 15.sp)
        Spacer(Modifier.height(6.dp))
        Text(
            reminder?.let { "${friendlyMoment(it.remindAt)} \u00b7 ${it.text}" }
                ?: "Hozircha eslatma yo'q. Yangi eslatma qo'shing.",
            color = MUTED,
            fontSize = 13.sp,
        )
    }
}

@Composable
private fun QuickChip(label: String, onClick: () -> Unit) {
    Row(
        Modifier
            .background(SURFACE, RoundedCornerShape(12.dp))
            .clickable { onClick() }
            .padding(horizontal = 14.dp, vertical = 10.dp),
    ) {
        Text(label, color = INK, fontSize = 13.sp)
    }
}

@Composable
private fun QuickMicCard(onVoice: () -> Unit) {
    Row(
        Modifier
            .fillMaxWidth()
            .background(SURFACE, RoundedCornerShape(20.dp))
            .padding(16.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text("Tezkor mikrofon", color = INK, fontSize = 15.sp, modifier = Modifier.weight(1f))
        Box(
            Modifier
                .size(48.dp)
                .background(
                    Brush.linearGradient(listOf(ACCENT, ACCENT_DEEP)),
                    RoundedCornerShape(14.dp),
                )
                .clickable { onVoice() },
            contentAlignment = Alignment.Center,
        ) {
            Icon(Icons.Filled.Mic, contentDescription = "Mikrofon", tint = Color.White)
        }
    }
}

// --------------------------- CHAT ---------------------------
data class UiMessage(val role: String, val text: String)

@Composable
private fun ChatScreen(
    session: Session,
    user: UserDto?,
    startVoice: Boolean = false,
    onVoiceHandled: () -> Unit = {},
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val json = remember { Json { ignoreUnknownKeys = true } }

    val messages = remember { mutableStateListOf<UiMessage>() }
    var input by remember { mutableStateOf("") }
    var sessionId by remember { mutableStateOf<Int?>(null) }
    var sending by remember { mutableStateOf(false) }
    var recording by remember { mutableStateOf<MediaRecorder?>(null) }
    var audioFile by remember { mutableStateOf<File?>(null) }
    val listState = rememberLazyListState()

    suspend fun sendText(text: String) {
        if (text.isBlank()) return
        messages.add(UiMessage("user", text))
        sending = true
        try {
            val response = Api.service.chat(session.bearer, ChatRequest(text, sessionId))
            sessionId = response.sessionId
            messages.add(UiMessage("assistant", response.reply))
        } catch (e: Exception) {
            messages.add(UiMessage("assistant", "Aloqa xatosi: ${e.message}"))
        } finally {
            sending = false
        }
    }

    fun startRecording() {
        val file = File(context.cacheDir, "voice_${System.currentTimeMillis()}.m4a")
        val recorder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            MediaRecorder(context)
        } else {
            @Suppress("DEPRECATION")
            MediaRecorder()
        }
        recorder.setAudioSource(MediaRecorder.AudioSource.MIC)
        recorder.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
        recorder.setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
        recorder.setAudioSamplingRate(16000)
        recorder.setOutputFile(file.absolutePath)
        recorder.prepare()
        recorder.start()
        audioFile = file
        recording = recorder
    }

    val recordPermission = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted -> if (granted) startRecording() }

    fun stopRecordingAndSend() {
        val recorder = recording ?: return
        runCatching { recorder.stop() }
        runCatching { recorder.release() }
        recording = null
        val file = audioFile ?: return

        scope.launch {
            sending = true
            try {
                val result = withContext(Dispatchers.IO) { uploadVoice(session, file, sessionId, json) }
                if (result != null) {
                    sessionId = result.session_id
                    messages.add(UiMessage("user", result.text))
                    messages.add(UiMessage("assistant", result.reply))
                } else {
                    messages.add(UiMessage("assistant", "Ovoz yuborilmadi, qayta urinib ko'ring."))
                }
            } catch (e: Exception) {
                messages.add(UiMessage("assistant", "Ovoz xatosi: ${e.message}"))
            } finally {
                sending = false
                file.delete()
            }
        }
    }

    LaunchedEffect(startVoice) {
        if (startVoice) {
            onVoiceHandled()
            val granted = ContextCompat.checkSelfPermission(
                context, Manifest.permission.RECORD_AUDIO
            ) == PackageManager.PERMISSION_GRANTED
            when {
                recording != null -> Unit
                granted -> startRecording()
                else -> recordPermission.launch(Manifest.permission.RECORD_AUDIO)
            }
        }
    }

    LaunchedEffect(messages.size) {
        if (messages.isNotEmpty()) listState.animateScrollToItem(messages.lastIndex)
    }

    Column(Modifier.fillMaxSize()) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            YunaLogo()
            Spacer(Modifier.weight(1f))
            Text(
                user?.name?.let { "Salom, $it" } ?: "Shaxsiy yordamchingiz",
                color = MUTED,
                fontSize = 12.sp,
            )
            Spacer(Modifier.width(10.dp))
            AvatarBadge(user?.name)
        }

        LazyColumn(
            state = listState,
            modifier = Modifier.weight(1f).fillMaxWidth().padding(horizontal = 12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
            contentPadding = PaddingValues(vertical = 8.dp),
        ) {
            if (messages.isEmpty()) {
                item {
                    Text(
                        "Salom! Men Yuna. Eslatma, ovqat hisobi, rasm yoki hujjat — " +
                            "shunchaki yozing yoki mikrofonni bosing.",
                        color = MUTED,
                        modifier = Modifier.padding(16.dp),
                    )
                }
            }
            items(messages) { message -> MessageBubble(message) }
        }

        Row(
            modifier = Modifier.fillMaxWidth().padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            OutlinedTextField(
                value = input,
                onValueChange = { input = it },
                modifier = Modifier.weight(1f),
                placeholder = { Text("Yunaga yozing...") },
                maxLines = 4,
            )
            Spacer(Modifier.width(8.dp))
            IconButton(
                onClick = {
                    val granted = ContextCompat.checkSelfPermission(
                        context, Manifest.permission.RECORD_AUDIO
                    ) == PackageManager.PERMISSION_GRANTED
                    when {
                        recording != null -> stopRecordingAndSend()
                        granted -> startRecording()
                        else -> recordPermission.launch(Manifest.permission.RECORD_AUDIO)
                    }
                },
                modifier = Modifier
                    .size(48.dp)
                    .background(
                        if (recording != null) Color(0xFFE74C3C) else ACCENT,
                        RoundedCornerShape(24.dp),
                    ),
            ) {
                Icon(
                    if (recording != null) Icons.Filled.Stop else Icons.Filled.Mic,
                    contentDescription = "Ovoz",
                    tint = Color.White,
                )
            }
            Spacer(Modifier.width(6.dp))
            IconButton(
                onClick = {
                    val text = input
                    input = ""
                    scope.launch { sendText(text) }
                },
                enabled = !sending,
            ) {
                Icon(Icons.Filled.Send, contentDescription = "Yuborish", tint = ACCENT)
            }
        }
    }
}

@Composable
private fun MessageBubble(message: UiMessage) {
    val isUser = message.role == "user"
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = if (isUser) Arrangement.End else Arrangement.Start,
    ) {
        Surface(
            color = if (isUser) ACCENT else SURFACE_HI,
            shape = RoundedCornerShape(14.dp),
            modifier = Modifier.widthIn(max = 300.dp),
        ) {
            Text(
                text = message.text,
                modifier = Modifier.padding(horizontal = 14.dp, vertical = 10.dp),
                color = if (isUser) Color.White else INK,
                fontFamily = if (message.text.contains("```")) FontFamily.Monospace else FontFamily.Default,
            )
        }
    }
}

// --------------------------- ESLATMALAR ---------------------------
@Composable
private fun RemindersScreen(session: Session) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var items by remember { mutableStateOf<List<ReminderDto>>(emptyList()) }
    var text by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    suspend fun load() {
        runCatching { Api.service.reminders(session.bearer) }
            .onSuccess { items = it.items.filter { r -> r.status == "pending" } }
            .onFailure { error = it.message }
        // Qo'ng'iroq vaqtlari qurilmada alarm sifatida qayta qo'yiladi.
        ReminderScheduler.syncAsync(context)
    }

    LaunchedEffect(Unit) { load() }

    fun add(offsetHours: Long) {
        if (text.isBlank()) return
        scope.launch {
            busy = true
            error = null
            runCatching {
                Api.service.createReminder(
                    session.bearer,
                    ReminderCreate(text.trim(), OffsetDateTime.now().plusHours(offsetHours).toString()),
                )
            }.onSuccess {
                text = ""
                load()
            }.onFailure { error = it.message }
            busy = false
        }
    }

    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(14.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        sectionCard("Yangi eslatma") {
            OutlinedTextField(
                value = text,
                onValueChange = { text = it },
                label = { Text("Nima eslatilsin?") },
                modifier = Modifier.fillMaxWidth(),
            )
            Spacer(Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                AssistChip(onClick = { add(1) }, label = { Text("1 soatdan") }, enabled = !busy)
                AssistChip(onClick = { add(3) }, label = { Text("3 soatdan") }, enabled = !busy)
                AssistChip(onClick = { add(24) }, label = { Text("Ertaga") }, enabled = !busy)
            }
            error?.let {
                Spacer(Modifier.height(6.dp))
                Text(it, color = MaterialTheme.colorScheme.error, fontSize = 12.sp)
            }
            Spacer(Modifier.height(6.dp))
            Text(
                "Eslatma vaqti kelganda matn ovoz bilan o'qiladi — ilova yopiq bo'lsa ham.",
                color = MUTED,
                fontSize = 11.sp,
            )
        }

        if (!ReminderScheduler.canUseExactAlarms(context)) {
            sectionCard("Aniq vaqt ruxsati") {
                Text(
                    "Eslatma aynan belgilangan daqiqada jiringlashi uchun " +
                        "\"Alarmlar va eslatmalar\" ruxsatini bering.",
                    color = MUTED,
                    fontSize = 12.sp,
                )
                Spacer(Modifier.height(8.dp))
                Button(
                    onClick = {
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                            runCatching {
                                context.startActivity(
                                    Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM).apply {
                                        data = android.net.Uri.parse("package:" + context.packageName)
                                        addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                                    }
                                )
                            }
                        }
                    },
                ) { Text("Ruxsat berish") }
            }
        }

        sectionCard("Eslatmalar (${items.size})") {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("Faol eslatmalar", color = MUTED, fontSize = 12.sp, modifier = Modifier.weight(1f))
                IconButton(onClick = { scope.launch { load() } }) {
                    Icon(Icons.Filled.Refresh, contentDescription = "Yangilash", tint = ACCENT)
                }
            }
            if (items.isEmpty()) {
                Text("Hozircha eslatma yo'q.", color = MUTED, fontSize = 13.sp)
            }
            items.forEach { reminder ->
                Row(
                    modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(Modifier.weight(1f)) {
                        Text(reminder.text, color = INK)
                        Text(formatMoment(reminder.remindAt), color = MUTED, fontSize = 12.sp)
                    }
                    IconButton(onClick = {
                        scope.launch {
                            runCatching { Api.service.deleteReminder(session.bearer, reminder.id) }
                            load()
                        }
                    }) {
                        Icon(Icons.Filled.Delete, contentDescription = "O'chirish", tint = Color(0xFFC0392B))
                    }
                }
                HorizontalDivider(color = Color(0xFF2B2B3D))
            }
        }
    }
}

private fun formatMoment(value: String): String = runCatching {
    OffsetDateTime.parse(value)
        .atZoneSameInstant(java.time.ZoneId.systemDefault())
        .format(DateTimeFormatter.ofPattern("dd.MM.yyyy HH:mm"))
}.getOrDefault(value)

// --------------------------- OVQAT ---------------------------
@Composable
private fun FoodScreen(session: Session) {
    val scope = rememberCoroutineScope()
    var summary by remember { mutableStateOf<FoodSummaryDto?>(null) }
    var text by remember { mutableStateOf("") }
    var note by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    suspend fun load() {
        runCatching { Api.service.foodSummary(session.bearer) }
            .onSuccess { summary = it }
            .onFailure { error = it.message }
    }

    LaunchedEffect(Unit) { load() }

    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(14.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        FoodBalanceCard(summary)

        sectionCard("Taom qo'shish") {
            OutlinedTextField(
                value = text,
                onValueChange = { text = it },
                label = { Text("Masalan: tushlikda 1 kosa osh") },
                modifier = Modifier.fillMaxWidth(),
            )
            Spacer(Modifier.height(8.dp))
            Button(
                onClick = {
                    if (text.isBlank()) return@Button
                    scope.launch {
                        busy = true
                        error = null
                        runCatching { Api.service.logFood(session.bearer, FoodLogRequest(text.trim())) }
                            .onSuccess {
                                note = it.reply
                                text = ""
                                load()
                            }
                            .onFailure { error = it.message }
                        busy = false
                    }
                },
                enabled = !busy,
            ) { Text(if (busy) "Yuborilmoqda..." else "Qo'shish") }
            if (note.isNotBlank()) {
                Spacer(Modifier.height(6.dp))
                Text(note, color = MUTED, fontSize = 12.sp)
            }
            error?.let { Text(it, color = MaterialTheme.colorScheme.error, fontSize = 12.sp) }
        }

        sectionCard("Taomlar") {
            val meals = summary?.meals ?: emptyList()
            if (meals.isEmpty()) {
                Text("Bugun hali taom qayd etilmagan.", color = MUTED, fontSize = 13.sp)
            }
            meals.forEach { meal ->
                Row(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                    Text(
                        MEAL_LABELS[meal.mealType] ?: meal.mealType,
                        modifier = Modifier.weight(1f),
                        color = INK,
                    )
                    Text("${meal.items} ta · ${meal.kcal.toInt()} kkal", color = MUTED, fontSize = 13.sp)
                }
                HorizontalDivider(color = Color(0xFF2B2B3D))
            }
        }
    }
}

// --------------------------- HUJJAT (WORD) ---------------------------
@Composable
private fun DocumentsScreen(session: Session, onBack: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var docs by remember { mutableStateOf<List<DocDto>>(emptyList()) }
    var selected by remember { mutableStateOf<DocDto?>(null) }
    var pickedUri by remember { mutableStateOf<Uri?>(null) }
    var pickedName by remember { mutableStateOf<String?>(null) }
    var instruction by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf<String?>(null) }
    var error by remember { mutableStateOf<String?>(null) }

    suspend fun load() {
        runCatching { Api.service.docs(session.bearer) }
            .onSuccess { docs = it.items }
            .onFailure { error = it.message }
    }

    LaunchedEffect(Unit) { load() }

    val picker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) {
            pickedUri = uri
            pickedName = documentName(context, uri)
            message = null
            error = null
        }
    }

    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(14.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = onBack) {
                Icon(Icons.Filled.ArrowBack, contentDescription = "Orqaga", tint = INK)
            }
            Text("Hujjatlar", fontWeight = FontWeight.SemiBold, fontSize = 18.sp, color = INK)
        }

        sectionCard("Word fayl yuklash") {
            Text(
                pickedName ?: "Fayl tanlanmagan",
                color = if (pickedName == null) MUTED else INK,
                fontSize = 13.sp,
            )
            Spacer(Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(onClick = { picker.launch(arrayOf("*/*")) }, enabled = !busy) {
                    Text("Fayl tanlash")
                }
                Button(
                    onClick = {
                        val uri = pickedUri ?: return@Button
                        scope.launch {
                            busy = true
                            error = null
                            message = null
                            runCatching { uploadDocument(session, context, uri) }
                                .onSuccess { doc ->
                                    selected = doc
                                    pickedUri = null
                                    pickedName = null
                                    message = "Yuklandi: ${doc.originalName} (v${doc.version})"
                                    load()
                                }
                                .onFailure { error = it.message }
                            busy = false
                        }
                    },
                    enabled = !busy && pickedUri != null,
                ) { Text(if (busy) "Kuting..." else "Yuklash") }
            }
            Spacer(Modifier.height(6.dp))
            Text("Faqat .docx fayl qabul qilinadi.", color = MUTED, fontSize = 12.sp)
        }

        sectionCard("AI bilan tahrirlash") {
            Text(
                selected?.let { "Tanlangan: ${it.originalName} (v${it.version})" }
                    ?: "Tahrirlash uchun hujjat tanlanmagan",
                color = MUTED,
                fontSize = 12.sp,
            )
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(
                value = instruction,
                onValueChange = { instruction = it },
                label = { Text("Masalan: matnni rasmiy uslubda qayta yoz") },
                modifier = Modifier.fillMaxWidth(),
                maxLines = 3,
            )
            Spacer(Modifier.height(8.dp))
            Button(
                onClick = {
                    val doc = selected ?: return@Button
                    scope.launch {
                        busy = true
                        error = null
                        message = null
                        runCatching {
                            Api.service.editDoc(
                                session.bearer,
                                DocEditRequest(doc.fileId, instruction.trim()),
                            )
                        }.onSuccess { newDoc ->
                            selected = newDoc
                            instruction = ""
                            message = "Yangi versiya tayyor: v${newDoc.version}"
                            load()
                        }.onFailure { error = it.message }
                        busy = false
                    }
                },
                enabled = !busy && selected != null && instruction.trim().length >= 2,
                modifier = Modifier.fillMaxWidth(),
            ) { Text(if (busy) "Tahrirlanmoqda..." else "Tahrirlash") }
            message?.let {
                Spacer(Modifier.height(6.dp))
                Text(it, color = Color(0xFF2E7D32), fontSize = 12.sp)
            }
            error?.let {
                Spacer(Modifier.height(6.dp))
                Text(it, color = MaterialTheme.colorScheme.error, fontSize = 12.sp)
            }
        }

        sectionCard("Hujjatlar va versiyalar (${docs.size})") {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("Har bir versiya alohida qator", color = MUTED, fontSize = 12.sp, modifier = Modifier.weight(1f))
                IconButton(onClick = { scope.launch { load() } }) {
                    Icon(Icons.Filled.Refresh, contentDescription = "Yangilash", tint = ACCENT)
                }
            }
            if (docs.isEmpty()) {
                Text("Hozircha hujjat yo'q.", color = MUTED, fontSize = 13.sp)
            }
            docs.forEach { doc ->
                val isSelected = selected?.fileId == doc.fileId
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { selected = doc }
                        .background(if (isSelected) SOFT else Color.Transparent, RoundedCornerShape(10.dp))
                        .padding(horizontal = 8.dp, vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(Modifier.weight(1f)) {
                        Text(doc.originalName, color = INK, fontSize = 14.sp)
                        Text(
                            "v${doc.version} · ${doc.sizeBytes / 1024} KB · " + formatMomentFlexible(doc.createdAt),
                            color = MUTED,
                            fontSize = 12.sp,
                        )
                    }
                    IconButton(
                        onClick = {
                            scope.launch {
                                busy = true
                                error = null
                                message = null
                                runCatching { withContext(Dispatchers.IO) { downloadDocument(session, context, doc) } }
                                    .onSuccess { message = "Saqlandi: $it" }
                                    .onFailure { error = it.message }
                                busy = false
                            }
                        },
                        enabled = !busy,
                    ) {
                        Icon(Icons.Filled.Download, contentDescription = "Yuklab olish", tint = ACCENT)
                    }
                }
                HorizontalDivider(color = Color(0xFF2B2B3D))
            }
        }
        Spacer(Modifier.height(16.dp))
    }
}

private fun formatMomentFlexible(value: String?): String {
    if (value.isNullOrBlank()) return ""
    val pattern = DateTimeFormatter.ofPattern("dd.MM.yyyy HH:mm")
    runCatching {
        return OffsetDateTime.parse(value)
            .atZoneSameInstant(java.time.ZoneId.systemDefault())
            .format(pattern)
    }
    return runCatching {
        java.time.LocalDateTime.parse(value)
            .atZone(java.time.ZoneOffset.UTC)
            .withZoneSameInstant(java.time.ZoneId.systemDefault())
            .format(pattern)
    }.getOrDefault(value)
}

// --------------------------- SOZLAMALAR ---------------------------
@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun SettingsScreen(
    session: Session,
    user: UserDto?,
    onUser: (UserDto) -> Unit,
    onLogout: () -> Unit,
    onOpenAdmin: () -> Unit,
) {
    val scope = rememberCoroutineScope()
    var name by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var language by remember { mutableStateOf("uz") }
    var timezone by remember { mutableStateOf("Asia/Tashkent") }
    var adviceTime by remember { mutableStateOf("08:00") }
    var kcalGoal by remember { mutableStateOf("2200") }
    var serverUrl by remember { mutableStateOf(Api.currentBaseUrl()) }
    var currentPassword by remember { mutableStateOf("") }
    var newPassword by remember { mutableStateOf("") }
    var message by remember { mutableStateOf<String?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }

    LaunchedEffect(user?.id) {
        val profile = runCatching { Api.service.me(session.bearer) }.getOrNull() ?: user
        if (profile != null) {
            name = profile.name
            email = profile.email ?: ""
            language = profile.language
            timezone = profile.timezone
            adviceTime = (profile.adviceTime ?: "08:00:00").take(5)
            kcalGoal = profile.kcalGoal.toString()
            onUser(profile)
        }
    }

    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(14.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        sectionCard("Profil") {
            OutlinedTextField(
                value = name,
                onValueChange = { name = it },
                label = { Text("Ism") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(
                value = email,
                onValueChange = { email = it },
                label = { Text("Email") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            Spacer(Modifier.height(10.dp))
            Text("Til", color = MUTED, fontSize = 12.sp)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("uz" to "O'zbekcha", "ru" to "Русский", "en" to "English").forEach { pair ->
                    FilterChip(
                        selected = language == pair.first,
                        onClick = { language = pair.first },
                        label = { Text(pair.second) },
                    )
                }
            }
        }

        sectionCard("Kundalik sozlamalar") {
            OutlinedTextField(
                value = timezone,
                onValueChange = { timezone = it },
                label = { Text("Vaqt zonasi") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(
                value = adviceTime,
                onValueChange = { adviceTime = it },
                label = { Text("Maslahat vaqti (HH:mm)") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(
                value = kcalGoal,
                onValueChange = { kcalGoal = it.filter { ch -> ch.isDigit() } },
                label = { Text("Kunlik kkal maqsadi") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            Spacer(Modifier.height(12.dp))
            Button(
                onClick = {
                    scope.launch {
                        busy = true
                        error = null
                        message = null
                        runCatching {
                            Api.service.updateMe(
                                session.bearer,
                                UpdateUserRequest(
                                    name = name.trim().ifBlank { null },
                                    email = email.trim().ifBlank { null },
                                    language = language,
                                    timezone = timezone.trim().ifBlank { null },
                                    adviceTime = adviceTime.trim().ifBlank { null },
                                    kcalGoal = kcalGoal.toIntOrNull(),
                                ),
                            )
                        }.onSuccess {
                            onUser(it)
                            message = "Sozlamalar saqlandi."
                        }.onFailure { error = it.message }
                        busy = false
                    }
                },
                enabled = !busy,
                modifier = Modifier.fillMaxWidth(),
            ) { Text(if (busy) "Saqlanmoqda..." else "Saqlash") }
            message?.let { Text(it, color = Color(0xFF2E7D32), fontSize = 12.sp) }
            error?.let { Text(it, color = MaterialTheme.colorScheme.error, fontSize = 12.sp) }
        }

        sectionCard("Parolni o'zgartirish") {
            OutlinedTextField(
                value = currentPassword,
                onValueChange = { currentPassword = it },
                label = { Text("Joriy parol") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(
                value = newPassword,
                onValueChange = { newPassword = it },
                label = { Text("Yangi parol (kamida 6 belgi)") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            Spacer(Modifier.height(10.dp))
            OutlinedButton(
                onClick = {
                    scope.launch {
                        error = null
                        message = null
                        runCatching {
                            Api.service.changePassword(
                                session.bearer,
                                PasswordChangeRequest(currentPassword, newPassword),
                            )
                        }.onSuccess {
                            currentPassword = ""
                            newPassword = ""
                            message = "Parol yangilandi."
                        }.onFailure { error = it.message }
                    }
                },
            ) { Text("Parolni yangilash") }
        }

        sectionCard("Server manzili") {
            OutlinedTextField(
                value = serverUrl,
                onValueChange = { serverUrl = it },
                label = { Text("http://192.168.0.102:8000") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            Spacer(Modifier.height(10.dp))
            OutlinedButton(
                onClick = {
                    val clean = serverUrl.trim().trimEnd('/')
                    if (!clean.startsWith("http")) {
                        error = "Manzil http:// bilan boshlansin."
                        return@OutlinedButton
                    }
                    session.serverUrl = clean
                    Api.setBaseUrl(clean)
                    message = "Manzil saqlandi."
                },
            ) { Text("Manzilni saqlash") }
        }

        if (user?.isAdmin == true) {
            sectionCard("Admin") {
                Text("Foydalanuvchilar va statistika", color = MUTED, fontSize = 13.sp)
                Spacer(Modifier.height(8.dp))
                Button(onClick = onOpenAdmin, modifier = Modifier.fillMaxWidth()) {
                    Icon(Icons.Filled.AdminPanelSettings, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Admin panelni ochish")
                }
            }
        }

        sectionCard("Hisob") {
            Text(
                "${user?.name ?: ""} · ${user?.email ?: ""} · " +
                    if (user?.isAdmin == true) "Admin" else "Foydalanuvchi",
                color = MUTED,
                fontSize = 13.sp,
            )
            Spacer(Modifier.height(10.dp))
            OutlinedButton(onClick = onLogout, modifier = Modifier.fillMaxWidth()) {
                Icon(Icons.Filled.Logout, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text("Hisobdan chiqish", color = Color(0xFFC0392B))
            }
        }
        Spacer(Modifier.height(16.dp))
    }
}

// --------------------------- ADMIN ---------------------------
@Composable
private fun AdminScreen(session: Session, onBack: () -> Unit) {
    var stats by remember { mutableStateOf<AdminStatsDto?>(null) }
    var users by remember { mutableStateOf<List<AdminUserDto>>(emptyList()) }
    var error by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(Unit) {
        runCatching { Api.service.adminStats(session.bearer) }
            .onSuccess { stats = it }
            .onFailure { error = it.message }
        runCatching { Api.service.adminUsers(session.bearer) }
            .onSuccess { users = it.items }
            .onFailure { error = it.message }
    }

    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(14.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = onBack) {
                Icon(Icons.Filled.ArrowBack, contentDescription = "Orqaga")
            }
            Text("Admin panel", fontWeight = FontWeight.SemiBold, fontSize = 18.sp, color = INK)
        }

        error?.let { Text(it, color = MaterialTheme.colorScheme.error, fontSize = 12.sp) }

        sectionCard("Statistika") {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                StatItem("Foydalanuvchi", stats?.users ?: 0)
                StatItem("Qurilma", stats?.devices ?: 0)
                StatItem("Suhbat", stats?.sessions ?: 0)
            }
            Spacer(Modifier.height(10.dp))
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                StatItem("Xabar", stats?.messages ?: 0)
                StatItem("Eslatma", stats?.reminders ?: 0)
                StatItem("Ovqat", stats?.foodLogs ?: 0)
            }
        }

        sectionCard("Foydalanuvchilar (${users.size})") {
            users.forEach { item ->
                Row(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                    Column(Modifier.weight(1f)) {
                        Text(item.name, color = INK)
                        Text(item.email ?: "—", color = MUTED, fontSize = 12.sp)
                    }
                    Text(
                        if (item.isAdmin) "Admin" else "User",
                        color = if (item.isAdmin) ACCENT else MUTED,
                        fontSize = 12.sp,
                    )
                }
                HorizontalDivider(color = Color(0xFF2B2B3D))
            }
        }
        Spacer(Modifier.height(16.dp))
    }
}

@Composable
private fun StatItem(label: String, value: Int) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(value.toString(), fontSize = 22.sp, fontWeight = FontWeight.Bold, color = ACCENT)
        Text(label, fontSize = 11.sp, color = MUTED)
    }
}

// --------------------------- HUJJAT YUBORISH/YUKLASH ---------------------------
private const val DOCX_MIME =
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

private fun documentName(context: Context, uri: Uri): String {
    runCatching {
        context.contentResolver
            .query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)
            ?.use { cursor -> if (cursor.moveToFirst()) cursor.getString(0) else null }
    }.getOrNull()?.let { return it }
    return "hujjat.docx"
}

private fun serverErrorMessage(body: String): String = runCatching {
    Json { ignoreUnknownKeys = true }
        .parseToJsonElement(body)
        .jsonObject["error"]
        ?.jsonObject
        ?.get("message")
        ?.jsonPrimitive
        ?.content
}.getOrNull() ?: "Server xatosi"

private fun uploadDocument(session: Session, context: Context, uri: Uri): DocDto {
    val bytes = context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
        ?: error("Faylni o'qib bo'lmadi")
    val name = documentName(context, uri)
    val body = MultipartBody.Builder()
        .setType(MultipartBody.FORM)
        .addFormDataPart("file", name, bytes.toRequestBody(DOCX_MIME.toMediaType()))
        .build()
    val request = Request.Builder()
        .url(Api.currentBaseUrl().trimEnd('/') + "/api/v1/docs/upload")
        .addHeader("Authorization", session.bearer)
        .post(body)
        .build()

    OkHttpClient().newCall(request).execute().use { response ->
        val text = response.body?.string().orEmpty()
        if (!response.isSuccessful) error(serverErrorMessage(text))
        return Json { ignoreUnknownKeys = true }.decodeFromString(DocDto.serializer(), text)
    }
}

private fun downloadDocument(session: Session, context: Context, doc: DocDto): String {
    val request = Request.Builder()
        .url(Api.currentBaseUrl().trimEnd('/') + "/api/v1/docs/${doc.fileId}/download")
        .addHeader("Authorization", session.bearer)
        .build()

    OkHttpClient().newCall(request).execute().use { response ->
        val bytes = response.body?.bytes()
        if (!response.isSuccessful || bytes == null) error("Yuklab bo'lmadi (${response.code})")

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val values = ContentValues().apply {
                put(MediaStore.Downloads.DISPLAY_NAME, doc.originalName)
                put(MediaStore.Downloads.MIME_TYPE, DOCX_MIME)
            }
            val target = context.contentResolver
                .insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values)
                ?: error("Saqlash joyi topilmadi")
            context.contentResolver.openOutputStream(target)?.use { it.write(bytes) }
                ?: error("Faylni yozib bo'lmadi")
            return "Download/${doc.originalName}"
        }

        val dir = context.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS) ?: context.cacheDir
        val file = File(dir, doc.originalName)
        file.writeBytes(bytes)
        return file.absolutePath
    }
}

// --------------------------- OVOZ YUBORISH ---------------------------
@Serializable
private data class VoiceResponse(
    val session_id: Int,
    val text: String,
    val reply: String,
    val audio_url: String? = null,
)

private fun uploadVoice(session: Session, file: File, sessionId: Int?, json: Json): VoiceResponse? {
    val client = OkHttpClient()
    val bodyBuilder = MultipartBody.Builder().setType(MultipartBody.FORM)
        .addFormDataPart(
            "audio",
            file.name,
            file.asRequestBody("audio/m4a".toMediaType()),
        )
    if (sessionId != null) bodyBuilder.addFormDataPart("session_id", sessionId.toString())

    val request = Request.Builder()
        .url(Api.currentBaseUrl().trimEnd('/') + "/api/v1/voice/chat")
        .addHeader("Authorization", session.bearer)
        .post(bodyBuilder.build())
        .build()

    client.newCall(request).execute().use { response ->
        val body = response.body?.string() ?: return null
        if (!response.isSuccessful) return null
        return json.decodeFromString(VoiceResponse.serializer(), body)
    }
}
