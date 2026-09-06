package com.gsgc.converter.core

import java.io.File

/**
 * LibreOffice 定位器
 * 用于文档高保真转换（PDF↔DOCX 等），调用 soffice --headless --convert-to
 */
object LibreOfficeLocator {

    /**
     * 查找 soffice 可执行文件路径
     */
    fun locateSoffice(): String? {
        // 常见安装路径
        val candidates = listOf(
            "C:\\Program Files\\LibreOffice\\program\\soffice.exe",
            "C:\\Program Files (x86)\\LibreOffice\\program\\soffice.exe",
            "D:\\Program Files\\LibreOffice\\program\\soffice.exe",
            "D:\\Program Files (x86)\\LibreOffice\\program\\soffice.exe",
            System.getProperty("user.home") + "\\AppData\\Local\\Programs\\LibreOffice\\program\\soffice.exe"
        )
        for (c in candidates) {
            if (File(c).exists()) return c
        }

        // 从 PATH 查找
        try {
            val pathDirs = System.getenv("PATH")?.split(File.pathSeparator) ?: emptyList()
            for (dir in pathDirs) {
                val candidate = File(dir, "soffice.exe")
                if (candidate.exists()) return candidate.absolutePath
            }
        } catch (_: Exception) {
        }

        return null
    }

    /**
     * LibreOffice 是否已安装
     */
    fun isAvailable(): Boolean = locateSoffice() != null
}
