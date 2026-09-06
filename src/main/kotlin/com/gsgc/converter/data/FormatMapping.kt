package com.gsgc.converter.data

/**
 * 文件格式映射模块
 * 定义每种源格式可转换的目标格式，按类别分组
 */
object FormatMapping {

    val FORMAT_CATEGORIES = mapOf(
        "video" to "视频",
        "audio" to "音频",
        "image" to "图片",
        "document" to "文档"
    )

    val VIDEO_FORMATS = mapOf(
        "mp4" to mapOf(
            "video" to listOf("flv", "avi", "mov", "wmv", "mkv", "webm", "m4v", "amv", "amkv"),
            "audio" to listOf("mp3", "aac", "wav", "m4a", "ogg")
        ),
        "flv" to mapOf(
            "video" to listOf("mp4", "avi", "mov", "wmv", "mkv"),
            "audio" to listOf("mp3", "aac", "wav", "m4a")
        ),
        "avi" to mapOf(
            "video" to listOf("mp4", "flv", "mov", "wmv", "mkv", "amv", "amkv"),
            "audio" to listOf("mp3", "aac", "wav")
        ),
        "mov" to mapOf(
            "video" to listOf("mp4", "flv", "avi", "wmv", "mkv"),
            "audio" to listOf("mp3", "aac", "wav", "m4a")
        ),
        "wmv" to mapOf(
            "video" to listOf("mp4", "flv", "avi", "mov", "mkv"),
            "audio" to listOf("mp3", "wav", "wma")
        ),
        "mkv" to mapOf(
            "video" to listOf("mp4", "flv", "avi", "mov", "wmv"),
            "audio" to listOf("mp3", "aac", "wav", "m4a")
        ),
        "webm" to mapOf(
            "video" to listOf("mp4", "mkv"),
            "audio" to listOf("mp3", "opus", "ogg")
        ),
        "amv" to mapOf(
            "video" to listOf("mp4", "avi", "mov", "mkv"),
            "audio" to listOf("mp3", "aac", "wav")
        ),
        "amkv" to mapOf(
            "video" to listOf("mp4", "avi", "mov", "mkv"),
            "audio" to listOf("mp3", "aac", "wav")
        ),
        "av1" to mapOf(
            "video" to listOf("mp4", "mkv", "webm"),
            "audio" to listOf("opus", "aac")
        ),
        "hevc" to mapOf(
            "video" to listOf("mp4", "mov", "mkv"),
            "audio" to listOf("aac", "ac3")
        ),
        "mpeg2" to mapOf(
            "video" to listOf("avi", "mpg", "vob"),
            "audio" to listOf("mp2", "ac3")
        )
    )

    val AUDIO_FORMATS = mapOf(
        "mp3" to mapOf("audio" to listOf("wav", "aac", "ogg", "wma", "m4a", "flac")),
        "wav" to mapOf("audio" to listOf("mp3", "aac", "ogg", "wma", "m4a", "flac")),
        "aac" to mapOf("audio" to listOf("mp3", "wav", "ogg", "wma", "m4a")),
        "ogg" to mapOf("audio" to listOf("mp3", "wav", "aac", "wma", "m4a")),
        "wma" to mapOf("audio" to listOf("mp3", "wav", "aac", "ogg", "m4a")),
        "m4a" to mapOf("audio" to listOf("mp3", "wav", "aac", "ogg", "wma")),
        "flac" to mapOf("audio" to listOf("mp3", "wav", "aac", "ogg", "wma", "m4a")),
        "ac3" to mapOf("audio" to listOf("dts", "aac", "mp3")),
        "dts" to mapOf("audio" to listOf("ac3", "wav", "flac"))
    )

    val IMAGE_FORMATS = mapOf(
        "jpg" to mapOf("image" to listOf("png", "bmp", "gif", "webp", "tiff", "ico")),
        "jpeg" to mapOf("image" to listOf("png", "bmp", "gif", "webp", "tiff", "ico")),
        "png" to mapOf("image" to listOf("jpg", "bmp", "gif", "webp", "tiff", "ico")),
        "bmp" to mapOf("image" to listOf("jpg", "png", "gif", "webp", "tiff")),
        "gif" to mapOf("image" to listOf("jpg", "png", "bmp", "webp", "tiff")),
        "webp" to mapOf("image" to listOf("jpg", "png", "bmp", "gif", "tiff")),
        "tiff" to mapOf("image" to listOf("jpg", "png", "bmp", "gif", "webp")),
        "ico" to mapOf("image" to listOf("png", "jpg"))
    )

    val DOCUMENT_FORMATS = mapOf(
        "pdf" to mapOf("document" to listOf("doc", "docx", "txt", "rtf", "html", "epub", "mobi")),
        "doc" to mapOf("document" to listOf("pdf", "docx", "txt", "rtf", "html")),
        "docx" to mapOf("document" to listOf("pdf", "doc", "txt", "rtf", "html")),
        "txt" to mapOf("document" to listOf("pdf", "doc", "docx", "rtf", "html")),
        "rtf" to mapOf("document" to listOf("pdf", "doc", "docx", "txt", "html")),
        "html" to mapOf("document" to listOf("pdf", "doc", "docx", "txt", "rtf")),
        "epub" to mapOf("document" to listOf("pdf", "mobi")),
        "mobi" to mapOf("document" to listOf("pdf", "epub"))
    )

    /**
     * 获取源文件格式可以转换的目标格式列表，按类别分组
     * @param sourceFormat 源文件格式（不含点号）
     * @return 按类别分组的可转换格式字典 { "视频": [...], "音频": [...] }
     */
    fun getTargetFormats(sourceFormat: String): Map<String, List<String>> {
        val ext = sourceFormat.lowercase()
        val result = mutableMapOf<String, List<String>>()

        val sourceMap = when {
            ext in VIDEO_FORMATS -> VIDEO_FORMATS[ext]
            ext in AUDIO_FORMATS -> AUDIO_FORMATS[ext]
            ext in IMAGE_FORMATS -> IMAGE_FORMATS[ext]
            ext in DOCUMENT_FORMATS -> DOCUMENT_FORMATS[ext]
            else -> null
        }

        sourceMap?.forEach { (category, formatList) ->
            if (formatList.isNotEmpty()) {
                val displayCategory = FORMAT_CATEGORIES[category] ?: category
                result[displayCategory] = formatList
            }
        }

        return result
    }
}
