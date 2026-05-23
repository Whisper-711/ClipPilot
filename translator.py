import hashlib
import logging
import os

from deep_translator import GoogleTranslator

import config

logger = logging.getLogger(__name__)

_CJK_RANGES = (
    (0x4E00, 0x9FFF),
    (0x3400, 0x4DBF),
    (0x2E80, 0x2EFF),
    (0xF900, 0xFAFF),
)

# deep_translator 使用 zh-CN 而非 zh
_GOOGLE_LANG_MAP = {'zh': 'zh-CN', 'en': 'en'}
_TARGET_MAP = {'zh': 'en', 'en': 'zh'}

# 如果用户配置了代理，在此设置
_PROXY_CONFIGURED = False


def _ensure_proxy():
    """从配置读取代理设置，设置 HTTPS_PROXY 环境变量（仅执行一次）。"""
    global _PROXY_CONFIGURED
    if _PROXY_CONFIGURED:
        return
    _PROXY_CONFIGURED = True
    proxy = config.load().get('translator_proxy', '')
    if proxy:
        os.environ.setdefault('HTTPS_PROXY', proxy)
        os.environ.setdefault('HTTP_PROXY', proxy)
        logger.info("翻译代理已设置: %s", proxy)


def detect_lang(text: str) -> str:
    for ch in text[:200]:
        cp = ord(ch)
        for lo, hi in _CJK_RANGES:
            if lo <= cp <= hi:
                return 'zh'
    return 'en'


class Translator:
    def __init__(self, db):
        self.db = db
        self._translators = {}
        _ensure_proxy()

    def _get_translator(self, source, target):
        key = (source, target)
        if key not in self._translators:
            gsrc = _GOOGLE_LANG_MAP.get(source, source)
            gtgt = _GOOGLE_LANG_MAP.get(target, target)
            # 支持自定义 API 基础地址（google.cn 或镜像站）
            custom_url = config.load().get('translator_custom_url', '')
            if custom_url:
                self._translators[key] = GoogleTranslator(
                    source=gsrc, target=gtgt, custom_url=custom_url)
            else:
                self._translators[key] = GoogleTranslator(
                    source=gsrc, target=gtgt, timeout=8)
        return self._translators[key]

    def translate(self, text: str):
        """返回 (翻译结果, 源语言, 是否命中缓存)"""
        if not text or not text.strip():
            return '', 'unknown', False

        content_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()

        # 查缓存
        cached = self.db.get_cached_translation(content_hash)
        if cached:
            return cached[0], cached[1], True

        src = detect_lang(text)
        tgt = _TARGET_MAP.get(src, 'en')

        try:
            t = self._get_translator(src, tgt)
            result = t.translate(text)
            self.db.cache_translation(content_hash, src, result)
            return result, src, False
        except Exception as e:
            logger.warning("翻译失败: %s", e)
            return f'[翻译失败] {e}', src, False
