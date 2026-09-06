package com.gsgc.converter.ui

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.gsgc.converter.data.ThemeMode
import com.gsgc.converter.domain.ConvertTask
import com.gsgc.converter.domain.TaskState
import com.gsgc.converter.util.FileOpener
import com.gsgc.converter.util.ThemeHelper

@Composable
fun TaskListScreen(viewModel: AppViewModel) {
    val tasks by viewModel.tasks.collectAsState()
    val themeMode by ThemeHelper.themeMode.collectAsState()
    val isDark = themeMode == ThemeMode.DARK ||
            (themeMode == ThemeMode.SYSTEM && ThemeHelper.isDark())

    Column(modifier = Modifier.fillMaxSize().padding(horizontal = 36.dp, vertical = 18.dp)) {
        // 标题与新建任务按钮
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                "任务列表",
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.weight(1f)
            )
            Button(
                onClick = { viewModel.openAddTaskDialog() },
                shape = RoundedCornerShape(6.dp),
                contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp)
            ) {
                Icon(Icons.Filled.Add, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(6.dp))
                Text("新建任务", fontSize = 14.sp)
            }
        }

        Spacer(Modifier.height(8.dp))
        Text(
            "在这里管理您的转换任务。您可以添加、取消和查看任务的进度。",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )

        Spacer(Modifier.height(16.dp))
        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f))
        Spacer(Modifier.height(16.dp))

        // 任务卡片列表
        if (tasks.isEmpty()) {
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    "暂无任务，点击\"新建任务\"开始",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    fontSize = 14.sp
                )
            }
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(tasks, key = { it.sourceFile + it.targetFile }) { task ->
                    TaskCard(task, isDark)
                }
            }
        }
    }
}

@Composable
fun TaskCard(task: ConvertTask, isDark: Boolean) {
    val state by task.state.collectAsState()
    val cardBg = if (isDark) Color(0xFF232323) else Color(0xFFF5F5F5)

    Surface(
        modifier = Modifier.fillMaxWidth(),
        color = cardBg,
        shape = RoundedCornerShape(8.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            // 文件信息行
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    Icons.Filled.Description,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.size(18.dp)
                )
                Spacer(Modifier.width(8.dp))
                Text(
                    task.sourceFile.substringAfterLast('\\'),
                    style = MaterialTheme.typography.bodyLarge,
                    modifier = Modifier.weight(1f, fill = false)
                )
                Spacer(Modifier.width(6.dp))
                Icon(
                    Icons.Filled.ArrowForward,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.size(16.dp)
                )
                Spacer(Modifier.width(6.dp))
                Text(
                    task.targetFile.substringAfterLast('\\'),
                    style = MaterialTheme.typography.bodyLarge,
                    modifier = Modifier.weight(1f, fill = false)
                )
                Spacer(Modifier.width(12.dp))

                // 状态按钮
                when (val s = state) {
                    is TaskState.Running -> {
                        OutlinedButton(
                            onClick = { task.cancel() },
                            shape = RoundedCornerShape(6.dp),
                            contentPadding = PaddingValues(horizontal = 12.dp, vertical = 6.dp),
                            colors = ButtonDefaults.outlinedButtonColors(
                                contentColor = MaterialTheme.colorScheme.error
                            )
                        ) {
                            Icon(Icons.Filled.Cancel, contentDescription = null, modifier = Modifier.size(16.dp))
                            Spacer(Modifier.width(4.dp))
                            Text("取消", fontSize = 13.sp)
                        }
                    }
                    is TaskState.Completed -> {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                Icons.Filled.CheckCircle,
                                contentDescription = null,
                                tint = Color(0xFF00A040),
                                modifier = Modifier.size(18.dp)
                            )
                            Spacer(Modifier.width(4.dp))
                            Text("完成", color = Color(0xFF00A040), fontSize = 13.sp)
                        }
                    }
                    is TaskState.Failed -> {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                Icons.Filled.Error,
                                contentDescription = null,
                                tint = MaterialTheme.colorScheme.error,
                                modifier = Modifier.size(18.dp)
                            )
                            Spacer(Modifier.width(4.dp))
                            Text(
                                s.message.take(30),
                                color = MaterialTheme.colorScheme.error,
                                fontSize = 13.sp
                            )
                        }
                    }
                    is TaskState.Cancelled -> {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                Icons.Filled.Cancel,
                                contentDescription = null,
                                tint = MaterialTheme.colorScheme.onSurfaceVariant,
                                modifier = Modifier.size(18.dp)
                            )
                            Spacer(Modifier.width(4.dp))
                            Text("已取消", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 13.sp)
                        }
                    }
                    else -> {}
                }
            }

            Spacer(Modifier.height(10.dp))

            // 进度条
            val progress = when (val s = state) {
                is TaskState.Running -> s.progress / 100f
                TaskState.Completed -> 1f
                else -> 0f
            }
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(6.dp)
                    .clip(RoundedCornerShape(3.dp))
                    .background(
                        if (isDark) Color(0xFF3A3A3A) else Color(0xFFE0E0E0)
                    )
            ) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth(progress)
                        .fillMaxHeight()
                        .background(MaterialTheme.colorScheme.primary)
                )
            }

            // 完成后显示的操作按钮
            AnimatedVisibility(
                visible = state is TaskState.Completed,
                enter = fadeIn(),
                exit = fadeOut()
            ) {
                Column {
                    Spacer(Modifier.height(10.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.End
                    ) {
                        TextButton(
                            onClick = { FileOpener.openFile(task.targetFile) },
                            shape = RoundedCornerShape(6.dp),
                            contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp)
                        ) {
                            Icon(Icons.Filled.Description, contentDescription = null, modifier = Modifier.size(16.dp))
                            Spacer(Modifier.width(4.dp))
                            Text("打开文件", fontSize = 13.sp)
                        }
                        Spacer(Modifier.width(8.dp))
                        TextButton(
                            onClick = { FileOpener.openFileLocation(task.targetFile) },
                            shape = RoundedCornerShape(6.dp),
                            contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp)
                        ) {
                            Icon(Icons.Filled.Folder, contentDescription = null, modifier = Modifier.size(16.dp))
                            Spacer(Modifier.width(4.dp))
                            Text("打开所在位置", fontSize = 13.sp)
                        }
                    }
                }
            }

            // 失败时显示重试按钮
            AnimatedVisibility(
                visible = state is TaskState.Failed,
                enter = fadeIn(),
                exit = fadeOut()
            ) {
                Column {
                    Spacer(Modifier.height(10.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.End
                    ) {
                        Text(
                            (state as TaskState.Failed).message,
                            color = MaterialTheme.colorScheme.error,
                            fontSize = 12.sp,
                            modifier = Modifier.weight(1f)
                        )
                    }
                }
            }
        }
    }
}
