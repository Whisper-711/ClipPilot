import os
import sys
import threading
import atexit
import logging

import webview
import pyperclip

import config

try:
    import win32con
    import win32gui
    _HAS_WIN32 = True
except ImportError:
    _HAS_WIN32 = False

_HWND_MESSAGE = -3

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════
#  全局热键（Win32 消息线程）
# ═══════════════════════════════════════════════

class GlobalHotkey:
    """Register a global hotkey via a message-only window in a daemon thread."""

    MOD_MAP = {"alt": 0x0001, "ctrl": 0x0002, "shift": 0x0004, "win": 0x0008}

    def __init__(self, modifiers, key, callback):
        self.callback = callback
        self._vk = ord(key.upper())
        self._mod_mask = 0
        for m in modifiers:
            self._mod_mask |= self.MOD_MAP.get(m.lower(), 0)
        self._hwnd = None
        self._thread = None

    def start(self):
        if not _HAS_WIN32:
            logger.warning("win32api 不可用，全局热键未注册")
            return
        self._thread = threading.Thread(target=self._msg_loop, daemon=True)
        self._thread.start()
        atexit.register(self.stop)

    def stop(self):
        if self._hwnd:
            win32gui.PostMessage(self._hwnd, win32con.WM_QUIT, 0, 0)

    def _wndproc(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_HOTKEY:
            self.callback()
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _msg_loop(self):
        hinst = win32gui.GetModuleHandle(None)

        cls_name = f"ClipPilotHK_{id(self)}"
        wc = win32gui.WNDCLASS()
        wc.style = 0
        wc.lpfnWndProc = self._wndproc
        wc.hInstance = hinst
        wc.lpszClassName = cls_name
        try:
            win32gui.RegisterClass(wc)
        except Exception:
            pass

        self._hwnd = win32gui.CreateWindowEx(
            0, cls_name, "CPHK", 0,
            0, 0, 0, 0,
            _HWND_MESSAGE, None, None, None,
        )
        try:
            win32gui.RegisterHotKey(self._hwnd, 1, self._mod_mask | 0x4000, self._vk)
        except win32gui.error as e:
            logger.warning("注册热键失败（可能已被占用）: %s", e)

        try:
            while True:
                rc, msg_tup = win32gui.GetMessage(None, 0, 0)
                if rc == 0:
                    break
                if msg_tup[1] == win32con.WM_HOTKEY:
                    self.callback()
                win32gui.TranslateMessage(msg_tup)
                win32gui.DispatchMessage(msg_tup)
        finally:
            try:
                win32gui.UnregisterHotKey(self._hwnd, 1)
            except Exception:
                pass
            win32gui.DestroyWindow(self._hwnd)


# ═══════════════════════════════════════════════
#  系统托盘（pystray 线程）
# ═══════════════════════════════════════════════

def _make_tray_image():
    """64x64 RGBA icon: clipboard + T mark."""
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([10, 6, 54, 58], radius=6, fill=(0, 110, 210, 255))
    draw.rounded_rectangle([14, 12, 50, 54], radius=4, fill=(80, 170, 255, 60))
    try:
        draw.text((22, 14), "T", fill=(255, 255, 255, 230), font=None)
    except Exception:
        draw.text((22, 14), "T", fill=(255, 255, 255, 230))
    return img


class TrayManager:
    def __init__(self, on_show, on_quit):
        self.on_show = on_show
        self.on_quit = on_quit
        self._icon = None
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def notify(self, text, title="ClipPilot"):
        if self._icon:
            try:
                self._icon.notify(text, title)
            except Exception:
                pass

    def _run(self):
        import pystray

        img = _make_tray_image()
        menu = pystray.Menu(
            pystray.MenuItem("显示 / 隐藏", lambda: self.on_show()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", lambda: self.on_quit()),
        )
        self._icon = pystray.Icon("ClipPilot", img, "ClipPilot", menu)
        self._icon.run()


# ═══════════════════════════════════════════════
#  PyWebView JS API (bridge to Python)
# ═══════════════════════════════════════════════

class WebApi:
    """所有 public 方法自动暴露给 JavaScript 调用。"""

    def __init__(self, db, translator):
        self.db = db
        self.translator = translator
        self._window = None
        self._on_hide = None  # callback: window hidden from JS

    def set_window(self, window):
        self._window = window

    # ── 历史记录 ──

    def get_history(self, search, offset, limit):
        q = search.strip() if search and search.strip() else None
        rows = self.db.get_history(limit=limit, offset=offset, search=q)
        total = self.db.get_history_count(search=q)
        items = [
            {"id": r[0], "content": r[1], "created_at": r[2] or ""}
            for r in rows
        ]
        loaded = offset + len(rows)
        remaining = max(0, total - loaded)
        return {
            "items": items,
            "has_more": remaining > 0,
            "remaining": remaining,
            "total": total,
        }

    def get_content_by_id(self, record_id):
        row = self.db.get_by_id(record_id)
        if row:
            return {"id": row[0], "content": row[1], "created_at": row[2] or ""}
        return None

    # ── 复制 ──

    def copy(self, text):
        pyperclip.copy(text)

    # ── 翻译 ──

    def translate(self, text):
        result, src_lang, _cached = self.translator.translate(text)
        return {"result": result, "source": src_lang}

    # ── 窗口管理 ──

    def hide_window(self):
        if self._window:
            self._window.hide()
        if self._on_hide:
            self._on_hide()

    def set_always_on_top(self, enabled):
        if _HAS_WIN32:
            try:
                hwnd = win32gui.FindWindow(None, "ClipPilot")
                if hwnd:
                    win32gui.SetWindowPos(
                        hwnd,
                        win32con.HWND_TOPMOST if enabled else win32con.HWND_NOTOPMOST,
                        0, 0, 0, 0,
                        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
                    )
            except Exception as e:
                logger.warning("set_always_on_top failed: %s", e)

    def clear_all(self):
        self.db.clear_all()


# ═══════════════════════════════════════════════
#  UI 主管理器
# ═══════════════════════════════════════════════

class UIManager:
    """管理 PyWebView 窗口、托盘图标、全局热键及视图刷新。"""

    def __init__(self, db, translator):
        self.db = db
        self.translator = translator
        self.api = WebApi(db, translator)
        self.api._on_hide = self._on_api_hide
        self._window = None
        self._tray = None
        self._hotkey = None
        self._visible = False
        self._auto_show = False

    # ── 生命周期 ──

    def start(self, debug=False, auto_show=False):
        self._auto_show = auto_show

        cfg = config.load()

        # HTML 文件路径（兼容 PyInstaller）
        if getattr(sys, "frozen", False):
            base = sys._MEIPASS
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.join(base, "assets", "index.html")

        # 创建窗口
        self._window = webview.create_window(
            "ClipPilot",
            url=html_path,
            js_api=self.api,
            width=cfg.get("window_width", 520),
            height=cfg.get("window_height", 650),
            frameless=True,
            resizable=True,
        )
        self.api.set_window(self._window)

        # 托盘
        self._setup_tray()

        # 热键
        self._setup_hotkey()

        # 启动 GUI 循环（阻塞）
        webview.start(
            func=self._on_startup,
            private_mode=False,
            debug=debug,
        )

    def _on_startup(self):
        """在 GUI 循环就绪后调用（UI 线程）。"""
        self._window.hide()
        self._visible = False
        if self._auto_show:
            threading.Timer(0.3, self.toggle_window).start()

    def _on_api_hide(self):
        """JS 调用 hide_window 时同步可见状态。"""
        self._visible = False

    def stop(self):
        if self._hotkey:
            self._hotkey.stop()

    # ── 剪贴板回调（来自 monitor 线程） ──

    def on_new_clipboard(self, text):
        """由 clipboard monitor 调用——可能来自后台线程。"""
        try:
            self.db.add_history(text)
        except Exception as e:
            logger.error("添加历史记录失败: %s", e)
            return
        if self._visible and self._window:
            try:
                self._window.evaluate_js("refreshHistory()")
            except Exception:
                pass

    # ── 窗口显示 / 隐藏 ──

    def toggle_window(self):
        if self._window is None:
            return
        if self._visible:
            self._window.hide()
            self._visible = False
        else:
            self._window.show()
            self._visible = True
            try:
                self._window.evaluate_js("refreshHistory()")
            except Exception as e:
                logger.debug("窗口刷新失败: %s", e)

    # ── 托盘 ──

    def _setup_tray(self):
        self._tray = TrayManager(
            on_show=self.toggle_window,
            on_quit=self._quit,
        )
        self._tray.start()

    # ── 热键 ──

    def _setup_hotkey(self):
        cfg = config.load()
        self._hotkey = GlobalHotkey(
            cfg.get("hotkey_modifiers", ["alt", "ctrl"]),
            cfg.get("hotkey_key", "v"),
            self.toggle_window,
        )
        self._hotkey.start()

    # ── 退出 ──

    def _quit(self):
        self.stop()
        # pystray 守护线程会随进程退出
        import os

        os._exit(0)
