import os
import sys
import shutil
import subprocess
import re
import logging
from typing import Callable, Dict, Tuple, List
import time
import threading
import tempfile
from PIL import Image
from docx import Document
from pdf2docx import Converter
import zipfile
import tarfile

# 配置详细的日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 只输出到控制台
    ]
)

flags = 0
if sys.platform == "win32":
    flags = subprocess.CREATE_NO_WINDOW

class FormatConverter:
    """ 格式转换器 """
    
    def __init__(self):
        self.is_cancelled = False
        self.logger = logging.getLogger(__name__)
        self.converters = {
            # 视频转换器
            ('video', 'video'): self._convert_video_to_video,
            ('video', 'audio'): self._convert_video_to_audio,
            
            # 音频转换器
            ('audio', 'audio'): self._convert_audio_to_audio,
            
            # 图片转换器
            ('image', 'image'): self._convert_image_to_image,
            
            # 文档转换器
            ('document', 'document'): self._convert_document_to_document,
            ('document', 'pdf'): self._convert_document_to_pdf,
            ('pdf', 'document'): self._convert_pdf_to_document,
            
            # 压缩文件转换器
            ('archive', 'archive'): self._convert_archive_to_archive,
        }
        
        # 文件类型映射
        self.type_map = {
            # 视频格式
            'mp4': 'video', 'avi': 'video', 'mov': 'video', 
            'flv': 'video', 'mkv': 'video', 'wmv': 'video',
            'webm': 'video', 'm4v': 'video',
            
            # 音频格式
            'mp3': 'audio', 'wav': 'audio', 'aac': 'audio',
            'flac': 'audio', 'm4a': 'audio', 'ogg': 'audio',
            'wma': 'audio', 'opus': 'audio',
            
            # 图片格式
            'jpg': 'image', 'jpeg': 'image', 'png': 'image',
            'bmp': 'image', 'gif': 'image', 'webp': 'image',
            'tiff': 'image', 'ico': 'image',
            
            # 文档格式
            'pdf': 'document',
            'docx': 'document', 'doc': 'document', 'txt': 'document',
            'rtf': 'document', 'html': 'document', 'epub': 'document',
            'mobi': 'document',
            
            # 压缩格式
            'zip': 'archive', 'rar': 'archive', '7z': 'archive',
            'tar': 'archive', 'gz': 'archive'
        }
        
    def convert(self, source_file: str, target_file: str, progress_callback: Callable[[int], None] = None) -> bool:
        """
        转换文件格式
        
        Args:
            source_file: 源文件路径
            target_file: 目标文件路径
            progress_callback: 进度回调函数，参数为进度值（0-100）
            
        Returns:
            bool: 转换是否成功
        """
        try:
            # 获取文件扩展名
            source_ext = os.path.splitext(source_file)[1][1:].lower()
            target_ext = os.path.splitext(target_file)[1][1:].lower()
            
            # 获取文件类型
            source_type = self.type_map.get(source_ext)
            target_type = self.type_map.get(target_ext)
            
            if not source_type or not target_type:
                raise ValueError(f"不支持的文件格式：{source_ext} -> {target_ext}")
            
            # 创建目标文件所在的目录
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            
            # 根据类型选择转换方法
            if source_type == 'video':
                if target_type == 'video':
                    return self._convert_video_to_video(source_file, target_file, progress_callback)
                elif target_type == 'audio':
                    return self._convert_video_to_audio(source_file, target_file, progress_callback)
            elif source_type == 'audio' and target_type == 'audio':
                return self._convert_audio_to_audio(source_file, target_file, progress_callback)
            elif source_type == 'image' and target_type == 'image':
                return self._convert_image_to_image(source_file, target_file, progress_callback)
            
            raise ValueError(f"不支持的转换类型：{source_type} -> {target_type}")
            
        except Exception as e:
            self.logger.error(f"转换失败：{e}")
            return False
            
    def _get_ffmpeg_executable(self, executable_name: str) -> str:
        """获取ffmpeg可执行文件路径"""
        try:
            # 1. 优先尝试在打包环境中查找
            if hasattr(sys, '_MEIPASS'):
                meipass_path = os.path.join(sys._MEIPASS, executable_name)
                if os.path.exists(meipass_path):
                    self.logger.info(f"在打包目录中找到 {executable_name}: {meipass_path}")
                    return meipass_path
            
            # 2. 尝试在当前目录查找
            current_dir = os.getcwd()
            current_path = os.path.join(current_dir, executable_name)
            if os.path.exists(current_path):
                self.logger.info(f"在当前目录找到 {executable_name}: {current_path}")
                return current_path
                
            # 3. 尝试在系统PATH中查找
            which_path = shutil.which(executable_name)
            if which_path:
                self.logger.info(f"在系统PATH中找到 {executable_name}: {which_path}")
                return which_path
                
            # 4. 尝试在已知位置查找
            known_paths = [
                # 标准bin子目录
                os.path.join(os.environ.get('ProgramFiles', ''), 'ffmpeg', 'bin', executable_name),
                os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'ffmpeg', 'bin', executable_name),
                os.path.join(os.path.expanduser('~'), 'ffmpeg', 'bin', executable_name),
                f'C:\\ffmpeg\\bin\\{executable_name}',
                f'D:\\ffmpeg\\bin\\{executable_name}',
                # 直接在ffmpeg根目录
                os.path.join(os.environ.get('ProgramFiles', ''), 'ffmpeg', executable_name),
                os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'ffmpeg', executable_name),
                os.path.join(os.path.expanduser('~'), 'ffmpeg', executable_name),
                f'C:\\ffmpeg\\{executable_name}',
                f'D:\\ffmpeg\\{executable_name}',
                # 保留原有目录
                f'D:\\ffmpeg-7.0.2-essentials_build\\bin\\{executable_name}'
            ]
            
            for path in known_paths:
                if os.path.exists(path):
                    self.logger.info(f"在已知位置找到 {executable_name}: {path}")
                    return path
            
            # 5. 从环境变量Path中的ffmpeg相关目录查找
            path_dirs = os.environ.get('Path', '').split(';')
            for dir_path in path_dirs:
                if 'ffmpeg' in dir_path.lower():
                    full_path = os.path.join(dir_path, executable_name)
                    if os.path.exists(full_path):
                        self.logger.info(f"在环境变量Path中找到 {executable_name}: {full_path}")
                        return full_path
                    
            # 6. 最后尝试直接使用名称
            self.logger.warning(f"未找到 {executable_name}，将尝试直接调用")
            return executable_name
            
        except Exception as e:
            self.logger.error(f"查找 {executable_name} 失败: {str(e)}")
            return executable_name
            
    def _convert_video_to_video(self, source: str, target: str, progress_callback: Callable[[int], None] = None) -> bool:
        """视频转视频"""
        try:
            self.logger.info(f"开始视频转换: {source} -> {target}")
            
            # 获取ffprobe路径
            ffprobe_path = self._get_ffmpeg_executable('ffprobe.exe')
            
            # 获取视频时长
            self.logger.debug("正在获取视频时长...")
            result = subprocess.run(
                [ffprobe_path, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', source],
                capture_output=True,
                text=True,
                encoding='utf-8',
                creationflags=flags
            )
            duration = float(result.stdout)
            self.logger.info(f"视频时长: {duration}秒")
            
            # 获取源视频信息
            self.logger.debug("正在获取源视频信息...")
            probe_cmd = [ffprobe_path, '-v', 'error', '-show_format', '-show_streams', '-print_format', 'json', source]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, encoding='utf-8', creationflags=flags)
            self.logger.debug(f"源视频信息: {probe_result.stdout}")
            
            # 获取ffmpeg路径
            ffmpeg_path = self._get_ffmpeg_executable('ffmpeg.exe')
            
            # 构建转换命令
            cmd = [
                ffmpeg_path,
                '-i', source,  # 输入文件
                '-y',  # 覆盖已存在的文件
                '-c:v', 'h264',  # 使用 H.264 编码
                '-preset', 'medium',  # 编码速度预设
                '-crf', '23',  # 视频质量参数
                '-c:a', 'aac',  # 音频编码
                '-b:a', '128k',  # 音频比特率
                '-movflags', '+faststart',  # 优化网络播放
                target  # 输出文件
            ]
            
            # 记录完整的命令
            self.logger.info(f"FFmpeg命令: {' '.join(cmd)}")
            
            # 执行转换
            self.logger.debug("开始执行转换...")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                encoding='utf-8',
                creationflags=flags
            )
            
            # 实时获取进度
            time_pattern = re.compile(r'time=(\d+):(\d+):(\d+\.\d+)')
            error_buffer = []
            while True:
                line = process.stderr.readline()
                
                if not line and process.poll() is not None:
                    # 确保在转换完成时显示100%
                    if process.returncode == 0 and progress_callback:
                        progress_callback(100)
                        self.logger.info("转换完成")
                    break
                
                # 记录FFmpeg的输出信息
                if line.strip():
                    self.logger.debug(f"FFmpeg输出: {line.strip()}")
                    error_buffer.append(line)  # 保存最近的错误信息
                    if len(error_buffer) > 50:  # 限制缓冲区大小
                        error_buffer.pop(0)
                    
                if self.is_cancelled:
                    self.logger.info("转换被用户取消")
                    process.terminate()
                    process.wait()  # 等待进程完全终止
                    # 删除未完成的输出文件
                    try:
                        if os.path.exists(target):
                            os.remove(target)
                            self.logger.debug(f"已删除未完成的输出文件: {target}")
                    except Exception as e:
                        self.logger.error(f"删除未完成文件失败: {str(e)}")
                    return False
                    
                match = time_pattern.search(line)
                if match and progress_callback:
                    h, m, s = map(float, match.groups())
                    current_time = h * 3600 + m * 60 + s
                    progress = min(int(current_time / duration * 100), 99)  # 最多显示99%，留1%给完成时
                    self.logger.debug(f"当前进度: {progress}% (时间: {current_time:.2f}s/{duration:.2f}s)")
                    if progress_callback:
                        progress_callback(progress)
            
            # 检查转换结果
            if process.returncode != 0:
                stderr_output = '\n'.join(error_buffer)
                self.logger.error(f"转换失败，FFmpeg返回码: {process.returncode}")
                self.logger.error(f"错误输出:\n{stderr_output}")
                # 如果转换失败，删除未完成的输出文件
                try:
                    if os.path.exists(target):
                        os.remove(target)
                        self.logger.debug(f"已删除失败的输出文件: {target}")
                except Exception as e:
                    self.logger.error(f"删除未完成文件失败: {str(e)}")
                    
                if stderr_output:
                    raise Exception(stderr_output)
                else:
                    raise Exception("转换过程中发生未知错误")
            
            # 验证输出文件
            self.logger.debug("正在验证输出文件...")
            if os.path.exists(target):
                file_size = os.path.getsize(target)
                self.logger.info(f"输出文件大小: {file_size/1024/1024:.2f}MB")
                if file_size == 0:
                    raise Exception("输出文件大小为0")
            else:
                raise Exception("输出文件不存在")
            
            return True
            
        except Exception as e:
            # 如果发生异常，删除未完成的输出文件
            try:
                if os.path.exists(target):
                    os.remove(target)
                    self.logger.debug(f"发生异常，已删除输出文件: {target}")
            except Exception as remove_error:
                self.logger.error(f"删除未完成文件失败: {str(remove_error)}")
                
            error_msg = str(e)
            self.logger.error(f"转换失败: {error_msg}")
            
            if "No such file or directory" in error_msg:
                raise Exception("找不到输入文件或无法创建输出文件")
            elif "Invalid data found" in error_msg:
                raise Exception("输入文件格式无效或已损坏")
            elif "Error while decoding" in error_msg:
                raise Exception("解码错误，输入文件可能已损坏")
            else:
                raise Exception(f"视频转换失败：{error_msg}")
            
    def _convert_video_to_audio(self, source: str, target: str, progress_callback: Callable[[int], None] = None) -> bool:
        """视频转音频"""
        try:
            # 获取ffprobe路径
            ffprobe_path = self._get_ffmpeg_executable('ffprobe.exe')
            
            # 获取视频时长
            result = subprocess.run(
                [ffprobe_path, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', source],
                capture_output=True,
                text=True,
                creationflags=flags
            )
            duration = float(result.stdout)
            
            # 获取ffmpeg路径
            ffmpeg_path = self._get_ffmpeg_executable('ffmpeg.exe')
            
            # 构建转换命令
            cmd = [
                ffmpeg_path,
                '-i', source,  # 输入文件
                '-vn',  # 不处理视频
                '-y',  # 覆盖已存在的文件
                target  # 输出文件
            ]
            
            # 启动转换进程
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                creationflags=flags
            )
            
            # 读取进度
            time_pattern = re.compile(r'out_time=(\d+):(\d+):(\d+\.\d+)')
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                    
                if self.is_cancelled:
                    process.terminate()
                    return False
                    
                match = time_pattern.search(line)
                if match:
                    h, m, s = map(float, match.groups())
                    current_time = h * 3600 + m * 60 + s
                    progress = min(int(current_time / duration * 100), 100)
                    if progress_callback:
                        progress_callback(progress)
            
            return process.returncode == 0
            
        except Exception as e:
            self.logger.error(f"视频转音频失败：{e}")
            return False
            
    def _convert_audio_to_audio(self, source: str, target: str, progress_callback: Callable[[int], None] = None) -> bool:
        """音频转音频"""
        try:
            # 获取ffprobe路径
            ffprobe_path = self._get_ffmpeg_executable('ffprobe.exe')
            
            # 获取音频时长
            result = subprocess.run(
                [ffprobe_path, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', source],
                capture_output=True,
                text=True,
                creationflags=flags
            )
            duration = float(result.stdout)
            
            # 获取ffmpeg路径
            ffmpeg_path = self._get_ffmpeg_executable('ffmpeg.exe')
            
            # 构建转换命令
            cmd = [
                ffmpeg_path,
                '-i', source,  # 输入文件
                '-y',  # 覆盖已存在的文件
                target  # 输出文件
            ]
            
            # 启动转换进程
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                creationflags=flags
            )
            
            # 读取进度
            time_pattern = re.compile(r'out_time=(\d+):(\d+):(\d+\.\d+)')
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                    
                if self.is_cancelled:
                    process.terminate()
                    return False
                    
                match = time_pattern.search(line)
                if match:
                    h, m, s = map(float, match.groups())
                    current_time = h * 3600 + m * 60 + s
                    progress = min(int(current_time / duration * 100), 100)
                    if progress_callback:
                        progress_callback(progress)
            
            return process.returncode == 0
            
        except Exception as e:
            self.logger.error(f"音频转换失败：{e}")
            return False
            
    def _convert_image_to_image(self, source: str, target: str, progress_callback: Callable[[int], None] = None) -> bool:
        """图片转图片"""
        try:
            # 图片转换通常很快，直接返回结果
            if progress_callback:
                progress_callback(100)
            
            # 使用PIL库进行图片转换
            with Image.open(source) as img:
                img.save(target)
                
            return True
            
        except Exception as e:
            self.logger.error(f"图片转换失败：{e}")
            return False
            
    def _convert_document_to_document(self, source: str, target: str, progress_callback: Callable[[int], None] = None) -> bool:
        try:
            # 读取源文档
            doc = Document(source)
            
            # 保存为新格式
            doc.save(target)
            
            if progress_callback:
                progress_callback(100)
            return True
            
        except Exception as e:
            self.logger.error(f"文档转换失败: {str(e)}")
            return False
            
    def _convert_document_to_pdf(self, source: str, target: str, progress_callback: Callable[[int], None] = None) -> bool:
        try:
            # 使用pdf2docx进行转换
            cv = Converter(source)
            cv.convert(target)
            cv.close()
            
            if progress_callback:
                progress_callback(100)
            return True
            
        except Exception as e:
            self.logger.error(f"文档转PDF失败: {str(e)}")
            return False
            
    def _convert_pdf_to_document(self, source: str, target: str, progress_callback: Callable[[int], None] = None) -> bool:
        try:
            # 使用pdf2docx进行转换
            cv = Converter(source)
            cv.convert(target)
            cv.close()
            
            if progress_callback:
                progress_callback(100)
            return True
            
        except Exception as e:
            self.logger.error(f"PDF转文档失败: {str(e)}")
            return False
            
    def _convert_archive_to_archive(self, source: str, target: str, progress_callback: Callable[[int], None] = None) -> bool:
        try:
            # 创建临时目录
            temp_dir = tempfile.mkdtemp(prefix='format_converter_temp_')
            
            # 解压源文件
            if source.endswith('.zip'):
                with zipfile.ZipFile(source, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            elif source.endswith(('.tar', '.gz')):
                with tarfile.open(source, 'r:*') as tar_ref:
                    tar_ref.extractall(temp_dir)
                    
            if progress_callback:
                progress_callback(50)
                
            # 压缩为目标格式
            if target.endswith('.zip'):
                with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zip_ref.write(file_path, arcname)
            elif target.endswith('.tar'):
                with tarfile.open(target, 'w') as tar_ref:
                    tar_ref.add(temp_dir, arcname='')
            elif target.endswith('.gz'):
                with tarfile.open(target, 'w:gz') as tar_ref:
                    tar_ref.add(temp_dir, arcname='')
                    
            # 清理临时目录
            shutil.rmtree(temp_dir)
            
            if progress_callback:
                progress_callback(100)
            return True
            
        except Exception as e:
            self.logger.error(f"压缩文件转换失败: {str(e)}")
            return False