import json
import os
from enum import Enum

class ThemeMode(Enum):
    LIGHT = "浅色主题"
    DARK = "深色主题"
    SYSTEM = "跟随系统"

class ConfigManager:
    def __init__(self):
        self.config_dir = os.path.join(os.path.expanduser('~'), '.gsgc')
        self.config_file = os.path.join(self.config_dir, 'config.json')
        self.default_config = {
            'theme_mode': ThemeMode.SYSTEM.name,
            'autostart': False
        }
        self._ensure_config_exists()
        self.config = self._load_config()

    def _ensure_config_exists(self):
        """确保配置文件存在"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        if not os.path.exists(self.config_file):
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.default_config, f, ensure_ascii=False, indent=4)

    def _load_config(self):
        """加载配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return self.default_config.copy()

    def _save_config(self):
        """保存配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

    def get_theme_mode(self):
        """获取主题模式"""
        theme_mode = self.config.get('theme_mode', ThemeMode.SYSTEM.name)
        return ThemeMode[theme_mode]

    def set_theme_mode(self, theme_mode: ThemeMode):
        """设置主题模式"""
        self.config['theme_mode'] = theme_mode.name
        self._save_config()

    def get_autostart(self):
        """获取开机自启动设置"""
        return self.config.get('autostart', False)

    def set_autostart(self, enabled: bool):
        """设置开机自启动"""
        self.config['autostart'] = enabled
        self._save_config()

# 创建全局配置管理器实例
config_manager = ConfigManager() 