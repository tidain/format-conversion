import sys
import os
import shutil
import tempfile
import logging
from PySide6.QtWidgets import QApplication, QMessageBox
from app.view.main_window import MainWindow
from app.view.ffmpeg_installer import FFmpegInstaller
from app.common.theme_helper import apply_theme

# 配置日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def setup_ffmpeg():
    """确保ffmpeg可用"""
    try:
        # 检查是否在Pyfuze打包环境中
        if hasattr(sys, '_MEIPASS'):
            # 创建临时目录存放ffmpeg
            temp_dir = tempfile.mkdtemp(prefix='format_converter_ffmpeg_')
            
            # 复制ffmpeg到临时目录
            ffmpeg_path = os.path.join(sys._MEIPASS, 'ffmpeg.exe')
            ffprobe_path = os.path.join(sys._MEIPASS, 'ffprobe.exe')
            
            if os.path.exists(ffmpeg_path):
                shutil.copy(ffmpeg_path, temp_dir)
            if os.path.exists(ffprobe_path):
                shutil.copy(ffprobe_path, temp_dir)
                
            # 添加到系统PATH
            os.environ['PATH'] = f"{temp_dir};{os.environ['PATH']}"
            logging.info(f"FFmpeg设置成功，临时目录: {temp_dir}")
            return True
            
        # 检查系统PATH中是否已有ffmpeg
        if shutil.which('ffmpeg') and shutil.which('ffprobe'):
            logging.info("检测到系统PATH中已有FFmpeg")
            return True
            
        return False
        
    except Exception as e:
        logging.error(f"设置ffmpeg失败: {str(e)}")
        return False

def check_ffmpeg():
    """检查ffmpeg是否可用"""
    try:
        # 先尝试ffmpeg
        if not shutil.which('ffmpeg'):
            logging.warning("未检测到FFmpeg")
            return False
            
        # 再尝试ffprobe
        if not shutil.which('ffprobe'):
            logging.warning("未检测到FFprobe")
            return False
            
        return True
    except Exception as e:
        logging.error(f"检查FFmpeg失败: {str(e)}")
        return False

if __name__ == '__main__':
    try:
        logging.info('应用程序启动')
        setup_ffmpeg()
        app = QApplication(sys.argv)
        logging.info('QApplication创建成功')
        try:
            apply_theme()
            logging.info('主题设置成功')
        except Exception as e:
            logging.error(f'主题设置失败: {str(e)}')
        if not check_ffmpeg():
            logging.warning('未检测到FFmpeg')
            from qfluentwidgets import MessageBox
            msg = MessageBox(
                '警告',
                '未检测到FFmpeg，部分功能可能受限。\n请确保系统中已安装FFmpeg并添加到PATH环境变量。',
                None
            )
            msg.exec()
        try:
            main_window = MainWindow()
            logging.info('主窗口创建成功')
            main_window.show()
            logging.info('主窗口显示成功')
        except Exception as e:
            logging.error(f'主窗口创建或显示失败: {str(e)}')
            raise
        sys.exit(app.exec())
    except Exception as e:
        logging.critical(f'程序发生致命错误: {str(e)}', exc_info=True)
        if 'app' in locals():
            from qfluentwidgets import MessageBox
            from PySide6.QtWidgets import QPushButton
            from PySide6.QtCore import QTimer
            error_msg = str(e)
            msg_box = MessageBox(
                '错误',
                f'程序启动失败: {error_msg}',
                None
            )
            copy_btn = QPushButton('点击复制错误信息')
            copy_btn.setStyleSheet('color: #888; font-size: 12px; background: transparent; border: none;')
            def on_copy():
                app.clipboard().setText(error_msg)
                copy_btn.setText('已复制')
                copy_btn.setStyleSheet('color: #4caf50; font-size: 12px; background: transparent; border: none;')
                QTimer.singleShot(1000, lambda: (
                    copy_btn.setText('点击复制错误信息'),
                    copy_btn.setStyleSheet('color: #888; font-size: 12px; background: transparent; border: none;')
                ))
            copy_btn.clicked.connect(on_copy)
            msg_box.addButton(copy_btn, MessageBox.ButtonRole.ActionRole)
            msg_box.exec()
        sys.exit(1)