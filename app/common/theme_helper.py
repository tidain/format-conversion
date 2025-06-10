import winreg
from PyQt6.QtGui import QColor
from qfluentwidgets import setThemeColor, Theme, setTheme
from .config_manager import ThemeMode, config_manager

def get_windows_accent_color():
    """获取 Windows 系统主题强调色"""
    try:
        # 打开注册表键
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Accent"
        )
        
        # 获取 AccentColorMenu 值（格式为 ABGR）
        color_dword = winreg.QueryValueEx(key, "AccentColorMenu")[0]
        
        # 关闭注册表键
        winreg.CloseKey(key)
        
        # 将 DWORD 值转换为 RGB 颜色
        # Windows 存储格式为 ABGR，我们需要转换为 RGB
        b = (color_dword >> 16) & 0xFF
        g = (color_dword >> 8) & 0xFF
        r = color_dword & 0xFF
        
        # 返回十六进制格式的颜色代码
        return f"#{r:02x}{g:02x}{b:02x}"
    except:
        # 如果获取失败，返回默认的 Windows 11 蓝色
        return "#0078d4"

def get_system_theme():
    """获取系统主题（深色/浅色）"""
    try:
        # 打开注册表键
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        )
        
        # 获取 AppsUseLightTheme 值（0 表示深色主题，1 表示浅色主题）
        is_light_theme = winreg.QueryValueEx(key, "AppsUseLightTheme")[0]
        
        # 关闭注册表键
        winreg.CloseKey(key)
        
        return "light" if is_light_theme else "dark"
    except:
        # 如果获取失败，返回默认的浅色主题
        return "light"

def apply_theme():
    """应用主题设置"""
    # 获取用户设置的主题模式
    theme_mode = config_manager.get_theme_mode()
    
    # 设置主题颜色
    accent_color = get_windows_accent_color()
    setThemeColor(accent_color)
    
    # 根据主题模式设置深浅主题
    if theme_mode == ThemeMode.SYSTEM:
        system_theme = get_system_theme()
        setTheme(Theme.DARK if system_theme == "dark" else Theme.LIGHT)
    elif theme_mode == ThemeMode.DARK:
        setTheme(Theme.DARK)
    else:  # ThemeMode.LIGHT
        setTheme(Theme.LIGHT)

def set_theme_mode(theme_mode: ThemeMode):
    """设置主题模式并立即应用"""
    config_manager.set_theme_mode(theme_mode)
    apply_theme() 