package com.gsgc.converter.util

import java.awt.Desktop
import java.io.File

/**
 * 文件操作工具：打开文件、打开文件所在位置
 */
object FileOpener {

    /** 打开文件（用系统默认程序） */
    fun openFile(filePath: String) {
        try {
            val file = File(filePath)
            if (file.exists()) {
                if (Desktop.isDesktopSupported()) {
                    Desktop.getDesktop().open(file)
                } else {
                    openWithSystem(filePath)
                }
            }
        } catch (_: Exception) {
            openWithSystem(filePath)
        }
    }

    /** 打开文件所在的文件夹并选中该文件 */
    fun openFileLocation(filePath: String) {
        try {
            val file = File(filePath)
            val parent = file.parentFile
            if (parent != null && parent.exists()) {
                val os = System.getProperty("os.name").lowercase()
                when {
                    os.contains("win") -> {
                        // Windows: explorer /select,"path"
                        ProcessBuilder("explorer.exe", "/select,\"$filePath\"").start()
                    }
                    os.contains("mac") -> {
                        // macOS: open -R path
                        ProcessBuilder("open", "-R", filePath).start()
                    }
                    else -> {
                        // Linux: 打开父目录
                        if (Desktop.isDesktopSupported()) {
                            Desktop.getDesktop().open(parent)
                        }
                    }
                }
            }
        } catch (_: Exception) {
            // 忽略错误
        }
    }

    private fun openWithSystem(filePath: String) {
        try {
            val os = System.getProperty("os.name").lowercase()
            when {
                os.contains("win") -> ProcessBuilder("cmd", "/c", "start", "", filePath).start()
                os.contains("mac") -> ProcessBuilder("open", filePath).start()
                else -> ProcessBuilder("xdg-open", filePath).start()
            }
        } catch (_: Exception) {
        }
    }
}
