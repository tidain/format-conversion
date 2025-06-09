from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from qfluentwidgets import (ScrollArea, ExpandLayout, SettingCardGroup,
                          SwitchSettingCard, ComboBoxSettingCard, PushSettingCard,
                          InfoBar, FluentIcon as FIF, InfoBarPosition, isDarkTheme)
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
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)
        
        # 设置对象名称
        self.setObjectName('settingInterface')
        self.scrollWidget.setObjectName('settingScrollWidget')
        
        # 初始化界面
        self.initUI()
        
        # 更新样式
        self.updateStyle()
        
    def initUI(self):
        """ 初始化界面 """
        self.setObjectName('settingInterface')
        
        # 创建滚动区域
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)
        
        # 设置滚动条
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 0, 0, 0)
        
        # 外观设置
        appearanceGroup = SettingCardGroup("外观", self.scrollWidget)
        
        # 主题模式
        self.themeModeCard = ComboBoxSettingCard(
            cfg.themeMode,
            FIF.BRUSH,
            "主题模式",
            "设置软件的主题模式",
            ["Light", "Dark", "System"],
            parent=appearanceGroup
        )
        
        # 背景特效
        self.backgroundEffectCard = SwitchSettingCard(
            FIF.TRANSPARENT,
            "背景特效",
            "启用或禁用背景模糊特效",
            cfg.enableBackgroundEffect,
            parent=appearanceGroup
        )
        
        appearanceGroup.addSettingCard(self.themeModeCard)
        appearanceGroup.addSettingCard(self.backgroundEffectCard)
        
        # 软件设置
        softwareGroup = SettingCardGroup("软件", self.scrollWidget)
        
        # 开机自启
        self.autoStartCard = SwitchSettingCard(
            FIF.POWER_BUTTON,
            "开机自启",
            "设置软件是否随系统启动",
            cfg.enableAutoStart,
            parent=softwareGroup
        )
        
        softwareGroup.addSettingCard(self.autoStartCard)
        
        # 添加设置组到布局
        self.expandLayout.addWidget(appearanceGroup)
        self.expandLayout.addWidget(softwareGroup)
        
        # 连接信号
        self.themeModeCard.comboBox.currentTextChanged.connect(self.onThemeModeChanged)
        self.backgroundEffectCard.switchButton.checkedChanged.connect(self.onBackgroundEffectChanged)
        self.autoStartCard.switchButton.checkedChanged.connect(self.onAutoStartChanged)
        
    def updateStyle(self):
        """更新样式"""
        self.scrollWidget.setStyleSheet("""
            QWidget#settingScrollWidget {
                background-color: """ + ('#1e1e1e' if isDarkTheme() else 'white') + """;
                border: none;
            }
            
            SettingCardGroup {
                background-color: transparent;
                border: none;
            }
            
            QLabel {
                background: transparent;
                border: none;
            }
            
            ComboBox {
                font-size: 14px;
                color: """ + ('white' if isDarkTheme() else 'black') + """;
                background: """ + ('#2b2b2b' if isDarkTheme() else '#f5f5f5') + """;
                border: 1px solid """ + ('rgba(255, 255, 255, 0.1)' if isDarkTheme() else 'rgba(0, 0, 0, 0.1)') + """;
                border-radius: 4px;
                padding: 5px;
            }
            
            ComboBox:disabled {
                color: """ + ('rgba(255, 255, 255, 0.3)' if isDarkTheme() else 'rgba(0, 0, 0, 0.3)') + """;
                background: """ + ('#1e1e1e' if isDarkTheme() else '#e0e0e0') + """;
            }
            
            SwitchButton {
                background: transparent;
                border: none;
            }
        """)
        
        self.setStyleSheet("""
            QScrollArea {
                background-color: """ + ('#1e1e1e' if isDarkTheme() else 'white') + """;
                border: none;
            }
            
            QScrollBar {
                background: """ + ('#2b2b2b' if isDarkTheme() else '#f5f5f5') + """;
                border: none;
                width: 4px;
            }
            
            QScrollBar::handle {
                background: """ + ('#666666' if isDarkTheme() else '#c0c0c0') + """;
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
        
    def onThemeModeChanged(self, value):
        """ 主题模式改变时的处理函数 """
        InfoBar.success(
            title='设置已保存',
            content="主题模式已更改",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
        self.updateStyle()
        
    def onBackgroundEffectChanged(self, value):
        """ 背景特效改变时的处理函数 """
        InfoBar.success(
            title='设置已保存',
            content="背景特效设置已更改",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
        
    def onAutoStartChanged(self, value):
        """ 开机自启改变时的处理函数 """
        InfoBar.success(
            title='设置已保存',
            content="开机自启动设置已更改",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        ) 