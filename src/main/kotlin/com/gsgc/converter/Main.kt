package com.gsgc.converter

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

    Window(
        onCloseRequest = ::exitApplication,
        title = "格式转换工具",
        state = rememberWindowState(
            width = 1050.dp,
            height = 750.dp,
            position = WindowPosition.PlatformDefault
        ),
        undecorated = true,
        icon = painterResource("logo.png")
    ) {
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
                        androidx.compose.foundation.layout.Column(
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
    }
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
