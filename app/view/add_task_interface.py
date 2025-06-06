import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog
from qfluentwidgets import (FluentIcon as FIF,
                          ComboBox, PushButton,
                          InfoBar, InfoBarPosition,
                          isDarkTheme, FluentStyleSheet)

from ..core.format_mapping import get_target_formats
from ..components.custom_mask_dialog_base import MaskDialogBase


class AddTaskDialog(MaskDialogBase):
    """新建任务对话框"""
    
    _instance = None
    _initialized = False
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.source_file = None
        
        # 设置对话框属性
        self.widget.setObjectName("addTaskDialog")
        self.widget.resize(480, 420)
        
        # 设置布局
        self.vBoxLayout = QVBoxLayout(self.widget)
        self.vBoxLayout.setContentsMargins(24, 24, 24, 24)
        self.vBoxLayout.setSpacing(16)
        
        # 添加标题
        self.titleLabel = QLabel("新建转换任务", self.widget)
        self.titleLabel.setObjectName("dialogTitleLabel")
        self.vBoxLayout.addWidget(self.titleLabel)
        
        # 添加文件选择区域
        self.fileGroup = QWidget(self.widget)
        self.fileLayout = QVBoxLayout(self.fileGroup)
        self.fileLayout.setContentsMargins(0, 0, 0, 0)
        self.fileLayout.setSpacing(8)
        
        # 文件选择按钮
        self.fileButtonLayout = QHBoxLayout()
        self.fileButtonLayout.setContentsMargins(0, 0, 0, 0)
        self.fileButtonLayout.setSpacing(8)
        
        self.selectFileButton = PushButton("选择文件", self.fileGroup)
        self.selectFileButton.setIcon(FIF.FOLDER)
        self.selectFileButton.clicked.connect(self.selectFile)
        self.fileButtonLayout.addWidget(self.selectFileButton)
        
        self.fileButtonLayout.addStretch()
        self.fileLayout.addLayout(self.fileButtonLayout)
        
        # 文件路径显示
        self.filePathLabel = QLabel(self.fileGroup)
        self.filePathLabel.setWordWrap(True)
        self.fileLayout.addWidget(self.filePathLabel)
        
        self.vBoxLayout.addWidget(self.fileGroup)
        
        # 添加格式选择区域
        self.formatGroup = QWidget(self.widget)
        self.formatLayout = QVBoxLayout(self.formatGroup)
        self.formatLayout.setContentsMargins(0, 0, 0, 0)
        self.formatLayout.setSpacing(8)
        
        self.formatLabel = QLabel("目标格式", self.formatGroup)
        self.formatLayout.addWidget(self.formatLabel)
        
        self.formatComboBox = ComboBox(self.formatGroup)
        self.formatComboBox.setPlaceholderText("请先选择源文件")
        self.formatComboBox.setEnabled(False)
        self.formatLayout.addWidget(self.formatComboBox)
        
        self.vBoxLayout.addWidget(self.formatGroup)
        
        # 添加保存位置选择区域
        self.saveGroup = QWidget(self.widget)
        self.saveLayout = QVBoxLayout(self.saveGroup)
        self.saveLayout.setContentsMargins(0, 0, 0, 0)
        self.saveLayout.setSpacing(8)
        
        self.saveLabel = QLabel("保存位置", self.saveGroup)
        self.saveLayout.addWidget(self.saveLabel)
        
        self.saveButtonLayout = QHBoxLayout()
        self.saveButtonLayout.setContentsMargins(0, 0, 0, 0)
        self.saveButtonLayout.setSpacing(8)
        
        self.sameAsSourceButton = PushButton("与源文件相同", self.saveGroup)
        self.sameAsSourceButton.clicked.connect(self.useSameLocation)
        self.saveButtonLayout.addWidget(self.sameAsSourceButton)
        
        self.customLocationButton = PushButton("自定义位置", self.saveGroup)
        self.customLocationButton.clicked.connect(self.selectSaveLocation)
        self.saveButtonLayout.addWidget(self.customLocationButton)
        
        self.saveLayout.addLayout(self.saveButtonLayout)
        
        self.savePathLabel = QLabel(self.saveGroup)
        self.savePathLabel.setWordWrap(True)
        self.saveLayout.addWidget(self.savePathLabel)
        
        self.vBoxLayout.addWidget(self.saveGroup)
        
        self.vBoxLayout.addStretch()
        
        # 添加底部按钮
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonLayout.setSpacing(8)
        
        self.cancelButton = PushButton("取消", self.widget)
        self.cancelButton.clicked.connect(self.close)
        self.buttonLayout.addWidget(self.cancelButton)
        
        self.confirmButton = PushButton("开始转换", self.widget)
        self.confirmButton.setEnabled(False)
        self.confirmButton.clicked.connect(self.startConvert)
        self.buttonLayout.addWidget(self.confirmButton)
        
        self.vBoxLayout.addLayout(self.buttonLayout)
        
        # 设置样式
        self.setShadowEffect(60, (0, 10), QColor(0, 0, 0, 50))
        self.setMaskColor(QColor(0, 0, 0, 76))
        self.setClosableOnMaskClicked(True)
        
        FluentStyleSheet.DIALOG.apply(self.widget)
        self.updateStyle()
        
    def updateStyle(self):
        """更新样式"""
        self.widget.setStyleSheet("""
            QWidget {
                background-color: """ + ('#1e1e1e' if isDarkTheme() else 'white') + """;
            }
            
            QLabel#dialogTitleLabel {
                font-size: 24px;
                font-weight: bold;
                color: """ + ('white' if isDarkTheme() else 'black') + """;
                background-color: transparent;
            }
            
            QLabel {
                font-size: 14px;
                color: """ + ('white' if isDarkTheme() else 'black') + """;
                background-color: transparent;
            }
        """)
        
    @classmethod
    def showDialog(cls, source_file=None, parent=None):
        """显示对话框"""
        if cls._initialized:
            if source_file:
                cls._instance.setSourceFile(source_file)
            cls._instance.exec()
        else:
            cls._instance = cls(parent)
            cls._initialized = True
            if source_file:
                cls._instance.setSourceFile(source_file)
            cls._instance.exec()
            
    def closeEvent(self, event):
        """关闭事件"""
        self.__class__._initialized = False
        self.__class__._instance = None
        super().closeEvent(event)
        
    def setSourceFile(self, file_path):
        """设置源文件"""
        if not os.path.isfile(file_path):
            return
            
        self.source_file = file_path
        self.filePathLabel.setText(file_path)
        
        # 更新格式选择
        ext = os.path.splitext(file_path)[1][1:]
        format_groups = get_target_formats(ext)
        
        if format_groups:
            self.formatComboBox.clear()
            
            for category, formats in format_groups.items():
                self.formatComboBox.addItem(f"---{category}---")
                
                for fmt in formats:
                    self.formatComboBox.addItem(fmt.upper())
            self.formatComboBox.setEnabled(True)
            
            # 设置默认保存位置
            self.useSameLocation()
        else:
            InfoBar.error(
                title='错误',
                content="不支持的文件格式",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            self.formatComboBox.setEnabled(False)
            self.confirmButton.setEnabled(False)
            
    def selectFile(self):
        """选择源文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择文件",
            os.path.expanduser("~"),
            "所有文件 (*.*)"
        )
        
        if file_path:
            self.setSourceFile(file_path)
            
    def useSameLocation(self):
        """使用相同位置保存"""
        if not self.source_file:
            return
            
        dir_path = os.path.dirname(self.source_file)
        self.savePathLabel.setText(dir_path)
        self.updateConfirmButton()
        
    def selectSaveLocation(self):
        """选择保存位置"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择保存位置",
            os.path.expanduser("~")
        )
        
        if dir_path:
            self.savePathLabel.setText(dir_path)
            self.updateConfirmButton()
            
    def updateConfirmButton(self):
        """更新确认按钮状态"""
        self.confirmButton.setEnabled(
            bool(self.source_file) and
            bool(self.formatComboBox.currentText()) and
            not "---" in self.formatComboBox.currentText() and
            bool(self.savePathLabel.text())
        )
        
    def startConvert(self):
        """开始转换"""
        if not self.source_file:
            return
            
        target_format = self.formatComboBox.currentText()
        if not target_format or "---" in target_format:
            return
            
        # 构建目标文件路径
        file_name = os.path.splitext(os.path.basename(self.source_file))[0]
        save_path = os.path.join(
            self.savePathLabel.text(),
            f"{file_name}.{target_format.lower()}"
        )
        
        # 添加转换任务
        self.parent().addConvertTask(self.source_file, save_path)
        self.close() 