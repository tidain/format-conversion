from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from qfluentwidgets import (SettingCardGroup, SwitchSettingCard,
                          ComboBoxSettingCard, ScrollArea,
                          ExpandLayout, InfoBar, InfoBarPosition,
                          FluentIcon as FIF)
from qfluentwidgets.common.config import (ConfigItem, QConfig, 
                                        OptionsConfigItem, OptionsValidator)


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
        
    def initUI(self):
        """ 初始化界面 """
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 0, 0, 0)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        
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