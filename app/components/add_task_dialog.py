from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
from qfluentwidgets import (FluentIcon as FIF, 
                          SubtitleLabel, LineEdit, PushButton,
                          ComboBox, InfoBar, InfoBarPosition,
                          SettingCardGroup, PushSettingCard,
                          RangeSettingCard, RangeConfigItem,
                          RangeValidator, TextEdit,
                          MessageBox)
from pathlib import Path
import os

class AddTaskDialog(MessageBox):
    """ 新建任务对话框 """
    
    def __init__(self, parent=None):
        super().__init__(
            title="新建任务",
            content="",
            parent=parent
        )
        
        # 创建主要部件
        self.widget = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.widget)
        
        # 创建输入区域
        self.urlEdit = TextEdit(self)
        self.urlEdit.setPlaceholderText("请输入或粘贴文件链接")
        self.urlEdit.setFixedHeight(100)
        
        # 创建设置组
        self.settingGroup = SettingCardGroup("下载设置", self)
        
        # 下载目录设置
        self.downloadFolderCard = PushSettingCard(
            "选择目录",
            FIF.FOLDER,
            "下载目录",
            "选择文件保存位置",
            parent=self.settingGroup
        )
        
        # 下载线程数设置
        self.blockNumCard = RangeSettingCard(
            RangeConfigItem("Download", "BlockNum", 8, RangeValidator(1, 32)),
            FIF.SPEED_HIGH,
            "下载线程数",
            "设置同时下载的线程数，建议不超过 16",
            parent=self.settingGroup
        )
        
        # 添加设置卡片
        self.settingGroup.addSettingCards([self.downloadFolderCard, self.blockNumCard])
        
        # 添加所有组件到主布局
        self.vBoxLayout.addWidget(self.urlEdit)
        self.vBoxLayout.addWidget(self.settingGroup)
        self.vBoxLayout.setSpacing(20)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        
        # 添加主部件到对话框
        self.textLayout.addWidget(self.widget)
        
        # 设置默认下载目录
        self.downloadFolderCard.setContent(str(Path.home() / "Downloads"))
        
        # 设置按钮文本
        self.yesButton.setText("开始下载")
        self.yesButton.setIcon(FIF.DOWNLOAD)
        self.cancelButton.setText("取消")
        
        # 连接信号
        self.downloadFolderCard.clicked.connect(self.__onDownloadFolderCardClicked)
        
    def __onDownloadFolderCardClicked(self):
        """ 选择下载目录 """
        folder = QFileDialog.getExistingDirectory(
            self, "选择下载目录", 
            self.downloadFolderCard.contentLabel.text()
        )
        if not folder or self.downloadFolderCard.contentLabel.text() == folder:
            return
            
        self.downloadFolderCard.setContent(folder)
        
    def getDownloadInfo(self):
        """ 获取下载信息 """
        return {
            'url': self.urlEdit.toPlainText().strip(),
            'path': self.downloadFolderCard.contentLabel.text(),
            'threads': self.blockNumCard.configItem.value
        } 