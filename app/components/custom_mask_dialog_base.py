from typing import Union

from PySide6.QtCore import Qt, QPoint, QSize, QObject, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QResizeEvent
from PySide6.QtWidgets import (QWidget, QFrame, QVBoxLayout, QHBoxLayout,
                             QDialog, QGraphicsDropShadowEffect)


class MaskDialogBase(QDialog):
    """遮罩对话框基类"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._hBoxLayout = QHBoxLayout(self)
        self.windowMask = QWidget(self)
        self.widget = QFrame(self)

        # 初始化窗口
        self.initWindow()

        # 初始化布局
        self.initLayout()

        # 连接信号
        self.windowMask.installEventFilter(self)

    def initWindow(self):
        """初始化窗口"""
        self.resize(800, 600)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowModality(Qt.ApplicationModal)
        self.windowMask.setObjectName('windowMask')
        self.widget.setObjectName('widget')

    def initLayout(self):
        """初始化布局"""
        self._hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self._hBoxLayout.addWidget(self.windowMask)
        self._hBoxLayout.setSpacing(0)

        # 设置遮罩样式
        self.windowMask.setStyleSheet("""
            #windowMask {
                background-color: rgba(0, 0, 0, 76);
            }
        """)

        # 设置窗口样式
        self.widget.setStyleSheet("""
            #widget {
                background-color: white;
                border-radius: 10px;
            }
        """)

    def setShadowEffect(self, blurRadius=60, offset=(0, 10), color=QColor(0, 0, 0, 50)):
        """设置阴影效果"""
        shadowEffect = QGraphicsDropShadowEffect(self.widget)
        shadowEffect.setBlurRadius(blurRadius)
        shadowEffect.setOffset(*offset)
        shadowEffect.setColor(color)
        self.widget.setGraphicsEffect(shadowEffect)

    def setMaskColor(self, color: Union[QColor, str, Qt.GlobalColor]):
        """设置遮罩颜色"""
        self.windowMask.setStyleSheet(f"""
            #windowMask {{
                background-color: {color if isinstance(color, str) else color.name(QColor.HexArgb)};
            }}
        """)

    def setClosableOnMaskClicked(self, closable: bool):
        """设置点击遮罩是否关闭对话框"""
        self._isClosableOnMaskClicked = closable

    def isClosableOnMaskClicked(self) -> bool:
        """获取点击遮罩是否关闭对话框"""
        return self._isClosableOnMaskClicked

    def resizeEvent(self, e: QResizeEvent):
        """调整大小事件"""
        super().resizeEvent(e)
        self.windowMask.resize(self.size())
        # 将窗口居中显示
        w, h = self.widget.width(), self.widget.height()
        self.widget.move(int(self.width()/2 - w/2), int(self.height()/2 - h/2)) 