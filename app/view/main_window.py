import sys
import os
import logging
from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout
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


def get_resource_path(relative_path):
    """获取资源文件的绝对路径"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 创建临时文件夹，将路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class MainWindow(FluentWindow):
    """ 主窗口 """
    
    def __init__(self):
        try:
            super().__init__()
            
            # 设置窗口标题
            self.setWindowTitle('格式转换工具')
            
            # 尝试设置图标
            try:
                # 首先尝试从 Qt 资源系统加载
                self.setWindowIcon(QIcon(":/icons/logo.png"))
            except Exception as e:
                logging.warning(f"从Qt资源系统加载图标失败: {str(e)}")
                try:
                    # 尝试从文件系统加载
                    icon_path = get_resource_path(os.path.join("app", "resource", "logo.png"))
                    if os.path.exists(icon_path):
                        self.setWindowIcon(QIcon(icon_path))
                    else:
                        logging.warning(f"图标文件不存在: {icon_path}")
                except Exception as e:
                    logging.warning(f"从文件系统加载图标失败: {str(e)}")
            
            # 设置窗口大小
            self.resize(1050, 750)
            
            # 初始化界面
            try:
                self.taskInterface = TaskInterface(self)
                self.settingInterface = SettingInterface(self)
            except Exception as e:
                logging.error(f"初始化界面失败: {str(e)}")
                raise
            
            # 添加子界面
            self.initNavigation()
            
            # 设置主题
            try:
                self.initTheme()
            except Exception as e:
                logging.warning(f"设置主题失败: {str(e)}")
                setTheme(Theme.LIGHT)  # 使用默认主题作为后备
            
            # 居中显示
            self.moveToCenter()
            
            # 允许拖拽
            self.setAcceptDrops(True)
            
            # 连接信号
            cfg.themeMode.valueChanged.connect(self.onThemeChanged)
            
            # 设置样式
            self.updateStyle()
            
            # 初始化主题设置
            try:
                self.init_theme_settings()
            except Exception as e:
                logging.warning(f"初始化主题设置失败: {str(e)}")
                
        except Exception as e:
            logging.critical(f"主窗口初始化失败: {str(e)}", exc_info=True)
            raise
        
    def updateStyle(self):
        """ 更新样式 """
        # 更新所有子界面样式
        for i in range(self.stackedWidget.count()):
            widget = self.stackedWidget.widget(i)
            if hasattr(widget, 'updateStyle'):
                widget.updateStyle()
        
    def initNavigation(self):
        """ 初始化导航栏 """
        self.addSubInterface(self.taskInterface, FIF.HOME, "任务列表")
        self.addSubInterface(self.settingInterface, FIF.SETTING, "设置")
        # 不连接信号，依赖 FluentWindow 中已有的 onNavigationItemChanged 回调
        
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
            dialog = AddTaskDialog(parent=self)
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
                from PySide6.QtWidgets import QVBoxLayout
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

    def onNavigationItemChanged(self, index: int, previous: int):
        """页面切换时更新样式"""
        widget = self.stackedWidget.widget(index)
        if hasattr(widget, 'updateStyle'):
            widget.updateStyle()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 