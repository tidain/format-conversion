package com.gsgc.converter.domain

import com.gsgc.converter.core.FFmpegInstaller
import com.gsgc.converter.core.FFmpegLocator
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * FFmpeg 领域服务
 * 封装 core 层的 FFmpegLocator/FFmpegInstaller，供 UI 层调用
 * UI 层不应直接依赖 core 包
 */
object FFmpegService {

    /**
     * 检查 FFmpeg 是否可用（IO 线程执行）
     */
    suspend fun isAvailable(): Boolean = withContext(Dispatchers.IO) {
        FFmpegLocator.isFFmpegAvailable()
    }

    /**
     * 同步检查（用于非协程上下文，如启动时快速判断）
     */
    fun isAvailableSync(): Boolean = FFmpegLocator.isFFmpegAvailable()

    /**
     * 安装 FFmpeg（IO 线程执行）
     */
    suspend fun install(
        progressCallback: ((Int) -> Unit)? = null,
        statusCallback: ((String) -> Unit)? = null
    ): Boolean = withContext(Dispatchers.IO) {
        FFmpegInstaller.install(progressCallback, statusCallback)
    }

    /**
     * 卸载 FFmpeg（IO 线程执行）
     */
    suspend fun uninstall(): Boolean = withContext(Dispatchers.IO) {
        FFmpegInstaller.uninstall()
    }
}
