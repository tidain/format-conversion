import os
import sys
import winreg
import subprocess
import shutil
from pathlib import Path

class AutoStartManager:
    def __init__(self):
        self.app_name = "文件格式转换器"
        self.startup_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        self.startup_dir = os.path.join(os.environ.get('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        
    def _get_startup_vbs_path(self):
        """获取启动脚本路径"""
        return os.path.join(self.startup_dir, f"{self.app_name}.vbs")
        
    def _get_startup_exe_path(self):
        """获取启动程序路径"""
        return os.path.join(self.startup_dir, f"{self.app_name}.exe")
        
    def _get_executable_path(self):
        """获取当前程序路径"""
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe
            current_exe = sys.executable
            startup_exe = self._get_startup_exe_path()
            
            # 复制exe到启动目录
            try:
                if os.path.exists(startup_exe):
                    os.remove(startup_exe)
                shutil.copy2(current_exe, startup_exe)
                return startup_exe
            except Exception as e:
                print(f"复制exe文件失败: {str(e)}")
                return current_exe
        else:
            # 如果是开发环境，创建启动脚本
            vbs_path = self._get_startup_vbs_path()
            
            # 获取 Python 解释器和主脚本的路径
            python_path = sys.executable
            main_script = os.path.abspath(sys.argv[0])
            
            # 创建 VBS 脚本来隐藏命令行窗口
            try:
                with open(vbs_path, 'w', encoding='utf-8') as f:
                    f.write(f'CreateObject("WScript.Shell").Run """"{python_path}"" ""{main_script}""", 0, False')
                return vbs_path
            except Exception as e:
                print(f"创建VBS脚本失败: {str(e)}")
                return None
            
    def _clean_startup_files(self):
        """清理启动文件"""
        try:
            # 清理VBS脚本
            vbs_path = self._get_startup_vbs_path()
            if os.path.exists(vbs_path):
                os.remove(vbs_path)
                
            # 清理EXE文件
            exe_path = self._get_startup_exe_path()
            if os.path.exists(exe_path):
                os.remove(exe_path)
                
            return True
        except Exception as e:
            print(f"清理启动文件失败: {str(e)}")
            return False
            
    def is_enabled(self):
        """检查是否已启用开机自启动"""
        # 检查启动目录中的文件
        vbs_exists = os.path.exists(self._get_startup_vbs_path())
        exe_exists = os.path.exists(self._get_startup_exe_path())
        
        # 检查注册表
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.startup_key,
                0,
                winreg.KEY_READ
            )
            
            try:
                value, _ = winreg.QueryValueEx(key, self.app_name)
                winreg.CloseKey(key)
                reg_exists = True
            except WindowsError:
                reg_exists = False
                winreg.CloseKey(key)
        except WindowsError:
            reg_exists = False
            
        return vbs_exists or exe_exists or reg_exists
            
    def enable(self):
        """启用开机自启动"""
        try:
            # 首先清理可能存在的旧文件
            self._clean_startup_files()
            
            # 获取可执行文件路径
            executable_path = self._get_executable_path()
            if not executable_path:
                return False
                
            # 添加到注册表
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.startup_key,
                0,
                winreg.KEY_WRITE
            )
            
            winreg.SetValueEx(
                key,
                self.app_name,
                0,
                winreg.REG_SZ,
                executable_path
            )
            
            winreg.CloseKey(key)
            return True
            
        except Exception as e:
            print(f"启用自启动失败: {str(e)}")
            return False
            
    def disable(self):
        """禁用开机自启动"""
        success = True
        
        # 清理启动文件
        if not self._clean_startup_files():
            success = False
            
        # 删除注册表项
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.startup_key,
                0,
                winreg.KEY_WRITE
            )
            
            try:
                winreg.DeleteValue(key, self.app_name)
            except WindowsError:
                success = False
                
            winreg.CloseKey(key)
            
        except WindowsError:
            success = False
            
        return success

# 创建全局自启动管理器实例
autostart_manager = AutoStartManager() 