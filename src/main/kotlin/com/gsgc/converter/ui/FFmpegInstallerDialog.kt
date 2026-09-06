package com.gsgc.converter.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.gsgc.converter.domain.FFmpegService
import kotlinx.coroutines.launch

@Composable
fun FFmpegInstallerDialog(onDismiss: () -> Unit) {
    var progress by remember { mutableStateOf(0) }
    var status by remember { mutableStateOf("正在准备...") }
    var finished by remember { mutableStateOf(false) }
    var success by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    LaunchedEffect(Unit) {
        scope.launch {
            val result = FFmpegService.install(
                progressCallback = { p -> progress = p },
                statusCallback = { s -> status = s }
            )
            success = result
            finished = true
        }
    }

    Dialog(
        onDismissRequest = { if (finished) onDismiss() },
        properties = DialogProperties(dismissOnClickOutside = false, dismissOnBackPress = finished)
    ) {
        Surface(
            modifier = Modifier.width(400.dp),
            shape = MaterialTheme.shapes.medium
        ) {
            Column(modifier = Modifier.padding(24.dp)) {
                Text("安装 FFmpeg", style = MaterialTheme.typography.titleLarge)
                Spacer(Modifier.height(16.dp))
                Text(status, style = MaterialTheme.typography.bodyMedium)
                Spacer(Modifier.height(8.dp))
                if (!finished) {
                    LinearProgressIndicator(
                        progress = { progress / 100f },
                        modifier = Modifier.fillMaxWidth().height(8.dp)
                    )
                } else {
                    Text(
                        if (success) "安装成功！" else "安装失败",
                        color = if (success) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error
                    )
                }
                Spacer(Modifier.height(16.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.End
                ) {
                    Button(
                        onClick = onDismiss,
                        enabled = finished
                    ) {
                        Text("关闭")
                    }
                }
            }
        }
    }
}
