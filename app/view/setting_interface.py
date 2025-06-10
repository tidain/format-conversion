from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QUrl
from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, 
                          ComboBoxSettingCard, PushSettingCard,
                          ScrollArea, ExpandLayout, InfoBar,
                          FluentIcon as FIF, InfoBarPosition)
from qfluentwidgets import isDarkTheme
from qfluentwidgets.common.config import (ConfigItem, QConfig, 
                                        OptionsConfigItem, OptionsValidator)

from ..common.config_manager import ThemeMode, config_manager
from ..common.theme_helper import set_theme_mode
from ..common.autostart_manager import autostart_manager


class Config:
    """ 配置类 """
    
    def __init__(self):
        self.themeMode = OptionsConfigItem(
            "Appearance",
            "ThemeMode",
            "Dark",  # 默认深色主题
            OptionsValidator(["Light", "Dark", "System"])
        )
        self.enableAutoStart = ConfigItem(
            "Software",
            "AutoStart",
            False
        )
        self.enableBackgroundEffect = ConfigItem(
            "Software",
            "BackgroundEffect",
            True
        )
        
        # 加载配置文件
        self.qconfig = QConfig()
        self.qconfig.load('config.json')
        
        # 添加配置项
        self.qconfig.themeMode = self.themeMode
        self.qconfig.enableAutoStart = self.enableAutoStart
        self.qconfig.enableBackgroundEffect = self.enableBackgroundEffect


# 创建全局配置对象
cfg = Config()


class SettingInterface(ScrollArea):
    """ 设置界面 """
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("settingInterface")
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)
        
        # 主题设置卡片
        self.themeCard = ComboBoxSettingCard(
            configItem=config_manager.theme_mode,
            icon=FIF.BRUSH,
            title='主题模式',
            content='设置应用的主题模式',
            texts=[mode.value for mode in ThemeMode],
            parent=self.scrollWidget
        )
        
        # 开机自启卡片
        self.autostartCard = SwitchSettingCard(
            icon=FIF.POWER_BUTTON,
            title="开机自启",
            content="设置是否开机自动启动",
            configItem=config_manager.autostart,
            parent=self.scrollWidget
        )
        
        # 初始化界面
        self.initWidget()
        
    def initWidget(self):
        """ 初始化界面 """
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 0, 0, 0)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        
        # 主题设置组
        self.themeGroup = SettingCardGroup(self.tr('主题设置'), self.scrollWidget)
        self.themeGroup.addSettingCard(self.themeCard)
        
        # 基本设置组
        self.basicGroup = SettingCardGroup(self.tr('基本设置'), self.scrollWidget)
        self.basicGroup.addSettingCard(self.autostartCard)
        
        # 添加组到布局
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.addWidget(self.themeGroup)
        self.expandLayout.addWidget(self.basicGroup)
        
        # 连接信号
        self.themeCard.comboBox.currentIndexChanged.connect(self.onThemeModeChanged)
        self.autostartCard.switchButton.checkedChanged.connect(self.onAutostartChanged)
        
    def onThemeModeChanged(self, index):
        """ 主题模式改变的处理函数 """
        theme_modes = [ThemeMode.LIGHT, ThemeMode.DARK, ThemeMode.SYSTEM]
        set_theme_mode(theme_modes[index])
        
    def onAutostartChanged(self, checked):
        """ 开机自启设置改变的处理函数 """
        try:
            if checked:
                autostart_manager.enable_autostart()
            else:
                autostart_manager.disable_autostart()
        except Exception as e:
            InfoBar.error(
                title='错误',
                content=str(e),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        
    def updateStyle(self):
        """更新样式"""
        self.scrollWidget.setStyleSheet("""
            QWidget {
                background-color: """ + ('white' if not isDarkTheme() else '#1e1e1e') + """;
            }
            
            SettingCardGroup {
                background-color: transparent;
                border: none;
            }
            
            QLabel {
                background: transparent;
                border: none;
                color: """ + ('black' if not isDarkTheme() else 'white') + """;
            }
            
            ComboBox {
                font-size: 14px;
                color: """ + ('black' if not isDarkTheme() else 'white') + """;
                background: """ + ('white' if not isDarkTheme() else '#2b2b2b') + """;
                border: 1px solid """ + ('#e5e5e5' if not isDarkTheme() else '#333333') + """;
                border-radius: 4px;
                padding: 5px;
            }
            
            ComboBox:hover {
                background: """ + ('#f5f5f5' if not isDarkTheme() else '#333333') + """;
            }
            
            ComboBox:disabled {
                color: """ + ('rgba(0, 0, 0, 0.3)' if not isDarkTheme() else 'rgba(255, 255, 255, 0.3)') + """;
                background: """ + ('#f0f0f0' if not isDarkTheme() else '#1e1e1e') + """;
            }
            
            SwitchButton {
                background: transparent;
                border: none;
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
                border: none;
                width: 4px;
            }
            
            QScrollBar::handle {
                background: """ + ('#c0c0c0' if not isDarkTheme() else '#666666') + """;
                border: none;
                border-radius: 2px;
                min-height: 32px;
            }
            
            QScrollBar::add-line, QScrollBar::sub-line {
                background: none;
                border: none;
            }
            
            QScrollBar::add-page, QScrollBar::sub-page {
                background: none;
                border: none;
            }
        """) 