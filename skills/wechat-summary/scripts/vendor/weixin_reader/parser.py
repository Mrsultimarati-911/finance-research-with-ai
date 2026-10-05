"""WeChat DOM extraction, adapted 2026-10-04 from upstream parser.py.

Copyright (c) 2026 weixin-articles-mcp contributors. MIT; see ../../../LICENSE.
Changes: omit all AV extraction; preserve image order, links and account IDs;
return local publication time and avoid claiming an empty body was read.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup

SHANGHAI = timezone(timedelta(hours=8))


def _text(node):
    return node.get_text(" ", strip=True) if node else ""


def image_manifest(body, base_url):
    seen, images = set(), []
    for img in body.find_all("img"):
        src = img.get("data-src") or img.get("data-original") or img.get("src") or ""
        if not src or src.startswith("data:"):
            continue
        src = urljoin(base_url, src)
        if src in seen:
            continue
        seen.add(src)
        images.append({"index": len(images), "url": src,
                       "alt": img.get("alt", ""), "caption": img.get("title", "")})
    return images


def parse_wechat(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    body = soup.select_one("#js_content")
    stamp = re.search(r'(?:var\s+)?ct\s*=\s*["\']?(\d{9,12})', html)
    published = ""
    if stamp:
        try:
            published = datetime.fromtimestamp(int(stamp.group(1)), SHANGHAI).isoformat()
        except (ValueError, OSError, OverflowError):
            pass
    identifiers = {}
    for name in ("biz", "mid", "idx"):
        match = re.search(r'(?:var\s+)?' + name + r'\s*=\s*["\']?([^"\';\s]+)', html)
        identifiers[name] = match.group(1) if match else ""
    warnings = []
    if body:
        excluded = body.select("iframe, video, audio, mp-common-videosnap, mpvoice, mp-audio")
        if excluded:
            warnings.append("音视频嵌入已忽略，未下载、转写或提取关键帧。")
        for element in excluded:
            element.decompose()
        for element in body.select("script, style"):
            element.decompose()
    author_node = soup.select_one("#js_author_name")
    if not author_node:
        author_node = soup.select_one(".rich_media_meta_text")
    return {
        "title": _text(soup.select_one("#activity-name")),
        "account": _text(soup.select_one("#js_name")),
        "author": _text(author_node), "published_at": published,
        "body_html": str(body) if body else "",
        "images": image_manifest(body, url) if body else [],
        "identifiers": identifiers, "warnings": warnings,
    }
