from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt, QThread, Signal
from qfluentwidgets import PrimaryPushButton, InfoBar, InfoBarPosition
import sys
import os
import subprocess
import requests
import zipfile
import winreg

class FFmpegInstallerThread(QThread):
    progress_updated = Signal(int, str)
    installation_finished = Signal(bool, str)

    def run(self):
        try:
            # 获取系统盘
            system_drive = os.environ.get('SystemDrive', 'C:')
            ffmpeg_dir = os.path.join(system_drive, 'ffmpeg')
            
            # 创建ffmpeg目录
            os.makedirs(ffmpeg_dir, exist_ok=True)
            self.progress_updated.emit(10, "正在下载FFmpeg...")
            
            # 下载ffmpeg
            url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
            response = requests.get(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded_size = 0
            
            zip_path = os.path.join(ffmpeg_dir, "ffmpeg.zip")
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        progress = int((downloaded_size / total_size) * 50)
                        self.progress_updated.emit(10 + progress, "正在下载FFmpeg...")
            
            self.progress_updated.emit(60, "正在解压文件...")
            # 解压文件
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(ffmpeg_dir)
            
            # 删除zip文件
            os.remove(zip_path)
            
            self.progress_updated.emit(80, "正在配置系统环境变量...")
            # 获取解压后的文件夹名称
            extracted_dir = next(d for d in os.listdir(ffmpeg_dir) if d.startswith('ffmpeg'))
            bin_path = os.path.join(ffmpeg_dir, extracted_dir, 'bin')
            
            # 添加到系统环境变量
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 0, winreg.KEY_ALL_ACCESS)
            current_path = winreg.QueryValueEx(key, 'Path')[0]
            if bin_path not in current_path:
                new_path = current_path + ';' + bin_path
                winreg.SetValueEx(key, 'Path', 0, winreg.REG_EXPAND_SZ, new_path)
            winreg.CloseKey(key)
            
            # 刷新环境变量
            os.environ['Path'] = os.environ['Path'] + ';' + bin_path
            
            self.progress_updated.emit(100, "安装完成！")
            self.installation_finished.emit(True, "FFmpeg安装成功！")
            
        except Exception as e:
            self.installation_finished.emit(False, f"安装失败：{str(e)}")

class FFmpegInstaller(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.installation_success = False
        
    def setup_ui(self):
        self.setWindowTitle("FFmpeg 安装器")
        self.resize(400, 200)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        # 添加说明文本
        self.status_label = QLabel("准备安装FFmpeg...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 添加进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)
        
        # 添加安装按钮
        self.install_button = PrimaryPushButton("开始安装")
        self.install_button.clicked.connect(self.start_installation)
        layout.addWidget(self.install_button)
        
    def start_installation(self):
        self.install_button.setEnabled(False)
        self.installer_thread = FFmpegInstallerThread()
        self.installer_thread.progress_updated.connect(self.update_progress)
        self.installer_thread.installation_finished.connect(self.installation_completed)
        self.installer_thread.start()
        
    def update_progress(self, progress, status):
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)
        
    def installation_completed(self, success, message):
        self.install_button.setEnabled(True)
        self.installation_success = success
        if success:
            InfoBar.success(
                title='成功',
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            self.accept()
        else:
            InfoBar.error(
                title='错误',
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=4000,
                parent=self
            )
            
    def exec(self):
        super().exec()
        return self.installation_success 