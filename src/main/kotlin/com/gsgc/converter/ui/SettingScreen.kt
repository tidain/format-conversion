package com.gsgc.converter.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.gsgc.converter.data.ConfigManager
import com.gsgc.converter.data.ThemeMode
import com.gsgc.converter.domain.FFmpegService
import com.gsgc.converter.util.AutostartManager
import com.gsgc.converter.util.ThemeHelper
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingScreen(viewModel: AppViewModel) {
    val config by ConfigManager.config.collectAsState()
    val scope = rememberCoroutineScope()
    var ffmpegInstallerVisible by remember { mutableStateOf(false) }
    var ffmpegStatus by remember { mutableStateOf("检测中...") }
    var ffmpegInstalled by remember { mutableStateOf(false) }

    // 异步检测 FFmpeg 状态，避免阻塞组合阶段
    LaunchedEffect(Unit) {
        val installed = FFmpegService.isAvailable()
        ffmpegInstalled = installed
        ffmpegStatus = if (installed) "已安装" else "未安装"
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp)
            .verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Text("设置", style = MaterialTheme.typography.headlineSmall)

        // 主题设置
        Text("主题设置", style = MaterialTheme.typography.titleMedium)
        ElevatedCard(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text("主题模式", style = MaterialTheme.typography.bodyLarge)
                Spacer(Modifier.height(8.dp))
                val options = listOf("浅色" to ThemeMode.LIGHT, "深色" to ThemeMode.DARK, "跟随系统" to ThemeMode.SYSTEM)
                var expanded by remember { mutableStateOf(false) }
                val current = try {
                    ThemeMode.valueOf(config.themeMode)
                } catch (e: Exception) {
                    ThemeMode.SYSTEM
                }
                Box {
                    OutlinedButton(onClick = { expanded = true }) {
                        Text(options.first { it.second == current }.first)
                    }
                    DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                        options.forEach { (label, mode) ->
                            DropdownMenuItem(
                                text = { Text(label) },
                                onClick = {
                                    ThemeHelper.setThemeMode(mode)
                                    expanded = false
                                }
                            )
                        }
                    }
                }
            }
        }

        // 基本设置
        Text("基本设置", style = MaterialTheme.typography.titleMedium)
        ElevatedCard(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text("开机自启动", style = MaterialTheme.typography.bodyLarge)
                        Text(
                            "开启后应用将在系统启动时自动运行",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                    Switch(
                        checked = config.autostart,
                        onCheckedChange = { enabled ->
                            scope.launch {
                                withContext(Dispatchers.IO) {
                                    if (enabled) AutostartManager.enable()
                                    else AutostartManager.disable()
                                }
                                ConfigManager.autostart = enabled
                                viewModel.showSnackbar(if (enabled) "已开启开机自启动" else "已关闭开机自启动")
                            }
                        }
                    )
                }
            }
        }

        // FFmpeg
        Text("FFmpeg", style = MaterialTheme.typography.titleMedium)
        ElevatedCard(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("状态: $ffmpegStatus", style = MaterialTheme.typography.bodyLarge)
                Row {
                    Button(onClick = {
                        scope.launch {
                            val installed = FFmpegService.isAvailable()
                            ffmpegInstalled = installed
                            ffmpegStatus = if (installed) "已安装" else "未安装"
                            viewModel.showSnackbar(if (installed) "FFmpeg 已安装" else "FFmpeg 未安装")
                        }
                    }) {
                        Text("检测")
                    }
                    // 未安装时显示安装按钮
                    if (!ffmpegInstalled) {
                        Spacer(Modifier.width(8.dp))
                        OutlinedButton(onClick = { ffmpegInstallerVisible = true }) {
                            Text("安装")
                        }
                    }
                    // 已安装时显示卸载按钮
                    if (ffmpegInstalled) {
                        Spacer(Modifier.width(8.dp))
                        OutlinedButton(onClick = {
                            scope.launch {
                                FFmpegService.uninstall()
                                ffmpegInstalled = false
                                ffmpegStatus = "未安装"
                                viewModel.showSnackbar("FFmpeg 已卸载")
                            }
                        }) {
                            Text("卸载")
                        }
                    }
                }
            }
        }
    }

    if (ffmpegInstallerVisible) {
        FFmpegInstallerDialog(
            onDismiss = {
                ffmpegInstallerVisible = false
                scope.launch {
                    val installed = FFmpegService.isAvailable()
                    ffmpegInstalled = installed
                    ffmpegStatus = if (installed) "已安装" else "未安装"
                    viewModel.showSnackbar(if (installed) "FFmpeg 安装成功" else "FFmpeg 安装失败")
                }
            }
        )
    }
}
