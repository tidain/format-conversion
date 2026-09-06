package com.gsgc.converter.domain

/**
 * 转换任务状态
 */
sealed class TaskState {
    object Pending : TaskState()
    data class Running(val progress: Int) : TaskState()
    object Completed : TaskState()
    data class Failed(val message: String) : TaskState()
    object Cancelled : TaskState()
}
