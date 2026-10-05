# 来源与修改记录

复用来源为 [jj-cheng25/weixin-articles-mcp](https://github.com/jj-cheng25/weixin-articles-mcp/tree/060fb3dd7e41d1c0950a19bc1367d66a6881f915)，锁定提交 `060fb3dd7e41d1c0950a19bc1367d66a6881f915`。上游 MIT 许可证原文保留于 [LICENSE](LICENSE)，`scripts/vendor/weixin_reader/` 标记复用代码与版权。

实际改编了上游 `src/weixin_articles_mcp/parser.py` 和 `src/weixin_articles_mcp/markdown.py` 中的 HTML 解析与 Markdown 转换方法，包括微信正文 DOM、延迟图片链接及 MarkdownConverter。采用独立轻量模块，没有分发上游整个服务、视频模块或其他检索项目代码。

代码改编包括：移除音视频解析、下载和关键帧；保留图片顺序与链接并按需分批读取；返回发布日期、文章标识与来源状态；增加公开搜狗搜索、网络访问处理和官网可见正文提取。未取得完整许可证文本的其他检索项目仅用于方法比较，没有复制代码。

本项目编写了 Skill 指令、来源核对流程、报告规范及公开检索适配。公开包保留三个只读 MCP 接口及 search/read/images 诊断入口，使用宿主逐次检索、核对和写作；不分发批量候选收集器或检索计划文件。本次发布整理未改变 MCP 实现。

Python 依赖通过 pip 安装，不随 ZIP 打包；依赖声明和 Windows/Python 3.12 锁文件保留，各依赖自己的许可证仍适用。Tavily 可作为宿主已有的可选公开搜索能力，其服务、密钥和配置不在本包中。其他科研 Skill 不是本包运行依赖。
