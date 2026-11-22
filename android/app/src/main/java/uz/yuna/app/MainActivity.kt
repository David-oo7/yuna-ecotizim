package uz.yuna.app

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.media.MediaRecorder
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AdminPanelSettings
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Chat
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Lightbulb
import androidx.compose.material.icons.filled.Logout
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Notifications
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Restaurant
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
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
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File
import java.time.OffsetDateTime
import java.time.format.DateTimeFormatter

private val ACCENT = Color(0xFF7C5CFF)
private val SOFT = Color(0xFFEDE9FF)
private val INK = Color(0xFF1A1A1A)
private val MUTED = Color(0xFF6B6B80)

private val MEAL_LABELS = mapOf(
    "breakfast" to "Nonushta",
    "lunch" to "Tushlik",
    "dinner" to "Kechki ovqat",
    "snack" to "Gazak",
)

private enum class Tabs(val title: String, val icon: ImageVector) {
    CHAT("Suhbat", Icons.Filled.Chat),
    REMINDERS("Eslatmalar", Icons.Filled.Notifications),
    FOOD("Ovqat", Icons.Filled.Restaurant),
    ADVICE("Maslahat", Icons.Filled.Lightbulb),
    SETTINGS("Sozlamalar", Icons.Filled.Settings),
}

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(colorScheme = lightColorScheme(primary = ACCENT)) {
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
    var tab by remember { mutableStateOf(Tabs.CHAT) }
    var adminOpen by remember { mutableStateOf(false) }

    Scaffold(
        containerColor = Color(0xFFF7F6FC),
        bottomBar = {
            NavigationBar(containerColor = Color.White) {
                Tabs.entries.forEach { item ->
                    NavigationBarItem(
                        selected = tab == item && !adminOpen,
                        onClick = {
                            adminOpen = false
                            tab = item
                        },
                        icon = { Icon(item.icon, contentDescription = item.title) },
                        label = { Text(item.title, fontSize = 11.sp) },
                    )
                }
            }
        },
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            if (adminOpen) {
                AdminScreen(session) { adminOpen = false }
            } else when (tab) {
                Tabs.CHAT -> ChatScreen(session, user)
                Tabs.REMINDERS -> RemindersScreen(session)
                Tabs.FOOD -> FoodScreen(session)
                Tabs.ADVICE -> AdviceScreen(session)
                Tabs.SETTINGS -> SettingsScreen(
                    session = session,
                    user = user,
                    onUser = onUser,
                    onLogout = onLogout,
                    onOpenAdmin = { adminOpen = true },
                )
            }
        }
    }
}

@Composable
private fun sectionCard(title: String, content: @Composable ColumnScope.() -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        shape = RoundedCornerShape(16.dp),
    ) {
        Column(Modifier.padding(16.dp)) {
            Text(title, fontWeight = FontWeight.SemiBold, color = INK)
            Spacer(Modifier.height(10.dp))
            content()
        }
    }
}

// --------------------------- CHAT ---------------------------
data class UiMessage(val role: String, val text: String)

@Composable
private fun ChatScreen(session: Session, user: UserDto?) {
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

    LaunchedEffect(messages.size) {
        if (messages.isNotEmpty()) listState.animateScrollToItem(messages.lastIndex)
    }

    Column(Modifier.fillMaxSize()) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f)) {
                Text("Yuna", fontSize = 22.sp, fontWeight = FontWeight.Bold, color = ACCENT)
                Text(
                    user?.name?.let { "Salom, $it" } ?: "Sizning shaxsiy yordamchingiz",
                    color = MUTED,
                    fontSize = 12.sp,
                )
            }
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
            color = if (isUser) ACCENT else Color(0xFFF0F0F5),
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
    val scope = rememberCoroutineScope()
    var items by remember { mutableStateOf<List<ReminderDto>>(emptyList()) }
    var text by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    suspend fun load() {
        runCatching { Api.service.reminders(session.bearer) }
            .onSuccess { items = it.items.filter { r -> r.status == "pending" } }
            .onFailure { error = it.message }
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
                HorizontalDivider(color = Color(0xFFF0EFF7))
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
        sectionCard("Bugungi hisob") {
            val totals = summary?.totals ?: emptyMap()
            Text(
                "${(totals["kcal"] ?: 0.0).toInt()} / ${summary?.goalKcal ?: 0} kkal",
                fontSize = 26.sp,
                fontWeight = FontWeight.Bold,
                color = ACCENT,
            )
            Text(
                "Oqsil ${(totals["protein"] ?: 0.0).toInt()} g · " +
                    "Yog' ${(totals["fat"] ?: 0.0).toInt()} g · " +
                    "Uglevod ${(totals["carbs"] ?: 0.0).toInt()} g",
                color = MUTED,
                fontSize = 13.sp,
            )
        }

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
                HorizontalDivider(color = Color(0xFFF0EFF7))
            }
        }
    }
}

// --------------------------- MASLAHAT ---------------------------
@Composable
private fun AdviceScreen(session: Session) {
    val scope = rememberCoroutineScope()
    var advice by remember { mutableStateOf<AdviceDto?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }

    suspend fun load() {
        busy = true
        runCatching { Api.service.advice(session.bearer) }
            .onSuccess { advice = it; error = null }
            .onFailure { error = it.message }
        busy = false
    }

    LaunchedEffect(Unit) { load() }

    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(14.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        sectionCard("Kunlik maslahat") {
            Text(advice?.date ?: "", color = MUTED, fontSize = 12.sp)
            Spacer(Modifier.height(8.dp))
            Text(
                when {
                    busy && advice == null -> "Yuklanmoqda..."
                    error != null -> "Xatolik: $error"
                    else -> advice?.text ?: ""
                },
                fontSize = 15.sp,
                color = INK,
            )
            Spacer(Modifier.height(12.dp))
            Button(onClick = { scope.launch { load() } }, enabled = !busy) {
                Text("Yangilash")
            }
        }
    }
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
                HorizontalDivider(color = Color(0xFFF0EFF7))
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
