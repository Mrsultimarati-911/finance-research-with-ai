# 工具接入与获取状态

## 独立 Python 环境

需要 Python 3.12+ 及公开页面网络访问。包不含解释器、虚拟环境、凭据或宿主配置。依赖范围见 [requirements.txt](../requirements.txt)，Windows/Python 3.12 可使用 [锁文件](../requirements-lock-windows-py312.txt)；其他组合不使用 `--lock`，按直接依赖安装。

```text
<python-3.12> -B -X utf8 <skill>/scripts/bootstrap.py --env <environment-directory> --lock
```

bootstrap 只在指定环境创建虚拟环境并 pip 安装，不负责 Skill 发现、MCP 配置、后台服务或凭据。环境与 Skill 可以位于不同目录，迁移后重建环境并更新实际路径。

## STDIO 接入

```text
<environment-python> -B -X utf8 <skill>/scripts/wechat_mcp.py
```

宿主通常根据配置启动进程，通过标准输入输出通信。手工打开服务器终端不代表已接入宿主。保留脚本及其资源，入口不依赖固定工作目录。

将 [JSON 示例](../examples/mcp-config.json)或 [Codex TOML 示例](../examples/codex-mcp.toml)中的两个占位符换成实际绝对路径：环境 Python 与 Skill 脚本。宿主配置规则分别处理；Codex 参考 [官方 MCP 说明](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)。Skill 目录安装参考 [官方 Skill 说明](https://learn.chatgpt.com/docs/build-skills)，应安装完整目录，不能只复制入口。安装 Skill 不会自动创建环境或接入 MCP。

## 三个只读接口

| 接口 | 参数 | 返回与宿主责任 |
| --- | --- | --- |
| `search_articles` | `account_name,query,page=1` | 状态、articles、has_next、search_url。宿主逐次检索和翻页，结合原页核对账号、日期、主题与文章标识。 |
| `read_article` | `url` | 元数据、body_markdown、图片清单、image_count、requested_url、resolved_url、source_type、completeness、warnings。宿主检查可见正文范围与来源。 |
| `read_article_images` | `article_url,start=0,count=4` | 首个文字块为 JSON 元数据，后续为成功图片的原生图片块，顺序与成功 items 对应。 |

图片索引从 0 开始，`count` 为 1–8 的单批大小；第十一张可使用 `start=10`。总图数不由批次大小限制，宿主按需要继续调用。原生图片解读需宿主提供图片块给视觉模型；只有元数据不算读图。超出资源限制时返回失败，动画只读首帧并警示。

```json
[
  {"name":"search_articles","arguments":{"account_name":"中国金融四十人论坛","query":"人工智能","page":1}},
  {"name":"read_article","arguments":{"url":"https://mp.weixin.qq.com/s/<article-slug>"}},
  {"name":"read_article_images","arguments":{"article_url":"https://mp.weixin.qq.com/s/<article-slug>","start":10,"count":4}}
]
```

## 诊断 CLI

```text
<environment-python> -B -X utf8 <skill>/scripts/wechat_mcp.py search --account 中国金融四十人论坛 --query 人工智能 --page 1
<environment-python> -B -X utf8 <skill>/scripts/wechat_mcp.py read <article-url>
<environment-python> -B -X utf8 <skill>/scripts/wechat_mcp.py images <article-url> --start 10 --count 4
```

CLI 使用同一底层服务。图片诊断只打印元数据，MCP 才返回原生图片块。脚本不自动生成报告或完成跨账号批量研究；候选、正文和图表由宿主逐次调用、核对，再依据 [报告规范](report.md)写作。

## 状态与限制

状态和警告是获取线索，需要结合可见原页判断；页面变化可能使解析或限制分类不准确。不能仅凭成功状态认定账号、日期、文章身份、同文关系或全文完整性。

- `ok/no_results`：搜索解析结果；`unrecognized_page` 不能当作没有文章。
- `text_available/images_only/empty`：可见正文存在、需读图片或未取得正文；不自动说明全文完整。
- `requires_render`：可能是 JavaScript 页面壳，可用宿主正常浏览器核对。CF40 页面的公开 GET 正文适配会记录 `content_source_url`，不自动认证同文。
- `blocked/auth_required/paywalled/rate_limited`：可能受限，结合原页确认后停止相应路径，不绕过访问限制。
- `network_error/unavailable/unsupported_format/unsupported_image/too_large/unresolved_redirect/invalid_url`：记录原因，必要时使用宿主已有且合适的只读能力。普通网络错误最多一次普通重试，429 不重试。

`source_type=public_web` 表示公开网页，是否为同机构官网对应文章由宿主核对。官网 `published_at` 不能未经依据充当微信日期。文章标识及搜狗临时索引只提供重复检查线索，宿主仍须结合原页核对，不承诺自动可靠去重或历史覆盖。

网络程序只访问公开网页及按需图片，不登录、不执行页面 JavaScript，不处理音视频。验证码、登录、付费或配额可能阻断获取；不要用搜索片段补写正文。正文仅暂存于进程内，退出清空；报告与必要来源记录由宿主保存。

## 可选补充工具

宿主已有 Tavily 或公开搜索时，可补查账号别名、准确题名和官网对应文章；它不是唯一依赖，也不能保证公众号覆盖。Tavily 接入方式参考 [官方 MCP 文档](https://docs.tavily.com/documentation/mcp)与 [keyless 说明](https://docs.tavily.com/documentation/keyless)，不自动配置、申请密钥或购买服务。

PDF 和需渲染页面使用宿主已有读取能力。缺少 Python、联网或等价工具时，交付获取情况与未完成队列，不声称已完成收集。部分或全部失败均保留固定五章报告。
