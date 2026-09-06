package com.gsgc.converter.core

import java.io.File

/**
 * FFmpeg 可执行文件查找器
 * 查找顺序：打包资源目录 → 当前目录 → 系统 PATH → 常见安装路径
 */
object FFmpegLocator {

    private val isWindows = System.getProperty("os.name").lowercase().contains("win")

    private val exeSuffix = if (isWindows) ".exe" else ""

    /**
     * 查找 ffmpeg 可执行文件路径
     */
    fun locateFfmpeg(): String? = locate("ffmpeg")

    /**
     * 查找 ffprobe 可执行文件路径
     */
    fun locateFfprobe(): String? = locate("ffprobe")

    private fun locate(name: String): String? {
        val exeName = if (name.endsWith(exeSuffix)) name else name + exeSuffix

        // 1. 打包资源目录（Compose Desktop 当前工作目录下的 ffmpeg）
        val resourceCandidates = listOf(
            File(System.getProperty("compose.application.resources.dir") ?: ""),
            File("."),
            File(System.getProperty("user.dir"))
        )
        for (dir in resourceCandidates) {
            val f = File(dir, exeName)
            if (f.exists()) return f.absolutePath
        }

        // 2. 系统 PATH
        val pathDirs = System.getenv("PATH")?.split(File.pathSeparator) ?: emptyList()
        for (dir in pathDirs) {
            val f = File(dir, exeName)
            if (f.exists()) return f.absolutePath
            // 也检查 dir/ffmpeg.exe 形式（有些 PATH 直接指向 bin）
        }

        // 3. 常见安装路径
        val userHome = System.getProperty("user.home")
        val programFiles = System.getenv("ProgramFiles") ?: "C:\\Program Files"
        val programFilesX86 = System.getenv("ProgramFiles(x86)") ?: "C:\\Program Files (x86)"

        val knownPaths = listOf(
            "C:\\ffmpeg\\bin",
            "C:\\ffmpeg",
            "$programFiles\\ffmpeg\\bin",
            "$programFiles\\ffmpeg",
            "$programFilesX86\\ffmpeg\\bin",
            "$programFilesX86\\ffmpeg",
            "$userHome\\ffmpeg\\bin",
            "$userHome\\ffmpeg",
            "D:\\ffmpeg\\bin",
            "D:\\ffmpeg-7.0.2-essentials_build\\bin"
        )
        for (base in knownPaths) {
            val f = File(base, exeName)
            if (f.exists()) return f.absolutePath
        }

        // 4. PATH 中含 ffmpeg 字样的目录
        for (dir in pathDirs) {
            if (dir.lowercase().contains("ffmpeg")) {
                val f = File(dir, exeName)
                if (f.exists()) return f.absolutePath
            }
        }

        return null
    }

    /**
     * 检查 FFmpeg 是否可用（能执行 ffmpeg -version）
     */
    fun isFFmpegAvailable(): Boolean {
        val ffmpeg = locateFfmpeg() ?: return false
        return try {
            val process = ProcessBuilder(ffmpeg, "-version")
                .redirectErrorStream(false)
                .start()
            process.waitFor()
            process.exitValue() == 0
        } catch (e: Exception) {
            false
        }
    }
}
