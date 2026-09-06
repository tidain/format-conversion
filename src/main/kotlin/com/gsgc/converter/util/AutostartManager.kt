package com.gsgc.converter.util

import java.io.File

/**
 * 开机自启动管理器
 * 在 %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup 创建/删除 .lnk 快捷方式
 */
object AutostartManager {

    private val appName = "文件格式转换器"
    private val startupDir = File(
        System.getenv("APPDATA"),
        "Microsoft\\Windows\\Start Menu\\Programs\\Startup"
    )
    private val shortcutPath = File(startupDir, "$appName.lnk")

    /**
     * 启用开机自启动（创建快捷方式）
     */
    fun enable(): Boolean {
        return try {
            disable()
            if (!startupDir.exists()) startupDir.mkdirs()

            val (target, args, workDir) = getLaunchCommand()

            // 使用 PowerShell + WScript.Shell 创建快捷方式
            val dollar = "\$"
            val argsPart = if (args.isNotEmpty()) "${dollar}sc.Arguments = '$args'" else ""
            val script = """
                ${dollar}ws = New-Object -ComObject WScript.Shell
                ${dollar}sc = ${dollar}ws.CreateShortcut('${shortcutPath.absolutePath}')
                ${dollar}sc.TargetPath = '$target'
                $argsPart
                ${dollar}sc.WorkingDirectory = '$workDir'
                ${dollar}sc.Save()
            """.trimIndent()

            val process = ProcessBuilder(
                "powershell.exe", "-NoProfile", "-Command", script
            ).redirectErrorStream(true).start()
            process.waitFor()
            process.exitValue() == 0 && shortcutPath.exists()
        } catch (e: Exception) {
            System.err.println("创建自启动快捷方式失败: ${e.message}")
            false
        }
    }

    /**
     * 禁用开机自启动（删除快捷方式）
     */
    fun disable(): Boolean {
        return try {
            if (shortcutPath.exists()) shortcutPath.delete() else true
        } catch (e: Exception) {
            System.err.println("删除自启动快捷方式失败: ${e.message}")
            false
        }
    }

    /**
     * 检查是否已启用开机自启动
     */
    fun isEnabled(): Boolean = shortcutPath.exists()

    /**
     * 获取启动命令三元组 (targetPath, arguments, workingDirectory)
     * 打包环境指向 exe；开发环境用 java -jar
     */
    private fun getLaunchCommand(): Triple<String, String, String> {
        val resourcesDir = System.getProperty("compose.application.resources.dir")
        return if (resourcesDir != null) {
            // 打包环境：exe 位于 resources.dir 的上级目录
            val appDir = File(resourcesDir).parentFile
            val exe = appDir?.listFiles { f -> f.extension.equals("exe", true) }
                ?.firstOrNull()
            val target = exe?.absolutePath
                ?: System.getProperty("java.home")?.let { "$it\\bin\\javaw.exe" }
                ?: "javaw.exe"
            val args = if (exe != null) "" else "-jar \"${appDir?.absolutePath}\\app.jar\""
            Triple(target, args, appDir?.absolutePath ?: System.getProperty("user.dir"))
        } else {
            // 开发环境：java -jar 指向构建的 jar
            val javaHome = System.getProperty("java.home")
            val javaExe = "$javaHome\\bin\\javaw.exe"
            val jarPath = File(System.getProperty("user.dir"), "build\\libs").listFiles { f ->
                f.extension.equals("jar", true)
            }?.firstOrNull()?.absolutePath ?: ""
            val args = if (jarPath.isNotEmpty()) "-jar \"$jarPath\"" else ""
            Triple(javaExe, args, System.getProperty("user.dir"))
        }
    }
}
