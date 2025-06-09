import os
import ffmpeg
from PIL import Image
from docx import Document
from pdf2docx import Converter
from openpyxl import load_workbook
import zipfile
import tarfile
import subprocess
from typing import Callable, Dict, Tuple, List
import time
import threading
import re


class FormatConverter:
    """ 格式转换器 """
    
    def __init__(self):
        self.is_cancelled = False
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
            print(f"转换失败：{e}")
            return False
            
    def _convert_video_to_video(self, source: str, target: str, progress_callback: Callable[[int], None] = None) -> bool:
        """视频转视频"""
        try:
            # 获取视频时长
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', source],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            duration = float(result.stdout)
            
            # 构建转换命令
            cmd = [
                'ffmpeg',
                '-i', source,  # 输入文件
                '-y',  # 覆盖已存在的文件
                '-c:v', 'libx264',  # 使用 H.264 编码
                '-preset', 'medium',  # 编码速度预设
                '-crf', '23',  # 视频质量参数
                '-c:a', 'aac',  # 音频编码
                '-b:a', '128k',  # 音频比特率
                '-movflags', '+faststart',  # 优化网络播放
                target  # 输出文件
            ]
            
            # 执行转换
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                encoding='utf-8'
            )
            
            # 实时获取进度
            time_pattern = re.compile(r'time=(\d+):(\d+):(\d+\.\d+)')
            while True:
                line = process.stderr.readline()
                
                if not line and process.poll() is not None:
                    # 确保在转换完成时显示100%
                    if process.returncode == 0 and progress_callback:
                        progress_callback(100)
                    break
                    
                if self.is_cancelled:
                    process.terminate()
                    process.wait()  # 等待进程完全终止
                    # 删除未完成的输出文件
                    try:
                        if os.path.exists(target):
                            os.remove(target)
                    except Exception as e:
                        print(f"删除未完成文件失败: {str(e)}")
                    return False
                    
                match = time_pattern.search(line)
                if match and progress_callback:
                    h, m, s = map(float, match.groups())
                    current_time = h * 3600 + m * 60 + s
                    progress = min(int(current_time / duration * 100), 99)  # 最多显示99%，留1%给完成时
                    progress_callback(progress)
            
            # 检查转换结果
            if process.returncode != 0:
                stderr_output = process.stderr.read()
                # 如果转换失败，删除未完成的输出文件
                try:
                    if os.path.exists(target):
                        os.remove(target)
                except Exception as e:
                    print(f"删除未完成文件失败: {str(e)}")
                    
                if stderr_output:
                    raise Exception(stderr_output)
                else:
                    raise Exception("转换过程中发生未知错误")
            
            return True
            
        except Exception as e:
            # 如果发生异常，删除未完成的输出文件
            try:
                if os.path.exists(target):
                    os.remove(target)
            except Exception as remove_error:
                print(f"删除未完成文件失败: {str(remove_error)}")
                
            error_msg = str(e)
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
            # 获取视频时长
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', source],
                capture_output=True,
                text=True
            )
            duration = float(result.stdout)
            
            # 构建转换命令
            cmd = [
                'ffmpeg',
                '-i', source,  # 输入文件
                '-vn',  # 不处理视频
                '-y',  # 覆盖已存在的文件
                '-progress', 'pipe:1',  # 输出进度信息
                '-nostats',  # 不输出统计信息
                target  # 输出文件
            ]
            
            # 启动转换进程
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
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
            print(f"视频转音频失败：{e}")
            return False
            
    def _convert_audio_to_audio(self, source: str, target: str, progress_callback: Callable[[int], None] = None) -> bool:
        """音频转音频"""
        try:
            # 获取音频时长
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', source],
                capture_output=True,
                text=True
            )
            duration = float(result.stdout)
            
            # 构建转换命令
            cmd = [
                'ffmpeg',
                '-i', source,  # 输入文件
                '-y',  # 覆盖已存在的文件
                '-progress', 'pipe:1',  # 输出进度信息
                '-nostats',  # 不输出统计信息
                target  # 输出文件
            ]
            
            # 启动转换进程
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
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
            print(f"音频转换失败：{e}")
            return False
            
    def _convert_image_to_image(self, source: str, target: str, progress_callback: Callable[[int], None] = None) -> bool:
        """图片转图片"""
        try:
            # 构建转换命令
            cmd = [
                'ffmpeg',
                '-i', source,  # 输入文件
                '-y',  # 覆盖已存在的文件
                target  # 输出文件
            ]
            
            # 启动转换进程
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            # 图片转换通常很快，直接返回结果
            if progress_callback:
                progress_callback(100)
            
            return process.returncode == 0
            
        except Exception as e:
            print(f"图片转换失败：{e}")
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
            raise Exception(f"文档转换失败: {str(e)}")
            
    def _convert_document_to_pdf(self, source: str, target: str, progress_callback: Callable[[int], None] = None) -> bool:
        try:
            # 使用 LibreOffice 进行转换
            process = subprocess.Popen([
                'soffice',
                '--headless',
                '--convert-to',
                'pdf',
                '--outdir',
                os.path.dirname(target),
                source
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            process.wait()
            
            if progress_callback:
                progress_callback(100)
            return process.returncode == 0
            
        except Exception as e:
            raise Exception(f"文档转PDF失败: {str(e)}")
            
    def _convert_pdf_to_document(self, source: str, target: str, progress_callback: Callable[[int], None] = None) -> bool:
        try:
            # 创建转换器
            cv = Converter(source)
            
            # 转换为Word
            cv.convert(target)
            
            # 关闭转换器
            cv.close()
            
            if progress_callback:
                progress_callback(100)
            return True
            
        except Exception as e:
            raise Exception(f"PDF转文档失败: {str(e)}")
            
    def _convert_archive_to_archive(self, source: str, target: str, progress_callback: Callable[[int], None] = None) -> bool:
        try:
            # 创建临时目录
            temp_dir = os.path.join(os.path.dirname(target), "_temp_extract")
            os.makedirs(temp_dir, exist_ok=True)
            
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
            for root, dirs, files in os.walk(temp_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(temp_dir)
            
            if progress_callback:
                progress_callback(100)
            return True
            
        except Exception as e:
            raise Exception(f"压缩文件转换失败: {str(e)}") 