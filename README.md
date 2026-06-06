# 微信公众号自动发布工具 (wechat-publisher)

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> 从 Markdown 一键发布文章到微信公众号 — 草稿创建、自动发布、状态追踪，全流程命令行化。

---

## 📖 目录

- [功能特性](#-功能特性)
- [项目架构](#-项目架构)
- [快速开始](#-快速开始)
  - [1. 环境要求](#1-环境要求)
  - [2. 安装](#2-安装)
  - [3. 获取凭证](#3-获取凭证)
  - [4. 配置](#4-配置)
  - [5. 发布第一篇文章](#5-发布第一篇文章)
- [使用手册](#-使用手册)
  - [一键发布（推荐）](#一键发布推荐)
  - [分步操作](#分步操作)
  - [草稿管理](#草稿管理)
  - [发布管理](#发布管理)
  - [配置管理](#配置管理)
  - [调试模式](#调试模式)
- [Markdown 写作指南](#-markdown-写作指南)
  - [支持的语法](#支持的语法)
  - [示例文章](#示例文章)
  - [封面图要求](#封面图要求)
- [模块详解](#-模块详解)
- [API 端点映射](#-api-端点映射)
- [配置文件](#-配置文件)
- [发布限制与注意事项](#-发布限制与注意事项)
- [与 Hermes Agent 集成](#-与-hermes-agent-集成)
- [错误码速查](#-错误码速查)
- [常见问题](#-常见问题)
- [开发指南](#-开发指南)
- [更新日志](#-更新日志)
- [许可证](#-许可证)

---

## ✨ 功能特性

- **Markdown 一键转换** — 将 Markdown 自动转换为微信公众号兼容的 HTML，支持标题、粗体、斜体、列表、引用、代码块、链接、图片等常见语法
- **Token 自动管理** — access_token 自动获取、缓存到本地文件、提前 5 分钟刷新，无需手动干预
- **封面图上传** — 支持本地图片自动上传为微信永久素材
- **分步操作** — 支持"创建草稿 → 提交发布 → 查询状态"的独立操作流程
- **一键发布** — `quick-publish` 一条命令完成草稿创建 + 发布
- **友好的错误提示** — 微信 API 错误码自动翻译为中文说明
- **Verbose 调试模式** — `--verbose` 输出详细的请求/响应日志

---

## 🏗 项目架构

```
wechat-publisher/
├── pyproject.toml                  # 项目元数据、依赖、entry points
├── README.md                       # 本文档
├── LICENSE                         # MIT 许可证
├── .gitignore
├── example-article.md              # 示例文章
└── wechat_publisher/               # 核心代码包
    ├── __init__.py                 # API 基类、错误码映射、_api_request()
    ├── cli.py                      # CLI 入口（Click 命令组）
    ├── config.py                   # 配置文件读写 (~/.wechat-publisher/config.json)
    ├── auth.py                     # Token 获取、缓存、刷新
    ├── formatter.py                # Markdown → 微信 HTML 转换器
    ├── drafts.py                   # 草稿 CRUD（创建/读取/列表/删除/更新）
    ├── media_api.py                # 媒体上传（正文图片、封面图）
    └── publish_api.py              # 发布管理（提交/状态/删除）
```

### 数据流

```
Markdown 文件 (.md)
        │
        ▼
  formatter.py         ← Markdown → 微信兼容 HTML
        │
        ▼
  cli.py               ← CLI 入口，组装参数
        │
        ├── media_api.py ← 上传封面图（返回 thumb_media_id）
        │
        ├── drafts.py    ← 创建草稿（返回 media_id）
        │
        └── publish_api.py ← 提交发布（返回 publish_id）
                │
                ▼
         微信公众号后台展示
```

---

## 🚀 快速开始

### 1. 环境要求

- **Python** ≥ 3.8
- **pip** 已安装
- 微信公众号 AppID 和 AppSecret（正式号或[测试号](https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login)均可）

### 2. 安装

```bash
# 进入项目目录
cd wechat-publisher

# 安装（开发模式，修改即时生效）
pip install -e .

# 或直接安装
pip install .
```

安装后，`wechat-publisher` 命令即可全局使用：

```bash
wechat-publisher --help
```

### 3. 获取凭证

#### 方案一：正式公众号

1. 登录 [mp.weixin.qq.com](https://mp.weixin.qq.com)
2. 左侧菜单 → **设置与开发** → **基本配置**
3. 在「公众号开发信息」下找到 **AppID** 和 **AppSecret**（需管理员扫码获取）
4. 将服务器 IP 加入 **IP 白名单**

#### 方案二：测试号（推荐用于开发测试）

1. 访问 [测试号管理页面](https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login)
2. 微信扫码登录
3. 页面直接显示 `appID` 和 `appsecret`
4. 在下方「测试号二维码」扫码关注你的测试号

### 4. 配置

```bash
# 设置 AppID 和 AppSecret
wechat-publisher config --appid wxXXXXXXXXXXXXXXXX --secret XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# 设置默认作者名（可选）
wechat-publisher config --author "我的名字"

# 查看当前配置
wechat-publisher config --show
```

输出示例：

```json
{
  "appid": "wx1234567890abcdef",
  "secret": "***",
  "default_author": "我的名字",
  "auto_publish": false,
  "access_token": "无",
  "token_expires_at": 0
}
```

### 5. 发布第一篇文章

```bash
# 使用项目自带的示例文章
wechat-publisher quick-publish \
  --title "我的第一篇文章" \
  --content-file example-article.md \
  --author "我的名字"
```

输出示例：

```
✓ 草稿已创建: LwB_xxxxxxxxxx
正在提交发布…
✓ 一键发布成功！
  media_id:   LwB_xxxxxxxxxx
  publish_id: 1234567890
  查询状态:   wechat-publisher publish status --publish-id 1234567890
```

---

## 📚 使用手册

### 一键发布（推荐）

```bash
wechat-publisher quick-publish \
  --title "文章标题" \
  --content-file article.md \
  [--author "作者名"] \
  [--thumb-image cover.jpg] \
  [--verbose]
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `--title` | ✅ | 文章标题，最多 64 字 |
| `--content-file` | ✅ | Markdown 文件路径（.md）或 HTML 文件路径（.html） |
| `--author` | ❌ | 作者名，不填则使用配置中的默认值 |
| `--thumb-image` | ❌ | 封面图片路径（JPG/PNG，≤2MB） |
| `--verbose`, `-v` | ❌ | 显示详细调试日志 |

### 分步操作

```bash
# 步骤 1：创建草稿
wechat-publisher draft create \
  --title "文章标题" \
  --content-file article.md \
  [--author "作者名"] \
  [--digest "摘要（可选，不填自动截取前54字）"] \
  [--thumb-image cover.jpg] \
  [--source-url https://example.com/original]

# 步骤 2：提交发布
wechat-publisher publish submit --media-id MEDIA_ID

# 步骤 3：查询发布状态
wechat-publisher publish status --publish-id PUBLISH_ID
```

### 草稿管理

```bash
# 列出所有草稿
wechat-publisher draft list
wechat-publisher draft list --offset 0 --count 20

# 获取草稿详情
wechat-publisher draft get --media-id MEDIA_ID

# 删除草稿
wechat-publisher draft delete --media-id MEDIA_ID
```

### 发布管理

```bash
# 查询发布状态
wechat-publisher publish status --publish-id PUBLISH_ID

# 删除已发布的文章
wechat-publisher publish delete --article-id ARTICLE_ID --index 1
```

### 配置管理

```bash
# 设置凭证
wechat-publisher config --appid wxXXXX --secret XXXX

# 设置默认作者
wechat-publisher config --author "作者名"

# 查看配置
wechat-publisher config --show
```

### 调试模式

在任意命令后添加 `--verbose`（或 `-v`）可查看详细的 API 请求/响应信息和内部处理日志：

```bash
wechat-publisher quick-publish --title "测试" --content-file article.md --verbose
```

---

## ✍️ Markdown 写作指南

### 支持的语法

| Markdown 语法 | 转换结果 | 效果描述 |
|---------------|---------|----------|
| `# 标题` ~ `###### 标题` | `<h1>` ~ `<h6>` | 六级标题 |
| `**加粗文字**` | `<strong>` | **加粗** |
| `*斜体文字*` | `<em>` | *斜体* |
| `- 列表项` / `* 列表项` | `<ul><li>` | 无序列表 |
| `1. 列表项` | `<ol><li>` | 有序列表 |
| `> 引用文字` | `<blockquote>` | 引用块 |
| `---` | `<hr>` | 分隔线 |
| `[链接文字](https://url)` | `<a>` | 超链接 |
| `` `行内代码` `` | `<code>` | 行内代码 |
| ` ```代码块``` ` | `<pre><code>` | 多行代码块 |
| `![图片](path)` | `<!-- IMAGE: ... -->` | 图片占位符 |
| 普通段落 | `<p>` | 正文段落 |

### 示例文章

项目中包含 `example-article.md`，展示了完整的 Markdown 语法：

```markdown
# 微信公众号排版测试

**这是一篇测试文章**，用于验证 *wechat-publisher* 的格式转换能力。

## 特色功能

- Markdown 一键转换
- Token 自动刷新
- 封面图自动上传
- 友好的命令行界面

## 代码示例

def hello_world():
    print("Hello, 微信公众号!")

> 不要限制你的想象力 — 从 Markdown 到发布，只需一条命令。

---

感谢阅读！
```

### 封面图要求

- **尺寸建议**：
  - 2.35:1 裁剪（推荐 900×383 或 900×500）
  - 1:1 裁剪（200×200，用于小图模式）
- **格式**：JPG、PNG
- **大小**：≤ 2MB
- **上传方式**：封面图自动上传到微信永久素材库，获取 `thumb_media_id`

---

## 🔧 模块详解

### `__init__.py` — API 基础设施

包含微信 API 基地址、错误码映射、以及统一的 `_api_request()` 请求封装：

```python
# 核心功能
_api_request(method, path, access_token, timeout, retry_on_token_error)
→ dict

# 错误码映射
ERROR_MESSAGES = {
    40001: "AppSecret 错误或 access_token 无效",
    40014: "access_token 无效",
    42001: "access_token 过期",
    # ...
}
```

**自动重试机制**：当 API 返回 Token 过期（42001）或无效（40014）时，自动清除缓存、刷新 Token、重试一次。

### `config.py` — 配置管理

配置存储路径：`~/.wechat-publisher/config.json`

- **Config 类**：配置文件的读写封装，支持 lazy loading
- **get_config()**：全局单例，避免重复加载
- **get_credentials()**：获取凭证时自动校验是否已配置，未配置则打印友好提示

### `auth.py` — Token 管理

- **get_access_token()**：获取有效 Token，自动判断是否需要刷新
- **Token 缓存策略**：缓存到 config.json，有效期 7200 秒，提前 300 秒（5 分钟）刷新
- **自动刷新**：Token 过期时通过 `_api_request` 的 `retry_on_token_error` 机制自动处理

### `formatter.py` — Markdown 转换器

采用**逐行解析**策略，支持：

- 块级元素：标题、代码块、引用、列表（有序/无序）、分隔线、段落
- 行内元素：粗体、斜体、行内代码、链接、图片
- HTML 转义：代码块内自动转义 `&<>`
- 内联样式表：生成适配微信公众号的内联 CSS

**图片处理说明**：正文中的 Markdown 图片语法 `![alt](path)` 会被替换为 HTML 注释占位符 `<!-- IMAGE: alt | path -->`，因为微信要求正文图片必须先上传到微信 CDN 才能使用。后续版本将支持自动上传并替换。

### `media_api.py` — 媒体上传

- **upload_body_image(path) → URL**：上传正文图片到微信 CDN，返回微信 CDN URL
- **upload_thumb(path) → media_id**：上传封面图到微信永久素材库，返回 media_id

| 接口 | 端点 | 用途 |
|------|------|------|
| 正文图片 | `POST /cgi-bin/media/uploadimg` | 返回 CDN URL |
| 封面图 | `POST /cgi-bin/material/add_material` | 返回 media_id |

### `drafts.py` — 草稿管理

完整的草稿 CRUD 操作：

| 函数 | 微信 API | 说明 |
|------|----------|------|
| `create_draft()` | `POST /cgi-bin/draft/add` | 创建草稿，返回 media_id |
| `get_draft(media_id)` | `POST /cgi-bin/draft/get` | 获取草稿详情 |
| `list_drafts(offset, count)` | `POST /cgi-bin/draft/batchget` | 分页获取草稿列表 |
| `delete_draft(media_id)` | `POST /cgi-bin/draft/delete` | 删除草稿 |
| `update_draft(media_id, ...)` | `POST /cgi-bin/draft/update` | 更新草稿（CLI 暂未暴露） |

### `publish_api.py` — 发布管理

| 函数 | 微信 API | 说明 |
|------|----------|------|
| `submit_publish(media_id)` | `POST /cgi-bin/freepublish/submit` | 提交发布（不推送） |
| `get_publish_status(publish_id)` | `POST /cgi-bin/freepublish/get` | 查询发布状态 |
| `delete_publish(article_id)` | `POST /cgi-bin/freepublish/delete` | 删除已发布文章 |

### `cli.py` — 命令行界面

基于 [Click](https://click.palletsprojects.com/) 构建的 CLI：

```
wechat-publisher
├── config          # 配置管理
├── draft           # 草稿管理
│   ├── create
│   ├── list
│   ├── get
│   └── delete
├── publish         # 发布管理
│   ├── submit
│   ├── status
│   └── delete
└── quick-publish   # 一键发布（创建草稿 + 提交发布）
```

---

## 🌐 API 端点映射

| 功能 | HTTP 方法 | 端点 | 说明 |
|------|-----------|------|------|
| 获取 Token | GET | `/cgi-bin/token` | 通过 AppID/Secret 获取 access_token |
| 创建草稿 | POST | `/cgi-bin/draft/add` | 创建图文草稿 |
| 获取草稿 | POST | `/cgi-bin/draft/get` | 获取单个草稿详情 |
| 草稿列表 | POST | `/cgi-bin/draft/batchget` | 分页获取草稿列表 |
| 删除草稿 | POST | `/cgi-bin/draft/delete` | 删除草稿 |
| 更新草稿 | POST | `/cgi-bin/draft/update` | 更新已有草稿内容 |
| 提交发布 | POST | `/cgi-bin/freepublish/submit` | 发布草稿（不推送） |
| 发布状态 | POST | `/cgi-bin/freepublish/get` | 查询发布状态 |
| 删除发布 | POST | `/cgi-bin/freepublish/delete` | 删除已发布文章 |
| 上传正文图片 | POST | `/cgi-bin/media/uploadimg` | 上传图片到微信 CDN |
| 上传封面图 | POST | `/cgi-bin/material/add_material` | 上传永久素材（封面） |

> **注意**：所有 API 调用需要在白名单 IP 环境下发请求。测试号无 IP 白名单限制。

---

## ⚙️ 配置文件

配置文件位于 `~/.wechat-publisher/config.json`：

```json
{
  "appid": "wx1234567890abcdef",
  "secret": "your-app-secret",
  "access_token": "78_xxxxxxxxxxxxxx",
  "token_expires_at": 1718000000,
  "default_author": "",
  "auto_publish": false
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `appid` | string | 微信公众号 AppID |
| `secret` | string | 微信公众号 AppSecret |
| `access_token` | string | 缓存的 access_token（自动管理） |
| `token_expires_at` | integer | Token 过期时间戳（Unix 秒） |
| `default_author` | string | 默认作者名（创建草稿时的回退值） |
| `auto_publish` | boolean | 是否自动发布（暂未实现功能） |

---

## ⚠️ 发布限制与注意事项

### 微信平台限制

| 项目 | 限制 |
|------|------|
| **订阅号群发** | 每天 **1 次** |
| **服务号群发** | 每月 **4 次** |
| **发布（不推送）** | **无次数限制** ✅ |
| **草稿数量** | 无限制 |
| **单篇文章字数** | 最多 20,000 字 |
| **标题字数** | 最多 64 字 |
| **封面图大小** | ≤ 2MB |
| **接口调用频率** | 有 QPS 限制（正常使用不会触发） |

### 重要说明

1. **「发布」vs「群发」**：本工具调用的是「发布」接口（`freepublish`），即文章发布后粉丝**不会收到推送通知**，但可在公众号主页看到。如需群发（粉丝收到推送），请在公众平台后台手动操作。

2. **正文图片**：当前版本将 Markdown 中的图片语法替换为 HTML 注释占位符。如需在正文中使用图片，请先调用 `upload_body_image()` 获取微信 CDN URL，然后在 HTML 中直接使用 `<img src="URL">`。

3. **IP 白名单**：正式公众号需要在后台配置服务器 IP 白名单。如果遇到 `40164` 错误，请检查 IP 白名单设置。测试号不受此限制。

4. **安全存储**：AppSecret 明文存储在 `~/.wechat-publisher/config.json` 中。请确保服务器的文件权限设置正确（建议 `chmod 600 ~/.wechat-publisher/config.json`）。

---

## 🤖 与 Hermes Agent 集成

### 作为 Skill 使用

项目中包含 Hermes Agent 的 skill 定义文件，位于 skill 系统 `social-media/wechat-publisher/`。当 Hermes Agent 加载此 skill 后，agent 可以直接调用 `wechat-publisher` CLI 完成公众号发布。

### 定时发布日报示例

使用 Hermes cronjob 功能设置每日自动推送：

```bash
# 在 Hermes Agent 中创建定时任务
hermes cron create \
  --name "微信日报发布" \
  --schedule "0 9 * * *" \
  --prompt "生成今日信息安全日报并发布到微信公众号" \
  --skills wechat-publisher,cybersecurity-news-digest
```

### 手动触发

在 Hermes Agent 对话中直接请求：

> "帮我把 article.md 发布到微信公众号"
> "用微信测试号发布今日日报"

Agent 会自动加载 `wechat-publisher` skill 并执行发布流程。

---

## 🚨 错误码速查

| 错误码 | 中文含义 | 解决方案 |
|--------|----------|----------|
| 0 | 请求成功 | — |
| 40001 | AppSecret 错误或 Token 无效 | 检查 AppSecret 是否正确 |
| 40014 | access_token 无效 | 自动刷新重试 |
| 40007 | media_id 无效 | 检查 media_id 是否正确 |
| 42001 | access_token 过期 | 自动刷新重试 |
| 44002 | 内容为空 | 检查文章内容是否为空 |
| 45009 | 接口调用超限 | 等待后重试 |
| 48001 | API 未授权 | 确认公众号类型和接口权限 |
| 40125 | AppSecret 错误 | 检查 AppSecret |
| 40164 | IP 不在白名单 | 在公众平台配置 IP 白名单 |

---

## ❓ 常见问题

### Q: 安装时报错 "No module named 'click'"

```bash
pip install click>=8.0 requests>=2.25 markdown>=3.0
```

或直接安装项目依赖：

```bash
cd wechat-publisher && pip install -e .
```

### Q: 发布后公众号里看不到文章？

- 本工具使用「发布」接口（不推送），文章会出现在公众号主页，但不会推送通知给粉丝
- 确认 `publish status` 返回的状态码为 `0`（成功）
- 部分公众号类型可能需要手动开启「发布」功能

### Q: Token 总是过期？

Token 自动缓存在 `config.json` 中，有效期 7200 秒，提前 5 分钟刷新。如果频繁出现 Token 失效错误：

1. 检查系统时间是否准确（`date`）
2. 删除配置文件重新设置：`rm ~/.wechat-publisher/config.json`
3. 使用 `--verbose` 查看详细错误日志

### Q: 如何发布多图文？

当前版本支持创建单篇草稿。多图文需要创建包含多篇文章的草稿（通过 `articles` 参数传入数组），该功能已预留但 CLI 暂未暴露。可通过 Python API 直接调用：

```python
from wechat_publisher.drafts import create_draft
# 传入 multiple articles 即可
```

### Q: 正文中的图片不显示？

当前版本会将 Markdown 图片替换为 HTML 注释占位符。使用前需：

1. `upload_body_image(path)` 上传图片到微信 CDN
2. 在 HTML 中手动替换占位符为 `<img src="CDN_URL">`

后续版本将支持自动上传正文图片。

---

## 🛠 开发指南

### 本地开发

```bash
# 克隆/进入项目
cd wechat-publisher

# 安装开发依赖
pip install -e .

# 测试命令行
wechat-publisher --help
```

### 依赖项

所有依赖声明在 `pyproject.toml` 中：

| 依赖 | 最低版本 | 用途 |
|------|----------|------|
| `click` | ≥ 8.0 | CLI 框架 |
| `requests` | ≥ 2.25 | HTTP 请求 |
| `markdown` | ≥ 3.0 | Markdown 解析（保留以备后续扩展） |

### 运行测试

```bash
# 使用测试号测试（推荐）
wechat-publisher config --appid <TEST_APPID> --secret <TEST_SECRET>

# 创建测试草稿
wechat-publisher draft create \
  --title "测试文章" \
  --content-file example-article.md

# 检查结果
wechat-publisher draft list
```

### 添加新功能

核心模块关系：

```
cli.py ─► drafts.py ─► __init__.py:_api_request() ─► 微信 API
       ─► publish_api.py ─┘
       ─► media_api.py ───┘
       ─► formatter.py（独立，不调用 API）
       ─► config.py（独立）
       ─► auth.py ─► config.py + __init__.py
```

要添加新的微信 API 功能：

1. 在对应模块中（如 `drafts.py`）编写函数
2. 使用 `_api_request()` 调用微信 API
3. 在 `cli.py` 中添加 CLI 命令
4. 更新 `__init__.py` 中的 `ERROR_MESSAGES`（如需要）

---

## 📝 更新日志

### v0.1.0（当前版本）

- ✅ 完整的草稿管理：创建、读取、列表、删除、更新
- ✅ 发布管理：提交发布、查询状态、删除发布
- ✅ Markdown → 微信 HTML 转换器
- ✅ Token 自动管理（缓存 + 提前刷新）
- ✅ 封面图自动上传
- ✅ 正文图片上传支持（API 层面）
- ✅ Click CLI 界面
- ✅ 一键发布命令 `quick-publish`
- ✅ 友好的中文错误提示
- ✅ `--verbose` 调试模式

---

## 📄 许可证

MIT License

---

**项目创建**：由 Hermes Agent 协助开发  
**问题反馈**：在微信对话中直接 @ Hermes Agent
