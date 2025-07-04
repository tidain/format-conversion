import sys
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QMessageBox, QPushButton, QApplication
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from qfluentwidgets import PrimaryPushButton, InfoBar, InfoBarPosition
import os
import requests
import zipfile
import shutil
import glob
import winreg
import ctypes

class FFmpegInstallerThread(QThread):
    progress_updated = Signal(int, str)
    installation_finished = Signal(bool, str)

    def run(self):
        try:
            # 获取系统盘
            system_drive = os.environ.get('SystemDrive', 'C:')
            # 确保路径分隔符正确
            if system_drive.endswith(':'):
                ffmpeg_dir = os.environ.get('FFmpegDir', f"{system_drive}\\ffmpeg")
            else:
                ffmpeg_dir = os.environ.get('FFmpegDir', os.path.join(system_drive, 'ffmpeg'))
            self.progress_updated.emit(5, f"准备安装目录: {ffmpeg_dir}")
            
            # 确保安装目录存在
            try:
                os.makedirs(ffmpeg_dir, exist_ok=True)
            except Exception as e:
                self.progress_updated.emit(5, f"创建目录失败: {str(e)}，尝试使用用户目录")
                # 如果无法在系统盘创建目录，尝试在用户目录创建
                user_home = os.path.expanduser('~')
                # 确保用户目录路径正确
                if user_home.endswith(':'):
                    ffmpeg_dir = f"{user_home}\\ffmpeg"
                else:
                    ffmpeg_dir = os.path.join(user_home, 'ffmpeg')
                os.makedirs(ffmpeg_dir, exist_ok=True)
            self.progress_updated.emit(10, "正在下载FFmpeg...")
            url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
            try:
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
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(ffmpeg_dir)
                os.remove(zip_path)
                # 自动查找bin目录或ffmpeg.exe所在目录
                bin_path = None
                for root, dirs, files in os.walk(ffmpeg_dir):
                    if 'bin' in dirs:
                        bin_path = os.path.join(root, 'bin')
                        break
                if not bin_path:
                    # 没有bin目录，找ffmpeg.exe
                    ffmpeg_exe_path = None
                    for root, dirs, files in os.walk(ffmpeg_dir):
                        if 'ffmpeg.exe' in files:
                            ffmpeg_exe_path = os.path.join(root, 'ffmpeg.exe')
                            break
                    if not ffmpeg_exe_path:
                        raise Exception('解压后未找到ffmpeg.exe')
                    bin_path = os.path.dirname(ffmpeg_exe_path)
            except Exception as e:
                self.progress_updated.emit(20, f"下载失败，尝试使用本地zip: {e}")
                app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                local_zips = glob.glob(os.path.join(app_dir, '*.zip'))
                if not local_zips:
                    raise Exception('未找到本地zip文件')
                
                self.progress_updated.emit(30, f"正在解压本地zip: {os.path.basename(local_zips[0])}")
                try:
                    with zipfile.ZipFile(local_zips[0], 'r') as zip_ref:
                        zip_ref.extractall(ffmpeg_dir)
                    self.progress_updated.emit(40, "解压完成，正在查找ffmpeg.exe")
                    
                    # 自动查找ffmpeg.exe所在目录
                    ffmpeg_exe_path = None
                    for root, dirs, files in os.walk(ffmpeg_dir):
                        if 'ffmpeg.exe' in files:
                            ffmpeg_exe_path = os.path.join(root, 'ffmpeg.exe')
                            self.progress_updated.emit(50, f"找到ffmpeg.exe: {ffmpeg_exe_path}")
                            break
                    
                    if not ffmpeg_exe_path:
                        # 列出解压后的文件结构，帮助诊断
                        files_list = []
                        for root, dirs, files in os.walk(ffmpeg_dir):
                            for file in files:
                                files_list.append(os.path.join(root, file))
                        raise Exception(f'解压后未找到ffmpeg.exe。解压目录内容: {", ".join(files_list[:5])}{"..." if len(files_list) > 5 else ""}')
                    
                    bin_path = os.path.dirname(ffmpeg_exe_path)
                    if not os.path.exists(bin_path):
                        raise Exception(f'找到的bin目录不存在: {bin_path}')
                    
                    self.progress_updated.emit(60, f"本地zip解压完成，找到可执行文件目录: {bin_path}")
                except Exception as local_zip_error:
                    raise Exception(f"处理本地zip文件失败: {str(local_zip_error)}")
            self.progress_updated.emit(80, "正在配置环境变量...")
            # 写入用户环境变量（HKEY_CURRENT_USER）
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Environment', 0, winreg.KEY_SET_VALUE | winreg.KEY_READ)
                try:
                    current_path = winreg.QueryValueEx(key, 'Path')[0]
                    self.progress_updated.emit(85, f"读取到当前Path: {current_path[:20]}...")
                except FileNotFoundError:
                    current_path = ''
                    self.progress_updated.emit(85, "未找到现有Path，将创建新Path")
                
                # 确保bin_path存在且有效
                if not bin_path or not os.path.exists(bin_path):
                    raise Exception(f"无效的可执行文件路径: {bin_path}")
                
                self.progress_updated.emit(90, f"准备添加路径: {bin_path}")
                if bin_path not in current_path:
                    # 确保路径分隔符是正确的Windows风格
                    if '/' in bin_path:
                        bin_path = bin_path.replace('/', '\\')
                        
                    new_path = current_path + ';' + bin_path if current_path else bin_path
                    winreg.SetValueEx(key, 'Path', 0, winreg.REG_EXPAND_SZ, new_path)
                    self.progress_updated.emit(95, "成功写入环境变量")
                else:
                    self.progress_updated.emit(95, "路径已存在，无需添加")
                winreg.CloseKey(key)
                
                # 更新当前进程环境变量
                if bin_path not in os.environ.get('Path', ''):
                    os.environ['Path'] = os.environ.get('Path', '') + ';' + bin_path
            except Exception as e:
                self.progress_updated.emit(90, f"配置环境变量时出错: {str(e)}")
                raise Exception(f"配置环境变量失败: {str(e)}")
            self.progress_updated.emit(100, "安装完成！")
            self.installation_finished.emit(True, "FFmpeg安装成功！")
        except Exception as e:
            self.installation_finished.emit(False, f"安装失败：{str(e)}")

class FFmpegInstaller(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(420, 220)
        self.setWindowTitle("FFmpeg 自动安装")
        try:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        except AttributeError:
            pass
        self.installation_success = False
        self.setup_ui()
        QTimer.singleShot(100, self.start_installation)
        QTimer.singleShot(200, self.bring_to_front)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        try:
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        except AttributeError:
            layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(24)
        # 标题
        title = QLabel("FFmpeg 自动安装")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0078d4; margin-bottom: 8px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter if hasattr(Qt, 'AlignmentFlag') else Qt.AlignCenter)
        layout.addWidget(title)
        # 说明
        self.status_label = QLabel("正在准备自动安装FFmpeg，请稍候...")
        try:
            self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        except AttributeError:
            self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; color: #444; margin-bottom: 8px;")
        layout.addWidget(self.status_label)
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setStyleSheet("QProgressBar {height: 18px; border-radius: 9px;} QProgressBar::chunk {background-color: #0078d4; border-radius: 9px;}")
        layout.addWidget(self.progress_bar)

    def start_installation(self):
        self.installer_thread = FFmpegInstallerThread()
        self.installer_thread.progress_updated.connect(self.update_progress)
        self.installer_thread.installation_finished.connect(self.installation_completed)
        self.installer_thread.start()

    def update_progress(self, progress, status):
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)

    def installation_completed(self, success, message):
        self.installation_success = success
        import sys, os
        from PySide6.QtCore import QTimer
        
        # 倒计时功能
        self.countdown_seconds = 5 if success else 10
        self.countdown_timer = QTimer(self)
        
        def update_countdown():
            self.countdown_seconds -= 1
            if success:
                self.status_label.setText(f"安装成功！ffmpeg安装窗口将在 {self.countdown_seconds} 秒后自动退出...")
            else:
                self.status_label.setText(f"安装失败！ffmpeg安装窗口将在 {self.countdown_seconds} 秒后自动退出...")
            
            if self.countdown_seconds <= 0:
                self.countdown_timer.stop()
                self.close()  # 只关闭安装窗口
        
        # 开始倒计时
        self.countdown_timer.timeout.connect(update_countdown)
        self.countdown_timer.start(1000)  # 每秒触发一次
                
        if success:
            # 更新状态标签
            self.status_label.setText(f"安装成功！ffmpeg安装窗口将在 {self.countdown_seconds} 秒后自动退出...")
            self.status_label.setStyleSheet("font-size: 14px; color: #4caf50; margin-bottom: 8px;")
            # InfoBar 只显示"安装完成"，3秒后自动消失
            InfoBar.success(
                title='成功',
                content='FFmpeg安装成功！',
                orient=Qt.Orientation.Horizontal if hasattr(Qt, 'Orientation') else Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        else:
            # 更新状态标签
            self.status_label.setText(f"安装失败！ffmpeg安装窗口将在 {self.countdown_seconds} 秒后自动退出...")
            self.status_label.setStyleSheet("font-size: 14px; color: #f44336; margin-bottom: 8px;")
            
            bar = InfoBar.error(
                title='错误',
                content=message,
                orient=Qt.Orientation.Horizontal if hasattr(Qt, 'Orientation') else Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=10000,
                parent=self
            )
            btn = QPushButton('点击复制')
            btn.setStyleSheet('color: #888; font-size: 12px; background: transparent; border: none;')
            btn.setFont(QApplication.font())
            def on_copy():
                QApplication.clipboard().setText(str(message))
                btn.setText('已复制')
                btn.setStyleSheet('color: #4caf50; font-size: 12px; background: transparent; border: none;')
                InfoBar.success(
                    title='成功',
                    content='复制成功',
                    orient=Qt.Orientation.Horizontal if hasattr(Qt, 'Orientation') else Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=1500,
                    parent=self
                )
                QTimer.singleShot(1000, lambda: (btn.setText('点击复制'), btn.setStyleSheet('color: #888; font-size: 12px; background: transparent; border: none;')))
            btn.clicked.connect(on_copy)
            bar.layout().addWidget(btn)

    def exec(self):
        super().exec()
        return self.installation_success

    def bring_to_front(self):
        self.show()
        self.raise_()
        self.activateWindow()
        
    def closeEvent(self, event):
        """确保关闭窗口时正确清理资源"""
        if hasattr(self, 'installer_thread') and self.installer_thread.isRunning():
            self.installer_thread.terminate()
            self.installer_thread.wait()
        super().closeEvent(event)