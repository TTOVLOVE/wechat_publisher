"""草稿管理 — 创建、查询、列表、删除、更新草稿"""

import time
from . import _api_request
from .auth import get_access_token
from .media_api import upload_thumb


def create_draft(
    title: str,
    content: str,
    author: str = "",
    digest: str = "",
    thumb_media_id: str = "",
    thumb_image_path: str = "",
    source_url: str = "",
    need_open_comment: int = 0,
) -> str:
    """创建草稿。

    Args:
        title: 标题
        content: 正文 HTML 内容
        author: 作者名（可选，默认使用配置中的 default_author）
        digest: 摘要（可选，不填则自动抓取正文前 54 字）
        thumb_media_id: 封面图 media_id（与 thumb_image_path 二选一）
        thumb_image_path: 封面图本地路径（自动上传并获取 media_id）
        source_url: 原文链接
        need_open_comment: 是否开启留言（0 否 1 是）

    Returns:
        media_id 字符串
    """
    token = get_access_token()

    # 上传封面图（如果提供了本地路径）
    if thumb_image_path and not thumb_media_id:
        thumb_media_id = upload_thumb(thumb_image_path)

    article = {
        "title": title,
        "content": content,
    }

    if author:
        article["author"] = author
    if digest:
        article["digest"] = digest
    if thumb_media_id:
        article["thumb_media_id"] = thumb_media_id
    if source_url:
        article["content_source_url"] = source_url
    article["need_open_comment"] = need_open_comment

    resp = _api_request(
        "POST",
        "/cgi-bin/draft/add",
        access_token=token,
        json={"articles": [article]},
    )

    return resp["media_id"]


def get_draft(media_id: str) -> dict:
    """获取草稿详情。

    Args:
        media_id: 草稿 media_id

    Returns:
        草稿详情 dict
    """
    token = get_access_token()
    return _api_request(
        "POST",
        "/cgi-bin/draft/get",
        access_token=token,
        json={"media_id": media_id},
    )


def list_drafts(offset: int = 0, count: int = 20, no_content: int = 1) -> dict:
    """获取草稿列表。

    Args:
        offset: 起始位置
        count: 每页数量（最大 20）
        no_content: 是否不返回内容（1=不返回，0=返回）

    Returns:
        草稿列表 dict（包含 item 列表和 total_count）
    """
    token = get_access_token()
    return _api_request(
        "POST",
        "/cgi-bin/draft/batchget",
        access_token=token,
        json={
            "offset": offset,
            "count": min(count, 20),
            "no_content": no_content,
        },
    )


def delete_draft(media_id: str) -> bool:
    """删除草稿。

    Args:
        media_id: 草稿 media_id

    Returns:
        True 表示删除成功
    """
    token = get_access_token()
    _api_request(
        "POST",
        "/cgi-bin/draft/delete",
        access_token=token,
        json={"media_id": media_id},
    )
    return True


def update_draft(
    media_id: str,
    index: int,
    title: str,
    content: str,
    author: str = "",
    digest: str = "",
    thumb_media_id: str = "",
    source_url: str = "",
    need_open_comment: int = 0,
) -> bool:
    """更新草稿。

    Args:
        media_id: 草稿 media_id
        index: 要修改的文章索引（从 0 开始）
        title: 标题
        content: 正文 HTML 内容
        其余参数同 create_draft

    Returns:
        True 表示更新成功
    """
    token = get_access_token()

    article = {"title": title, "content": content}
    if author:
        article["author"] = author
    if digest:
        article["digest"] = digest
    if thumb_media_id:
        article["thumb_media_id"] = thumb_media_id
    if source_url:
        article["content_source_url"] = source_url
    article["need_open_comment"] = need_open_comment

    _api_request(
        "POST",
        "/cgi-bin/draft/update",
        access_token=token,
        json={
            "media_id": media_id,
            "index": index,
            "articles": article,
        },
    )
    return True
