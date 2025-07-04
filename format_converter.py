import sys
import os
import subprocess
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor
from PySide6.QtCore import QThread, Signal, QTimer
from qfluentwidgets import MessageBox

from app.view.main_window import MainWindow
from app.view.ffmpeg_installer import FFmpegInstaller
from app.common.theme_helper import apply_theme

# 配置日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

flags = 0
if sys.platform == "win32":
    import subprocess
    flags = subprocess.CREATE_NO_WINDOW

class FFmpegCheckThread(QThread):
    ffmpeg_missing = Signal()

    def run(self):
        try:
            # 尝试直接运行ffmpeg命令
            try:
                subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=flags)
                return  # FFmpeg 可用，不发出信号
            except FileNotFoundError:
                pass
            
            # 如果直接运行失败，尝试在常见位置查找
            ffmpeg_paths = [
                r"C:\ffmpeg\ffmpeg.exe",  # 直接在ffmpeg根目录下
                r"C:\ffmpeg\bin\ffmpeg.exe",
                os.path.join(os.path.expanduser('~'), 'ffmpeg', 'ffmpeg.exe'),
                os.path.join(os.path.expanduser('~'), 'ffmpeg', 'bin', 'ffmpeg.exe'),
                r"D:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe"  # 保留原有目录
            ]
            
            for path in ffmpeg_paths:
                if os.path.exists(path):
                    subprocess.run([path, '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=flags)
                    return  # FFmpeg 可用，不发出信号
            
            # 从PATH环境变量中查找
            path_dirs = os.environ.get('Path', '').split(';')
            for dir_path in path_dirs:
                if 'ffmpeg' in dir_path.lower():
                    # 检查目录下是否有ffmpeg.exe
                    ffmpeg_exe = os.path.join(dir_path, 'ffmpeg.exe')
                    if os.path.exists(ffmpeg_exe):
                        subprocess.run([ffmpeg_exe, '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=flags)
                        return  # FFmpeg 可用，不发出信号
            
            # 都找不到，报告不可用
            self.ffmpeg_missing.emit()
            
        except Exception:
            # 出现任何异常，认为FFmpeg不可用
            self.ffmpeg_missing.emit()

if __name__ == '__main__':
    try:
        logging.info('应用程序启动')
        
        # 1. 创建应用程序实例
        app = QApplication(sys.argv)
        logging.info('QApplication创建成功')
        
        # 2. 创建并显示主窗口（必须最先做，保证"秒开"）
        window = MainWindow()
        window.show()
        logging.info('主窗口创建并显示成功')

        # 3. 主题设置异步（主窗口显示后再设置）
        def async_apply_theme():
            try:
                apply_theme()
                logging.info('主题设置成功')
            except Exception as e:
                logging.error(f'主题设置失败: {str(e)}')
        QTimer.singleShot(0, async_apply_theme)

        # 4. 后台线程检查ffmpeg（主窗口显示后再检查）
        def on_ffmpeg_missing():
            msg = MessageBox(
                '检测到系统未安装FFmpeg',
                '是否现在安装FFmpeg？\n\n注意：安装过程可能需要几分钟，请耐心等待。',
                window
            )
            if msg.exec():
                # 启动安装器
                installer = FFmpegInstaller(window)
                installer.exec()  # 使用模态对话框，确保安装完成后再继续
                
                # 检查安装结果
                if installer.installation_success:
                    # 安装成功
                    pass
                else:
                    # 安装失败，显示警告
                    MessageBox(
                        '警告',
                        'FFmpeg安装失败。\n程序将继续运行，但部分功能可能受限。',
                        window
                    ).exec()
        def start_ffmpeg_check():
            window.ffmpeg_thread = FFmpegCheckThread()
            window.ffmpeg_thread.ffmpeg_missing.connect(on_ffmpeg_missing)
            window.ffmpeg_thread.start()
        QTimer.singleShot(0, start_ffmpeg_check)

        # 5. 给主窗口加closeEvent，安全退出线程
        from PySide6.QtWidgets import QMainWindow
        old_closeEvent = window.closeEvent if hasattr(window, 'closeEvent') else None
        def new_closeEvent(self, event):
            if hasattr(self, 'ffmpeg_thread') and self.ffmpeg_thread.isRunning():
                self.ffmpeg_thread.quit()
                self.ffmpeg_thread.wait()
            if old_closeEvent:
                old_closeEvent(event)
            else:
                super(QMainWindow, self).closeEvent(event)
        import types
        window.closeEvent = types.MethodType(new_closeEvent, window)

        # 6. 运行应用程序
        sys.exit(app.exec())
        
    except Exception as e:
        logging.critical(f'程序发生致命错误: {str(e)}', exc_info=True)
        # 显示错误对话框
        if 'app' in locals():
            from PySide6.QtWidgets import QPushButton
            from qfluentwidgets import InfoBar, InfoBarPosition
            from PySide6.QtCore import Qt
            
            # 创建错误提示窗口
            error_msg = str(e)
            msg_box = MessageBox(
                '错误',
                f'程序启动失败: {error_msg}',
                None
            )
            
            # 在MessageBox中添加"点击复制"按钮
            copy_btn = QPushButton('点击复制错误信息')
            copy_btn.setStyleSheet('color: #888; font-size: 12px; background: transparent; border: none;')
            
            def on_copy():
                QApplication.clipboard().setText(error_msg)
                copy_btn.setText('已复制')
                copy_btn.setStyleSheet('color: #4caf50; font-size: 12px; background: transparent; border: none;')
                # 显示复制成功提示
                if hasattr(msg_box, 'parent') and msg_box.parent():
                    InfoBar.success(
                        title='成功',
                        content='错误信息已复制到剪贴板',
                        orient=Qt.Orientation.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=1500,
                        parent=msg_box.parent()
                    )
                # 1秒后恢复按钮状态
                QTimer.singleShot(1000, lambda: (
                    copy_btn.setText('点击复制错误信息'),
                    copy_btn.setStyleSheet('color: #888; font-size: 12px; background: transparent; border: none;')
                ))
                
            copy_btn.clicked.connect(on_copy)
            msg_box.addButton(copy_btn, MessageBox.ButtonRole.ActionRole)
            msg_box.exec()
        sys.exit(1) 