package uz.yuna.app

import android.content.Context
import android.content.Intent
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/** O'rnatilgan ilovalar ro'yxatini backendga yuboradi va buyruq bo'yicha ochadi. */
object AppsSync {

    fun installedApps(context: Context): List<AppInfo> {
        val pm = context.packageManager
        return pm.getInstalledApplications(PackageManager.GET_META_DATA)
            .filter { app: ApplicationInfo -> pm.getLaunchIntentForPackage(app.packageName) != null }
            .map { app ->
                AppInfo(
                    appName = pm.getApplicationLabel(app).toString(),
                    packageName = app.packageName,
                )
            }
    }

    fun sync(context: Context, session: Session) {
        val apps = installedApps(context)
        CoroutineScope(Dispatchers.IO).launch {
            runCatching {
                Api.service.registerDevice(
                    session.bearer,
                    DeviceRegister(
                        deviceUid = session.deviceUid,
                        model = "${android.os.Build.MANUFACTURER} ${android.os.Build.MODEL}",
                    ),
                )
                Api.service.syncApps(session.bearer, AppsSyncRequest(session.deviceUid, apps))
            }
        }
    }

    /** Buyruqdan kelgan paketni ochadi. */
    fun openPackage(context: Context, packageName: String?): Boolean {
        if (packageName.isNullOrBlank()) return false
        val intent = context.packageManager.getLaunchIntentForPackage(packageName) ?: return false
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
        return true
    }

    /** Nomi bo'yicha ilovani topib ochadi (zaxira yo'l). */
    fun openByName(context: Context, appName: String?): Boolean {
        if (appName.isNullOrBlank()) return false
        val match = installedApps(context).firstOrNull {
            it.appName.equals(appName, ignoreCase = true) ||
                it.appName.lowercase().contains(appName.lowercase())
        } ?: return false
        return openPackage(context, match.packageName)
    }
}
