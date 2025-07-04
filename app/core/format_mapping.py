"""
文件格式映射模块
"""

# 格式分类
FORMAT_CATEGORIES = {
    'video': '视频',
    'audio': '音频',
    'image': '图片',
    'document': '文档',
}

# 视频格式转换映射
VIDEO_FORMATS = {
    'mp4': {
        'video': ['flv', 'avi', 'mov', 'wmv', 'mkv', 'webm', 'm4v'],
        'audio': ['mp3', 'aac', 'wav', 'm4a', 'ogg']
    },
    'flv': {
        'video': ['mp4', 'avi', 'mov', 'wmv', 'mkv'],
        'audio': ['mp3', 'aac', 'wav', 'm4a']
    },
    'avi': {
        'video': ['mp4', 'flv', 'mov', 'wmv', 'mkv'],
        'audio': ['mp3', 'aac', 'wav']
    },
    'mov': {
        'video': ['mp4', 'flv', 'avi', 'wmv', 'mkv'],
        'audio': ['mp3', 'aac', 'wav', 'm4a']
    },
    'wmv': {
        'video': ['mp4', 'flv', 'avi', 'mov', 'mkv'],
        'audio': ['mp3', 'wav', 'wma']
    },
    'mkv': {
        'video': ['mp4', 'flv', 'avi', 'mov', 'wmv'],
        'audio': ['mp3', 'aac', 'wav', 'm4a']
    },
    'webm': {
        'video': ['mp4', 'mkv'],
        'audio': ['mp3', 'opus', 'ogg']
    },
}

# 音频格式转换映射
AUDIO_FORMATS = {
    'mp3': {
        'audio': ['wav', 'aac', 'ogg', 'wma', 'm4a', 'flac']
    },
    'wav': {
        'audio': ['mp3', 'aac', 'ogg', 'wma', 'm4a', 'flac']
    },
    'aac': {
        'audio': ['mp3', 'wav', 'ogg', 'wma', 'm4a']
    },
    'ogg': {
        'audio': ['mp3', 'wav', 'aac', 'wma', 'm4a']
    },
    'wma': {
        'audio': ['mp3', 'wav', 'aac', 'ogg', 'm4a']
    },
    'm4a': {
        'audio': ['mp3', 'wav', 'aac', 'ogg', 'wma']
    },
    'flac': {
        'audio': ['mp3', 'wav', 'aac', 'ogg', 'wma', 'm4a']
    },
}

# 图片格式转换映射
IMAGE_FORMATS = {
    'jpg': {
        'image': ['png', 'bmp', 'gif', 'webp', 'tiff', 'ico']
    },
    'jpeg': {
        'image': ['png', 'bmp', 'gif', 'webp', 'tiff', 'ico']
    },
    'png': {
        'image': ['jpg', 'bmp', 'gif', 'webp', 'tiff', 'ico']
    },
    'bmp': {
        'image': ['jpg', 'png', 'gif', 'webp', 'tiff']
    },
    'gif': {
        'image': ['jpg', 'png', 'bmp', 'webp', 'tiff']
    },
    'webp': {
        'image': ['jpg', 'png', 'bmp', 'gif', 'tiff']
    },
    'tiff': {
        'image': ['jpg', 'png', 'bmp', 'gif', 'webp']
    },
    'ico': {
        'image': ['png', 'jpg']
    },
}

# 文档格式转换映射
DOCUMENT_FORMATS = {
    'pdf': {
        'document': ['doc', 'docx', 'txt', 'rtf', 'html', 'epub', 'mobi']
    },
    'doc': {
        'document': ['pdf', 'docx', 'txt', 'rtf', 'html']
    },
    'docx': {
        'document': ['pdf', 'doc', 'txt', 'rtf', 'html']
    },
    'txt': {
        'document': ['pdf', 'doc', 'docx', 'rtf', 'html']
    },
    'rtf': {
        'document': ['pdf', 'doc', 'docx', 'txt', 'html']
    },
    'html': {
        'document': ['pdf', 'doc', 'docx', 'txt', 'rtf']
    },
    'epub': {
        'document': ['pdf', 'mobi']
    },
    'mobi': {
        'document': ['pdf', 'epub']
    },
}

def get_target_formats(source_format: str) -> dict:
    """获取源文件格式可以转换的目标格式列表，按类别分组
    
    Args:
        source_format: 源文件格式（不含点号）
        
    Returns:
        按类别分组的可转换格式字典，格式为：
        {
            'category_name': ['format1', 'format2', ...],
            ...
        }
    """
    source_format = source_format.lower()
    result = {}
    
    # 检查各个格式映射
    if source_format in VIDEO_FORMATS:
        formats = VIDEO_FORMATS[source_format]
        for category, format_list in formats.items():
            if format_list:  # 只添加非空的类别
                result[FORMAT_CATEGORIES[category]] = format_list
    elif source_format in AUDIO_FORMATS:
        formats = AUDIO_FORMATS[source_format]
        for category, format_list in formats.items():
            if format_list:  # 只添加非空的类别
                result[FORMAT_CATEGORIES[category]] = format_list
    elif source_format in IMAGE_FORMATS:
        formats = IMAGE_FORMATS[source_format]
        for category, format_list in formats.items():
            if format_list:  # 只添加非空的类别
                result[FORMAT_CATEGORIES[category]] = format_list
    elif source_format in DOCUMENT_FORMATS:
        formats = DOCUMENT_FORMATS[source_format]
        for category, format_list in formats.items():
            if format_list:  # 只添加非空的类别
                result[FORMAT_CATEGORIES[category]] = format_list
    
    return result 