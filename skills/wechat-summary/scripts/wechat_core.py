"""Public discovery and source reading; no account login or model API.

Network operations are injectable for deterministic fixtures. Only temporary
in-memory article caching is used. Writing reports belongs to the host agent.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
from html import escape
import io
import ipaddress
import json
import os
import re
import socket
import time
import unicodedata
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date, datetime
from urllib.parse import parse_qs, parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import httpx
from bs4 import BeautifulSoup
from PIL import Image, UnidentifiedImageError
import trafilatura

from vendor.weixin_reader.parser import SHANGHAI, image_manifest, parse_wechat
from vendor.weixin_reader.markdown import html_to_markdown

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"
SOGOU = "https://weixin.sogou.com/weixin"
MAX_BYTES = 16 * 1024 * 1024
AV_SUFFIXES = (".mp3", ".mp4", ".wav", ".m4a", ".aac", ".ogg", ".webm", ".mov", ".avi", ".m3u8", ".flv")


def is_av_url(url):
    return urlsplit(url).path.lower().endswith(AV_SUFFIXES)


class FetchFailure(Exception):
    def __init__(self, status, message, url="", attempts=1):
        super().__init__(message)
        self.status, self.url, self.attempts = status, url, attempts


def normalize_account(value: str) -> str:
    return re.sub(r"[\s\u200b\ufeff]+", "", unicodedata.normalize("NFKC", value)).strip()


def published_date(value: str) -> date | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(SHANGHAI).date() if dt.tzinfo else dt.date()
    except ValueError:
        match = re.search(r"(\d{4})[-年/](\d{1,2})[-月/](\d{1,2})", value)
        if match:
            try:
                return date(*map(int, match.groups()))
            except ValueError:
                pass
    return None


@dataclass(frozen=True)
class DateRange:
    start: date
    end: date

    @classmethod
    def resolve(cls, as_of: str = "", start: str = "", end: str = ""):
        today = date.fromisoformat(as_of) if as_of else datetime.now(SHANGHAI).date()
        last = date.fromisoformat(end) if end else today
        if start:
            first = date.fromisoformat(start)
        else:
            try:
                first = last.replace(year=last.year - 1)
            except ValueError:
                first = last.replace(year=last.year - 1, day=28)
        if first > last:
            raise ValueError("start must be on or before end")
        return cls(first, last)

    def contains(self, value: str) -> bool | None:
        day = published_date(value)
        return None if day is None else self.start <= day <= self.end


def classify_candidate(row: dict, accounts: list[str], period: DateRange) -> str:
    if not row.get("account"):
        return "account_pending"
    if normalize_account(row["account"]) not in {normalize_account(a) for a in accounts}:
        return "other_account"
    included = period.contains(row.get("published_at", ""))
    return "date_pending" if included is None else "in_scope" if included else "outside_window"


def canonical_article_key(url: str, identifiers: dict | None = None) -> str:
    parts = urlsplit(url)
    query = parse_qs(parts.query)
    identifiers = identifiers or {}
    biz = identifiers.get("biz") or query.get("__biz", [""])[0]
    mid = identifiers.get("mid") or query.get("mid", query.get("appmsgid", [""]))[0]
    idx = identifiers.get("idx") or query.get("idx", ["1"])[0]
    if parts.hostname == "mp.weixin.qq.com" and biz and mid:
        return f"wechat:{biz}:{mid}:{idx}"
    if parts.hostname == "mp.weixin.qq.com" and parts.path.startswith("/s/"):
        return "https://mp.weixin.qq.com" + parts.path.rstrip("/")
    if parts.hostname == "weixin.sogou.com" and parts.path == "/link" and query.get("url"):
        return "sogou-link:" + query["url"][0]
    skip = {"from", "scene", "isappinstalled", "clicktime", "enterid", "sessionid", "ascene", "wx_header"}
    kept = sorted((k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
                  if k not in skip and not k.startswith("utm_"))
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path,
                      urlencode(kept), ""))


def merge_candidates(pages: list[dict]) -> list[dict]:
    """Merge every returned row; title alone is never an identity."""
    result, seen = [], {}
    for page in pages:
        for original in page.get("articles", []):
            row = dict(original)
            key = row.get("canonical_id") or canonical_article_key(row.get("url", ""))
            if not key:
                key = "unresolved:" + hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
            if key in seen:
                prior = result[seen[key]]
                for alias in row.get("discovery_urls", []) + [row.get("url", "")]:
                    if alias and alias not in prior["discovery_urls"]:
                        prior["discovery_urls"].append(alias)
                continue
            row["canonical_id"] = key
            row["discovery_urls"] = list(dict.fromkeys(row.get("discovery_urls", []) + [row.get("url", "")]))
            seen[key] = len(result)
            result.append(row)
    return result


class SearchProgress:
    """Supplementary rounds stop at two consecutive rounds with no new IDs."""
    def __init__(self):
        self.seen, self.empty_rounds = set(), 0

    def observe_round(self, identifiers):
        current = set(identifiers)
        fresh = current - self.seen
        self.seen.update(current)
        self.empty_rounds = 0 if fresh else self.empty_rounds + 1
        return len(fresh)

    @property
    def exhausted(self):
        return self.empty_rounds >= 2


def validate_public_url(url: str) -> str:
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password:
        raise FetchFailure("invalid_url", "只允许没有内嵌凭据的公开 HTTP(S) 地址。", url)
    host = parts.hostname.lower()
    if host in ("localhost", "localhost.localdomain") or host.endswith((".local", ".internal", ".localhost")):
        raise FetchFailure("invalid_url", "不读取本机或内部网络地址。", url)
    try:
        address = ipaddress.ip_address(host)
        if not address.is_global:
            raise FetchFailure("invalid_url", "不读取非公开网络地址。", url)
    except ValueError:
        pass
    try:
        port = parts.port
    except ValueError as error:
        raise FetchFailure("invalid_url", "无效端口。", url) from error
    if port not in (None, 80, 443):
        raise FetchFailure("invalid_url", "仅支持公开网页的标准 HTTP(S) 端口。", url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path or "/", parts.query, ""))


def decode_html(data: bytes, content_type: str) -> str:
    match = re.search(r"charset\s*=\s*[\"']?([\w-]+)", content_type, re.I)
    if not match:
        match = re.search(rb"charset\s*=\s*[\"']?([\w-]+)", data[:4096], re.I)
    encoding = match.group(1) if match else "utf-8"
    if isinstance(encoding, bytes):
        encoding = encoding.decode("ascii", errors="ignore")
    try:
        return data.decode(encoding)
    except (LookupError, UnicodeDecodeError):
        try:
            return data.decode("gb18030")
        except UnicodeDecodeError:
            return data.decode("utf-8", errors="replace")


class PublicFetcher:
    def __init__(self, transport=None, interval=1.0, search_interval=5.0):
        self.transport = transport
        self.interval, self.search_interval = interval, search_interval
        self._last, self._lock = {}, asyncio.Lock()
        self._dns_cache = {}

    async def _check_dns(self, url):
        url = validate_public_url(url)
        # MockTransport is entirely in-memory, with no network capability.
        if isinstance(self.transport, httpx.MockTransport):
            return url
        host = urlsplit(url).hostname
        if self._dns_cache.get(host, 0) > time.monotonic():
            return url
        try:
            info = await asyncio.get_running_loop().getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        except OSError as error:
            raise FetchFailure("network_error", "域名解析失败。", url) from error
        if not info or any(not ipaddress.ip_address(entry[4][0]).is_global for entry in info):
            raise FetchFailure("invalid_url", "该域名解析到非公开网络地址。", url)
        self._dns_cache[host] = time.monotonic() + 60
        return url

    async def _throttle(self, url):
        host = urlsplit(url).hostname
        minimum = self.search_interval if host == "weixin.sogou.com" else self.interval
        async with self._lock:
            delay = minimum - (time.monotonic() - self._last.get(host, 0))
            if delay > 0:
                await asyncio.sleep(delay)
            self._last[host] = time.monotonic()

    async def get(self, url: str, referer: str = "", json_body=None) -> tuple[bytes, str, str]:
        for attempt in (1, 2):
            current = url
            try:
                async with httpx.AsyncClient(transport=self.transport, timeout=20,
                                            follow_redirects=False, trust_env=False) as client:
                    for _ in range(8):
                        current = await self._check_dns(current)
                        if is_av_url(current):
                            raise FetchFailure("unsupported_format", "跳转目标为音视频，未发起媒体网络调用。", current, attempt)
                        await self._throttle(current)
                        headers = {"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"}
                        if referer:
                            headers["Referer"] = referer
                        if json_body is not None:
                            headers["Content-Type"] = "application/json;charset=utf-8"
                            headers["Accept"] = "application/json, text/plain, */*"
                        async with client.stream("GET", current, headers=headers, json=json_body) as response:
                            code = response.status_code
                            if code in (301, 302, 303, 307, 308):
                                location = response.headers.get("location")
                                if not location:
                                    raise FetchFailure("unresolved_redirect", "跳转缺少目标地址。", current, attempt)
                                referer, current = current, urljoin(current, location)
                                continue
                            if code in (401, 403):
                                raise FetchFailure("blocked", f"HTTP {code}，访问受限。", current, attempt)
                            if code == 402:
                                raise FetchFailure("paywalled", "HTTP 402，需要付费。", current, attempt)
                            if code == 429:
                                raise FetchFailure("rate_limited", "HTTP 429，停止该检索来源，保留当前进度。", current, attempt)
                            if code in (408, 500, 502, 503, 504):
                                if attempt == 1:
                                    break
                                raise FetchFailure("network_error", f"HTTP {code}，一次重试后失败。", current, attempt)
                            if code != 200:
                                raise FetchFailure("unavailable", f"HTTP {code}。", current, attempt)
                            if response.headers.get("content-type", "").lower().startswith(("audio/", "video/")):
                                raise FetchFailure("unsupported_format", "音视频响应已拒绝，未读取媒体载荷。", current, attempt)
                            chunks, length = [], 0
                            async for chunk in response.aiter_bytes():
                                length += len(chunk)
                                if length > MAX_BYTES:
                                    raise FetchFailure("too_large", "单个资源超过 16 MiB，未完整读取。", current, attempt)
                                chunks.append(chunk)
                            return b"".join(chunks), current, response.headers.get("content-type", "")
                    else:
                        raise FetchFailure("unresolved_redirect", "跳转次数超过上限。", current, attempt)
            except httpx.TransportError as error:
                if attempt == 2:
                    raise FetchFailure("network_error", "网络错误，一次重试后失败：" + str(error), current, attempt) from error
            if attempt == 1:
                await asyncio.sleep(0.5)
        raise FetchFailure("network_error", "网络读取失败。", url, 2)


def access_problem(html: str, url: str, *, search=False) -> str | None:
    soup = BeautifulSoup(html, "lxml")
    if soup.select_one('input[type="password"]'):
        return "auth_required"
    real_body = soup.select_one("#js_content")
    if "antispider" in url or soup.select_one("#seccodeImage, #verify_code, .captcha-container"):
        return "blocked"
    if not real_body and (not search or not soup.select_one("ul.news-list > li")):
        visible = soup.get_text(" ", strip=True)
        if any(term in visible for term in ("请输入验证码", "访问过于频繁", "环境异常", "完成验证后继续访问", "请输入图中的验证码")):
            return "blocked"
    if soup.select_one(".paywall, #js_pay_preview, .pay_read_box"):
        return "paywalled"
    return None


def parse_search_page(html: str, page_url: str, account_name: str, query: str, page: int) -> dict:
    problem = access_problem(html, page_url, search=True)
    if problem:
        return {"status": problem, "articles": [], "has_next": False,
                "message": "公开检索访问受限，未尝试绕过验证。", "search_url": page_url}
    soup = BeautifulSoup(html, "lxml")
    articles = []
    for item in soup.select("ul.news-list > li"):
        title_link = item.select_one("h3 a")
        if not title_link or not title_link.get("href"):
            continue
        source = (item.select_one("a.account") or item.select_one(".s-p .all-time-y2")
                  or item.select_one(".s-p a") or item.select_one(".account"))
        account = source.get_text(" ", strip=True) if source else ""
        stamp = re.search(r"timeConvert\(['\"](\d+)['\"]\)", str(item))
        published = ""
        if stamp:
            try:
                published = datetime.fromtimestamp(int(stamp.group(1)), SHANGHAI).isoformat()
            except (ValueError, OSError, OverflowError):
                pass
        url = urljoin(page_url, title_link["href"]).replace(" ", "%20")
        digest = item.select_one(".txt-info")
        articles.append({"title": title_link.get_text("", strip=True), "account": account,
                         "published_at": published, "url": url,
                         "snippet": digest.get_text(" ", strip=True) if digest else "",
                         "account_match": bool(account) and normalize_account(account) == normalize_account(account_name),
                         "canonical_id": ("sogou-result:" + item["d"]) if item.get("d") else canonical_article_key(url),
                         "search_result_id": item.get("d", ""),
                         "identity_status": "resolved_url" if urlsplit(url).hostname == "mp.weixin.qq.com" else "provisional_index_identifier" if item.get("d") else "provisional_discovery_link"})
    next_link = soup.select_one("a#sogou_next")
    if not next_link:
        next_link = next((a for a in soup.find_all("a", href=True) if a.get_text(strip=True) == "下一页"), None)
    has_next = False
    if next_link:
        next_url = urljoin(page_url, next_link["href"])
        try:
            has_next = int(parse_qs(urlsplit(next_url).query).get("page", ["0"])[0]) > page
        except ValueError:
            pass
    recognized_empty = any(text in soup.get_text(" ", strip=True) for text in ("没有找到", "未找到", "找不到"))
    status = "ok" if articles else "no_results" if recognized_empty else "unrecognized_page"
    return {"status": status, "requested_account": account_name, "query": query, "page": page,
            "articles": articles, "has_next": has_next, "search_url": page_url,
            "next_page": page + 1 if has_next else None, "next_url": next_url if has_next else "",
            "message": "搜索摘要仅用于发现，不代表正文已读。"}


def parse_public_article(html: str, url: str) -> dict:
    visible = BeautifulSoup(html, "lxml").get_text(" ", strip=True)
    if ("doesn't work properly without JavaScript" in visible or "enable JavaScript to continue" in visible):
        return {"status": "requires_render", "title": "", "account": "", "published_at": "",
                "body_markdown": "", "images": [], "image_count": 0, "source_type": "public_web",
                "message": "返回 JavaScript 应用壳，未取得文章正文；请用宿主正常浏览器读取，或核对官网公开正文接口。",
                "completeness": "no_text", "warnings": ["提示页不是正文。"]}
    if urlsplit(url).hostname == "mp.weixin.qq.com":
        result = parse_wechat(html, url)
        result["body_markdown"] = html_to_markdown(result.pop("body_html"))
        result["source_type"] = "wechat"
    else:
        soup = BeautifulSoup(html, "lxml")
        excluded = soup.select("iframe, video, audio, mp-common-videosnap, mpvoice, mp-audio")
        excluded_count = len(excluded)
        for node in excluded:
            node.decompose()
        for img in soup.find_all("img"):
            src = img.get("data-src") or img.get("data-original") or img.get("src")
            if src and not src.startswith("data:"):
                img["src"] = urljoin(url, src)
        cleaned = str(soup)
        metadata = trafilatura.extract_metadata(cleaned, default_url=url)
        markdown = trafilatura.extract(cleaned, url=url, output_format="markdown", include_comments=False,
                                       include_tables=True, include_images=True, include_links=True) or ""
        # Inventory is not capped; host decides which figures support the claim.
        body = soup.select_one("article, main, [itemprop='articleBody'], .article-content, .content-detail") or soup.body or soup
        result = {"title": getattr(metadata, "title", "") or "", "account": "",
                  "author": getattr(metadata, "author", "") or "",
                  "published_at": getattr(metadata, "date", "") or "",
                  "body_markdown": markdown, "images": image_manifest(body, url), "identifiers": {},
                  "source_type": "public_web", "warnings": [
                      "公开网页正文已提取；是否为同一机构官网同文须核对，工具不自动认证该关系。",
                      "网页日期不能未经核对当作公众号原始发布日期。"]}
        if excluded_count:
            result["warnings"].append("音视频嵌入已忽略，未下载、转写或提取关键帧。")
    prose = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", result["body_markdown"]).strip()
    result["status"] = "text_available" if prose else "images_only" if result["images"] else "empty"
    result["image_count"] = len(result["images"])
    result["canonical_id"] = canonical_article_key(url, result.get("identifiers"))
    result["completeness"] = "visible_page_body" if prose else "no_text"
    result["line_count"] = len(result["body_markdown"].splitlines())
    return result


class ArticleService:
    def __init__(self, fetcher=None):
        self.fetcher = fetcher or PublicFetcher()
        self._cache = OrderedDict()

    @staticmethod
    def _failure(error, url):
        return {"status": error.status, "requested_url": url, "resolved_url": error.url or url,
                "message": str(error), "attempts": error.attempts, "body_markdown": "",
                "images": [], "image_count": 0}

    async def search_articles(self, account_name: str, query: str, page: int = 1) -> dict:
        if not account_name.strip() or not query.strip() or page < 1:
            return {"status": "invalid_input", "articles": [], "has_next": False,
                    "message": "公众号、主题词不能为空，page 从 1 开始。"}
        combined = f"{account_name.strip()} {query.strip()}"
        url = SOGOU + "?" + urlencode({"type": 2, "query": combined, "page": page, "ie": "utf8"})
        try:
            data, final, kind = await self.fetcher.get(url)
            return parse_search_page(decode_html(data, kind), final, account_name, query, page)
        except FetchFailure as error:
            return {"status": error.status, "articles": [], "has_next": False,
                    "message": str(error), "search_url": url, "attempts": error.attempts}

    async def read_article(self, url: str) -> dict:
        try:
            normalized = validate_public_url(url)
            if is_av_url(normalized):
                raise FetchFailure("unsupported_format", "音视频地址不处理，未发起网络调用。", normalized)
            parts = urlsplit(normalized)
            if parts.hostname == "mp.weixin.qq.com" and not (
                (parts.path.startswith("/s/") and len(parts.path) > 3) or
                (parts.path == "/s" and parts.query)
            ):
                raise FetchFailure("invalid_url", "需要具体微信文章地址，不能读取平台登录页。", url)
            key = canonical_article_key(normalized)
            cached = self._cache.get(key)
            if cached and time.monotonic() - cached[0] < 600:
                self._cache.move_to_end(key)
                return cached[1]
            data, final, kind = await self.fetcher.get(normalized)
            if "pdf" in kind.lower() or data.startswith(b"%PDF"):
                raise FetchFailure("unsupported_format", "这是 PDF；请用宿主已有 PDF 读取能力核对。", final)
            if kind.lower().startswith(("image/", "audio/", "video/", "application/json")):
                raise FetchFailure("unsupported_format", "该地址不是文章 HTML；图片使用文章图片接口，官网 API 使用对应文章页面。音视频不处理。", final)
            html = decode_html(data, kind)
            problem = access_problem(html, final)
            if problem:
                raise FetchFailure(problem, "原文访问受限，未绕过登录、付费或验证码。", final)
            # Sogou may use an ordinary JavaScript navigation page. Only follow
            # a literal public WeChat destination; never execute page scripts.
            if urlsplit(final).hostname == "weixin.sogou.com":
                match = re.search(r'https?://mp\.weixin\.qq\.com/s(?:/|\?)[^\s"\'<>]+', html)
                if not match:
                    raise FetchFailure("unresolved_redirect", "未取得可直接读取的微信原文地址。", final)
                result = dict(await self.read_article(match.group(0).replace("&amp;", "&")))
                result["discovery_url"] = url
                result["requested_url"] = url
                return result
            result = parse_public_article(html, final)
            # CF40's normal public Vue frontend uses this same GET API and JSON
            # body. No Authorization header, token, login or admin endpoint.
            route = re.fullmatch(r"/article/(\d+)/(\d+)/?", urlsplit(final).path)
            if result["status"] == "requires_render" and route and urlsplit(final).hostname in ("cf40.org.cn", "www.cf40.org.cn"):
                api_url = urljoin(final, f"/api/web/data/{route[1]}/{route[2]}")
                payload, actual_api, api_kind = await self.fetcher.get(api_url, referer=final, json_body={"unusekey": False})
                try:
                    document = json.loads(payload)
                except (ValueError, UnicodeDecodeError):
                    document = {}
                record = document.get("data", {})
                if document.get("code") == 200 and isinstance(record, dict) and record.get("content"):
                    article_html = '<html><head><title>' + escape(record.get("title", "")) + '</title></head><body><article>' + record["content"] + '</article></body></html>'
                    result = parse_public_article(article_html, final)
                    result.update({"title": record.get("title", ""), "author": record.get("author", ""),
                                   "published_at": record.get("send_time", ""), "content_source_url": actual_api,
                                   "retrieval_method": "official_public_article_api", "official_article_id": record.get("id"),
                                   "original_link_field": record.get("jump_link", "")})
                    result["warnings"].append("官网正文来自页面正常使用的公开 GET 接口；同机构同文与微信日期仍需另行核对。")
                elif document.get("code") in (401, 403):
                    raise FetchFailure("auth_required", "官网正文接口需要授权，停止该路径。", actual_api)
                elif document.get("code") in (402, 429):
                    raise FetchFailure("rate_limited" if document["code"] == 429 else "paywalled", "官网接口额度或付费限制，停止该路径。", actual_api)
            result.update({"requested_url": url, "resolved_url": final})
            if result["status"] in ("text_available", "images_only"):
                self._cache[key] = (time.monotonic(), result)
                while len(self._cache) > 64:
                    self._cache.popitem(last=False)
            return result
        except FetchFailure as error:
            return self._failure(error, url)

    async def read_article_images(self, article_url: str, start: int = 0, count: int = 4) -> dict:
        if start < 0 or not 1 <= count <= 8:
            return {"status": "invalid_input", "message": "start 从 0 开始；count 为 1–8，分批大小不限制总图数。", "items": []}
        article = await self.read_article(article_url)
        if article["status"] not in ("text_available", "images_only"):
            return {"status": article["status"], "message": article.get("message", "正文与图片清单不可用。"), "items": []}
        images = article["images"]
        items = []
        for entry in images[start:start + count]:
            try:
                if is_av_url(entry["url"]):
                    raise FetchFailure("unsupported_image", "图像标签指向音视频地址，未发起媒体网络调用。", entry["url"])
                data, final, kind = await self.fetcher.get(entry["url"], referer=article["resolved_url"])
                with Image.open(io.BytesIO(data)) as picture:
                    if picture.width * picture.height > 40_000_000:
                        raise FetchFailure("too_large", "图像超过 4000 万像素，未完整核对。", final)
                    animated = getattr(picture, "n_frames", 1) > 1
                    picture.seek(0)
                    normalized = picture.convert("RGBA" if "A" in picture.getbands() else "RGB")
                    output = io.BytesIO()
                    normalized.save(output, format="PNG")
                items.append({**entry, "status": "ok", "mime_type": "image/png",
                              "width": normalized.width, "height": normalized.height,
                              "data": base64.b64encode(output.getvalue()).decode("ascii"),
                              "warning": "动画图仅提供第一帧。" if animated else ""})
            except FetchFailure as error:
                items.append({**entry, "status": error.status, "message": str(error)})
            except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
                items.append({**entry, "status": "unsupported_image", "message": str(error)})
        next_start = min(start + count, len(images))
        ok = sum(i["status"] == "ok" for i in items)
        return {"status": "ok" if ok == len(items) else "partial" if ok else "failed",
                "article_url": article["resolved_url"], "image_count": len(images), "start": start,
                "next_start": next_start, "has_more": next_start < len(images), "items": items}
