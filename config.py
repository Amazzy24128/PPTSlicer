import json
import os

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "save_path": "",
    "threshold": 5.0,
    "hotkey_timeout": 5,
    "auto_mode": False  # 新增配置项
}

def load_settings():
    """从 settings.json 加载配置，如果文件不存在则返回默认配置"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                for key, value in DEFAULT_SETTINGS.items():
                    settings.setdefault(key, value)
                return settings
        except (json.JSONDecodeError, IOError):
            return DEFAULT_SETTINGS
    return DEFAULT_SETTINGS

def save_settings(settings):
    """将配置保存到 settings.json"""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)
    except IOError as e:
        print(f"[-] 保存配置失败: {e}")