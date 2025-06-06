import os
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from qfluentwidgets import (FluentIcon as FIF,
                          ScrollArea, ProgressBar,
                          PushButton, InfoBar,
                          InfoBarPosition, ExpandLayout,
                          BodyLabel, isDarkTheme)

from ..core.converter import FormatConverter
from .add_task_interface import AddTaskDialog


class ConvertTask(QThread):
    progressUpdated = Signal(int)
    completed = Signal()
    error = Signal(str)
    
    def __init__(self, source_file, target_file):
        super().__init__()
        self.source_file = source_file
        self.target_file = target_file
        self.is_cancelled = False
        self.converter = FormatConverter()
        
    def run(self):
        try:
            # 执行转换
            success = self.converter.convert(
                self.source_file,
                self.target_file,
                self.progressUpdated.emit
            )
            
            if success and not self.is_cancelled:
                self.completed.emit()
            elif not success and not self.is_cancelled:
                self.error.emit("转换失败")
                
        except Exception as e:
            if not self.is_cancelled:
                self.error.emit(str(e))
            
    def cancel(self):
        self.is_cancelled = True
        self.converter.is_cancelled = True


class TaskCard(QWidget):
    def __init__(self, source_file, target_file, parent=None):
        super().__init__(parent)
        self.source_file = source_file
        self.target_file = target_file
        
        # 创建转换任务
        self.task = ConvertTask(source_file, target_file)
        self.task.progressUpdated.connect(self.updateProgress)
        self.task.completed.connect(self.onCompleted)
        self.task.error.connect(self.onError)
        
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # 文件信息
        infoLayout = QHBoxLayout()
        
        # 源文件名
        sourceLabel = QLabel(os.path.basename(self.source_file))
        infoLayout.addWidget(sourceLabel)
        
        # 箭头
        arrowLabel = QLabel("→")
        infoLayout.addWidget(arrowLabel)
        
        # 目标文件名
        targetLabel = QLabel(os.path.basename(self.target_file))
        infoLayout.addWidget(targetLabel)
        
        infoLayout.addStretch()
        
        # 取消按钮
        self.cancelButton = PushButton("取消", self)
        self.cancelButton.setIcon(FIF.CANCEL)
        self.cancelButton.clicked.connect(self.cancelTask)
        infoLayout.addWidget(self.cancelButton)
        
        layout.addLayout(infoLayout)
        
        # 进度条
        self.progressBar = ProgressBar(self)
        self.progressBar.setValue(0)
        layout.addWidget(self.progressBar)
        
        # 开始转换
        self.task.start()
        
    def updateProgress(self, value):
        self.progressBar.setValue(value)
        
    def onCompleted(self):
        self.cancelButton.setText("完成")
        self.cancelButton.setIcon(FIF.COMPLETED)
        self.cancelButton.setEnabled(False)
        InfoBar.success(
            title='转换完成',
            content=f"文件已保存到: {self.target_file}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
        
    def onError(self, error_msg):
        self.cancelButton.setText("失败")
        self.cancelButton.setIcon(FIF.CANCEL)
        self.cancelButton.setEnabled(False)
        InfoBar.error(
            title='转换失败',
            content=error_msg,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
        
    def cancelTask(self):
        self.task.cancel()
        self.cancelButton.setText("已取消")
        self.cancelButton.setEnabled(False)
        InfoBar.warning(
            title='已取消',
            content="转换任务已取消",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )


class TaskInterface(ScrollArea):
    """任务列表界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("taskInterface")
        self.scrollWidget = QWidget()
        self.scrollWidget.setObjectName("scrollWidget")
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        
        # 设置布局属性
        self.vBoxLayout.setContentsMargins(36, 18, 36, 18)
        self.vBoxLayout.setSpacing(18)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 添加标题区域
        self.headerWidget = QWidget(self)
        self.headerLayout = QVBoxLayout(self.headerWidget)
        self.headerLayout.setContentsMargins(0, 0, 0, 0)
        self.headerLayout.setSpacing(8)
        
        # 标题和按钮布局
        self.titleButtonLayout = QHBoxLayout()
        self.titleButtonLayout.setContentsMargins(0, 0, 0, 0)
        self.titleButtonLayout.setSpacing(16)
        
        # 添加标题
        self.titleLabel = QLabel("任务列表", self)
        self.titleLabel.setObjectName("taskTitleLabel")
        self.titleButtonLayout.addWidget(self.titleLabel)
        
        # 添加新建任务按钮
        self.addTaskButton = PushButton("新建任务", self)
        self.addTaskButton.setIcon(FIF.ADD)
        self.addTaskButton.clicked.connect(self.showAddTaskDialog)
        self.titleButtonLayout.addWidget(self.addTaskButton)
        
        self.titleButtonLayout.addStretch()
        self.headerLayout.addLayout(self.titleButtonLayout)
        
        # 添加提示文本
        self.descriptionLabel = BodyLabel(
            "在这里管理您的转换任务。您可以添加、删除和查看任务的进度。", self)
        self.headerLayout.addWidget(self.descriptionLabel)
        
        # 添加分隔线
        self.separator = QFrame(self)
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Sunken)
        self.headerLayout.addWidget(self.separator)
        
        self.vBoxLayout.addWidget(self.headerWidget)
        
        # 设置滚动区域
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        
        # 设置样式
        self.updateStyle()
        
    def updateStyle(self):
        """更新样式"""
        self.scrollWidget.setStyleSheet("""
            QWidget {
                background-color: """ + ('#1e1e1e' if isDarkTheme() else 'white') + """;
            }
        """)
        
        self.setStyleSheet("""
            QScrollArea {
                background-color: """ + ('#1e1e1e' if isDarkTheme() else 'white') + """;
                border: none;
            }
            
            QLabel#taskTitleLabel {
                font-size: 28px;
                font-weight: bold;
                color: """ + ('white' if isDarkTheme() else 'black') + """;
                background-color: transparent;
            }
            
            BodyLabel {
                font-size: 14px;
                color: """ + ('white' if isDarkTheme() else 'black') + """;
                background-color: transparent;
            }
            
            QFrame {
                border: 1px solid """ + ('#333333' if isDarkTheme() else '#e0e0e0') + """;
                background-color: transparent;
            }
        """)
        
    def showAddTaskDialog(self):
        """显示新建任务对话框"""
        AddTaskDialog.showDialog(parent=self)
        
    def addConvertTask(self, source_file, target_file):
        """添加转换任务"""
        task_card = TaskCard(source_file, target_file, self.scrollWidget)
        self.vBoxLayout.addWidget(task_card) 