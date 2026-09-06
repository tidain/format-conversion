package com.gsgc.converter.ui

import androidx.compose.animation.AnimatedContent
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.hoverable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsHoveredAsState
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Fullscreen
import androidx.compose.material.icons.filled.FullscreenExit
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Remove
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.awt.ComposeWindow
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.gsgc.converter.domain.ConvertTask
import com.gsgc.converter.util.ThemeHelper
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.awt.Frame
import java.io.File

/**
 * 导航项
 */
enum class NavItem(val label: String, val icon: ImageVector) {
    TASKS("任务列表", Icons.Filled.Home),
    SETTINGS("设置", Icons.Filled.Settings)
}

/**
 * 应用全局状态
 */
class AppViewModel {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    private val _tasks = MutableStateFlow<List<ConvertTask>>(emptyList())
    val tasks: StateFlow<List<ConvertTask>> = _tasks.asStateFlow()

    private val _showAddTaskDialog = MutableStateFlow(false)
    val showAddTaskDialog: StateFlow<Boolean> = _showAddTaskDialog.asStateFlow()

    private val _pendingSourceFile = MutableStateFlow<String?>(null)
    val pendingSourceFile: StateFlow<String?> = _pendingSourceFile.asStateFlow()

    // 浮窗提示
    val snackbarHostState = SnackbarHostState()

    fun showSnackbar(message: String) {
        scope.launch { snackbarHostState.showSnackbar(message) }
    }

    fun addTask(source: String, target: String) {
        val task = ConvertTask(source, target)
        _tasks.value = _tasks.value + task
        task.start()
        showSnackbar("任务已添加：${File(source).name}")
    }

    fun openAddTaskDialog(preFillSource: String? = null) {
        _pendingSourceFile.value = preFillSource
        _showAddTaskDialog.value = true
    }

    fun closeAddTaskDialog() {
        _showAddTaskDialog.value = false
        _pendingSourceFile.value = null
    }
}

@Composable
fun MainWindow(viewModel: AppViewModel, window: ComposeWindow) {
    var selectedItem by remember { mutableStateOf(NavItem.TASKS) }
    var showAbout by remember { mutableStateOf(false) }

    Box(modifier = Modifier.fillMaxSize()) {
        Surface(modifier = Modifier.fillMaxSize()) {
            Column(modifier = Modifier.fillMaxSize()) {
                // 自定义标题栏（无边框模式）
                WindowTitleBar(window, onInfoClick = { showAbout = true })

                // 主体内容：左侧导航 + 右侧内容
                Row(modifier = Modifier.fillMaxSize().weight(1f)) {
                    // 左侧导航栏
                    NavigationRail(
                        modifier = Modifier.width(80.dp),
                        containerColor = MaterialTheme.colorScheme.surface
                    ) {
                        Spacer(Modifier.height(16.dp))
                        NavItem.entries.forEach { item ->
                            NavigationRailItem(
                                icon = { Icon(item.icon, contentDescription = item.label) },
                                label = { Text(item.label, style = MaterialTheme.typography.labelSmall) },
                                selected = selectedItem == item,
                                onClick = { selectedItem = item }
                            )
                        }
                    }

                    // 内容区
                    AnimatedContent(
                        targetState = selectedItem,
                        modifier = Modifier.fillMaxSize(),
                        contentAlignment = Alignment.TopStart
                    ) { target ->
                        when (target) {
                            NavItem.TASKS -> TaskListScreen(viewModel)
                            NavItem.SETTINGS -> SettingScreen(viewModel)
                        }
                    }
                }
            }
        }

        // 浮窗提示
        SnackbarHost(
            hostState = viewModel.snackbarHostState,
            modifier = Modifier.align(Alignment.BottomCenter).padding(bottom = 24.dp)
        )
    }

    // 新建任务对话框
    val showDialog by viewModel.showAddTaskDialog.collectAsState()
    if (showDialog) {
        AddTaskDialog(viewModel)
    }

    // 关于对话框
    if (showAbout) {
        AboutDialog(onDismiss = { showAbout = false })
    }
}

/**
 * 自定义无边框标题栏：图标 + 标题 + 最小化/最大化/关闭，支持拖拽移动、双击最大化
 */
@Composable
private fun WindowTitleBar(window: ComposeWindow, onInfoClick: () -> Unit) {
    var isMaximized by remember {
        mutableStateOf(window.extendedState and Frame.MAXIMIZED_BOTH != 0)
    }

    // 同步外部最大化状态变化
    LaunchedEffect(window) {
        window.addComponentListener(object : java.awt.event.ComponentAdapter() {
            override fun componentResized(e: java.awt.event.ComponentEvent) {
                isMaximized = window.extendedState and Frame.MAXIMIZED_BOTH != 0
            }
        })
        // 启用 AWT 窗口拖拽与双击最大化
        enableWindowDrag(window, titleBarHeightPx = 40, buttonCount = 4)
    }

    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .height(40.dp),
        color = MaterialTheme.colorScheme.surface,
        shadowElevation = 2.dp
    ) {
        Row(
            modifier = Modifier.fillMaxSize(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // 图标 + 标题区域（拖拽/双击通过 AWT 监听器处理，见下方 enableWindowDrag）
            Row(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxHeight()
                    .padding(start = 12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                androidx.compose.foundation.Image(
                    painter = painterResource("logo.png"),
                    contentDescription = null,
                    modifier = Modifier.size(22.dp)
                )
                Spacer(Modifier.width(8.dp))
                Text(
                    "格式转换工具",
                    style = MaterialTheme.typography.titleSmall,
                    color = MaterialTheme.colorScheme.onSurface
                )
            }

            // 窗口控制按钮
            WindowControlButton(
                icon = Icons.Filled.Info,
                contentDescription = "更多信息",
                onClick = onInfoClick
            )
            WindowControlButton(
                icon = Icons.Filled.Remove,
                contentDescription = "最小化",
                onClick = {
                    window.extendedState = window.extendedState or Frame.ICONIFIED
                }
            )
            WindowControlButton(
                icon = if (isMaximized) Icons.Filled.FullscreenExit else Icons.Filled.Fullscreen,
                contentDescription = if (isMaximized) "还原" else "最大化",
                onClick = { toggleMaximize(window, isMaximized) }
            )
            WindowControlButton(
                icon = Icons.Filled.Close,
                contentDescription = "关闭",
                onClick = { window.dispose() },
                hoverColor = Color(0xFFE81123)
            )
        }
    }
}

private fun toggleMaximize(window: ComposeWindow, isMaximized: Boolean) {
    window.extendedState = if (isMaximized) {
        window.extendedState and Frame.MAXIMIZED_BOTH.inv()
    } else {
        window.extendedState or Frame.MAXIMIZED_BOTH
    }
}

/**
 * 窗口控制按钮（最小化/最大化/关闭）
 */
@Composable
private fun WindowControlButton(
    icon: ImageVector,
    contentDescription: String,
    onClick: () -> Unit,
    hoverColor: Color = MaterialTheme.colorScheme.primary
) {
    val interactionSource = remember { MutableInteractionSource() }
    val hovered by interactionSource.collectIsHoveredAsState()
    Box(
        modifier = Modifier
            .size(46.dp, 40.dp)
            .background(if (hovered) hoverColor else Color.Transparent)
            .clickable(interactionSource = interactionSource, indication = null, onClick = onClick)
            .hoverable(interactionSource),
        contentAlignment = Alignment.Center
    ) {
        Icon(
            imageVector = icon,
            contentDescription = contentDescription,
            modifier = Modifier.size(18.dp),
            tint = if (hovered) Color.White else MaterialTheme.colorScheme.onSurface
        )
    }
}

/**
 * 通过 AWT 全局事件监听实现窗口拖拽与双击最大化。
 *
 * Compose 内容渲染在原生 Skia 重量级画布上，Swing 的 Glass Pane / MouseListener
 * 可能被原生画布覆盖而收不到事件。改用 Toolkit.addAWTEventListener 在事件分派
 * 到组件之前拦截鼠标事件，通过 SwingUtilities.getWindowAncestor 过滤本窗口，
 * 再用相对窗口的坐标(e.x, e.y)判断是否落在标题栏区域。
 *
 * 坐标：e.xOnScreen/yOnScreen 为物理屏幕像素，与 window.setLocation 直接对应，
 * 避免 Compose pointer 坐标（逻辑像素/DPI 缩放）与窗口物理坐标不匹配导致飞屏。
 */
fun enableWindowDrag(window: ComposeWindow, titleBarHeightPx: Int = 40, buttonCount: Int = 3) {
    var startScreenX = 0
    var startScreenY = 0
    var startWinX = 0
    var startWinY = 0
    var dragging = false
    var lastPressTime = 0L
    // 每个窗口控制按钮 46dp，按屏幕 DPI 换算为物理像素，确保按钮区不被拖拽拦截
    val dpiScale = window.graphicsConfiguration.defaultTransform.scaleX.toFloat()
    val buttonsWidth = (buttonCount * 46 * dpiScale).toInt()

    val listener = java.awt.event.AWTEventListener { event ->
        val e = event as? java.awt.event.MouseEvent ?: return@AWTEventListener
        val srcWin = javax.swing.SwingUtilities.getWindowAncestor(e.component)
        if (srcWin !== window) return@AWTEventListener

        when (event.id) {
            java.awt.event.MouseEvent.MOUSE_PRESSED -> {
                if (e.y > titleBarHeightPx) return@AWTEventListener
                if (e.x > window.width - buttonsWidth) return@AWTEventListener
                startScreenX = e.xOnScreen
                startScreenY = e.yOnScreen
                startWinX = window.x
                startWinY = window.y
                dragging = true
                val now = System.currentTimeMillis()
                if (now - lastPressTime < 300) {
                    // 双击标题栏 → 最大化/还原
                    val isMax = window.extendedState and java.awt.Frame.MAXIMIZED_BOTH != 0
                    window.extendedState = if (isMax) {
                        window.extendedState and java.awt.Frame.MAXIMIZED_BOTH.inv()
                    } else {
                        window.extendedState or java.awt.Frame.MAXIMIZED_BOTH
                    }
                    lastPressTime = 0
                } else {
                    lastPressTime = now
                }
            }
            java.awt.event.MouseEvent.MOUSE_DRAGGED -> {
                if (!dragging) return@AWTEventListener
                window.setLocation(
                    startWinX + (e.xOnScreen - startScreenX),
                    startWinY + (e.yOnScreen - startScreenY)
                )
            }
            java.awt.event.MouseEvent.MOUSE_RELEASED -> {
                dragging = false
            }
        }
    }

    java.awt.Toolkit.getDefaultToolkit().addAWTEventListener(
        listener,
        java.awt.AWTEvent.MOUSE_EVENT_MASK or java.awt.AWTEvent.MOUSE_MOTION_EVENT_MASK
    )
}

/**
 * 关于/更多信息对话框：显示软件版本、开源信息与字体声明
 */
@Composable
private fun AboutDialog(onDismiss: () -> Unit) {
    val scrollState = rememberScrollState()
    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(dismissOnClickOutside = true)
    ) {
        Surface(
            modifier = Modifier.width(520.dp).heightIn(max = 560.dp),
            shape = RoundedCornerShape(12.dp),
            color = MaterialTheme.colorScheme.surface
        ) {
            Column(modifier = Modifier.padding(24.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    androidx.compose.foundation.Image(
                        painter = painterResource("logo.png"),
                        contentDescription = null,
                        modifier = Modifier.size(40.dp)
                    )
                    Spacer(Modifier.width(12.dp))
                    Column {
                        Text("格式转换工具", style = MaterialTheme.typography.titleLarge)
                        Text("版本 2.0.0", style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }

                Spacer(Modifier.height(16.dp))
                HorizontalDivider()
                Spacer(Modifier.height(16.dp))

                Column(
                    modifier = Modifier.weight(1f).verticalScroll(scrollState),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Text("软件说明", style = MaterialTheme.typography.titleMedium)
                    Text(
                        "一款支持音视频、图片、文档、压缩包格式转换的桌面工具。\n" +
                            "使用 Kotlin + JetBrains Compose Multiplatform 开发。",
                        style = MaterialTheme.typography.bodyMedium
                    )

                    Text("开源许可", style = MaterialTheme.typography.titleMedium)
                    Text(
                        "本软件为开源软件，采用 MIT 许可证。\n" +
                            "源代码：https://github.com/tidain/format-conversion",
                        style = MaterialTheme.typography.bodyMedium
                    )

                    Text("使用的开源组件", style = MaterialTheme.typography.titleMedium)
                    Text(
                        "• JetBrains Compose Multiplatform (Apache 2.0)\n" +
                            "• Kotlin Coroutines (Apache 2.0)\n" +
                            "• Apache POI (Apache 2.0)\n" +
                            "• Apache PDFBox (Apache 2.0)\n" +
                            "• Apache Commons Compress (Apache 2.0)\n" +
                            "• FFmpeg (LGPL 2.1+)\n" +
                            "• JNA (Apache 2.0)",
                        style = MaterialTheme.typography.bodyMedium
                    )

                    Text("字体声明", style = MaterialTheme.typography.titleMedium)
                    Text(
                        "本软件内置「思源黑体 Source Han Sans SC」字体，\n" +
                            "由 Adobe 与 Google 联合开发，采用 SIL Open Font License 1.1 授权。\n" +
                            "© 2014-2025 Adobe (http://www.adobe.com/)",
                        style = MaterialTheme.typography.bodyMedium
                    )
                }

                Spacer(Modifier.height(16.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.End
                ) {
                    Button(onClick = onDismiss) {
                        Text("关闭")
                    }
                }
            }
        }
    }
}
