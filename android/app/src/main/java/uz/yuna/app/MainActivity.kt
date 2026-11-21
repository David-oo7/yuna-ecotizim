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
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
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

private val ACCENT = Color(0xFF7C5CFF)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(
                colorScheme = lightColorScheme(primary = ACCENT)
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

    if (loggedIn) {
        ChatScreen(session) {
            session.clear()
            loggedIn = false
        }
    } else {
        LoginScreen(session) {
            loggedIn = true
            AppsSync.sync(context, session)
        }
    }
}

// --------------------------- LOGIN ---------------------------
@OptIn(ExperimentalMaterial3Api::class)
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
        Text("Sizning shaxsiy yordamchingiz", color = Color.Gray)
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

// --------------------------- CHAT ---------------------------
data class UiMessage(val role: String, val text: String)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ChatScreen(session: Session, onLogout: () -> Unit) {
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

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Yuna", color = ACCENT, fontWeight = FontWeight.Bold) },
                actions = { TextButton(onClick = onLogout) { Text("Chiqish") } },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.White),
            )
        }
    ) { padding ->
        Column(Modifier.padding(padding).fillMaxSize()) {
            LazyColumn(
                state = listState,
                modifier = Modifier.weight(1f).fillMaxWidth().padding(horizontal = 12.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
                contentPadding = PaddingValues(vertical = 12.dp),
            ) {
                if (messages.isEmpty()) {
                    item {
                        Text(
                            "Salom! Men Yuna. Eslatma, ovqat hisobi, rasm yoki hujjat — " +
                                "shunchaki yozing yoki mikrofonni bosing.",
                            color = Color.Gray,
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
                color = if (isUser) Color.White else Color(0xFF1A1A1A),
                fontFamily = if (message.text.contains("```")) FontFamily.Monospace else FontFamily.Default,
            )
        }
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
        .url(BuildConfig.API_URL.trimEnd('/') + "/api/v1/voice/chat")
        .addHeader("Authorization", session.bearer)
        .post(bodyBuilder.build())
        .build()

    client.newCall(request).execute().use { response ->
        val body = response.body?.string() ?: return null
        if (!response.isSuccessful) return null
        return json.decodeFromString(VoiceResponse.serializer(), body)
    }
}
