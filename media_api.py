"""媒体上传 — 正文图片 + 封面图上传"""

import os
import mimetypes
from . import _api_request
from .auth import get_access_token


def _guess_mime_type(image_path: str) -> str:
    """根据文件扩展名推测 MIME 类型。"""
    mime, _ = mimetypes.guess_type(image_path)
    if mime and mime.startswith("image/"):
        return mime
    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".webp": "image/webp",
    }
    return mime_map.get(ext, "image/jpeg")


def upload_body_image(image_path: str) -> str:
    """上传正文图片到微信 CDN。

    正文图片使用 /cgi-bin/media/uploadimg 接口，
    返回微信 CDN URL，可直接在 HTML 的 <img> 中使用。

    Args:
        image_path: 本地图片路径

    Returns:
        微信 CDN URL 字符串

    Raises:
        RuntimeError: 上传失败时抛出
        FileNotFoundError: 图片不存在时抛出
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"图片文件不存在: {image_path}")

    token = get_access_token()
    filename = os.path.basename(image_path)
    mime_type = _guess_mime_type(image_path)

    with open(image_path, "rb") as f:
        resp = _api_request(
            "POST",
            "/cgi-bin/media/uploadimg",
            access_token=token,
            files={"media": (filename, f, mime_type)},
            data={"type": "image"},
        )

    return resp["url"]


def upload_thumb(image_path: str) -> str:
    """上传封面图到微信永久素材库。

    封面图使用 /cgi-bin/material/add_material 接口，
    返回 media_id，可在草稿的 thumb_media_id 中使用。

    Args:
        image_path: 本地图片路径

    Returns:
        media_id 字符串

    Raises:
        RuntimeError: 上传失败时抛出
        FileNotFoundError: 图片不存在时抛出
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"图片文件不存在: {image_path}")

    token = get_access_token()
    filename = os.path.basename(image_path)
    mime_type = _guess_mime_type(image_path)

    with open(image_path, "rb") as f:
        resp = _api_request(
            "POST",
            "/cgi-bin/material/add_material",
            access_token=token,
            params={"type": "image"},
            files={"media": (filename, f, mime_type)},
        )

    return resp["media_id"]
