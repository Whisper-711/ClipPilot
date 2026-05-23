import threading
import time
import logging
import pyperclip

import config

logger = logging.getLogger(__name__)


class ClipboardMonitor:
    def __init__(self, on_new_text, poll_interval=None):
        self.on_new_text = on_new_text
        self.interval = poll_interval or config.load().get('poll_interval', 0.3)
        self._last_content = None
        self._running = False
        self._thread = None

    def start(self):
        try:
            self._last_content = pyperclip.paste()
        except Exception:
            self._last_content = ''
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name='ClipMonitor')
        self._thread.start()
        logger.info("剪贴板监听已启动 (间隔 %.1fs)", self.interval)

    def stop(self):
        self._running = False

    @property
    def running(self):
        return self._running

    def _loop(self):
        while self._running:
            try:
                text = pyperclip.paste()
            except Exception:
                text = None

            if text and text != self._last_content:
                self._last_content = text
                try:
                    self.on_new_text(text)
                except Exception as e:
                    logger.error("on_new_text 回调异常: %s", e)
            time.sleep(self.interval)
