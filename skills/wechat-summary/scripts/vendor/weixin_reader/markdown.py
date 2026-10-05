"""Adapted 2026-10-04 from upstream markdown.py (060fb3dd).

Copyright (c) 2026 weixin-articles-mcp contributors. MIT; see ../../../LICENSE.
Changes: AV is removed, never resolved; lazy images retain source references.
"""
from __future__ import annotations

import re
from markdownify import MarkdownConverter


class WeixinConverter(MarkdownConverter):
    def convert_img(self, el, text, parent_tags):
        src = el.get("data-src") or el.get("data-original") or el.get("src") or ""
        if not src or src.startswith("data:"):
            return ""
        return f"![{el.get('alt', '')}]({src})"

    def convert_iframe(self, el, text, parent_tags):
        return ""

    def convert_video(self, el, text, parent_tags):
        return ""

    def convert_audio(self, el, text, parent_tags):
        return ""


def html_to_markdown(html: str) -> str:
    md = WeixinConverter(heading_style="ATX", bullets="-", escape_asterisks=False,
                         escape_underscores=False).convert(html)
    return re.sub(r"\n{3,}", "\n\n", md).strip()
