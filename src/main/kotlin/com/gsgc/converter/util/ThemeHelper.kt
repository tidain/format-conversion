package com.gsgc.converter.util

import androidx.compose.material3.ColorScheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.ExperimentalTextApi
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.platform.asComposeFontFamily
import androidx.compose.ui.unit.sp
import com.gsgc.converter.data.ConfigManager
import com.gsgc.converter.data.ThemeMode
import com.sun.jna.platform.win32.Advapi32Util
import com.sun.jna.platform.win32.WinReg
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * 主题管理：读取 Windows 强调色与系统主题，提供 Compose ColorScheme
 */
@OptIn(ExperimentalTextApi::class)
object ThemeHelper {

    private const val DEFAULT_ACCENT = "#0078d4"

    /**
     * 解析 #rrggbb 十六进制颜色字符串为 Compose Color
     */
    private fun parseHexColor(hex: String): Color {
        val clean = hex.removePrefix("#")
        val r = clean.substring(0, 2).toInt(16)
        val g = clean.substring(2, 4).toInt(16)
        val b = clean.substring(4, 6).toInt(16)
        return Color(r, g, b)
    }

    /**
     * 计算颜色相对亮度（0=黑, 1=白）
     */
    private fun luminance(color: Color): Float {
        fun ch(c: Float) = if (c <= 0.03928f) c / 12.92f else Math.pow(((c + 0.055) / 1.055).toDouble(), 2.4).toFloat()
        return 0.2126f * ch(color.red) + 0.7152f * ch(color.green) + 0.0722f * ch(color.blue)
    }

    /**
     * 两种颜色按比例混合
     */
    private fun blend(a: Color, b: Color, ratio: Float): Color {
        return Color(
            red = a.red * (1 - ratio) + b.red * ratio,
            green = a.green * (1 - ratio) + b.green * ratio,
            blue = a.blue * (1 - ratio) + b.blue * ratio
        )
    }

    /**
     * 获取 Windows 系统强调色（ABGR -> RGB），返回 #rrggbb
     */
    fun getWindowsAccentColor(): String {
        return try {
            val colorDword = Advapi32Util.registryGetIntValue(
                WinReg.HKEY_CURRENT_USER,
                "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Accent",
                "AccentColorMenu"
            )
            // Windows stores as ABGR
            val b = (colorDword shr 16) and 0xFF
            val g = (colorDword shr 8) and 0xFF
            val r = colorDword and 0xFF
            String.format("#%02x%02x%02x", r, g, b)
        } catch (e: Exception) {
            DEFAULT_ACCENT
        }
    }

    /**
     * 获取系统主题：light / dark
     */
    fun getSystemTheme(): String {
        return try {
            val isLight = Advapi32Util.registryGetIntValue(
                WinReg.HKEY_CURRENT_USER,
                "Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize",
                "AppsUseLightTheme"
            )
            if (isLight == 0) "dark" else "light"
        } catch (e: Exception) {
            "light"
        }
    }

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    private val _themeMode = MutableStateFlow(ConfigManager.themeMode)
    val themeMode: StateFlow<ThemeMode> = _themeMode.asStateFlow()

    init {
        scope.launch {
            ConfigManager.config.collect {
                _themeMode.value = try {
                    ThemeMode.valueOf(it.themeMode)
                } catch (e: Exception) {
                    ThemeMode.SYSTEM
                }
            }
        }
    }

    /**
     * 设置主题模式并持久化
     */
    fun setThemeMode(mode: ThemeMode) {
        ConfigManager.themeMode = mode
    }

    /**
     * 基于强调色构建完整浅色配色
     */
    private fun lightScheme(accent: Color): ColorScheme {
        val onPrimary = if (luminance(accent) > 0.5f) Color.Black else Color.White
        val primaryContainer = blend(accent, Color.White, 0.75f)
        val onPrimaryContainer = blend(accent, Color.Black, 0.6f)
        val secondary = blend(accent, Color(0xFF6B6B6B), 0.5f)
        val surfaceVariant = blend(accent, Color(0xFFF2F2F2), 0.85f)
        return lightColorScheme(
            primary = accent,
            onPrimary = onPrimary,
            primaryContainer = primaryContainer,
            onPrimaryContainer = onPrimaryContainer,
            secondary = secondary,
            onSecondary = if (luminance(secondary) > 0.5f) Color.Black else Color.White,
            surface = Color(0xFFFBFBFB),
            onSurface = Color(0xFF1B1B1F),
            surfaceVariant = surfaceVariant,
            onSurfaceVariant = Color(0xFF44474F),
            background = Color(0xFFFBFBFB),
            onBackground = Color(0xFF1B1B1F),
            outline = Color(0xFF74777F),
            outlineVariant = Color(0xFFC4C6D0)
        )
    }

    /**
     * 基于强调色构建完整深色配色
     */
    private fun darkScheme(accent: Color): ColorScheme {
        // 深色模式下提亮强调色以保证可见性
        val primary = blend(accent, Color.White, 0.35f)
        val onPrimary = if (luminance(primary) > 0.5f) Color.Black else Color.White
        val primaryContainer = blend(accent, Color.Black, 0.5f)
        val onPrimaryContainer = blend(accent, Color.White, 0.7f)
        val secondary = blend(accent, Color(0xFFB0B0B0), 0.5f)
        val surfaceVariant = blend(accent, Color(0xFF2B2930), 0.8f)
        return darkColorScheme(
            primary = primary,
            onPrimary = onPrimary,
            primaryContainer = primaryContainer,
            onPrimaryContainer = onPrimaryContainer,
            secondary = secondary,
            onSecondary = if (luminance(secondary) > 0.5f) Color.Black else Color.White,
            surface = Color(0xFF1B1B1F),
            onSurface = Color(0xFFE3E2E6),
            surfaceVariant = surfaceVariant,
            onSurfaceVariant = Color(0xFFC4C6D0),
            background = Color(0xFF1B1B1F),
            onBackground = Color(0xFFE3E2E6),
            outline = Color(0xFF8E9099),
            outlineVariant = Color(0xFF44474F)
        )
    }

    /**
     * 根据当前模式构建 Compose ColorScheme
     */
    @Composable
    fun colorScheme(): ColorScheme {
        val mode by themeMode.collectAsState()
        val accent = parseHexColor(getWindowsAccentColor())
        return when (mode) {
            ThemeMode.DARK -> darkScheme(accent)
            ThemeMode.LIGHT -> lightScheme(accent)
            ThemeMode.SYSTEM -> {
                if (getSystemTheme() == "dark") darkScheme(accent) else lightScheme(accent)
            }
        }
    }

    /**
     * 当前是否深色模式（供非 Composable 代码使用）
     */
    fun isDark(): Boolean {
        return when (ConfigManager.themeMode) {
            ThemeMode.DARK -> true
            ThemeMode.LIGHT -> false
            ThemeMode.SYSTEM -> getSystemTheme() == "dark"
        }
    }

    // —— 字体：思源黑体（Source Han Sans SC）——
    // 通过 asComposeFontFamily 直接将 OTF 字体注入 Skia 渲染管线，
    // 保证矢量字形在任意 DPI 缩放下清晰锐利；默认 Regular 字重，文字不过细。
    private fun loadFontFamily(path: String): FontFamily {
        val stream = Thread.currentThread().contextClassLoader.getResourceAsStream(path)
            ?: return FontFamily.Default
        return try {
            java.awt.Font.createFont(java.awt.Font.TRUETYPE_FONT, stream).asComposeFontFamily()
        } catch (_: Exception) {
            FontFamily.Default
        }
    }

    private val regularFamily by lazy { loadFontFamily("fonts/SourceHanSansSC-Regular.otf") }
    private val mediumFamily by lazy { loadFontFamily("fonts/SourceHanSansSC-Medium.otf") }
    private val boldFamily by lazy { loadFontFamily("fonts/SourceHanSansSC-Bold.otf") }

    val SourceHanSans: FontFamily get() = regularFamily

    /**
     * 应用排版：统一使用思源黑体，正文 Regular，标题 Medium/Bold，避免文字过细。
     * 每个字重直接绑定对应字体文件，确保 Skia 渲染时使用正确的矢量字形。
     */
    val typography: Typography by lazy {
        Typography(
            displayLarge = TextStyle(fontFamily = boldFamily, fontWeight = FontWeight.Bold, fontSize = 57.sp),
            displayMedium = TextStyle(fontFamily = boldFamily, fontWeight = FontWeight.Bold, fontSize = 45.sp),
            displaySmall = TextStyle(fontFamily = boldFamily, fontWeight = FontWeight.Bold, fontSize = 36.sp),
            headlineLarge = TextStyle(fontFamily = boldFamily, fontWeight = FontWeight.Bold, fontSize = 32.sp),
            headlineMedium = TextStyle(fontFamily = boldFamily, fontWeight = FontWeight.Bold, fontSize = 28.sp),
            headlineSmall = TextStyle(fontFamily = boldFamily, fontWeight = FontWeight.Bold, fontSize = 24.sp),
            titleLarge = TextStyle(fontFamily = mediumFamily, fontWeight = FontWeight.Medium, fontSize = 22.sp),
            titleMedium = TextStyle(fontFamily = mediumFamily, fontWeight = FontWeight.Medium, fontSize = 16.sp),
            titleSmall = TextStyle(fontFamily = mediumFamily, fontWeight = FontWeight.Medium, fontSize = 14.sp),
            bodyLarge = TextStyle(fontFamily = regularFamily, fontWeight = FontWeight.Normal, fontSize = 16.sp),
            bodyMedium = TextStyle(fontFamily = regularFamily, fontWeight = FontWeight.Normal, fontSize = 14.sp),
            bodySmall = TextStyle(fontFamily = regularFamily, fontWeight = FontWeight.Normal, fontSize = 12.sp),
            labelLarge = TextStyle(fontFamily = mediumFamily, fontWeight = FontWeight.Medium, fontSize = 14.sp),
            labelMedium = TextStyle(fontFamily = mediumFamily, fontWeight = FontWeight.Medium, fontSize = 12.sp),
            labelSmall = TextStyle(fontFamily = regularFamily, fontWeight = FontWeight.Normal, fontSize = 11.sp)
        )
    }
}
