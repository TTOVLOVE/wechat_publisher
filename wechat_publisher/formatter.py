"""Markdown → 微信公众号 HTML 转换器

微信公众平台支持的 HTML 标签有限:
  <h1>~<h6>, <p>, <br>, <hr>
  <strong>, <b>, <em>, <i>
  <ul>, <ol>, <li>
  <blockquote>
  <img> (src 必须是微信 CDN URL)
  <a> (href)
  <span> (style="color:...")
  <section>, <div>
  <pre>, <code>
"""

import re

# 微信友好的基础 CSS 样式
WECHAT_STYLE = """<style>
body {
    max-width: 100%;
    font-size: 16px;
    line-height: 1.8;
    color: #333;
    padding: 0 12px;
    box-sizing: border-box;
    word-wrap: break-word;
}
h1 { font-size: 24px; margin: 20px 0 16px; }
h2 { font-size: 20px; margin: 18px 0 14px; }
h3 { font-size: 18px; margin: 16px 0 12px; }
h4 { font-size: 17px; margin: 14px 0 10px; }
h5 { font-size: 16px; margin: 12px 0 8px; }
h6 { font-size: 15px; margin: 10px 0 6px; color: #666; }
p { margin: 10px 0; }
strong, b { font-weight: bold; }
em, i { font-style: italic; }
blockquote {
    margin: 12px 0;
    padding: 8px 16px;
    border-left: 4px solid #ddd;
    background: #f9f9f9;
    color: #666;
}
blockquote p { margin: 6px 0; }
ul, ol { margin: 10px 0; padding-left: 24px; }
li { margin: 4px 0; }
pre {
    margin: 12px 0;
    padding: 12px;
    background: #f5f5f5;
    border-radius: 4px;
    overflow-x: auto;
    font-size: 14px;
    line-height: 1.6;
}
code {
    background: #f0f0f0;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 14px;
    font-family: "Courier New", monospace;
}
pre code {
    background: none;
    padding: 0;
    font-size: 14px;
}
a { color: #576b95; text-decoration: none; }
hr { border: none; border-top: 1px solid #eee; margin: 20px 0; }
img { max-width: 100%; height: auto; }
</style>"""


def markdown_to_wechat_html(md_text: str) -> str:
    """将 Markdown 文本转换为微信公众号兼容的 HTML。

    支持的语法:
        # ~ ###### → <h1>~<h6>
        **text** → <strong>text</strong>
        *text* → <em>text</em>
        - item → <ul><li>item</li></ul>
        1. item → <ol><li>item</li></ol>
        > quote → <blockquote><p>quote</p></blockquote>
        [text](url) → <a href="url">text</a>
        ![alt](path) → <!-- IMAGE: alt | path -->（占位符，需后续处理）
        `code` → <code>code</code>
        ```block``` → <pre><code>block</code></pre>
        --- → <hr>
        纯文本段落 → <p>text</p>

    Args:
        md_text: Markdown 格式文本

    Returns:
        微信兼容的 HTML 字符串
    """
    lines = md_text.split("\n")
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # ── 分隔线 ──
        if re.match(r"^[-*_]{3,}\s*$", line.strip()):
            result.append("<hr>")
            i += 1
            continue

        # ── 标题 ──
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading_match:
            level = len(heading_match.group(1))
            content = _process_inline(heading_match.group(2))
            result.append(f"<h{level}>{content}</h{level}>")
            i += 1
            continue

        # ── 图片 ──
        img_match = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", line)
        if img_match:
            alt = img_match.group(1)
            path = img_match.group(2)
            # 占位符：后续可通过正文图片上传替换
            result.append(f"<!-- IMAGE: {alt} | {path} -->")
            i += 1
            continue

        # ── 行内图片（段落中的图片） ──
        # 交给 _process_inline 处理

        # ── 代码块 ──
        if line.strip().startswith("```"):
            lang = line.strip()[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```
            code_content = "\n".join(code_lines)
            # 转义 HTML
            code_content = _escape_html(code_content)
            result.append(f"<pre><code>{code_content}</code></pre>")
            continue

        # ── 引用块 ──
        if line.strip().startswith("> "):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith("> "):
                quote_lines.append(lines[i].strip()[2:])
                i += 1
            quote_text = "\n".join(quote_lines)
            quote_text = _process_inline(quote_text)
            result.append(f"<blockquote><p>{quote_text}</p></blockquote>")
            continue
        if line.strip().startswith(">"):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                raw = lines[i].strip()
                # Remove leading '>' and optional space
                quote_lines.append(raw[1:].lstrip() if len(raw) > 1 else "")
                i += 1
            quote_text = "\n".join(quote_lines)
            quote_text = _process_inline(quote_text)
            result.append(f"<blockquote><p>{quote_text}</p></blockquote>")
            continue

        # ── 无序列表 ──
        ul_match = re.match(r"^\s*[-*+]\s+(.+)$", line)
        if ul_match:
            ul_items = []
            while i < len(lines) and re.match(r"^\s*[-*+]\s+(.+)$", lines[i]):
                item_text = re.match(r"^\s*[-*+]\s+(.+)$", lines[i]).group(1)
                ul_items.append(f"<li>{_process_inline(item_text)}</li>")
                i += 1
            result.append(f"<ul>{''.join(ul_items)}</ul>")
            continue

        # ── 有序列表 ──
        ol_match = re.match(r"^\s*\d+\.\s+(.+)$", line)
        if ol_match:
            ol_items = []
            while i < len(lines) and re.match(r"^\s*\d+\.\s+(.+)$", lines[i]):
                item_text = re.match(r"^\s*\d+\.\s+(.+)$", lines[i]).group(1)
                ol_items.append(f"<li>{_process_inline(item_text)}</li>")
                i += 1
            result.append(f"<ol>{''.join(ol_items)}</ol>")
            continue

        # ── 空行（段落分隔） ──
        if line.strip() == "":
            i += 1
            continue

        # ── 普通段落 ──
        para_lines = []
        while i < len(lines) and lines[i].strip() != "":
            # Stop at special lines
            if (re.match(r"^(#{1,6})\s+", lines[i]) or
                re.match(r"^[-*_]{3,}\s*$", lines[i].strip()) or
                re.match(r"^!\[", lines[i]) or
                lines[i].strip().startswith("```") or
                lines[i].strip().startswith(">") or
                re.match(r"^\s*[-*+]\s+", lines[i]) or
                re.match(r"^\s*\d+\.\s+", lines[i])):
                break
            para_lines.append(lines[i])
            i += 1
        paragraph = " ".join(para_lines).strip()
        if paragraph:
            result.append(f"<p>{_process_inline(paragraph)}</p>")

    html_body = "\n".join(result)
    return f"{WECHAT_STYLE}\n{html_body}"


def _process_inline(text: str) -> str:
    """处理行内元素：粗体、斜体、代码、链接、图片。"""
    # 行内图片 ![alt](path)
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<!-- IMAGE: \1 | \2 -->', text)

    # 行内代码 `code`
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    # 粗体 **text**
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

    # 斜体 *text*（注意不要匹配 ** 残留）
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)

    # 链接 [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)

    return text


def _escape_html(text: str) -> str:
    """转义 HTML 特殊字符。"""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text
