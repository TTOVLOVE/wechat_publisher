"""微信公众平台发布工具"""

version = "0.1.0"

import json
import requests

WECHAT_API_BASE = "https://api.weixin.qq.com"

# ── Error code mapping ────────────────────────────────────────────
ERROR_MESSAGES = {
    40001: "AppSecret 错误或 access_token 无效",
    40014: "access_token 无效",
    42001: "access_token 过期",
    40007: "media_id 无效",
    44002: "内容为空",
    45009: "接口调用超出限制",
    48001: "API 功能未授权，请确认公众号类型",
    40125: "AppSecret 错误",
}


def _api_request(
    method: str,
    path: str,
    access_token: str = None,
    timeout: int = 30,
    retry_on_token_error: bool = True,
    _retry_count: int = 0,
    **kwargs,
) -> dict:
    """统一 API 请求封装 — 自动处理 access_token 和错误重试。

    Args:
        method: HTTP 方法 ("GET" 或 "POST")
        path: API 路径（例如 "/cgi-bin/token"）
        access_token: access_token 字符串，如果未在 URL 中则自动拼接
        timeout: 请求超时秒数
        retry_on_token_error: 遇到 token 错误时是否自动刷新重试
        _retry_count: 内部重试计数（调用者不要传入）

    Returns:
        API 响应的 dict

    Raises:
        RuntimeError: 当 API 返回错误时
    """
    url = path if path.startswith("http") else f"{WECHAT_API_BASE}{path}"

    # 自动拼接 access_token（如果 URL 中还没有）
    if access_token and "access_token=" not in url:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}access_token={access_token}"

    headers = kwargs.pop("headers", {})
    if method.upper() == "POST" and "Content-Type" not in headers:
        headers["Content-Type"] = "application/json"

    try:
        resp = requests.request(
            method=method,
            url=url,
            timeout=timeout,
            headers=headers,
            **kwargs,
        )
        data = resp.json()
    except json.JSONDecodeError:
        raise RuntimeError(f"API 返回非 JSON 数据，状态码: {resp.status_code}")
    except requests.RequestException as e:
        raise RuntimeError(f"网络请求失败: {e}")

    errcode = data.get("errcode", 0)
    if errcode == 0:
        return data

    errmsg = data.get("errmsg", "未知错误")
    friendly_msg = ERROR_MESSAGES.get(errcode, f"API 错误 (errcode={errcode}): {errmsg}")

    # Token 过期/无效 — 刷新后重试一次
    if retry_on_token_error and errcode in (42001, 40014) and _retry_count < 1:
        from .auth import get_access_token, _clear_cached_token
        _clear_cached_token()
        new_token = get_access_token()
        return _api_request(
            method=method,
            path=path,
            access_token=new_token,
            timeout=timeout,
            retry_on_token_error=True,
            _retry_count=_retry_count + 1,
            **kwargs,
        )

    raise RuntimeError(friendly_msg)
