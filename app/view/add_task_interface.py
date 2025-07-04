import os
from PySide6.QtCore import Qt, Signal, QPoint, QPropertyAnimation, QSize
from PySide6.QtGui import QColor, QMouseEvent
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QLabel, QFileDialog, QFrame, QWidget,
                             QGraphicsDropShadowEffect, QGraphicsOpacityEffect)
from qfluentwidgets import (FluentIcon as FIF,
                          ComboBox, PushButton,
                          InfoBar, InfoBarPosition,
                          isDarkTheme, FluentStyleSheet,
                          RadioButton, LineEdit,
                          SubtitleLabel)

from app.core.format_mapping import get_target_formats
from ..core.converter import FormatConverter

class CustomTitleBar(QWidget):
    """自定义标题栏"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(48)
        self.setObjectName("customTitleBar")
        
        # 布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(8)
        
        # 标题
        self.title_label = QLabel("新建转换任务", self)
        self.title_label.setObjectName("titleLabel")
        layout.addWidget(self.title_label)
        
        # 设置样式
        # self.setStyleSheet("""
        #     QWidget#customTitleBar {
        #         background-color: """ + ('#2b2b2b' if isDarkTheme() else '#f5f5f5') + """;
        #         border-top-left-radius: 8px;
        #         border-top-right-radius: 8px;
        #     }
        #     QLabel#titleLabel {
        #         font-size: 16px;
        #         font-weight: bold;
        #         color: """ + ('white' if isDarkTheme() else 'black') + """;
        #     }
        # """)

class AddTaskDialog(QDialog):
    """新建转换任务对话框"""
    
    taskCreated = Signal(str, str)  # 发送源文件路径和目标文件路径
    _instance = None
    _initialized = False
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.source_file = None
        self.target_file = None
        
        # 设置无边框窗口
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(480, 550)  # 稍微增加高度
        
        # 设置模态
        self.setModal(True)
        
        # 创建遮罩
        self.windowMask = QWidget(self)
        self.windowMask.resize(self.size())
        
        # 创建中心窗口部件
        self.centerWidget = QFrame(self)
        self.centerWidget.setObjectName("centerWidget")
        self.centerWidget.setFixedSize(460, 530)  # 稍微缩小中心部件，预留边距
        self.centerWidget.setGeometry((self.width() - self.centerWidget.width()) // 2,
                                     (self.height() - self.centerWidget.height()) // 2,
                                     self.centerWidget.width(), 
                                     self.centerWidget.height())
        
        # 设置阴影效果
        self.setShadowEffect()
        
        self.setup_ui()
        self.updateStyle()
        
    def setShadowEffect(self, blurRadius=60, offset=(0, 10), color=QColor(0, 0, 0, 50)):
        """设置阴影效果"""
        shadowEffect = QGraphicsDropShadowEffect(self.centerWidget)
        shadowEffect.setBlurRadius(blurRadius)
        shadowEffect.setOffset(*offset)
        shadowEffect.setColor(color)
        self.centerWidget.setGraphicsEffect(shadowEffect)
        
    def setup_ui(self):
        """初始化界面"""
        # 设置对话框属性
        self.setObjectName("addTaskDialog")
        self.resize(480, 420)
        
        # 设置主布局
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 设置中心窗口布局
        self.center_layout = QVBoxLayout(self.centerWidget)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        self.center_layout.setSpacing(0)
        
        # 添加自定义标题栏
        self.title_bar = CustomTitleBar(self.centerWidget)
        self.center_layout.addWidget(self.title_bar)
        
        # 创建内容容器
        self.content_widget = QWidget(self.centerWidget)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(24, 24, 24, 24)
        self.content_layout.setSpacing(16)
        
        # 添加文件选择区域
        self.fileGroup = QWidget(self.content_widget)
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
        
        self.content_layout.addWidget(self.fileGroup)
        
        # 添加格式选择区域
        self.formatGroup = QWidget(self.content_widget)
        self.formatLayout = QVBoxLayout(self.formatGroup)
        self.formatLayout.setContentsMargins(0, 0, 0, 0)
        self.formatLayout.setSpacing(8)
        
        self.formatLabel = QLabel("目标格式", self.formatGroup)
        self.formatLayout.addWidget(self.formatLabel)
        
        self.formatComboBox = ComboBox(self.formatGroup)
        self.formatComboBox.setPlaceholderText("请先选择源文件")
        self.formatComboBox.setEnabled(False)
        self.formatLayout.addWidget(self.formatComboBox)
        
        self.content_layout.addWidget(self.formatGroup)
        
        # 添加保存位置选择区域
        self.saveGroup = QWidget(self.content_widget)
        self.saveLayout = QVBoxLayout(self.saveGroup)
        self.saveLayout.setContentsMargins(0, 0, 0, 0)
        self.saveLayout.setSpacing(8)
        
        self.saveLabel = QLabel("保存位置", self.saveGroup)
        self.saveLayout.addWidget(self.saveLabel)
        
        # 保存位置选项
        self.saveButtonLayout = QVBoxLayout()
        self.saveButtonLayout.setContentsMargins(0, 0, 0, 0)
        self.saveButtonLayout.setSpacing(8)
        
        # 与源文件相同选项
        self.sameAsSourceButton = RadioButton("与源文件相同", self.saveGroup)
        self.sameAsSourceButton.setChecked(True)
        self.saveButtonLayout.addWidget(self.sameAsSourceButton)
        
        # 自定义位置选项
        self.customLocationButton = RadioButton("自定义位置", self.saveGroup)
        self.saveButtonLayout.addWidget(self.customLocationButton)
        
        # 自定义位置选择按钮
        self.customLocationWidget = QWidget(self.saveGroup)
        self.customLocationLayout = QHBoxLayout(self.customLocationWidget)
        self.customLocationLayout.setContentsMargins(20, 0, 0, 0)  # 左侧缩进
        self.customLocationLayout.setSpacing(8)
        
        self.browseButton = PushButton("浏览...", self.customLocationWidget)
        self.browseButton.clicked.connect(self.selectSaveLocation)
        self.browseButton.setEnabled(False)
        self.customLocationLayout.addWidget(self.browseButton)
        
        self.saveButtonLayout.addWidget(self.customLocationWidget)
        
        self.saveLayout.addLayout(self.saveButtonLayout)
        
        # 保存路径显示
        self.savePathLabel = QLabel(self.saveGroup)
        self.savePathLabel.setWordWrap(True)
        self.saveLayout.addWidget(self.savePathLabel)
        
        self.content_layout.addWidget(self.saveGroup)
        
        self.content_layout.addStretch()
        
        # 添加底部按钮
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonLayout.setSpacing(8)
        
        self.cancelButton = PushButton("取消", self.content_widget)
        self.cancelButton.clicked.connect(self.reject)
        self.buttonLayout.addWidget(self.cancelButton)
        
        self.confirmButton = PushButton("开始转换", self.content_widget)
        self.confirmButton.setEnabled(False)
        self.confirmButton.clicked.connect(self.createTask)
        self.buttonLayout.addWidget(self.confirmButton)
        
        self.content_layout.addLayout(self.buttonLayout)
        
        # 添加内容容器到中心窗口
        self.center_layout.addWidget(self.content_widget)
        
        # 将中心窗口添加到主布局
        self.main_layout.addWidget(self.centerWidget)
        
        # 连接信号
        self.sameAsSourceButton.toggled.connect(self._on_save_location_changed)
        self.customLocationButton.toggled.connect(self._on_save_location_changed)
        self.formatComboBox.currentTextChanged.connect(self.updateConfirmButton)
        self.confirmButton.clicked.disconnect()  # 断开之前的连接
        self.confirmButton.clicked.connect(self.createTask)
        
    def _findMainWindow(self):
        # 递归查找顶层 QMainWindow
        parent = self.parentWidget()
        from PySide6.QtWidgets import QMainWindow, QApplication
        while parent and not isinstance(parent, QMainWindow):
            parent = parent.parentWidget()
        if parent is None:
            # 兜底用 activeWindow
            parent = QApplication.activeWindow()
        return parent

    def _addMask(self):
        from PySide6.QtWidgets import QApplication, QWidget
        from PySide6.QtCore import Qt, QPropertyAnimation
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        mainWin = self._findMainWindow()
        if mainWin is not None and not hasattr(self, '_maskWidget'):
            self._maskWidget = QWidget(mainWin)
            self._maskWidget.setObjectName('_dialogMask')
            self._maskWidget.setStyleSheet('background: rgba(0,0,0,0.32);')
            self._maskWidget.setAttribute(Qt.WA_TransparentForMouseEvents)
            self._maskWidget.setGeometry(mainWin.rect())
            # 设置淡入效果
            opacity = QGraphicsOpacityEffect(self._maskWidget)
            self._maskWidget.setGraphicsEffect(opacity)
            self._maskWidget.show()
            self._maskWidget.raise_()
            mainWin.installEventFilter(self)
            # 动画
            self._maskAni = QPropertyAnimation(opacity, b'opacity', self)
            self._maskAni.setDuration(200)
            self._maskAni.setStartValue(0)
            self._maskAni.setEndValue(1)
            self._maskAni.start()

    def _removeMask(self):
        from PySide6.QtCore import QPropertyAnimation
        mainWin = self._findMainWindow()
        if hasattr(self, '_maskWidget'):
            if self._maskWidget is not None:
                # 淡出动画
                opacity = self._maskWidget.graphicsEffect()
                if opacity:
                    ani = QPropertyAnimation(opacity, b'opacity', self)
                    ani.setDuration(200)
                    ani.setStartValue(opacity.opacity())
                    ani.setEndValue(0)
                    def cleanup():
                        self._maskWidget.hide()
                        self._maskWidget.deleteLater()
                        if mainWin:
                            mainWin.removeEventFilter(self)
                        del self._maskWidget
                    ani.finished.connect(cleanup)
                    ani.start()
                    return
                self._maskWidget.hide()
                self._maskWidget.deleteLater()
            if mainWin:
                mainWin.removeEventFilter(self)
            if hasattr(self, '_maskWidget'):
                del self._maskWidget

    def _updateMaskGeometry(self):
        mainWin = self._findMainWindow()
        if hasattr(self, '_maskWidget') and mainWin:
            self._maskWidget.setGeometry(mainWin.rect())

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if obj == self._findMainWindow() and event.type() == QEvent.Resize:
            self._updateMaskGeometry()
        return super().eventFilter(obj, event)
        
    def showEvent(self, e):
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        from PySide6.QtCore import QPropertyAnimation
        self.setWindowModality(Qt.ApplicationModal)
        self._addMask()
        # 只对 centerWidget 做淡入
        self._dlg_opacity = QGraphicsOpacityEffect(self.centerWidget)
        self.centerWidget.setGraphicsEffect(self._dlg_opacity)
        self._dlg_opacity.setOpacity(0)
        self._dlg_ani = QPropertyAnimation(self._dlg_opacity, b'opacity', self)
        self._dlg_ani.setDuration(200)
        self._dlg_ani.setStartValue(0)
        self._dlg_ani.setEndValue(1)
        self._dlg_ani.start()
        super().showEvent(e)
        
    def _fadeOutAndClose(self, close_type='close'):
        from PySide6.QtCore import QPropertyAnimation
        if hasattr(self, '_dlg_opacity') and self._dlg_opacity:
            ani = QPropertyAnimation(self._dlg_opacity, b'opacity', self)
            ani.setDuration(200)
            ani.setStartValue(self._dlg_opacity.opacity())
            ani.setEndValue(0)
            def do_close():
                if close_type == 'accept':
                    super(AddTaskDialog, self).accept()
                elif close_type == 'reject':
                    super(AddTaskDialog, self).reject()
                else:
                    super(AddTaskDialog, self).close()
            ani.finished.connect(do_close)
            ani.start()
        else:
            if close_type == 'accept':
                super().accept()
            elif close_type == 'reject':
                super().reject()
            else:
                super().close()
            
    def closeEvent(self, event):
        self._removeMask()
        self._fadeOutAndClose('close')
        event.ignore()  # 动画结束后再真正关闭

    def accept(self):
        self._removeMask()
        self._fadeOutAndClose('accept')

    def reject(self):
        self._removeMask()
        self._fadeOutAndClose('reject')
        
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
            if self.sameAsSourceButton.isChecked():
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
            
    def _on_save_location_changed(self, checked):
        """保存位置选项改变时的处理"""
        if self.sameAsSourceButton.isChecked():
            self.browseButton.setEnabled(False)
            if self.source_file:
                self.useSameLocation()
        else:
            self.browseButton.setEnabled(True)
            if not self.savePathLabel.text():
                self.savePathLabel.setText("请选择保存位置")
        
        self.updateConfirmButton()
        
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
        has_save_path = (
            (self.sameAsSourceButton.isChecked() and self.source_file) or
            (self.customLocationButton.isChecked() and self.savePathLabel.text() != "请选择保存位置")
        )
        
        self.confirmButton.setEnabled(
            bool(self.source_file) and
            bool(self.formatComboBox.currentText()) and
            has_save_path and
            not self.formatComboBox.currentText().startswith('---')
        ) 
        
    def createTask(self):
        """创建转换任务"""
        if not self.source_file:
            return
            
        # 获取目标格式
        target_format = self.formatComboBox.currentText().lower()
        if not target_format or target_format.startswith('---'):
            return
            
        # 获取保存路径
        if self.sameAsSourceButton.isChecked():
            save_dir = os.path.dirname(self.source_file)
        else:
            save_dir = self.savePathLabel.text()
            if not save_dir or save_dir == "请选择保存位置":
                return
                
        # 构建目标文件路径
        source_name = os.path.splitext(os.path.basename(self.source_file))[0]
        self.target_file = os.path.join(save_dir, f"{source_name}.{target_format}")
        
        # 发送信号
        self.taskCreated.emit(self.source_file, self.target_file)
        
        # 关闭对话框
        self.accept() 

    def updateStyle(self):
        # 让中心窗口和内容区背景色与主菜单栏一致，四个角都是圆角
        radius = "12px"
        if isDarkTheme():
            self.centerWidget.setStyleSheet(f"""
                QFrame#centerWidget {{
                    background-color: #232323; 
                    border-radius: {radius};
                }}
            """)
            self.content_widget.setStyleSheet(f"""
                background-color: #232323;
                border-bottom-left-radius: {radius};
                border-bottom-right-radius: {radius};
            """)
            self.title_bar.setStyleSheet(f"""
                background-color: #232323;
                border-top-left-radius: {radius};
                border-top-right-radius: {radius};
            """)
            self.title_bar.title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        else:
            self.centerWidget.setStyleSheet(f"""
                QFrame#centerWidget {{
                    background-color: #f5f5f5; 
                    border-radius: {radius};
                }}
            """)
            self.content_widget.setStyleSheet(f"""
                background-color: #f5f5f5;
                border-bottom-left-radius: {radius};
                border-bottom-right-radius: {radius};
            """)
            self.title_bar.setStyleSheet(f"""
                background-color: #f5f5f5;
                border-top-left-radius: {radius};
                border-top-right-radius: {radius};
            """)
            self.title_bar.title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: black;")
            
        # 设置窗口背景透明，以便显示圆角
        self.setAttribute(Qt.WA_TranslucentBackground) 