import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor
from qfluentwidgets import setThemeColor

from app.view.main_window import MainWindow

if __name__ == '__main__':
    # 创建应用
    app = QApplication(sys.argv)
    
    # 设置主题颜色
    setThemeColor('#0078d4')  # 使用 Windows 11 默认主题蓝
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec()) 