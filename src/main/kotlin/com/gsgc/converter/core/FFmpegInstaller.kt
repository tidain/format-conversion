package com.gsgc.converter.core

import com.sun.jna.platform.win32.Advapi32Util
import com.sun.jna.platform.win32.WinReg
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.net.URI
import java.util.zip.ZipInputStream

/**
 * FFmpeg 安装器
 * 优先从官方源下载，失败时使用内置 ffmpeg.zip，安装到 C:\ffmpeg 并写入用户 PATH
 */
object FFmpegInstaller {

    private const val INSTALL_DIR = "C:\\ffmpeg"
    private const val BIN_DIR = "C:\\ffmpeg\\bin"
    private const val OFFICIAL_URL =
        "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

    /**
     * 安装 FFmpeg
     * @param progressCallback 进度回调 (0-100)
     * @param statusCallback 状态文字回调
     */
    fun install(
        progressCallback: ((Int) -> Unit)? = null,
        statusCallback: ((String) -> Unit)? = null
    ): Boolean {
        return try {
            statusCallback?.invoke("正在下载 FFmpeg...")
            val zipFile = downloadFFmpeg(progressCallback, statusCallback)
                ?: run {
                    statusCallback?.invoke("下载失败，使用内置备用包...")
                    extractBundledFFmpeg()
                }

            if (zipFile == null || !zipFile.exists()) {
                throw RuntimeException("无法获取 FFmpeg 安装包")
            }

            statusCallback?.invoke("正在解压...")
            extractZip(zipFile, File(INSTALL_DIR))
            progressCallback?.invoke(80)

            statusCallback?.invoke("正在配置环境变量...")
            addToPath(BIN_DIR)
            progressCallback?.invoke(100)

            statusCallback?.invoke("安装完成")
            true
        } catch (e: Exception) {
            statusCallback?.invoke("安装失败: ${e.message}")
            false
        }
    }

    private fun downloadFFmpeg(
        progressCallback: ((Int) -> Unit)?,
        statusCallback: ((String) -> Unit)?
    ): File? {
        return try {
            val tempFile = File(System.getProperty("java.io.tmpdir"), "ffmpeg_install.zip")
            val uri = URI(OFFICIAL_URL)
            val connection = uri.toURL().openConnection()
            connection.connectTimeout = 15000
            connection.readTimeout = 30000
            val contentLength = connection.contentLengthLong

            connection.getInputStream().use { input ->
                FileOutputStream(tempFile).use { output ->
                    val buffer = ByteArray(8192)
                    var totalRead = 0L
                    var read: Int
                    while (input.read(buffer).also { read = it } != -1) {
                        output.write(buffer, 0, read)
                        totalRead += read
                        if (contentLength > 0) {
                            val progress = (totalRead * 50 / contentLength).toInt()
                            progressCallback?.invoke(progress)
                        }
                    }
                }
            }
            tempFile
        } catch (e: Exception) {
            statusCallback?.invoke("官方下载失败: ${e.message}")
            null
        }
    }

    private fun extractBundledFFmpeg(): File? {
        return try {
            // 从 classpath 资源读取 ffmpeg.zip
            val resource = javaClass.classLoader.getResourceAsStream("ffmpeg.zip")
                ?: return null
            val tempFile = File(System.getProperty("java.io.tmpdir"), "ffmpeg_bundled.zip")
            FileOutputStream(tempFile).use { output ->
                resource.copyTo(output)
            }
            tempFile
        } catch (e: Exception) {
            null
        }
    }

    private fun extractZip(zipFile: File, destDir: File) {
        destDir.mkdirs()
        ZipInputStream(FileInputStream(zipFile)).use { zis ->
            var entry = zis.nextEntry
            while (entry != null) {
                // 解压时去掉顶层目录（gyan.dev 的包有 ffmpeg-xxx-essentials_build/ 前缀）
                val name = entry.name.substringAfter('/', "")
                if (name.isEmpty()) {
                    entry = zis.nextEntry
                    continue
                }
                val outFile = File(destDir, name)
                if (entry.isDirectory) {
                    outFile.mkdirs()
                } else {
                    outFile.parentFile?.mkdirs()
                    FileOutputStream(outFile).use { output ->
                        zis.copyTo(output)
                    }
                }
                zis.closeEntry()
                entry = zis.nextEntry
            }
        }
    }

    private fun addToPath(binDir: String) {
        try {
            val currentPath = Advapi32Util.registryGetStringValue(
                WinReg.HKEY_CURRENT_USER,
                "Environment",
                "Path"
            )
            if (!currentPath.contains(binDir, ignoreCase = true)) {
                val newPath = "$currentPath;$binDir"
                Advapi32Util.registrySetStringValue(
                    WinReg.HKEY_CURRENT_USER,
                    "Environment",
                    "Path",
                    newPath
                )
            }
        } catch (e: Exception) {
            // 注册表 Path 不存在时创建
            try {
                Advapi32Util.registrySetStringValue(
                    WinReg.HKEY_CURRENT_USER,
                    "Environment",
                    "Path",
                    binDir
                )
            } catch (_: Exception) {
            }
        }
        // 同步到当前进程环境变量
        val currentEnvPath = System.getenv("Path") ?: ""
        if (!currentEnvPath.contains(binDir, ignoreCase = true)) {
            // ProcessBuilder 环境变量无法直接修改 JVM 的，依赖新进程读取注册表
        }
    }

    /**
     * 卸载 FFmpeg
     */
    fun uninstall(): Boolean {
        return try {
            File(INSTALL_DIR).deleteRecursively()
            removeFromPath(BIN_DIR)
            true
        } catch (e: Exception) {
            false
        }
    }

    private fun removeFromPath(binDir: String) {
        try {
            val currentPath = Advapi32Util.registryGetStringValue(
                WinReg.HKEY_CURRENT_USER,
                "Environment",
                "Path"
            )
            val entries = currentPath.split(";").filter {
                it.isNotBlank() && !it.equals(binDir, ignoreCase = true)
                        && !it.startsWith(binDir, ignoreCase = true)
            }
            Advapi32Util.registrySetStringValue(
                WinReg.HKEY_CURRENT_USER,
                "Environment",
                "Path",
                entries.joinToString(";")
            )
        } catch (_: Exception) {
        }
    }
}
