package com.gsgc.converter.core

import java.io.File
import java.util.concurrent.atomic.AtomicBoolean
import java.util.regex.Pattern

/**
 * 格式转换器
 * 支持视频/音频/图片/文档/压缩包转换
 */
class FormatConverter {

    @Volatile
    var isCancelled = false

    private val timePattern = Pattern.compile("time=(\\d+):(\\d+):(\\d+\\.\\d+)")

    /**
     * 主转换入口，根据扩展名调度
     */
    fun convert(
        sourceFile: String,
        targetFile: String,
        progressCallback: ((Int) -> Unit)? = null
    ): Boolean {
        val sourceExt = File(sourceFile).extension.lowercase()
        val targetExt = File(targetFile).extension.lowercase()

        val sourceType = typeMap[sourceExt]
        val targetType = typeMap[targetExt]

        if (sourceType == null || targetType == null) {
            throw IllegalArgumentException("不支持的文件格式：$sourceExt -> $targetExt")
        }

        // 确保输出目录存在
        File(targetFile).parentFile?.mkdirs()

        return when {
            sourceType == "video" && targetType == "video" ->
                convertVideoToVideo(sourceFile, targetFile, progressCallback)
            sourceType == "video" && targetType == "audio" ->
                convertVideoToAudio(sourceFile, targetFile, progressCallback)
            sourceType == "audio" && targetType == "audio" ->
                convertAudioToAudio(sourceFile, targetFile, progressCallback)
            sourceType == "image" && targetType == "image" ->
                convertImage(sourceFile, targetFile, progressCallback)
            sourceType == "document" && targetType == "document" ->
                convertDocument(sourceFile, targetFile, progressCallback)
            sourceType == "archive" && targetType == "archive" ->
                convertArchive(sourceFile, targetFile, progressCallback)
            else -> throw IllegalArgumentException("不支持的转换类型：$sourceType -> $targetType")
        }
    }

    // ==================== 音视频转换 ====================

    fun convertVideoToVideo(
        source: String,
        target: String,
        progressCallback: ((Int) -> Unit)? = null
    ): Boolean {
        val ffmpeg = FFmpegLocator.locateFfmpeg() ?: throw IllegalStateException("未找到 ffmpeg")
        val ffprobe = FFmpegLocator.locateFfprobe() ?: throw IllegalStateException("未找到 ffprobe")

        val duration = getDuration(ffprobe, source)

        val cmd = listOf(
            ffmpeg,
            "-i", source,
            "-y",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            target
        )

        return runFfmpegWithProgress(cmd, duration, target, progressCallback)
    }

    fun convertVideoToAudio(
        source: String,
        target: String,
        progressCallback: ((Int) -> Unit)? = null
    ): Boolean {
        val ffmpeg = FFmpegLocator.locateFfmpeg() ?: throw IllegalStateException("未找到 ffmpeg")
        val ffprobe = FFmpegLocator.locateFfprobe() ?: throw IllegalStateException("未找到 ffprobe")

        val duration = getDuration(ffprobe, source)

        val cmd = listOf(ffmpeg, "-i", source, "-vn", "-y", target)
        return runFfmpegWithProgress(cmd, duration, target, progressCallback)
    }

    fun convertAudioToAudio(
        source: String,
        target: String,
        progressCallback: ((Int) -> Unit)? = null
    ): Boolean {
        val ffmpeg = FFmpegLocator.locateFfmpeg() ?: throw IllegalStateException("未找到 ffmpeg")
        val ffprobe = FFmpegLocator.locateFfprobe() ?: throw IllegalStateException("未找到 ffprobe")

        val duration = getDuration(ffprobe, source)

        val cmd = listOf(ffmpeg, "-i", source, "-y", target)
        return runFfmpegWithProgress(cmd, duration, target, progressCallback)
    }

    private fun getDuration(ffprobe: String, source: String): Double {
        val process = ProcessBuilder(
            ffprobe, "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", source
        ).redirectErrorStream(false).start()
        val output = process.inputStream.bufferedReader().readText().trim()
        process.waitFor()
        return output.toDoubleOrNull() ?: 0.0
    }

    private fun runFfmpegWithProgress(
        cmd: List<String>,
        duration: Double,
        target: String,
        progressCallback: ((Int) -> Unit)?
    ): Boolean {
        return try {
            val process = ProcessBuilder(cmd)
                .redirectErrorStream(false)
                .start()

            // 读取 stderr 获取进度，累积错误信息
            val reader = process.errorStream.bufferedReader()
            val errorBuffer = StringBuilder()
            var line: String?
            while (reader.readLine().also { line = it } != null) {
                line?.let {
                    errorBuffer.appendLine(it)
                    if (isCancelled) {
                        process.destroyForcibly()
                        deleteOutput(target)
                        return false
                    }
                    val matcher = timePattern.matcher(it)
                    if (matcher.find() && duration > 0) {
                        val h = matcher.group(1).toDouble()
                        val m = matcher.group(2).toDouble()
                        val s = matcher.group(3).toDouble()
                        val currentTime = h * 3600 + m * 60 + s
                        val progress = minOf((currentTime / duration * 100).toInt(), 99)
                        progressCallback?.invoke(progress)
                    }
                }
            }

            process.waitFor()
            if (process.exitValue() != 0) {
                deleteOutput(target)
                val error = errorBuffer.toString().trim()
                throw RuntimeException("FFmpeg 转换失败: ${error.ifEmpty { "未知错误" }}")
            }

            progressCallback?.invoke(100)

            val outFile = File(target)
            if (!outFile.exists() || outFile.length() == 0L) {
                throw RuntimeException("输出文件不存在或为空")
            }
            true
        } catch (e: Exception) {
            deleteOutput(target)
            throw e
        }
    }

    private fun deleteOutput(target: String) {
        try {
            val f = File(target)
            if (f.exists()) f.delete()
        } catch (_: Exception) {
        }
    }

    // ==================== 图片转换 ====================

    fun convertImage(
        source: String,
        target: String,
        progressCallback: ((Int) -> Unit)? = null
    ): Boolean {
        if (isCancelled) { deleteOutput(target); return false }
        progressCallback?.invoke(0)
        return try {
            if (isCancelled) { deleteOutput(target); return false }
            val img = javax.imageio.ImageIO.read(File(source))
                ?: throw RuntimeException("无法读取图片: $source")
            if (isCancelled) { deleteOutput(target); return false }
            val ext = File(target).extension.lowercase()
            val format = when (ext) {
                "jpg", "jpeg" -> "jpg"
                else -> ext
            }
            val written = javax.imageio.ImageIO.write(img, format, File(target))
            if (isCancelled) { deleteOutput(target); return false }
            progressCallback?.invoke(100)
            if (!written) throw RuntimeException("不支持的图片格式: $ext")
            true
        } catch (e: Exception) {
            deleteOutput(target)
            throw RuntimeException("图片转换失败: ${e.message}", e)
        }
    }

    // ==================== 文档转换 ====================

    fun convertDocument(
        source: String,
        target: String,
        progressCallback: ((Int) -> Unit)? = null
    ): Boolean {
        if (isCancelled) { deleteOutput(target); return false }
        progressCallback?.invoke(0)
        return try {
            if (isCancelled) { deleteOutput(target); return false }
            val srcExt = File(source).extension.lowercase()
            val tgtExt = File(target).extension.lowercase()

            // 优先使用 LibreOffice 实现高保真转换
            val libreOffice = LibreOfficeLocator.locateSoffice()
            if (libreOffice != null) {
                val success = convertWithLibreOffice(libreOffice, source, target, srcExt, tgtExt, progressCallback)
                if (success) {
                    if (isCancelled) { deleteOutput(target); return false }
                    progressCallback?.invoke(100)
                    return true
                }
                // LibreOffice 失败时回退到内置实现
            }

            if (isCancelled) { deleteOutput(target); return false }
            when {
                srcExt == "pdf" && tgtExt == "docx" -> pdfToDocx(source, target)
                srcExt == "docx" && tgtExt == "pdf" -> docxToPdf(source, target)
                srcExt == "docx" && tgtExt == "txt" -> docxToTxt(source, target)
                else -> throw RuntimeException("不支持的文档转换: $srcExt -> $tgtExt")
            }
            if (isCancelled) { deleteOutput(target); return false }
            progressCallback?.invoke(100)
            true
        } catch (e: Exception) {
            deleteOutput(target)
            throw RuntimeException("文档转换失败: ${e.message}", e)
        }
    }

    /**
     * 使用 LibreOffice headless 进行高保真文档转换
     * 支持 PDF↔DOCX、DOCX→PDF、DOCX→TXT 等
     */
    private fun convertWithLibreOffice(
        soffice: String,
        source: String,
        target: String,
        srcExt: String,
        tgtExt: String,
        progressCallback: ((Int) -> Unit)?
    ): Boolean {
        val supportedPairs = setOf(
            "pdf" to "docx", "docx" to "pdf", "doc" to "pdf",
            "docx" to "txt", "doc" to "docx", "rtf" to "docx",
            "html" to "pdf", "txt" to "pdf"
        )
        if (srcExt to tgtExt !in supportedPairs) return false

        // 转换到临时目录，再移动到目标位置
        val tmpDir = File(System.getProperty("java.io.tmpdir"), "fc_lo_${System.nanoTime()}")
        tmpDir.mkdirs()
        return try {
            if (isCancelled) { deleteOutput(target); return false }
            progressCallback?.invoke(10)

            val cmd = listOf(
                soffice,
                "--headless",
                "--norestore",
                "--nolockcheck",
                "--convert-to", tgtExt,
                "--outdir", tmpDir.absolutePath,
                source
            )
            val process = ProcessBuilder(cmd)
                .redirectErrorStream(true)
                .start()

            // 读取输出（避免管道阻塞），并检测取消
            val reader = process.inputStream.bufferedReader()
            while (reader.readLine() != null) {
                if (isCancelled) {
                    process.destroyForcibly()
                    deleteOutput(target)
                    return false
                }
            }
            process.waitFor()

            if (isCancelled) { deleteOutput(target); return false }
            progressCallback?.invoke(70)

            if (process.exitValue() != 0) {
                return false
            }

            // LibreOffice 输出的文件名为 <basename>.<tgtExt>
            val baseName = File(source).nameWithoutExtension
            val outFile = File(tmpDir, "$baseName.$tgtExt")
            if (!outFile.exists()) {
                // 某些版本输出扩展名可能不同，搜索目录
                val found = tmpDir.listFiles { f -> f.extension.equals(tgtExt, true) }
                    ?.firstOrNull()
                if (found == null) return false
                found.renameTo(File(target))
            } else {
                outFile.renameTo(File(target))
            }

            File(target).exists()
        } finally {
            tmpDir.deleteRecursively()
        }
    }

    private fun pdfToDocx(source: String, target: String) {
        val document = org.apache.pdfbox.Loader.loadPDF(File(source))
        val stripper = org.apache.pdfbox.text.PDFTextStripper()
        val text = stripper.getText(document)
        document.close()

        val doc = org.apache.poi.xwpf.usermodel.XWPFDocument()
        for (line in text.lines()) {
            if (line.isNotBlank()) {
                doc.createParagraph().createRun().setText(line)
            }
        }
        File(target).outputStream().use { doc.write(it) }
        doc.close()
    }

    private fun docxToPdf(source: String, target: String) {
        // 简化实现：提取文本写入 PDF
        val doc = org.apache.poi.xwpf.usermodel.XWPFDocument(File(source).inputStream())
        val text = buildString {
            for (p in doc.paragraphs) {
                append(p.text).append("\n")
            }
        }
        doc.close()

        val pdfDoc = org.apache.pdfbox.pdmodel.PDDocument()
        val page = org.apache.pdfbox.pdmodel.PDPage()
        pdfDoc.addPage(page)
        val contentStream = org.apache.pdfbox.pdmodel.PDPageContentStream(pdfDoc, page)
        contentStream.beginText()
        contentStream.setFont(
            org.apache.pdfbox.pdmodel.font.PDType1Font(
                org.apache.pdfbox.pdmodel.font.Standard14Fonts.FontName.HELVETICA
            ), 12f
        )
        contentStream.newLineAtOffset(50f, 750f)
        var y = 750f
        for (line in text.lines()) {
            if (y < 50f) break
            contentStream.newLineAtOffset(0f, -15f)
            contentStream.showText(line.take(100))
            y -= 15f
        }
        contentStream.endText()
        contentStream.close()
        pdfDoc.save(target)
        pdfDoc.close()
    }

    private fun docxToTxt(source: String, target: String) {
        val doc = org.apache.poi.xwpf.usermodel.XWPFDocument(File(source).inputStream())
        val text = buildString {
            for (p in doc.paragraphs) {
                append(p.text).append("\n")
            }
        }
        doc.close()
        File(target).writeText(text, Charsets.UTF_8)
    }

    // ==================== 压缩包转换 ====================

    fun convertArchive(
        source: String,
        target: String,
        progressCallback: ((Int) -> Unit)? = null
    ): Boolean {
        if (isCancelled) { deleteOutput(target); return false }
        progressCallback?.invoke(0)
        val tempDir = File(System.getProperty("java.io.tmpdir"), "fc_${System.nanoTime()}")
        tempDir.mkdirs()
        return try {
            if (isCancelled) { tempDir.deleteRecursively(); deleteOutput(target); return false }
            // 解压
            extractArchive(source, tempDir)
            progressCallback?.invoke(50)
            if (isCancelled) { tempDir.deleteRecursively(); deleteOutput(target); return false }

            // 压缩
            compressArchive(tempDir, target)
            if (isCancelled) { tempDir.deleteRecursively(); deleteOutput(target); return false }
            progressCallback?.invoke(100)
            true
        } catch (e: Exception) {
            deleteOutput(target)
            throw RuntimeException("压缩包转换失败: ${e.message}", e)
        } finally {
            tempDir.deleteRecursively()
        }
    }

    private fun extractArchive(source: String, destDir: File) {
        val srcExt = File(source).extension.lowercase()
        when {
            srcExt == "zip" -> {
                java.util.zip.ZipFile(source).use { zip ->
                    for (entry in zip.entries()) {
                        val outFile = File(destDir, entry.name)
                        if (entry.isDirectory) {
                            outFile.mkdirs()
                        } else {
                            outFile.parentFile?.mkdirs()
                            zip.getInputStream(entry).use { input ->
                                outFile.outputStream().use { output -> input.copyTo(output) }
                            }
                        }
                    }
                }
            }
            srcExt in listOf("tar", "gz", "tgz") -> {
                val input = if (srcExt == "gz" || srcExt == "tgz") {
                    org.apache.commons.compress.compressors.gzip.GzipCompressorInputStream(File(source).inputStream())
                } else {
                    File(source).inputStream()
                }
                org.apache.commons.compress.archivers.tar.TarArchiveInputStream(input).use { tar ->
                    var entry = tar.nextEntry
                    while (entry != null) {
                        val outFile = File(destDir, entry.name)
                        if (entry.isDirectory) {
                            outFile.mkdirs()
                        } else {
                            outFile.parentFile?.mkdirs()
                            outFile.outputStream().use { output -> tar.copyTo(output) }
                        }
                        entry = tar.nextEntry
                    }
                }
            }
            else -> throw RuntimeException("不支持的压缩格式: $srcExt")
        }
    }

    private fun compressArchive(sourceDir: File, target: String) {
        val tgtExt = File(target).extension.lowercase()
        when {
            tgtExt == "zip" -> {
                java.util.zip.ZipOutputStream(File(target).outputStream()).use { zip ->
                    sourceDir.walkTopDown().filter { it.isFile }.forEach { file ->
                        val entryName = file.relativeTo(sourceDir).path
                        zip.putNextEntry(java.util.zip.ZipEntry(entryName))
                        file.inputStream().use { it.copyTo(zip) }
                        zip.closeEntry()
                    }
                }
            }
            tgtExt == "tar" -> {
                org.apache.commons.compress.archivers.tar.TarArchiveOutputStream(File(target).outputStream()).use { tar ->
                    sourceDir.walkTopDown().filter { it.isFile }.forEach { file ->
                        val entryName = file.relativeTo(sourceDir).path
                        val entry = org.apache.commons.compress.archivers.tar.TarArchiveEntry(entryName)
                        entry.size = file.length()
                        tar.putArchiveEntry(entry)
                        file.inputStream().use { it.copyTo(tar) }
                        tar.closeArchiveEntry()
                    }
                    tar.finish()
                }
            }
            tgtExt == "gz" -> {
                val gzipOut = org.apache.commons.compress.compressors.gzip.GzipCompressorOutputStream(File(target).outputStream())
                org.apache.commons.compress.archivers.tar.TarArchiveOutputStream(gzipOut).use { tar ->
                    sourceDir.walkTopDown().filter { it.isFile }.forEach { file ->
                        val entryName = file.relativeTo(sourceDir).path
                        val entry = org.apache.commons.compress.archivers.tar.TarArchiveEntry(entryName)
                        entry.size = file.length()
                        tar.putArchiveEntry(entry)
                        file.inputStream().use { it.copyTo(tar) }
                        tar.closeArchiveEntry()
                    }
                    tar.finish()
                }
            }
            else -> throw RuntimeException("不支持的目标压缩格式: $tgtExt")
        }
    }

    companion object {
        val typeMap = mapOf(
            // 视频
            "mp4" to "video", "avi" to "video", "mov" to "video",
            "flv" to "video", "mkv" to "video", "wmv" to "video",
            "webm" to "video", "m4v" to "video", "3gp" to "video",
            // 音频
            "mp3" to "audio", "wav" to "audio", "aac" to "audio",
            "flac" to "audio", "m4a" to "audio", "ogg" to "audio",
            "wma" to "audio", "opus" to "audio",
            // 图片
            "jpg" to "image", "jpeg" to "image", "png" to "image",
            "bmp" to "image", "gif" to "image", "webp" to "image",
            "tiff" to "image", "ico" to "image",
            // 文档
            "pdf" to "document", "docx" to "document", "doc" to "document",
            "txt" to "document", "rtf" to "document", "html" to "document",
            "epub" to "document", "mobi" to "document",
            // 压缩包
            "zip" to "archive", "tar" to "archive", "gz" to "archive", "tgz" to "archive"
        )
    }
}
