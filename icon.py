"""应用图标生成。"""
from PIL import Image, ImageDraw, ImageFont

_SIZE = 64


def create_icon() -> Image.Image:
    """返回 64x64 RGBA 托盘/窗口图标。"""
    img = Image.new("RGBA", (_SIZE, _SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 剪贴板主体
    draw.rounded_rectangle([10, 6, 54, 58], radius=6, fill=(0, 110, 210, 255))
    draw.rounded_rectangle([14, 12, 50, 54], radius=4, fill=(255, 255, 255, 200))

    # "T" 字母（翻译）
    try:
        font = ImageFont.truetype("segoeui.ttf", 28)
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), "T", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (_SIZE - tw) // 2 - bbox[0]
    ty = (_SIZE - th) // 2 - bbox[1]
    draw.text((tx, ty), "T", fill=(0, 110, 210, 255), font=font)

    return img
