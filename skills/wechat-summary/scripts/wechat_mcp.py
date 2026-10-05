"""STDIO MCP entry point; writes no articles and exposes no publishing tools."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

from fastmcp import FastMCP
from mcp.types import ImageContent, TextContent
from wechat_core import ArticleService

mcp = FastMCP("wechat-summary", instructions=(
    "公开公众号主题检索与图文读取。先 search_articles，核对账号和日期后 read_article；"
    "按正文清单用 read_article_images 读取关键图表。搜索摘要不是正文；"
    "public_web 来源是否为同机构官网同文由调用者核实。音视频不处理。"))
service = ArticleService()
READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": True}


@mcp.tool(annotations=READ_ONLY)
async def search_articles(account_name: str, query: str, page: int = 1) -> dict:
    """公开检索指定账号相关候选；按返回账号核对，has_next 为真时继续分页。

    未施加总条数上限。时间筛选由调用者根据 published_at 和原文日期执行。
    blocked/rate_limited/unrecognized_page 不代表该账号没有相关文章。
    """
    return await service.search_articles(account_name, query, page)


@mcp.tool(annotations=READ_ONLY)
async def read_article(url: str) -> dict:
    """读取微信短/长链接或公开官网候选同文，返回可见正文与完整图片清单。

    text_available 表示可见正文已提取；public_web 不自动等同已核实官网同文。
    工具不下载音视频；受限页面可能无法取得正文，状态须结合原页判断。原文只在内存短暂缓存。
    """
    return await service.read_article(url)


@mcp.tool(annotations=READ_ONLY, output_schema=None)
async def read_article_images(article_url: str, start: int = 0, count: int = 4) -> list:
    """按正文图片索引返回原生图片块。start 从 0 开始，count 1–8。

    首个文字块含获取状态/编号/URL/尺寸/下一批位置，后续图片与成功条目顺序对应。
    可 start=10 读取第十一张及之后的图片；总图片清单不截断。
    """
    result = await service.read_article_images(article_url, start, count)
    metadata = {k: v for k, v in result.items() if k != "items"}
    metadata["items"] = [{k: v for k, v in item.items() if k != "data"} for item in result.get("items", [])]
    blocks = [TextContent(type="text", text=json.dumps(metadata, ensure_ascii=False))]
    for item in result.get("items", []):
        if item.get("status") == "ok":
            blocks.append(ImageContent(type="image", data=item["data"], mimeType=item["mime_type"]))
    return blocks


async def _cli(args):
    if args.action == "search":
        result = await service.search_articles(args.account, args.query, args.page)
    elif args.action == "read":
        result = await service.read_article(args.url)
    else:
        result = await service.read_article_images(args.url, args.start, args.count)
        for item in result.get("items", []):
            item.pop("data", None)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="wechat-summary MCP 或只读诊断 CLI")
    sub = parser.add_subparsers(dest="action")
    search = sub.add_parser("search")
    search.add_argument("--account", required=True)
    search.add_argument("--query", required=True)
    search.add_argument("--page", type=int, default=1)
    read = sub.add_parser("read")
    read.add_argument("url")
    images = sub.add_parser("images")
    images.add_argument("url")
    images.add_argument("--start", type=int, default=0)
    images.add_argument("--count", type=int, default=4)
    args = parser.parse_args()
    if args.action:
        asyncio.run(_cli(args))
    else:
        mcp.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
