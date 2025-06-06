import sys
from PySide6.QtWidgets import QApplication, QWidget
from qfluentwidgets import FluentWindow, setTheme, Theme, FluentIcon

from app.view.add_task_interface import AddTaskDialog

class MainInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("mainInterface")

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("格式工厂")
        self.resize(900, 700)
        
        # 设置菜单按钮
        self.addSubInterface(
            interface=MainInterface(),
            icon=FluentIcon.HOME,
            text="主页",
            position=0
        )
        
        # 测试新建任务对话框
        self.dialog = AddTaskDialog(self)
        self.dialog.resize(self.size())
        self.dialog.exec()

if __name__ == '__main__':
    # 创建应用实例
    app = QApplication(sys.argv)
    
    # 设置暗色主题
    setTheme(Theme.DARK)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec()) 