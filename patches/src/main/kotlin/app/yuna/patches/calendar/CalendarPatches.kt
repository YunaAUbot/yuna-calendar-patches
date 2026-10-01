package app.yuna.patches.calendar

import app.morphe.patcher.Fingerprint
import app.morphe.patcher.extensions.InstructionExtensions.addInstructions
import app.morphe.patcher.patch.bytecodePatch
import app.morphe.patcher.patch.Compatibility
import app.morphe.patcher.patch.AppTarget
import app.morphe.patcher.patch.ApkFileType
import com.android.tools.smali.dexlib2.AccessFlags

private const val UTILITY = "Lde/mash/android/calendar/core/utility/Utility;"
private const val CONTEXT = "Landroid/content/Context;"
private const val PRODUCT = "Lde/mash/android/calendar/core/purchase/InAppProduct;"

private object PromotionEventFingerprint : Fingerprint(
    definingClass = UTILITY,
    name = "createPromotionEvent",
    accessFlags = listOf(AccessFlags.PUBLIC, AccessFlags.STATIC),
    returnType = "V",
    parameters = listOf(CONTEXT, "I", "Ljava/util/List;")
)

private object ProductPremiumFingerprint : Fingerprint(
    definingClass = UTILITY,
    name = "isProVersion",
    accessFlags = listOf(AccessFlags.PUBLIC, AccessFlags.STATIC),
    returnType = "Z",
    parameters = listOf(CONTEXT, PRODUCT)
)

private object DatabasePremiumFingerprint : Fingerprint(
    definingClass = UTILITY,
    name = "isProVersion",
    accessFlags = listOf(AccessFlags.PUBLIC, AccessFlags.STATIC),
    returnType = "Z",
    parameters = listOf(CONTEXT, "Landroid/database/sqlite/SQLiteDatabase;")
)

@Suppress("unused")
val hideFreeEditionEvents = bytecodePatch(
    name = "Hide Free Edition reminder events",
    description = "Stops synthetic Free Edition events from being inserted into the widget agenda. Does not unlock premium or change real calendar reminders.",
    default = true
) {
    compatibleWith(Compatibility(
        name = "Your Calendar Widget",
        packageName = "de.mash.android.calendar",
        apkFileType = ApkFileType.APK,
        appIconColor = 0x4285F4,
        targets = listOf(AppTarget(version = "1.71.3"))
    ))
    execute {
        PromotionEventFingerprint.method.addInstructions(0, "return-void")
    }
}

@Suppress("unused")
val enableLocalPremiumFeatures = bytecodePatch(
    name = "Enable local premium features",
    description = "Optional: enables the two local Pro checks. Does not grant a Play purchase or subscription, and cannot guarantee Google/Microsoft account integrations after re-signing.",
    default = false
) {
    compatibleWith(Compatibility(
        name = "Your Calendar Widget",
        packageName = "de.mash.android.calendar",
        apkFileType = ApkFileType.APK,
        appIconColor = 0x4285F4,
        targets = listOf(AppTarget(version = "1.71.3"))
    ))
    execute {
        // Resolve both targets before changing either: fail rather than partially patch.
        val productMethod = ProductPremiumFingerprint.method
        val databaseMethod = DatabasePremiumFingerprint.method
        for (method in listOf(productMethod, databaseMethod)) {
            method.addInstructions(0, "const/4 v0, 0x1\nreturn v0")
        }
    }
}
