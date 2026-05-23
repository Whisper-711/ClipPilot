# ClipPilot

轻量级 Windows 剪贴板历史管理工具，支持中英互译。

## 功能

- **剪贴板历史** — 自动记录复制的内容，按时间倒序排列
- **实时搜索** — 快速过滤历史记录
- **中英互译** — 一键翻译选中的文本（Google Translate）
- **系统托盘** — 后台运行，Ctrl+Alt+V 随时唤出
- **窗口置顶** — 对比参考时固定窗口位置
- **奶油风格 UI** — 简洁现代的界面设计

## 使用方法

| 操作 | 方式 |
|---|---|
| 唤出 / 隐藏窗口 | `Ctrl+Alt+V` 或点击托盘图标 |
| 复制记录 | 点击卡片内容或"复制"按钮 |
| 翻译 | 点击卡片"翻译"按钮 |
| 搜索 | 搜索框输入关键词（实时过滤） |
| 窗口置顶 | 标题栏 📌 按钮 |
| 清空历史 | 状态栏"清空历史" |
| 隐藏窗口 | `Esc` 或点击 ✕ |

## 截图

![ClipPilot](<img width="499" height="606" alt="image" src="https://github.com/user-attachments/assets/f1d0c2ef-6e8d-4bc9-b355-86f3e64a1d69" />
)

> 截图待补充

## 安装

### 直接运行

从 [Releases](https://github.com/Whisper-711/ClipPilot/releases) 下载最新版 `ClipPilot.exe`，双击运行即可。

### 源码运行

```bash
# 克隆仓库
git clone https://github.com/Whisper-711/ClipPilot.git
cd ClipPilot

# 安装依赖
pip install -r requirements.txt

# 启动
python main.py --debug --show
```

## 打包

```bash
pip install pyinstaller
python build.py
```

生成的 exe 位于 `dist/ClipPilot.exe`。

## 配置

配置文件位于 `%APPDATA%/ClipPilot/config.json`，支持自定义：

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `max_history` | `200` | 最大历史记录数 |
| `poll_interval` | `0.3` | 剪贴板轮询间隔（秒） |
| `hotkey_modifiers` | `["alt", "ctrl"]` | 全局热键修饰键 |
| `hotkey_key` | `"v"` | 全局热键按键 |
| `window_width` | `520` | 窗口宽度 |
| `window_height` | `650` | 窗口高度 |
| `translator_proxy` | `""` | 翻译代理地址（如 `http://127.0.0.1:7890`） |
| `translator_custom_url` | `""` | 自定义翻译 API 地址（如 `google.cn`） |

## 技术栈

- **前端**: HTML / CSS / JavaScript（PyWebView + WebView2）
- **后端**: Python
- **翻译**: deep-translator（Google Translate）
- **打包**: PyInstaller

## 许可证

MIT
