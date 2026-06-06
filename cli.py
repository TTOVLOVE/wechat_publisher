"""命令行入口 — 微信公众号发布工具"""

import json
import os
import sys

import click

from . import version
from .config import get_config
from .auth import get_access_token
from .drafts import create_draft, list_drafts, get_draft, delete_draft
from .formatter import markdown_to_wechat_html
from .media_api import upload_body_image, upload_thumb
from .publish_api import submit_publish, get_publish_status, delete_publish


# ── 全局 verbose 标记 ──
_verbose = False


def _log(msg: str):
    """打印日志（verbose 模式下）。"""
    if _verbose:
        click.echo(f"[DEBUG] {msg}", err=True)


def _read_content_file(content_file: str) -> tuple:
    """读取内容文件，支持 .md 和 .html。

    如果是 .md 文件，自动转换为微信 HTML；
    如果是 .html 文件，直接读取。

    Returns:
        (content, source_format) 元组
    """
    if not os.path.isfile(content_file):
        raise click.FileError(content_file, f"文件不存在: {content_file}")

    with open(content_file, "r", encoding="utf-8") as f:
        raw = f.read()

    ext = os.path.splitext(content_file)[1].lower()
    if ext in (".md", ".markdown"):
        _log(f"检测到 Markdown 文件，正在转换为微信 HTML…")
        return markdown_to_wechat_html(raw), "markdown"
    else:
        return raw, "html"


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="显示详细调试信息")
def cli(verbose):
    """微信公众号发布工具 — 从 Markdown 一键发布到微信公众号。

    支持功能:
      \b
      • 配置管理: wechat-publisher config
      • 草稿管理: wechat-publisher draft
      • 发布管理: wechat-publisher publish
      • 一键发布: wechat-publisher quick-publish

    使用测试号免费体验:
      https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login
    """
    global _verbose
    _verbose = verbose


# ═══════════════════════════════════════════════════════════════════
#  config 命令
# ═══════════════════════════════════════════════════════════════════

@cli.command("config")
@click.option("--appid", help="微信公众号 AppID")
@click.option("--secret", help="微信公众号 AppSecret")
@click.option("--author", help="默认作者名")
@click.option("--auto-publish", is_flag=True, help="启用自动发布")
@click.option("--show", is_flag=True, help="显示当前配置")
def config_command(appid, secret, author, auto_publish, show):
    """配置管理 — 设置或查看 AppID、AppSecret 等。

    \b
    示例:
      wechat-publisher config --appid wx123 --secret abc456
      wechat-publisher config --show
    """
    cfg = get_config()

    if show or not any([appid, secret, author, auto_publish]):
        # 显示配置
        data = {
            "appid": cfg.get("appid", ""),
            "secret": "***" if cfg.get("secret", "") else "",
            "default_author": cfg.get("default_author", ""),
            "auto_publish": cfg.get("auto_publish", False),
            "access_token": "已缓存" if cfg.get("access_token", "") else "无",
            "token_expires_at": cfg.get("token_expires_at", 0),
        }
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        if not cfg.get("appid") and not cfg.get("secret"):
            click.echo()
            click.echo("请先配置 AppID 和 AppSecret:")
            click.echo("  wechat-publisher config --appid APPID --secret SECRET")
            click.echo()
            click.echo("获取方式:")
            click.echo("  正式公众号: mp.weixin.qq.com → 设置与开发 → 基本配置")
            click.echo("  测试号: https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login")
        return

    if appid:
        cfg.set("appid", appid)
        click.echo(f"✓ AppID 已设置: {appid}")
    if secret:
        cfg.set("secret", secret)
        click.echo("✓ AppSecret 已设置")
    if author:
        cfg.set("default_author", author)
        click.echo(f"✓ 默认作者已设置: {author}")
    if auto_publish:
        cfg.set("auto_publish", True)
        click.echo("✓ 自动发布已启用")


# ═══════════════════════════════════════════════════════════════════
#  draft 子命令组
# ═══════════════════════════════════════════════════════════════════

@cli.group()
def draft():
    """草稿管理 — 创建、查看、列出、删除草稿。"""
    pass


@draft.command("create")
@click.option("--title", required=True, help="文章标题")
@click.option("--content-file", required=True, type=click.Path(exists=True), help="内容文件路径（.md 或 .html）")
@click.option("--author", help="作者名（可选）")
@click.option("--digest", help="摘要（可选，不填则抓取前 54 字）")
@click.option("--thumb-image", type=click.Path(exists=True), help="封面图路径（可选）")
@click.option("--source-url", help="原文链接（可选）")
def draft_create(title, content_file, author, digest, thumb_image, source_url):
    """创建草稿。

    \b
    示例:
      wechat-publisher draft create --title "我的文章" --content-file article.md
      wechat-publisher draft create --title "我的文章" --content-file article.md --thumb-image cover.jpg
    """
    try:
        content, fmt = _read_content_file(content_file)
        _log(f"读取内容文件: {content_file} (格式: {fmt})，共 {len(content)} 字")

        # 使用配置中的默认作者
        if not author:
            author = get_config().get("default_author", "")

        media_id = create_draft(
            title=title,
            content=content,
            author=author,
            digest=digest or "",
            thumb_image_path=thumb_image or "",
            source_url=source_url or "",
        )

        click.echo(f"✓ 草稿创建成功！")
        click.echo(f"  media_id: {media_id}")
        click.echo(f"  下一步: wechat-publisher publish submit --media-id {media_id}")

    except Exception as e:
        click.echo(f"✗ 创建草稿失败: {e}", err=True)
        sys.exit(1)


@draft.command("list")
@click.option("--offset", type=int, default=0, help="起始位置（默认 0）")
@click.option("--count", type=int, default=20, help="每页数量（默认 20，最大 20）")
def draft_list(offset, count):
    """列出草稿。"""
    try:
        resp = list_drafts(offset=offset, count=count)
        total = resp.get("total_count", 0)
        items = resp.get("item", [])

        if not items:
            click.echo("暂无草稿。")
            return

        click.echo(f"共 {total} 个草稿（显示 {offset}-{offset + len(items) - 1}）:\n")
        for item in items:
            media_id = item.get("media_id", "")
            update_time = item.get("update_time", "")
            content_info = item.get("content", {}).get("news_item", [{}])
            if content_info:
                title = content_info[0].get("title", "无标题")
            else:
                title = "无标题"
            click.echo(f"  • {title}")
            click.echo(f"    media_id: {media_id}  更新时间: {update_time}")
            click.echo()

    except Exception as e:
        click.echo(f"✗ 获取草稿列表失败: {e}", err=True)
        sys.exit(1)


@draft.command("get")
@click.option("--media-id", required=True, help="草稿 media_id")
def draft_get(media_id):
    """获取草稿详情。"""
    try:
        resp = get_draft(media_id)
        click.echo(json.dumps(resp, indent=2, ensure_ascii=False))
    except Exception as e:
        click.echo(f"✗ 获取草稿失败: {e}", err=True)
        sys.exit(1)


@draft.command("delete")
@click.option("--media-id", required=True, help="草稿 media_id")
@click.confirmation_option(prompt="确认删除此草稿？")
def draft_delete(media_id):
    """删除草稿。"""
    try:
        delete_draft(media_id)
        click.echo(f"✓ 草稿已删除: {media_id}")
    except Exception as e:
        click.echo(f"✗ 删除草稿失败: {e}", err=True)
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════
#  publish 子命令组
# ═══════════════════════════════════════════════════════════════════

@cli.group()
def publish():
    """发布管理 — 提交发布、查询状态、删除发布。"""
    pass


@publish.command("submit")
@click.option("--media-id", required=True, help="草稿的 media_id")
def publish_submit(media_id):
    """提交发布。

    将草稿发布到公众号（不推送通知，关注者不会收到推送）。
    如需群发推送，请在公众平台后台操作。
    """
    try:
        publish_id = submit_publish(media_id)
        click.echo(f"✓ 发布已提交！")
        click.echo(f"  publish_id: {publish_id}")
        click.echo(f"  查询状态: wechat-publisher publish status --publish-id {publish_id}")
    except Exception as e:
        click.echo(f"✗ 发布失败: {e}", err=True)
        sys.exit(1)


@publish.command("status")
@click.option("--publish-id", required=True, help="发布 ID")
def publish_status(publish_id):
    """查询发布状态。

    状态码说明:
      0: 成功
      1: 发布中
      2: 原创失败
      3: 发布失败
      4: 审核中
      5: 审核失败
    """
    try:
        resp = get_publish_status(publish_id)
        click.echo(json.dumps(resp, indent=2, ensure_ascii=False))

        # 友好提示
        status_map = {
            0: "✓ 发布成功",
            1: "⏳ 发布中，请稍候…",
            2: "✗ 原创声明失败",
            3: "✗ 发布失败",
            4: "⏳ 审核中…",
            5: "✗ 审核失败",
        }
        status_code = resp.get("publish_status", -1)
        if status_code in status_map:
            click.echo(status_map[status_code])

    except Exception as e:
        click.echo(f"✗ 查询状态失败: {e}", err=True)
        sys.exit(1)


@publish.command("delete")
@click.option("--article-id", required=True, help="文章 ID（格式: msgid_index，如 224748_1）")
@click.option("--index", type=int, default=1, help="文章位置（默认 1）")
@click.confirmation_option(prompt="确认删除此发布？")
def publish_delete(article_id, index):
    """删除已发布的文章。"""
    try:
        delete_publish(article_id, index)
        click.echo(f"✓ 发布已删除: {article_id}")
    except Exception as e:
        click.echo(f"✗ 删除发布失败: {e}", err=True)
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════
#  quick-publish 命令
# ═══════════════════════════════════════════════════════════════════

@cli.command("quick-publish")
@click.option("--title", required=True, help="文章标题")
@click.option("--content-file", required=True, type=click.Path(exists=True), help="内容文件路径（.md 或 .html）")
@click.option("--author", help="作者名（可选）")
@click.option("--thumb-image", type=click.Path(exists=True), help="封面图路径（可选）")
def quick_publish(title, content_file, author, thumb_image):
    """一键发布 — 创建草稿并立即提交发布。

    \b
    示例:
      wechat-publisher quick-publish --title "我的文章" --content-file article.md
      wechat-publisher quick-publish --title "我的文章" --content-file article.md --thumb-image cover.jpg
    """
    try:
        # 1. 读取内容
        content, fmt = _read_content_file(content_file)
        _log(f"读取内容文件: {content_file} (格式: {fmt})，共 {len(content)} 字")

        if not author:
            author = get_config().get("default_author", "")

        # 2. 上传封面图
        thumb_id = ""
        if thumb_image:
            click.echo("正在上传封面图…")
            thumb_id = upload_thumb(thumb_image)
            _log(f"封面图 media_id: {thumb_id}")

        # 3. 创建草稿
        click.echo("正在创建草稿…")
        media_id = create_draft(
            title=title,
            content=content,
            author=author,
            thumb_media_id=thumb_id,
        )
        click.echo(f"✓ 草稿已创建: {media_id}")

        # 4. 提交发布
        click.echo("正在提交发布…")
        publish_id = submit_publish(media_id)

        click.echo()
        click.echo("✓ 一键发布成功！")
        click.echo(f"  media_id:   {media_id}")
        click.echo(f"  publish_id: {publish_id}")
        click.echo(f"  查询状态:   wechat-publisher publish status --publish-id {publish_id}")

    except Exception as e:
        click.echo(f"✗ 发布失败: {e}", err=True)
        if _verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
