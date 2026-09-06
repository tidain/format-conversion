package com.gsgc.converter

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.awt.ComposeWindow
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Window
import androidx.compose.ui.window.WindowPosition
import androidx.compose.ui.window.application
import androidx.compose.ui.window.rememberWindowState
import com.gsgc.converter.domain.FFmpegService
import com.gsgc.converter.ui.AppViewModel
import com.gsgc.converter.ui.FFmpegInstallerDialog
import com.gsgc.converter.ui.MainWindow
import com.gsgc.converter.util.ThemeHelper
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.awt.datatransfer.DataFlavor
import java.awt.dnd.DnDConstants
import java.awt.dnd.DropTarget
import java.awt.dnd.DropTargetAdapter
import java.awt.dnd.DropTargetDropEvent
import java.io.File

fun main() {
    // 启用 Per-Monitor V2 DPI 感知，避免 Windows 缩放（如 125%）下文字模糊
    enablePerMonitorDpiAwareness()
    application {
        val viewModel = remember { AppViewModel() }
        val scope = remember { CoroutineScope(SupervisorJob() + Dispatchers.Default) }
        var showFFmpegDialog by remember { mutableStateOf(false) }
        var showFFmpegInstaller by remember { mutableStateOf(false) }

        // 启动画面与主窗口的引用，用于控制透明度动画
        var splashWindow by remember { mutableStateOf<ComposeWindow?>(null) }
        var mainWindow by remember { mutableStateOf<ComposeWindow?>(null) }
        var showSplash by remember { mutableStateOf(true) }
        var closing by remember { mutableStateOf(false) }

        // 启动画面窗口
        if (showSplash) {
            Window(
                onCloseRequest = {},
                undecorated = true,
                transparent = true,
                resizable = false,
                focusable = false,
                state = rememberWindowState(
                    width = 420.dp,
                    height = 280.dp,
                    position = WindowPosition.PlatformDefault
                ),
                alwaysOnTop = true
            ) {
                splashWindow = window
                SplashContent()
            }
        }

        // 主窗口
        Window(
            onCloseRequest = {
                if (closing) return@Window
                closing = true
                scope.launch {
                    mainWindow?.let { fadeOut(it) }
                    exitApplication()
                }
            },
            title = "格式转换工具",
            state = rememberWindowState(
                width = 1050.dp,
                height = 750.dp,
                position = WindowPosition.PlatformDefault
            ),
            undecorated = true,
            icon = painterResource("logo.png")
        ) {
            mainWindow = window
            // 主窗口初始透明
            LaunchedEffect(Unit) { window.opacity = 0f }

            // 启用文件拖拽
            enableFileDrop(window) { files ->
                files.firstOrNull()?.let { viewModel.openAddTaskDialog(it.absolutePath) }
            }

            MaterialTheme(colorScheme = ThemeHelper.colorScheme(), typography = ThemeHelper.typography) {
                Surface(modifier = Modifier.fillMaxSize()) {
                    MainWindow(viewModel, window)
                }

                // 启动时后台检测 FFmpeg
                LaunchedEffect(Unit) {
                    val available = FFmpegService.isAvailable()
                    if (!available) {
                        showFFmpegDialog = true
                    }
                }

                // FFmpeg 缺失提示
                if (showFFmpegDialog) {
                    androidx.compose.ui.window.Dialog(
                        onDismissRequest = { showFFmpegDialog = false },
                        properties = androidx.compose.ui.window.DialogProperties(dismissOnClickOutside = false)
                    ) {
                        Surface(shape = MaterialTheme.shapes.medium) {
                            Column(
                                modifier = Modifier.padding(24.dp),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                Text("检测到系统未安装 FFmpeg", style = MaterialTheme.typography.titleLarge)
                                Spacer(Modifier.height(12.dp))
                                Text("是否现在安装 FFmpeg？\n\n注意：安装过程可能需要几分钟，请耐心等待。")
                                Spacer(Modifier.height(16.dp))
                                Row {
                                    TextButton(onClick = { showFFmpegDialog = false }) {
                                        Text("取消")
                                    }
                                    Spacer(Modifier.width(8.dp))
                                    Button(onClick = {
                                        showFFmpegDialog = false
                                        showFFmpegInstaller = true
                                    }) {
                                        Text("安装")
                                    }
                                }
                            }
                        }
                    }
                }

                if (showFFmpegInstaller) {
                    FFmpegInstallerDialog(onDismiss = { showFFmpegInstaller = false })
                }
            }
        }

        // 启动动画：启动画面淡入 → 主窗口淡入同时启动画面淡出
        LaunchedEffect(Unit) {
            // 等两个窗口都准备好
            var waited = 0
            while ((splashWindow == null || mainWindow == null) && waited < 3000) {
                delay(50)
                waited += 50
            }
            val splash = splashWindow
            val main = mainWindow
            if (splash != null && main != null) {
                // 启动画面淡入
                fadeIn(splash)
                // 模拟初始化（字体、资源加载等）
                delay(600)
                // 交叉淡入淡出
                val fadeJob = scope.launch { fadeOut(splash) }
                fadeIn(main)
                fadeJob.join()
            }
            showSplash = false
        }
    }
}

/**
 * 启动画面内容：Logo + 加载提示
 */
@Composable
private fun SplashContent() {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(androidx.compose.ui.graphics.Color.Transparent),
        contentAlignment = Alignment.Center
    ) {
        Surface(
            modifier = Modifier.fillMaxSize(),
            shape = androidx.compose.foundation.shape.RoundedCornerShape(16.dp),
            color = MaterialTheme.colorScheme.surface,
            shadowElevation = 8.dp
        ) {
            Column(
                modifier = Modifier.fillMaxSize(),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center
            ) {
                androidx.compose.foundation.Image(
                    painter = painterResource("logo.png"),
                    contentDescription = null,
                    modifier = Modifier.size(96.dp)
                )
                Spacer(Modifier.height(20.dp))
                Text(
                    "格式转换工具",
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(Modifier.height(8.dp))
                Text(
                    "版本 2.0.0",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(Modifier.height(24.dp))
                androidx.compose.material3.CircularProgressIndicator(
                    modifier = Modifier.size(28.dp),
                    strokeWidth = 3.dp
                )
            }
        }
    }
}

/**
 * 窗口淡入动画（透明度 0 → 1）
 */
private suspend fun fadeIn(window: ComposeWindow) {
    try {
        var alpha = 0f
        while (alpha < 1f) {
            alpha = (alpha + 0.08f).coerceAtMost(1f)
            window.opacity = alpha
            delay(16)
        }
    } catch (_: Throwable) {}
}

/**
 * 窗口淡出动画（透明度 1 → 0）
 */
private suspend fun fadeOut(window: ComposeWindow) {
    try {
        var alpha = window.opacity
        while (alpha > 0f) {
            alpha = (alpha - 0.08f).coerceAtLeast(0f)
            window.opacity = alpha
            delay(16)
        }
    } catch (_: Throwable) {}
}

/**
 * 启用窗口文件拖放
 */
private fun enableFileDrop(window: ComposeWindow, onFilesDropped: (List<File>) -> Unit) {
    window.dropTarget = DropTarget(window, object : DropTargetAdapter() {
        override fun drop(event: DropTargetDropEvent) {
            try {
                event.acceptDrop(DnDConstants.ACTION_COPY)
                val transferable = event.transferable
                if (transferable.isDataFlavorSupported(DataFlavor.javaFileListFlavor)) {
                    @Suppress("UNCHECKED_CAST")
                    val files = transferable.getTransferData(DataFlavor.javaFileListFlavor) as List<File>
                    onFilesDropped(files)
                }
                event.dropComplete(true)
            } catch (e: Exception) {
                event.dropComplete(false)
            }
        }
    })
}

/**
 * 启用 Per-Monitor V2 DPI 感知。
 * 在 Windows 缩放下（如 125%、150%）让应用按物理像素渲染，
 * 避免系统对窗口进行位图拉伸导致文字模糊。
 */
private interface User32Ex : com.sun.jna.platform.win32.User32 {
    fun SetProcessDpiAwarenessContext(dpiContext: com.sun.jna.Pointer): Boolean
    fun SetProcessDPIAware(): Boolean

    companion object {
        val INSTANCE = com.sun.jna.Native.load("user32", User32Ex::class.java) as User32Ex
    }
}

private fun enablePerMonitorDpiAwareness() {
    if (System.getProperty("os.name")?.contains("Windows", ignoreCase = true) != true) return
    try {
        // DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
        User32Ex.INSTANCE.SetProcessDpiAwarenessContext(com.sun.jna.Pointer(-4))
    } catch (_: Throwable) {
        // 旧版 Windows 不支持时回退到系统 DPI 感知
        try {
            User32Ex.INSTANCE.SetProcessDPIAware()
        } catch (_: Throwable) {
        }
    }
}
