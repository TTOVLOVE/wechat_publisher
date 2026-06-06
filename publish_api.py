"""发布管理 — 提交发布、查询状态、删除发布"""

from . import _api_request
from .auth import get_access_token


def submit_publish(media_id: str) -> str:
    """提交发布。

    将草稿提交发布（不推送），关注者不会收到推送通知。
    订阅号每天只能群发 1 次，但发布无次数限制。

    Args:
        media_id: 草稿的 media_id

    Returns:
        publish_id 字符串
    """
    token = get_access_token()
    resp = _api_request(
        "POST",
        "/cgi-bin/freepublish/submit",
        access_token=token,
        json={"media_id": media_id},
    )
    return resp.get("publish_id", "")


def get_publish_status(publish_id: str) -> dict:
    """查询发布状态。

    Args:
        publish_id: 发布 ID

    Returns:
        发布状态 dict，包含 status 字段:
            0: 成功
            1: 发布中
            2: 原创失败
            3: 发布失败
            4: 审核中
            5: 审核失败
    """
    token = get_access_token()
    return _api_request(
        "POST",
        "/cgi-bin/freepublish/get",
        access_token=token,
        json={"publish_id": publish_id},
    )


def delete_publish(article_id: str, index: int = 1) -> bool:
    """删除已发布的文章。

    Args:
        article_id: 文章 ID（格式: msgid_index，如 "224748_1"）
        index: 文章在发布中的位置（从 1 开始，默认 1）

    Returns:
        True 表示删除成功
    """
    token = get_access_token()
    _api_request(
        "POST",
        "/cgi-bin/freepublish/delete",
        access_token=token,
        json={
            "article_id": article_id,
            "index": index,
        },
    )
    return True
