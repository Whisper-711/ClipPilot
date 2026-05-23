"""
ClipPilot —— 轻量级剪贴板历史 + 中英互译工具

用法:
    python main.py         # 正常启动（后台托盘）
    python main.py --debug # 启动并输出日志到控制台
"""
import sys
import os
import logging

# 确保项目目录在 path 中（兼容 PyInstaller 打包）
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

import config
from database import Database
from translator import Translator
from clipboard_monitor import ClipboardMonitor
from ui import UIManager


def setup_logging(debug: bool):
    level = logging.DEBUG if debug else logging.WARNING
    fmt = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter(fmt, datefmt="%H:%M:%S"))
        root.addHandler(h)
    else:
        for h in root.handlers:
            h.setLevel(level)
    # 静默第三方库的调试日志
    for lib in ("PIL", "webview", "bottle", "pywebview"):
        logging.getLogger(lib).setLevel(logging.WARNING)


def main():
    debug = "--debug" in sys.argv
    auto_show = "--show" in sys.argv
    setup_logging(debug)

    logger = logging.getLogger("main")
    logger.info("ClipPilot 启动中…")

    cfg = config.load()
    logger.debug("配置: %s", cfg)

    # 初始化模块
    db = Database()
    translator = Translator(db)
    ui = UIManager(db, translator)

    # 剪贴板监听
    monitor = ClipboardMonitor(on_new_text=ui.on_new_clipboard)
    monitor.start()

    logger.info("剪贴板监听已启动")

    # 启动 UI（阻塞，直到退出）
    try:
        ui.start(debug=debug, auto_show=auto_show)
    except KeyboardInterrupt:
        logger.info("收到中断信号")
    finally:
        monitor.stop()
        ui.stop()
        logger.info("ClipPilot 已退出")


if __name__ == "__main__":
    main()
