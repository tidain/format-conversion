package com.gsgc.converter.data

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.io.File

/**
 * 主题模式
 */
enum class ThemeMode {
    LIGHT, DARK, SYSTEM
}

/**
 * 应用配置数据类
 */
@Serializable
data class AppConfig(
    val themeMode: String = ThemeMode.SYSTEM.name,
    val autostart: Boolean = false
)

/**
 * 配置管理器：读取/写入 ~/.gsgc/config.json
 */
object ConfigManager {

    private val configDir = File(System.getProperty("user.home"), ".gsgc")
    private val configFile = File(configDir, "config.json")

    private val json = Json { prettyPrint = true; encodeDefaults = true }

    private val _config = MutableStateFlow(loadOrCreate())
    val config: StateFlow<AppConfig> = _config.asStateFlow()

    private fun loadOrCreate(): AppConfig {
        return try {
            if (!configDir.exists()) configDir.mkdirs()
            if (!configFile.exists()) {
                val default = AppConfig()
                save(default)
                default
            } else {
                json.decodeFromString<AppConfig>(configFile.readText(Charsets.UTF_8))
            }
        } catch (e: Exception) {
            AppConfig()
        }
    }

    private fun save(config: AppConfig) {
        try {
            if (!configDir.exists()) configDir.mkdirs()
            configFile.writeText(json.encodeToString(config), Charsets.UTF_8)
        } catch (e: Exception) {
            System.err.println("保存配置失败: ${e.message}")
        }
    }

    private fun update(transform: (AppConfig) -> AppConfig) {
        val newConfig = transform(_config.value)
        _config.value = newConfig
        save(newConfig)
    }

    var themeMode: ThemeMode
        get() = try {
            ThemeMode.valueOf(_config.value.themeMode)
        } catch (e: Exception) {
            ThemeMode.SYSTEM
        }
        set(value) = update { it.copy(themeMode = value.name) }

    var autostart: Boolean
        get() = _config.value.autostart
        set(value) = update { it.copy(autostart = value) }
}
