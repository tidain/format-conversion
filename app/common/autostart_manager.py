import os
import sys
from pathlib import Path
from win32com.client import Dispatch  # 需 pip install pywin32

class AutoStartManager:
    def __init__(self):
        self.app_name = "文件格式转换器"
        self.startup_dir = os.path.join(os.environ.get('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        self.shortcut_path = os.path.join(self.startup_dir, f"{self.app_name}.lnk")

    def _get_target_path(self):
        """获取快捷方式目标路径（开发环境为python.exe+脚本，打包后为exe）"""
        if getattr(sys, 'frozen', False):
            # 打包后，指向exe
            return sys.executable, os.path.dirname(sys.executable)
        else:
            # 开发环境，指向python.exe和主脚本
            python_path = sys.executable
            script_path = os.path.abspath(sys.argv[0])
            return f'{python_path} "{script_path}"', os.path.dirname(script_path)

    def enable(self):
        """启用开机自启动（创建快捷方式）"""
        try:
            self.disable()  # 先清理旧的
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(self.shortcut_path)
            target, workdir = self._get_target_path()
            if getattr(sys, 'frozen', False):
                shortcut.Targetpath = target
                shortcut.WorkingDirectory = workdir
            else:
                shortcut.Targetpath = sys.executable
                shortcut.Arguments = f'"{os.path.abspath(sys.argv[0])}"'
                shortcut.WorkingDirectory = workdir
            shortcut.save()
            return True
        except Exception as e:
            print(f"创建自启动快捷方式失败: {str(e)}")
            return False

    def disable(self):
        """禁用开机自启动（删除快捷方式）"""
        try:
            if os.path.exists(self.shortcut_path):
                os.remove(self.shortcut_path)
            return True
        except Exception as e:
            print(f"删除自启动快捷方式失败: {str(e)}")
            return False

    def is_enabled(self):
        """检查是否已启用开机自启动（是否有快捷方式）"""
        return os.path.exists(self.shortcut_path)

# 创建全局自启动管理器实例
autostart_manager = AutoStartManager() 