import sys
import os
from PyQt6.QtCore import Qt, QSize, QPoint
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout
from qfluentwidgets import (FluentIcon as FIF, 
                          setTheme, Theme, isDarkTheme,
                          NavigationItemPosition, MSFluentWindow, FluentWindow,
                          SwitchButton, ComboBox, InfoBar, InfoBarPosition)

from .task_interface import TaskInterface
from .setting_interface import SettingInterface, cfg
from .add_task_interface import AddTaskDialog
from ..resource import icons_rc
from ..common.config_manager import ThemeMode, config_manager
from ..common.theme_helper import set_theme_mode
from ..common.autostart_manager import autostart_manager


class MainWindow(FluentWindow):
    """ 主窗口 """
    
    def __init__(self):
        super().__init__()
        
        # 设置窗口标题和图标
        self.setWindowTitle('格式转换工具')
        self.setWindowIcon(QIcon(":/icons/logo.png"))
        
        # 设置窗口大小
        self.resize(1050, 750)  # 增加宽度和高度
        
        # 初始化界面
        self.taskInterface = TaskInterface(self)
        self.settingInterface = SettingInterface(self)
        
        # 添加子界面
        self.initNavigation()
        
        # 设置主题
        self.initTheme()
        
        # 居中显示
        self.moveToCenter()
        
        # 允许拖拽
        self.setAcceptDrops(True)
        
        # 连接信号
        cfg.themeMode.valueChanged.connect(self.onThemeChanged)
        
        # 设置样式
        self.updateStyle()
        
        self.init_theme_settings()
        
    def updateStyle(self):
        """ 更新样式 """
        self.setStyleSheet("""
            QMainWindow, QWidget, QStackedWidget, NavigationInterface, NavigationInterface QScrollArea, TitleBar {
                background-color: """ + ('white' if not isDarkTheme() else '#1e1e1e') + """;
            }
            
            MinimizeButton, MaximizeButton, CloseButton {
                background-color: transparent;
                border: none;
                border-radius: 0;
            }
            
            QLabel {
                color: """ + ('black' if not isDarkTheme() else 'white') + """;
                background-color: transparent;
            }
            
            QPushButton {
                padding: 8px 16px;
                font-size: 14px;
                border-radius: 4px;
                background-color: """ + ('#f0f0f0' if not isDarkTheme() else '#333333') + """;
                color: """ + ('black' if not isDarkTheme() else 'white') + """;
                border: none;
            }
            
            QPushButton:hover {
                background-color: """ + ('#e5e5e5' if not isDarkTheme() else '#404040') + """;
            }
            
            QPushButton:pressed {
                background-color: """ + ('#d9d9d9' if not isDarkTheme() else '#2b2b2b') + """;
            }
            
            QScrollArea {
                background-color: """ + ('white' if not isDarkTheme() else '#1e1e1e') + """;
                border: none;
            }
            
            QScrollArea > QWidget > QWidget {
                background-color: """ + ('white' if not isDarkTheme() else '#1e1e1e') + """;
            }
            
            QScrollBar {
                background-color: """ + ('white' if not isDarkTheme() else '#1e1e1e') + """;
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
            dialog = AddTaskDialog(self)
            dialog.resize(self.size())
            dialog.setSourceFile(files[0])
            dialog.exec()

    def init_theme_settings(self):
        """初始化主题设置"""
        # 创建主题选择下拉框
        self.theme_combobox = ComboBox()
        for theme_mode in ThemeMode:
            self.theme_combobox.addItem(theme_mode.value)
        
        # 设置当前选中的主题
        current_theme = config_manager.get_theme_mode()
        self.theme_combobox.setCurrentText(current_theme.value)
        
        # 连接信号
        self.theme_combobox.currentIndexChanged.connect(self._on_theme_changed)
        
        # 将主题选择器添加到设置页面
        settings_interface = self.findChild(QWidget, "设置")
        if settings_interface:
            layout = settings_interface.layout()
            if not layout:
                from PyQt6.QtWidgets import QVBoxLayout
                layout = QVBoxLayout(settings_interface)
            layout.addWidget(self.theme_combobox)

    def _on_theme_changed(self, index):
        """主题改变时的处理函数"""
        theme_mode = ThemeMode[ThemeMode(self.theme_combobox.currentText()).name]
        set_theme_mode(theme_mode)

    def init_autostart_settings(self):
        """初始化自启动设置"""
        # 自启动设置
        autostart_label = QLabel("开机自启动")
        autostart_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.settings_layout.addWidget(autostart_label)

        self.autostart_switch = SwitchButton()
        self.autostart_switch.setChecked(config_manager.get_autostart())
        self.autostart_switch.checkedChanged.connect(self._on_autostart_changed)
        self.settings_layout.addWidget(self.autostart_switch)

    def _on_autostart_changed(self, checked):
        """自启动设置改变时的处理函数"""
        success = autostart_manager.enable() if checked else autostart_manager.disable()
        
        if success:
            config_manager.set_autostart(checked)
            InfoBar.success(
                title='成功',
                content='自启动设置已更新',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        else:
            InfoBar.error(
                title='错误',
                content='自启动设置更新失败',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )

    def moveToCenter(self):
        """将窗口移动到屏幕中央"""
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 