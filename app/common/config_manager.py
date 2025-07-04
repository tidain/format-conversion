import json
import os
from enum import Enum
from qfluentwidgets import QConfig, OptionsConfigItem, OptionsValidator

class ThemeMode(Enum):
    LIGHT = "浅色主题"
    DARK = "深色主题"
    SYSTEM = "跟随系统"

class Config(QConfig):
    """ 配置类 """
    
    def __init__(self, config_dir=None):
        super().__init__()
        if config_dir is None:
            config_dir = os.path.join(os.path.expanduser('~'), '.gsgc')
        self.config_dir = config_dir
        self.config_file = os.path.join(self.config_dir, 'config.json')
        self._ensure_config_exists()
        
        # 主题模式
        theme_options = [mode.name for mode in ThemeMode]
        self.theme_mode = OptionsConfigItem(
            "Theme", "ThemeMode",
            ThemeMode.SYSTEM.name,
            OptionsValidator(theme_options)
        )
        
        # 开机自启
        self.autostart = OptionsConfigItem(
            "Startup", "AutoStart",
            False,
            OptionsValidator([True, False])
        )

    def _ensure_config_exists(self):
        """确保配置文件存在"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        if not os.path.exists(self.config_file):
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'theme_mode': ThemeMode.SYSTEM.name,
                    'autostart': False
                }, f, ensure_ascii=False, indent=4)

    def get_theme_mode(self):
        """获取主题模式"""
        return ThemeMode[self.theme_mode.value]

    def set_theme_mode(self, theme_mode: ThemeMode):
        """设置主题模式"""
        self.theme_mode.value = theme_mode.name
        self.save()

    def get_autostart(self):
        """获取开机自启动设置"""
        return self.autostart.value

    def set_autostart(self, enabled: bool):
        """设置开机自启动"""
        self.autostart.value = enabled
        self.save()

# 创建全局配置管理器实例
config_manager = Config() 