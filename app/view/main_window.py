import sys
import os
from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from qfluentwidgets import (FluentIcon as FIF, 
                          setTheme, Theme, isDarkTheme,
                          NavigationItemPosition, MSFluentWindow, FluentWindow)

from .task_interface import TaskInterface
from .setting_interface import SettingInterface, cfg
from .add_task_interface import AddTaskDialog
from ..resource import icons_rc


class MainWindow(FluentWindow):
    """ 主窗口 """
    
    def __init__(self):
        super().__init__()
        
        # 设置窗口属性
        self.setWindowTitle("格式转换工具")
        self.resize(960, 780)
        self.setWindowIcon(QIcon(":/icons/logo.png"))
        
        # 创建子界面
        self.taskInterface = TaskInterface(self)
        self.settingInterface = SettingInterface(self)
        
        # 初始化导航栏
        self.initNavigation()
        
        # 设置主题
        self.initTheme()
        
        # 允许拖拽
        self.setAcceptDrops(True)
        
        # 连接信号
        cfg.themeMode.valueChanged.connect(self.onThemeChanged)
        
        # 设置样式
        self.updateStyle()
        
    def updateStyle(self):
        """ 更新样式 """
        self.setStyleSheet("""
            QMainWindow {
                background-color: """ + ('#1e1e1e' if isDarkTheme() else 'white') + """;
            }
            
            QWidget {
                background-color: """ + ('#1e1e1e' if isDarkTheme() else 'white') + """;
            }
            
            QStackedWidget {
                background-color: """ + ('#1e1e1e' if isDarkTheme() else 'white') + """;
            }
            
            NavigationInterface {
                background-color: """ + ('#1e1e1e' if isDarkTheme() else 'white') + """;
            }
            
            NavigationInterface QScrollArea {
                background-color: """ + ('#1e1e1e' if isDarkTheme() else 'white') + """;
            }
            
            MinimizeButton {
                background-color: transparent;
                border: none;
                border-radius: 0;
            }
            
            MaximizeButton {
                background-color: transparent;
                border: none;
                border-radius: 0;
            }
            
            CloseButton {
                background-color: transparent;
                border: none;
                border-radius: 0;
            }
            
            TitleBar {
                background-color: """ + ('#1e1e1e' if isDarkTheme() else 'white') + """;
            }
            
            QLabel {
                color: """ + ('white' if isDarkTheme() else 'black') + """;
            }
        """)
        
        # 更新子界面样式
        self.taskInterface.updateStyle()
        
    def initNavigation(self):
        """ 初始化导航栏 """
        self.addSubInterface(self.taskInterface, FIF.HOME, "任务列表")
        self.addSubInterface(self.settingInterface, FIF.SETTING, "设置")
        
    def initTheme(self):
        """ 初始化主题 """
        theme = cfg.themeMode.value
        if theme == "Light":
            setTheme(Theme.LIGHT)
        elif theme == "Dark":
            setTheme(Theme.DARK)
        else:  # System
            if isDarkTheme():
                setTheme(Theme.DARK)
            else:
                setTheme(Theme.LIGHT)
        
        # 更新样式
        self.updateStyle()
        
    def onThemeChanged(self, theme):
        """ 主题改变时的处理函数 """
        if theme == "Light":
            setTheme(Theme.LIGHT)
        elif theme == "Dark":
            setTheme(Theme.DARK)
        else:  # System
            if isDarkTheme():
                setTheme(Theme.DARK)
            else:
                setTheme(Theme.LIGHT)
        
        # 更新样式
        self.updateStyle()
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        if files:
            # 显示新建任务对话框
            AddTaskDialog.showDialog(files[0], self)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 