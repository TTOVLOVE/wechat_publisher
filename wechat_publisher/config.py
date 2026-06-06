"""配置管理 — 读写 ~/.wechat-publisher/config.json"""

import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".wechat-publisher"
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "appid": "",
    "secret": "",
    "access_token": "",
    "token_expires_at": 0,
    "default_author": "",
    "auto_publish": False,
}


class Config:
    """微信公众号配置管理器。

    配置存储在 ~/.wechat-publisher/config.json。
    首次加载时自动创建目录和空配置文件。
    """

    def __init__(self):
        self._data = DEFAULT_CONFIG.copy()
        self._loaded = False

    def _ensure_dir(self):
        """确保配置目录存在。"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict:
        """从配置文件加载，如果文件不存在则创建默认配置。"""
        self._ensure_dir()
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                self._data.update(loaded)
            except (json.JSONDecodeError, IOError):
                # 文件损坏，使用默认配置
                pass
        else:
            self.save()
        self._loaded = True
        return self._data

    def save(self):
        """保存配置到文件。"""
        self._ensure_dir()
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default=None):
        """获取配置项。"""
        if not self._loaded:
            self.load()
        return self._data.get(key, default)

    def set(self, key: str, value):
        """设置配置项并保存。"""
        if not self._loaded:
            self.load()
        self._data[key] = value
        self.save()

    def get_credentials(self) -> tuple:
        """获取 AppID 和 AppSecret。

        Returns:
            (appid, secret) 元组

        Raises:
            RuntimeError: 如果凭证未配置，打印友好提示
        """
        if not self._loaded:
            self.load()
        appid = self._data.get("appid", "")
        secret = self._data.get("secret", "")
        if not appid or not secret:
            raise RuntimeError(
                "请先配置 AppID 和 AppSecret:\n"
                "  wechat-publisher config --appid APPID --secret SECRET\n\n"
                "获取方式:\n"
                "  • 正式公众号: mp.weixin.qq.com → 设置与开发 → 基本配置\n"
                "  • 测试号: https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login"
            )
        return appid, secret


# 全局单例
_config_instance = None


def get_config() -> Config:
    """获取全局配置单例。"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
