package uz.yuna.app

import android.content.Context
import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.Path
import java.util.concurrent.TimeUnit

// ---------------- Modellar ----------------
@Serializable
data class LoginRequest(val email: String, val password: String)

@Serializable
data class RegisterRequest(val name: String, val email: String, val password: String)

@Serializable
data class UserDto(val id: Int, val name: String, val email: String? = null)

@Serializable
data class TokenResponse(
    @SerialName("access_token") val accessToken: String,
    @SerialName("refresh_token") val refreshToken: String,
    val user: UserDto,
)

@Serializable
data class ChatRequest(
    val text: String,
    @SerialName("session_id") val sessionId: Int? = null,
    val mode: String = "auto",
)

@Serializable
data class ActionDto(val type: String, val id: Int? = null)

@Serializable
data class ChatResponse(
    @SerialName("session_id") val sessionId: Int,
    @SerialName("message_id") val messageId: Int,
    val reply: String,
    val actions: List<ActionDto> = emptyList(),
)

@Serializable
data class MessageDto(
    val id: Int,
    val role: String,
    val content: String,
)

@Serializable
data class SessionDto(val id: Int, val title: String)

@Serializable
data class SessionDetail(
    val id: Int,
    val title: String,
    val messages: List<MessageDto> = emptyList(),
)

@Serializable
data class SessionList(val items: List<SessionDto>)

@Serializable
data class DeviceRegister(
    @SerialName("device_uid") val deviceUid: String,
    val type: String = "android",
    val model: String? = null,
    @SerialName("fcm_token") val fcmToken: String? = null,
)

@Serializable
data class AppInfo(
    @SerialName("app_name") val appName: String,
    @SerialName("package_name") val packageName: String,
)

@Serializable
data class AppsSyncRequest(
    @SerialName("device_uid") val deviceUid: String,
    val apps: List<AppInfo>,
)

// ---------------- API ----------------
interface YunaService {
    @POST("api/v1/auth/login")
    suspend fun login(@Body body: LoginRequest): TokenResponse

    @POST("api/v1/auth/register")
    suspend fun register(@Body body: RegisterRequest): TokenResponse

    @POST("api/v1/chat")
    suspend fun chat(
        @Header("Authorization") bearer: String,
        @Body body: ChatRequest,
    ): ChatResponse

    @GET("api/v1/sessions")
    suspend fun sessions(@Header("Authorization") bearer: String): SessionList

    @GET("api/v1/sessions/{id}")
    suspend fun session(
        @Header("Authorization") bearer: String,
        @Path("id") id: Int,
    ): SessionDetail

    @POST("api/v1/devices/register")
    suspend fun registerDevice(
        @Header("Authorization") bearer: String,
        @Body body: DeviceRegister,
    )

    @POST("api/v1/devices/apps/sync")
    suspend fun syncApps(
        @Header("Authorization") bearer: String,
        @Body body: AppsSyncRequest,
    )
}

object Api {
    private val json = Json { ignoreUnknownKeys = true; encodeDefaults = true }

    val service: YunaService by lazy {
        val logging = HttpLoggingInterceptor().apply { level = HttpLoggingInterceptor.Level.BASIC }
        val client = OkHttpClient.Builder()
            .connectTimeout(20, TimeUnit.SECONDS)
            .readTimeout(90, TimeUnit.SECONDS)
            .addInterceptor { chain ->
                val request = chain.request().newBuilder()
                    .header("Accept", "application/json")
                    .build()
                chain.proceed(request)
            }
            .addInterceptor(logging)
            .build()

        Retrofit.Builder()
            .baseUrl(BuildConfig.API_URL.trimEnd('/') + "/")
            .client(client)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
            .create(YunaService::class.java)
    }
}

/** Token va qurilma identifikatorini xavfsiz saqlash. */
class Session(context: Context) {
    private val prefs = context.getSharedPreferences("yuna", Context.MODE_PRIVATE)

    var accessToken: String?
        get() = prefs.getString("access", null)
        set(value) = prefs.edit().putString("access", value).apply()

    var refreshToken: String?
        get() = prefs.getString("refresh", null)
        set(value) = prefs.edit().putString("refresh", value).apply()

    var userName: String?
        get() = prefs.getString("name", null)
        set(value) = prefs.edit().putString("name", value).apply()

    val deviceUid: String
        get() = prefs.getString("device_uid", null) ?: java.util.UUID.randomUUID().toString()
            .also { prefs.edit().putString("device_uid", it).apply() }

    val bearer: String get() = "Bearer ${accessToken.orEmpty()}"

    fun save(tokens: TokenResponse) {
        accessToken = tokens.accessToken
        refreshToken = tokens.refreshToken
        userName = tokens.user.name
    }

    fun clear() = prefs.edit().clear().apply()
}
