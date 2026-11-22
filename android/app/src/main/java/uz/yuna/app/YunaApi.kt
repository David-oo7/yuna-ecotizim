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
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query
import java.util.concurrent.TimeUnit

// ---------------- Modellar ----------------
@Serializable
data class LoginRequest(val email: String, val password: String)

@Serializable
data class RegisterRequest(val name: String, val email: String, val password: String)

@Serializable
data class UserDto(
    val id: Int,
    val name: String,
    val email: String? = null,
    val language: String = "uz",
    val timezone: String = "Asia/Tashkent",
    @SerialName("kcal_goal") val kcalGoal: Int = 2200,
    @SerialName("advice_time") val adviceTime: String? = null,
    @SerialName("is_admin") val isAdmin: Boolean = false,
)

@Serializable
data class UpdateUserRequest(
    val name: String? = null,
    val email: String? = null,
    val language: String? = null,
    val timezone: String? = null,
    @SerialName("advice_time") val adviceTime: String? = null,
    @SerialName("kcal_goal") val kcalGoal: Int? = null,
)

@Serializable
data class PasswordChangeRequest(
    @SerialName("current_password") val currentPassword: String,
    @SerialName("new_password") val newPassword: String,
)

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

// ---------------- Eslatmalar ----------------
@Serializable
data class ReminderDto(
    val id: Int,
    val text: String,
    @SerialName("remind_at") val remindAt: String,
    @SerialName("repeat_rule") val repeatRule: String? = null,
    val channel: String = "both",
    val status: String = "pending",
)

@Serializable
data class ReminderList(val items: List<ReminderDto> = emptyList())

@Serializable
data class ReminderCreate(
    val text: String,
    @SerialName("remind_at") val remindAt: String,
    val channel: String = "both",
)

// ---------------- Ovqat ----------------
@Serializable
data class MealDto(
    @SerialName("meal_type") val mealType: String,
    val items: Int = 0,
    val kcal: Double = 0.0,
)

@Serializable
data class FoodSummaryDto(
    val date: String,
    @SerialName("goal_kcal") val goalKcal: Int = 2200,
    val totals: Map<String, Double> = emptyMap(),
    val meals: List<MealDto> = emptyList(),
    val note: String = "Raqamlar taxminiy.",
)

@Serializable
data class FoodLogRequest(val text: String, val source: String = "text")

@Serializable
data class FoodItemDto(
    val id: Int,
    val name: String,
    @SerialName("meal_type") val mealType: String,
    @SerialName("amount_text") val amountText: String? = null,
    val kcal: Double = 0.0,
    val protein: Double = 0.0,
    val fat: Double = 0.0,
    val carbs: Double = 0.0,
)

@Serializable
data class FoodLogResponse(
    val reply: String,
    val items: List<FoodItemDto> = emptyList(),
)

// ---------------- Hujjat (Word) ----------------
@Serializable
data class DocDto(
    @SerialName("file_id") val fileId: Int,
    val version: Int = 1,
    @SerialName("original_name") val originalName: String,
    @SerialName("size_bytes") val sizeBytes: Long = 0,
    @SerialName("created_at") val createdAt: String? = null,
    @SerialName("download_url") val downloadUrl: String? = null,
    @SerialName("parent_id") val parentId: Int? = null,
)

@Serializable
data class DocList(val items: List<DocDto> = emptyList())

@Serializable
data class DocEditRequest(
    @SerialName("file_id") val fileId: Int,
    val instruction: String,
)

// ---------------- Maslahat / admin ----------------
@Serializable
data class AdviceDto(val date: String, val text: String)

@Serializable
data class AdminUserDto(
    val id: Int,
    val name: String,
    val email: String? = null,
    val language: String = "uz",
    val timezone: String = "Asia/Tashkent",
    @SerialName("kcal_goal") val kcalGoal: Int = 2200,
    @SerialName("is_admin") val isAdmin: Boolean = false,
    @SerialName("is_active") val isActive: Boolean = true,
)

@Serializable
data class AdminUserList(val items: List<AdminUserDto> = emptyList())

@Serializable
data class AdminStatsDto(
    val users: Int = 0,
    val devices: Int = 0,
    val sessions: Int = 0,
    val messages: Int = 0,
    val reminders: Int = 0,
    @SerialName("food_logs") val foodLogs: Int = 0,
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

    @GET("api/v1/me")
    suspend fun me(@Header("Authorization") bearer: String): UserDto

    @PATCH("api/v1/me")
    suspend fun updateMe(
        @Header("Authorization") bearer: String,
        @Body body: UpdateUserRequest,
    ): UserDto

    @POST("api/v1/auth/change-password")
    suspend fun changePassword(
        @Header("Authorization") bearer: String,
        @Body body: PasswordChangeRequest,
    )

    @GET("api/v1/reminders")
    suspend fun reminders(
        @Header("Authorization") bearer: String,
        @Query("status") status: String? = null,
    ): ReminderList

    @POST("api/v1/reminders")
    suspend fun createReminder(
        @Header("Authorization") bearer: String,
        @Body body: ReminderCreate,
    ): ReminderDto

    @DELETE("api/v1/reminders/{id}")
    suspend fun deleteReminder(
        @Header("Authorization") bearer: String,
        @Path("id") id: Int,
    )

    @GET("api/v1/food/summary")
    suspend fun foodSummary(@Header("Authorization") bearer: String): FoodSummaryDto

    @POST("api/v1/food/log")
    suspend fun logFood(
        @Header("Authorization") bearer: String,
        @Body body: FoodLogRequest,
    ): FoodLogResponse

    @GET("api/v1/advice/today")
    suspend fun advice(@Header("Authorization") bearer: String): AdviceDto

    @GET("api/v1/docs")
    suspend fun docs(@Header("Authorization") bearer: String): DocList

    @POST("api/v1/docs/edit")
    suspend fun editDoc(
        @Header("Authorization") bearer: String,
        @Body body: DocEditRequest,
    ): DocDto

    @GET("api/v1/admin/users")
    suspend fun adminUsers(@Header("Authorization") bearer: String): AdminUserList

    @GET("api/v1/admin/stats")
    suspend fun adminStats(@Header("Authorization") bearer: String): AdminStatsDto

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

    /** Server manzili — sozlamalardan o'zgartirilishi mumkin. */
    private var baseUrl: String = BuildConfig.API_URL
    private var cached: YunaService? = null
    private var cachedBase: String? = null

    fun setBaseUrl(url: String) {
        val clean = url.trim().trimEnd('/')
        if (clean.isNotBlank() && clean != baseUrl) {
            baseUrl = clean
            cached = null
        }
    }

    fun currentBaseUrl(): String = baseUrl

    val service: YunaService
        get() {
            val base = baseUrl.trimEnd('/') + "/"
            val existing = cached
            if (existing != null && cachedBase == base) return existing

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

            val service = Retrofit.Builder()
                .baseUrl(base)
                .client(client)
                .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
                .build()
                .create(YunaService::class.java)
            cached = service
            cachedBase = base
            return service
        }
}

/** Token, qurilma va server manzilini xavfsiz saqlash. */
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

    var serverUrl: String?
        get() = prefs.getString("server_url", null)
        set(value) = prefs.edit().putString("server_url", value).apply()

    val deviceUid: String
        get() = prefs.getString("device_uid", null) ?: java.util.UUID.randomUUID().toString()
            .also { prefs.edit().putString("device_uid", it).apply() }

    val bearer: String get() = "Bearer ${accessToken.orEmpty()}"

    fun save(tokens: TokenResponse) {
        accessToken = tokens.accessToken
        refreshToken = tokens.refreshToken
        userName = tokens.user.name
    }

    fun clear() {
        val device = prefs.getString("device_uid", null)
        val server = prefs.getString("server_url", null)
        prefs.edit().clear().apply()
        prefs.edit().putString("device_uid", device).putString("server_url", server).apply()
    }
}
