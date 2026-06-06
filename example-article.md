# 微信公众号排版测试

**这是一篇测试文章**，用于验证 *wechat-publisher* 的 Markdown → 微信 HTML 转换能力。

---

## 特色功能

- Markdown 一键转换为微信公众号兼容的 HTML
- access_token 自动缓存，提前 5 分钟刷新，无需手动管理
- 封面图自动上传为微信永久素材
- 友好的中文错误提示
- **Verbose 调试模式**便于排查问题

## 支持的语法一览

下面逐个展示 wechat-publisher 支持的 Markdown 语法：

### 标题

工具支持 h1 到 h6 共六级标题，微信公众平台也能正常渲染。

### 文本样式

这段文字中有 **粗体**、*斜体*、还有 `` `行内代码` ``。

### 引用块

> 微信公众号的发布接口分两种：
> 
> - **群发**：粉丝会收到推送通知，订阅号每天限 1 次
> - **发布**：不推送通知，但无次数限制
> 
> 本工具默认使用「发布」模式，适合日报、周报等定期内容。

### 列表

#### 无序列表

- 支持 `-` 开头的无序列表
- 支持 `*` 开头的无序列表
- 可以嵌套缩进

#### 有序列表

1. 打开终端
2. 运行 `wechat-publisher quick-publish --title "标题" --content-file article.md`
3. 等待发布完成
4. 在公众号主页查看文章

### 代码块

```python
def markdown_to_wechat_html(md_text: str) -> str:
    """将 Markdown 转换为微信兼容的 HTML"""
    lines = md_text.split("\n")
    result = []
    # 逐行解析...
    return "\n".join(result)
```

### 链接

本项目使用了 [微信公众平台 API](https://developers.weixin.qq.com/doc/offiaccount/Getting_Started/Overview.html) 提供的官方接口。

---

## 发布状态码

| 状态码 | 含义 |
|--------|------|
| 0 | 发布成功 ✅ |
| 1 | 发布中 ⏳ |
| 2 | 原创失败 |
| 3 | 发布失败 |
| 4 | 审核中 ⏳ |
| 5 | 审核失败 |

---

*由 wechat-publisher v0.1.0 生成 · 测试于微信公众平台*
