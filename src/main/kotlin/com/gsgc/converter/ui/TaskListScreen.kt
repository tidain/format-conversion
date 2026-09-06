package com.gsgc.converter.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Cancel
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.gsgc.converter.domain.ConvertTask
import com.gsgc.converter.domain.TaskState

@Composable
fun TaskListScreen(viewModel: AppViewModel) {
    val tasks by viewModel.tasks.collectAsState()

    Column(modifier = Modifier.fillMaxSize().padding(24.dp)) {
        // 标题与新建任务按钮
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                "任务列表",
                style = MaterialTheme.typography.headlineSmall,
                modifier = Modifier.weight(1f)
            )
            Button(
                onClick = { viewModel.openAddTaskDialog() },
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.primary
                )
            ) {
                Icon(Icons.Filled.Add, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text("新建任务")
            }
        }

        Spacer(Modifier.height(8.dp))
        Text(
            "在这里管理您的转换任务。您可以添加、取消和查看任务的进度。",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )

        Spacer(Modifier.height(16.dp))
        HorizontalDivider()
        Spacer(Modifier.height(16.dp))

        // 任务卡片列表
        if (tasks.isEmpty()) {
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    "暂无任务，点击\"新建任务\"开始",
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(tasks, key = { it.sourceFile + it.targetFile }) { task ->
                    TaskCard(task)
                }
            }
        }
    }
}

@Composable
fun TaskCard(task: ConvertTask) {
    val state by task.state.collectAsState()

    ElevatedCard(
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            // 文件信息行
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    task.sourceFile.substringAfterLast('\\'),
                    style = MaterialTheme.typography.bodyLarge,
                    modifier = Modifier.weight(1f, fill = false)
                )
                Text(" → ", color = MaterialTheme.colorScheme.onSurfaceVariant)
                Text(
                    task.targetFile.substringAfterLast('\\'),
                    style = MaterialTheme.typography.bodyLarge,
                    modifier = Modifier.weight(1f, fill = false)
                )
                Spacer(Modifier.width(8.dp))

                // 状态按钮
                when (val s = state) {
                    is TaskState.Running -> {
                        OutlinedButton(
                            onClick = { task.cancel() },
                            colors = ButtonDefaults.outlinedButtonColors(
                                contentColor = MaterialTheme.colorScheme.error
                            )
                        ) {
                            Icon(Icons.Filled.Cancel, contentDescription = null, modifier = Modifier.size(18.dp))
                            Spacer(Modifier.width(4.dp))
                            Text("取消")
                        }
                    }
                    is TaskState.Completed -> {
                        Icon(
                            Icons.Filled.CheckCircle,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.primary
                        )
                        Spacer(Modifier.width(4.dp))
                        Text("完成", color = MaterialTheme.colorScheme.primary)
                    }
                    is TaskState.Failed -> {
                        Text(s.message, color = MaterialTheme.colorScheme.error)
                    }
                    is TaskState.Cancelled -> {
                        Text("已取消", color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    else -> {}
                }
            }

            Spacer(Modifier.height(8.dp))

            // 进度条
            val progress = when (val s = state) {
                is TaskState.Running -> s.progress / 100f
                TaskState.Completed -> 1f
                else -> 0f
            }
            LinearProgressIndicator(
                progress = { progress },
                modifier = Modifier.fillMaxWidth().height(8.dp)
            )
        }
    }
}
