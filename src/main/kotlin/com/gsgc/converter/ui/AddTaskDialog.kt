package com.gsgc.converter.ui

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Folder
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.gsgc.converter.data.FormatMapping
import java.awt.FileDialog
import java.io.File

@Composable
fun AddTaskDialog(viewModel: AppViewModel) {
    var sourceFile by remember { mutableStateOf(viewModel.pendingSourceFile.value) }
    var targetFormat by remember { mutableStateOf<String?>(null) }
    var saveSameAsSource by remember { mutableStateOf(true) }
    var customSaveDir by remember { mutableStateOf<String?>(null) }
    var errorMessage by remember { mutableStateOf<String?>(null) }

    val targetFormats = remember(sourceFile) {
        sourceFile?.let { FormatMapping.getTargetFormats(File(it).extension) } ?: emptyMap()
    }

    Dialog(
        onDismissRequest = { viewModel.closeAddTaskDialog() },
        properties = DialogProperties(
            dismissOnBackPress = true,
            dismissOnClickOutside = false
        )
    ) {
        // 遮罩 + 对话框
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.Black.copy(alpha = 0.32f)),
            contentAlignment = Alignment.Center
        ) {
            AnimatedVisibility(
                visible = true,
                enter = fadeIn(),
                exit = fadeOut()
            ) {
                Surface(
                    modifier = Modifier.width(480.dp).heightIn(max = 600.dp),
                    shape = RoundedCornerShape(12.dp),
                    color = MaterialTheme.colorScheme.surface,
                    shadowElevation = 8.dp
                ) {
                    Column(
                        modifier = Modifier
                            .padding(24.dp)
                            .verticalScroll(rememberScrollState()),
                        verticalArrangement = Arrangement.spacedBy(16.dp)
                    ) {
                        Text("新建转换任务", style = MaterialTheme.typography.titleLarge)

                        // 源文件选择
                        OutlinedButton(
                            onClick = {
                                val file = chooseFile()
                                if (file != null) {
                                    sourceFile = file.absolutePath
                                    targetFormat = null
                                }
                            },
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Icon(Icons.Filled.Folder, contentDescription = null)
                            Spacer(Modifier.width(8.dp))
                            Text("选择文件")
                        }
                        sourceFile?.let {
                            Text(it, style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }

                        // 目标格式
                        Text("目标格式", style = MaterialTheme.typography.bodyMedium)
                        var expanded by remember { mutableStateOf(false) }
                        Box {
                            OutlinedButton(
                                onClick = { expanded = true },
                                modifier = Modifier.fillMaxWidth(),
                                enabled = sourceFile != null
                            ) {
                                Text(targetFormat ?: if (sourceFile == null) "请先选择源文件" else "请选择目标格式")
                            }
                            DropdownMenu(
                                expanded = expanded,
                                onDismissRequest = { expanded = false }
                            ) {
                                targetFormats.forEach { (category, formats) ->
                                    DropdownMenuItem(
                                        text = { Text("--- $category ---", color = MaterialTheme.colorScheme.onSurfaceVariant) },
                                        onClick = {},
                                        enabled = false
                                    )
                                    formats.forEach { fmt ->
                                        DropdownMenuItem(
                                            text = { Text(fmt.uppercase()) },
                                            onClick = {
                                                targetFormat = fmt
                                                expanded = false
                                            }
                                        )
                                    }
                                }
                            }
                        }

                        // 保存位置
                        Text("保存位置", style = MaterialTheme.typography.bodyMedium)
                        Column {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                RadioButton(
                                    selected = saveSameAsSource,
                                    onClick = { saveSameAsSource = true }
                                )
                                Text("与源文件相同")
                            }
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                RadioButton(
                                    selected = !saveSameAsSource,
                                    onClick = { saveSameAsSource = false }
                                )
                                Text("自定义位置")
                            }
                            if (!saveSameAsSource) {
                                Row(
                                    modifier = Modifier.padding(start = 24.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    OutlinedButton(onClick = { customSaveDir = chooseDirectory() }) {
                                        Text("浏览...")
                                    }
                                    Spacer(Modifier.width(8.dp))
                                    Text(
                                        customSaveDir ?: "请选择保存位置",
                                        style = MaterialTheme.typography.bodySmall
                                    )
                                }
                            }
                        }

                        // 错误提示
                        errorMessage?.let {
                            Text(it, color = MaterialTheme.colorScheme.error)
                        }

                        Spacer(Modifier.weight(1f))

                        // 底部按钮
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.End
                        ) {
                            TextButton(onClick = { viewModel.closeAddTaskDialog() }) {
                                Text("取消")
                            }
                            Spacer(Modifier.width(8.dp))
                            Button(
                                onClick = {
                                    val src = sourceFile
                                    val fmt = targetFormat
                                    if (src == null) {
                                        errorMessage = "请选择源文件"
                                        return@Button
                                    }
                                    if (fmt == null) {
                                        errorMessage = "请选择目标格式"
                                        return@Button
                                    }
                                    val saveDir = if (saveSameAsSource) {
                                        File(src).parent
                                    } else {
                                        customSaveDir
                                    }
                                    if (saveDir == null) {
                                        errorMessage = "请选择保存位置"
                                        return@Button
                                    }
                                    val sourceName = File(src).nameWithoutExtension
                                    val targetFile = File(saveDir, "$sourceName.$fmt").absolutePath
                                    viewModel.addTask(src, targetFile)
                                    viewModel.closeAddTaskDialog()
                                },
                                enabled = sourceFile != null && targetFormat != null
                            ) {
                                Text("开始转换")
                            }
                        }
                    }
                }
            }
        }
    }
}

/**
 * 弹出文件选择对话框（AWT FileDialog）
 */
private fun chooseFile(): File? {
    val dialog = FileDialog(java.awt.Frame(), "选择文件", FileDialog.LOAD)
    dialog.isVisible = true
    val dir = dialog.directory ?: return null
    val file = dialog.file ?: return null
    return File(dir, file)
}

/**
 * 弹出目录选择对话框
 */
private fun chooseDirectory(): String? {
    val chooser = javax.swing.JFileChooser().apply {
        fileSelectionMode = javax.swing.JFileChooser.DIRECTORIES_ONLY
    }
    return if (chooser.showOpenDialog(null) == javax.swing.JFileChooser.APPROVE_OPTION) {
        chooser.selectedFile.absolutePath
    } else null
}
