"""Token 管理 — 自动获取 + 文件缓存"""

import time
from .config import get_config
from . import _api_request


def _clear_cached_token():
    """清除缓存的 token（供 _api_request 在 token 失效时调用）。"""
    cfg = get_config()
    cfg.set("access_token", "")
    cfg.set("token_expires_at", 0)


def get_access_token() -> str:
    """获取有效的 access_token，自动刷新过期的 token。

    Token 缓存到 config.json，有效期 7200 秒。
    提前 5 分钟（300 秒）刷新，避免使用过期的 token。

    Returns:
        access_token 字符串

    Raises:
        RuntimeError: 获取 token 失败时抛出
    """
    cfg = get_config()
    now = int(time.time())

    # 检查缓存的 token 是否有效
    cached_token = cfg.get("access_token", "")
    expires_at = cfg.get("token_expires_at", 0)

    if cached_token and now < expires_at:
        return cached_token

    # 需要获取新 token
    appid, secret = cfg.get_credentials()

    resp = _api_request(
        "GET",
        "/cgi-bin/token",
        params={
            "grant_type": "client_credential",
            "appid": appid,
            "secret": secret,
        },
        retry_on_token_error=False,  # 获取 token 时不需要重试
    )

    token = resp.get("access_token", "")
    if not token:
        raise RuntimeError(f"获取 access_token 失败: {resp}")

    expires_in = resp.get("expires_in", 7200)
    # 提前 5 分钟刷新
    expires_at = now + expires_in - 300

    cfg.set("access_token", token)
    cfg.set("token_expires_at", expires_at)

    return token
