package com.gsgc.converter.domain

import com.gsgc.converter.core.FormatConverter
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * 转换任务封装
 * 持有 StateFlow<TaskState> 供 UI 收集
 * 转换在 Dispatchers.IO 执行，状态更新通过 StateFlow 自动在 Main 线程收集
 */
class ConvertTask(
    val sourceFile: String,
    val targetFile: String
) {
    private val converter = FormatConverter()
    private val scope = CoroutineScope(Dispatchers.Default)
    private var job: Job? = null

    private val _state = MutableStateFlow<TaskState>(TaskState.Pending)
    val state: StateFlow<TaskState> = _state.asStateFlow()

    fun start() {
        if (job != null) return
        job = scope.launch {
            _state.value = TaskState.Running(0)
            try {
                // IO 线程执行转换
                withContext(Dispatchers.IO) {
                    converter.convert(sourceFile, targetFile) { progress ->
                        // 进度回调在 IO 线程，更新 StateFlow（线程安全）
                        _state.value = TaskState.Running(progress)
                    }
                }
                if (converter.isCancelled) {
                    _state.value = TaskState.Cancelled
                } else {
                    _state.value = TaskState.Completed
                }
            } catch (e: Exception) {
                _state.value = if (converter.isCancelled) {
                    TaskState.Cancelled
                } else {
                    TaskState.Failed(e.message ?: "转换失败")
                }
            }
        }
    }

    fun cancel() {
        converter.isCancelled = true
        _state.value = TaskState.Cancelled
    }
}
