import sys
import os
import subprocess
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor
from qfluentwidgets import MessageBox

from app.view.main_window import MainWindow
from app.view.ffmpeg_installer import FFmpegInstaller
from app.common.theme_helper import apply_theme

def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False

if __name__ == '__main__':
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 应用主题设置
    apply_theme()
    
    # 检查ffmpeg
    if not check_ffmpeg():
        msg = MessageBox(
            '检测到系统未安装FFmpeg',
            '是否现在安装FFmpeg？\n\n注意：安装过程可能需要几分钟，请耐心等待。',
            app.activeWindow()
        )
        if msg.exec():
            installer = FFmpegInstaller()
            installer.show()
            if not installer.exec():
                MessageBox(
                    '警告',
                    'FFmpeg不存在，可能是安装失败或系统变量配置错误。\n程序将继续运行，但部分功能可能受限。',
                    app.activeWindow()
                ).exec()
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec()) 