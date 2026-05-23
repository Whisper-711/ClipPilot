import sys
import os
import json

# 数据目录：打包后使用 APPDATA，源码运行使用当前目录
def get_data_dir():
    if getattr(sys, 'frozen', False):
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
        data_dir = os.path.join(base, 'ClipPilot')
    else:
        data_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

DATA_DIR = get_data_dir()
CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')
DB_FILE = os.path.join(DATA_DIR, 'clipboard.db')

DEFAULT_CONFIG = {
    "max_history": 200,
    "poll_interval": 0.3,
    "hotkey_modifiers": ["alt", "ctrl"],
    "hotkey_key": "v",
    "window_width": 520,
    "window_height": 650,
    "max_preview_length": 120,
    "appearance_mode": "system",
    "color_theme": "blue",
    "auto_translate": False,
    "auto_detect_lang": True,
    "source_lang": "auto",
    "target_lang_zh": "en",
    "target_lang_en": "zh",
    "max_content_size": 10240,
    "translator_proxy": "",
    "translator_custom_url": ""
}


def load():
    cfg = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg.update(json.load(f))
        except Exception:
            pass
    return cfg


def save(cfg):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
