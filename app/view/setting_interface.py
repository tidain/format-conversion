from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QApplication
from PySide6.QtCore import Qt, QUrl, QThread, Signal
from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, 
                          ComboBoxSettingCard, PushSettingCard,
                          ScrollArea, ExpandLayout, InfoBar,
                          FluentIcon as FIF, InfoBarPosition, MessageBox)
from qfluentwidgets import isDarkTheme
from qfluentwidgets.common.config import (ConfigItem, QConfig, 
                                        OptionsConfigItem, OptionsValidator)

from ..common.config_manager import ThemeMode, config_manager
from ..common.theme_helper import set_theme_mode
from ..common.autostart_manager import autostart_manager
from app.view.ffmpeg_installer import FFmpegInstaller
import subprocess
import sys
import os
import shutil
import winreg
from typing import List


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


class FFmpegCheckThread(QThread):
    check_finished = Signal(bool)
    
    def run(self):
        try:
            flags = 0
            if sys.platform == "win32":
                import subprocess
                flags = subprocess.CREATE_NO_WINDOW
            
            # 尝试直接运行ffmpeg命令
            try:
                subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=flags)
                self.check_finished.emit(True)
                return
            except FileNotFoundError:
                pass
            
            # 如果直接运行失败，尝试在常见位置查找
            ffmpeg_paths = [
                r"C:\ffmpeg\ffmpeg.exe",  # 直接在ffmpeg根目录下
                r"C:\ffmpeg\bin\ffmpeg.exe",
                os.path.join(os.path.expanduser('~'), 'ffmpeg', 'ffmpeg.exe'),
                os.path.join(os.path.expanduser('~'), 'ffmpeg', 'bin', 'ffmpeg.exe'),
                r"D:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe"  # 保留原有目录
            ]
            
            for path in ffmpeg_paths:
                if os.path.exists(path):
                    subprocess.run([path, '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=flags)
                    self.check_finished.emit(True)
                    return
            
            # 从PATH环境变量中查找
            path_dirs = os.environ.get('Path', '').split(';')
            for dir_path in path_dirs:
                if 'ffmpeg' in dir_path.lower():
                    # 检查目录下是否有ffmpeg.exe
                    ffmpeg_exe = os.path.join(dir_path, 'ffmpeg.exe')
                    if os.path.exists(ffmpeg_exe):
                        subprocess.run([ffmpeg_exe, '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=flags)
                        self.check_finished.emit(True)
                        return
            
            # 都找不到，报告不可用
            self.check_finished.emit(False)
            
        except Exception:
            self.check_finished.emit(False)


class FFmpegUninstallThread(QThread):
    uninstall_finished = Signal(bool, str)
    
    def run(self):
        try:
            # 查找FFmpeg可能的安装位置
            ffmpeg_paths = self._find_ffmpeg_paths()
            if not ffmpeg_paths:
                self.uninstall_finished.emit(False, "未找到FFmpeg安装目录")
                return
                
            # 从环境变量中删除FFmpeg路径
            self._remove_from_path(ffmpeg_paths)
            
            # 删除FFmpeg目录
            deleted_paths = []
            for path in ffmpeg_paths:
                if os.path.exists(path):
                    try:
                        shutil.rmtree(path)
                        deleted_paths.append(path)
                    except Exception as e:
                        self.uninstall_finished.emit(False, f"删除目录失败: {path}, 错误: {str(e)}")
                        return
            
            if deleted_paths:
                self.uninstall_finished.emit(True, f"FFmpeg已成功卸载，删除的目录: {', '.join(deleted_paths)}")
            else:
                self.uninstall_finished.emit(True, "FFmpeg路径已从环境变量中移除")
                
        except Exception as e:
            self.uninstall_finished.emit(False, f"卸载过程中发生错误: {str(e)}")
    
    def _find_ffmpeg_paths(self) -> List[str]:
        """查找FFmpeg可能的安装路径"""
        ffmpeg_paths = []
        
        # 检查常见的安装位置
        common_paths = [
            r"C:\ffmpeg",  # 直接以ffmpeg目录作为主目录
            os.path.join(os.path.expanduser('~'), 'ffmpeg'),
            r"C:\Program Files\ffmpeg",
            r"C:\Program Files (x86)\ffmpeg",
            r"D:\ffmpeg-7.0.2-essentials_build"  # 保留原有目录
        ]
        
        # 添加系统盘上的ffmpeg目录
        for drive in ['C:', 'D:', 'E:', 'F:']:
            if os.path.exists(drive):
                common_paths.append(f"{drive}\\ffmpeg")
        
        # 首先检查哪些路径下有ffmpeg.exe
        for base_path in common_paths:
            if os.path.exists(base_path):
                # 检查根目录
                if os.path.exists(os.path.join(base_path, 'ffmpeg.exe')):
                    ffmpeg_paths.append(base_path)
                # 检查bin目录
                bin_path = os.path.join(base_path, 'bin')
                if os.path.exists(bin_path) and os.path.exists(os.path.join(bin_path, 'ffmpeg.exe')):
                    ffmpeg_paths.append(base_path)  # 添加主目录，而不是bin子目录
        
        # 从环境变量中查找
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Environment', 0, winreg.KEY_READ)
            try:
                path_value = winreg.QueryValueEx(key, 'Path')[0]
                
                for path_entry in path_value.split(';'):
                    path_entry = path_entry.strip()
                    if not path_entry:
                        continue
                        
                    if 'ffmpeg' in path_entry.lower():
                        # 路径本身可能指向bin目录或根目录
                        # 如果是bin目录，查找其父目录
                        if path_entry.lower().endswith('bin'):
                            parent_dir = os.path.dirname(path_entry)
                            if os.path.exists(parent_dir) and parent_dir not in ffmpeg_paths:
                                ffmpeg_paths.append(parent_dir)
                        # 否则直接添加路径本身
                        elif path_entry not in ffmpeg_paths and os.path.exists(path_entry):
                            ffmpeg_paths.append(path_entry)
            except Exception:
                pass
            finally:
                winreg.CloseKey(key)
        except Exception:
            pass
            
        return ffmpeg_paths
    
    def _remove_from_path(self, ffmpeg_paths: List[str]) -> None:
        """从环境变量中删除FFmpeg路径"""
        try:
            # 修改用户环境变量（不涉及系统环境变量）
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Environment', 0, winreg.KEY_READ | winreg.KEY_SET_VALUE)
            try:
                path_value = winreg.QueryValueEx(key, 'Path')[0]
                
                # 分割路径并过滤掉FFmpeg相关路径
                path_entries = path_value.split(';')
                filtered_entries = []
                
                for entry in path_entries:
                    entry = entry.strip()
                    if not entry:
                        continue
                        
                    # 检查是否是FFmpeg相关路径
                    is_ffmpeg_path = False
                    for ffmpeg_path in ffmpeg_paths:
                        # 检查是主目录本身
                        if entry == ffmpeg_path:
                            is_ffmpeg_path = True
                            break
                        # 检查是否是bin子目录
                        if entry.startswith(ffmpeg_path + '\\'):
                            is_ffmpeg_path = True
                            break
                        # 检查bin子目录自身
                        bin_path = os.path.join(ffmpeg_path, 'bin')
                        if entry == bin_path:
                            is_ffmpeg_path = True
                            break
                    
                    # 通用检查，包含ffmpeg字样但不在我们已知的路径中
                    if not is_ffmpeg_path and 'ffmpeg' in entry.lower():
                        # 额外检查是否是我们要保留的路径
                        if 'D:\\ffmpeg-7.0.2-essentials_build\\bin' in entry:
                            # 保留这个特定路径
                            filtered_entries.append(entry)
                            continue
                        is_ffmpeg_path = True
                        
                    if not is_ffmpeg_path:
                        filtered_entries.append(entry)
                
                # 重新组合路径并保存
                new_path = ';'.join(filtered_entries)
                winreg.SetValueEx(key, 'Path', 0, winreg.REG_EXPAND_SZ, new_path)
                
                # 更新当前进程的环境变量
                os.environ['Path'] = new_path
                
            finally:
                winreg.CloseKey(key)
                
        except Exception as e:
            raise Exception(f"修改环境变量失败: {str(e)}")


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
        
        # 检测FFmpeg按钮
        self.checkFFmpegCard = PushSettingCard(
            text="检测",
            icon=FIF.SEARCH,
            title="检测FFmpeg",
            content="检测FFmpeg是否可用",
            parent=self.scrollWidget
        )
        
        # 卸载FFmpeg按钮
        self.uninstallFFmpegCard = PushSettingCard(
            text="卸载",
            icon=FIF.DELETE,
            title="卸载FFmpeg",
            content="卸载FFmpeg并从环境变量中删除",
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
        self.basicGroup.addSettingCard(self.checkFFmpegCard)
        self.basicGroup.addSettingCard(self.uninstallFFmpegCard)
        
        # 添加组到布局
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.addWidget(self.themeGroup)
        self.expandLayout.addWidget(self.basicGroup)
        
        # 连接信号
        self.themeCard.comboBox.currentIndexChanged.connect(self.onThemeModeChanged)
        self.autostartCard.switchButton.checkedChanged.connect(self.onAutostartChanged)
        self.checkFFmpegCard.button.clicked.connect(self.onCheckFFmpegClicked)
        self.uninstallFFmpegCard.button.clicked.connect(self.onUninstallFFmpegClicked)
        
        # 同步自启动开关状态到实际系统状态
        self._autostart_syncing = True
        actual_autostart = autostart_manager.is_enabled()
        if config_manager.autostart.value != actual_autostart:
            config_manager.autostart.value = actual_autostart
            if hasattr(config_manager, 'save'):
                config_manager.save()
        self.autostartCard.switchButton.setChecked(actual_autostart)
        self._autostart_syncing = False
        
    def onThemeModeChanged(self, index):
        """ 主题模式改变的处理函数 """
        theme_modes = [ThemeMode.LIGHT, ThemeMode.DARK, ThemeMode.SYSTEM]
        set_theme_mode(theme_modes[index])
        
    def onAutostartChanged(self, checked):
        """ 开机自启设置改变的处理函数 """
        try:
            if checked:
                success = autostart_manager.enable()
                msg = '开机自启动设置成功'
            else:
                success = autostart_manager.disable()
                msg = '开机自启动关闭成功'
            if success:
                if not getattr(self, '_autostart_syncing', False):
                    InfoBar.success(
                        title='成功',
                        content=msg,
                        orient=Qt.Orientation.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
            else:
                self.show_autostart_error('未知错误')
        except Exception as e:
            self.show_autostart_error(str(e))

    def show_autostart_error(self, err_msg):
        from PySide6.QtWidgets import QPushButton
        from PySide6.QtGui import QFont
        import functools
        bar = InfoBar.error(
                title='错误',
            content=f'开机自启动设置失败: {err_msg}',
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=10000,  # 停留10秒
            parent=self
        )
        # 添加"点击复制"按钮
        btn = QPushButton('点击复制')
        btn.setStyleSheet('color: #888; font-size: 12px; background: transparent; border: none;')
        btn.setFont(QFont('', 9))
        def on_copy():
            QApplication.clipboard().setText(str(err_msg))
            btn.setText('已复制')
            btn.setStyleSheet('color: #4caf50; font-size: 12px; background: transparent; border: none;')
            InfoBar.success(
                title='成功',
                content='复制成功',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=1500,
                parent=self
            )
            from PySide6.QtCore import QTimer
            QTimer.singleShot(1000, lambda: (btn.setText('点击复制'), btn.setStyleSheet('color: #888; font-size: 12px; background: transparent; border: none;')))
        btn.clicked.connect(on_copy)
        bar.layout().addWidget(btn)
        
    def onCheckFFmpegClicked(self):
        self.checkFFmpegCard.button.setEnabled(False)
        self.ffmpegCheckThread = FFmpegCheckThread()
        self.ffmpegCheckThread.check_finished.connect(self.onFFmpegCheckResult)
        self.ffmpegCheckThread.finished.connect(lambda: self.checkFFmpegCard.button.setEnabled(True))
        self.ffmpegCheckThread.start()

    def onFFmpegCheckResult(self, available):
        if available:
            InfoBar.success(
                title='成功',
                content='FFmpeg 可用',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        else:
            msg = MessageBox(
                '检测到系统未安装FFmpeg',
                '是否现在安装FFmpeg？\n\n注意：安装过程可能需要几分钟，请耐心等待。',
                self
            )
            if msg.exec():
                installer = FFmpegInstaller(self)
                installer.show()
                def on_finished():
                    if installer.installation_success:
                        InfoBar.success(
                            title='成功',
                            content='FFmpeg 安装成功',
                            orient=Qt.Orientation.Horizontal,
                            isClosable=True,
                            position=InfoBarPosition.TOP,
                            duration=2000,
                            parent=self
                        )
                    else:
                        InfoBar.error(
                            title='错误',
                            content='FFmpeg 安装失败',
                            orient=Qt.Orientation.Horizontal,
                            isClosable=True,
                            position=InfoBarPosition.TOP,
                            duration=2000,
                            parent=self
                        )
                installer.finished.connect(on_finished)
            else:
                InfoBar.info(
                    title='提示',
                    content='用户已取消安装ffmpeg',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
        
    def onUninstallFFmpegClicked(self):
        """卸载FFmpeg按钮点击事件"""
        # 确认对话框
        msg = MessageBox(
            '卸载FFmpeg',
            '确定要卸载FFmpeg吗？这将删除FFmpeg目录并从环境变量中移除相关路径。',
            self
        )
        if not msg.exec():
            return
            
        # 禁用按钮，防止重复点击
        self.uninstallFFmpegCard.button.setEnabled(False)
        
        # 创建并启动卸载线程
        self.uninstallThread = FFmpegUninstallThread()
        self.uninstallThread.uninstall_finished.connect(self.onUninstallFinished)
        self.uninstallThread.finished.connect(lambda: self.uninstallFFmpegCard.button.setEnabled(True))
        self.uninstallThread.start()
        
        # 显示进行中提示
        InfoBar.info(
            title='提示',
            content='正在卸载FFmpeg，请稍候...',
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
    def onUninstallFinished(self, success, message):
        """卸载完成回调"""
        if success:
            InfoBar.success(
                title='成功',
                content=message,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        else:
            from PySide6.QtWidgets import QPushButton
            
            # 显示错误信息
            bar = InfoBar.error(
                title='错误',
                content=f'卸载失败: {message}',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            
            # 添加"点击复制"按钮
            btn = QPushButton('点击复制')
            btn.setStyleSheet('color: #888; font-size: 12px; background: transparent; border: none;')
            btn.setFont(QApplication.font())
            
            def on_copy():
                QApplication.clipboard().setText(message)
                btn.setText('已复制')
                btn.setStyleSheet('color: #4caf50; font-size: 12px; background: transparent; border: none;')
                InfoBar.success(
                    title='成功',
                    content='复制成功',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=1500,
                    parent=self
                )
                from PySide6.QtCore import QTimer
                QTimer.singleShot(1000, lambda: (
                    btn.setText('点击复制'), 
                    btn.setStyleSheet('color: #888; font-size: 12px; background: transparent; border: none;')
                ))
                
            btn.clicked.connect(on_copy)
            bar.layout().addWidget(btn)
        
    def updateStyle(self):
        # 设置整个页面背景色
        if isDarkTheme():
            self.setStyleSheet("QScrollArea { background-color: #1e1e1e; border: none; }")
            self.scrollWidget.setStyleSheet("QWidget { background-color: #1e1e1e; }")
            self.themeGroup.titleLabel.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
            self.basicGroup.titleLabel.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        else:
            self.setStyleSheet("QScrollArea { background-color: white; border: none; }")
            self.scrollWidget.setStyleSheet("QWidget { background-color: white; }")
            self.themeGroup.titleLabel.setStyleSheet("font-size: 20px; font-weight: bold; color: black;")
            self.basicGroup.titleLabel.setStyleSheet("font-size: 20px; font-weight: bold; color: black;")
        # 不要对卡片内容和按钮 setStyleSheet 