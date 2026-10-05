#!/usr/bin/env python3
"""Public metadata adapter. Original implementation; methods adapted from nature-skills.

Public subset: metadata queries, complete abstracts, cursor pages and real
publication dates. Results are printed as JSON. See PROVENANCE.md.
Licensed under Apache-2.0; no external dependencies or mandatory MCP.
"""
from __future__ import annotations

import argparse
import calendar
from datetime import date, datetime, timezone
import hashlib
from html import unescape
from html.parser import HTMLParser
import json
import os
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlencode
from urllib.request import Request, urlopen


def normalize_doi(value):
    value = unquote(str(value or '').strip())
    value = re.sub(r'^https?://(?:dx\.)?doi\.org/', '', value, flags=re.I)
    value = re.sub(r'^doi:\s*', '', value, flags=re.I).strip().lower()
    return value if re.fullmatch(r'10\.\d{4,9}/\S+', value) else None


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if tag.split(':')[-1] in {'p', 'br', 'sec', 'title'}:
            self.parts.append(' ')

    def handle_endtag(self, tag):
        if tag.split(':')[-1] in {'p', 'sec', 'title'}:
            self.parts.append(' ')


def plain_text(value):
    if not value:
        return None
    parser = TextParser()
    parser.feed(value)
    return re.sub(r'\s+', ' ', unescape(''.join(parser.parts))).strip() or None


def inverted_abstract(index):
    positions = {int(p): word for word, locations in (index or {}).items() for p in locations}
    return ' '.join(positions[p] for p in sorted(positions)) or None


def default_window(as_of):
    end = date.fromisoformat(as_of)
    year = end.year - 5
    start = end.replace(year=year, day=min(end.day, calendar.monthrange(year, end.month)[1]))
    return start.isoformat(), end.isoformat()


def date_value(parts):
    try:
        parts = [int(x) for x in parts][:3]
        if not 1000 <= parts[0] <= 9999:
            return None, 'unknown'
        if len(parts) == 1:
            return str(parts[0]), 'year'
        calendar.monthrange(parts[0], parts[1])
        if len(parts) == 2:
            return f'{parts[0]:04d}-{parts[1]:02d}', 'month'
        return date(*parts).isoformat(), 'day'
    except (IndexError, TypeError, ValueError):
        return None, 'unknown'


def time_status(record, start, end, classic=False):
    if classic:
        return 'classic_supplement'
    value = record.get('publication_date')
    if not value:
        return 'date_unknown'
    parts = list(map(int, value.split('-')))
    low = date(parts[0], parts[1] if len(parts) > 1 else 1, parts[2] if len(parts) > 2 else 1)
    high = low if len(parts) == 3 else date(parts[0], parts[1], calendar.monthrange(*parts[:2])[1]) if len(parts) == 2 else date(parts[0], 12, 31)
    begin, finish = date.fromisoformat(start), date.fromisoformat(end)
    if high < begin or low > finish:
        return 'outside_window'
    return 'within_window' if low >= begin and high <= finish else 'date_uncertain'


def base_record(source, identifier, doi, title, authors, pubdate, precision, venue,
                kind, language, abstract, url, references, citations, dates):
    return dict(id='doi:' + doi if doi else source + ':' + identifier,
                platform_ids={source: identifier}, doi=doi, title=title or '', authors=authors,
                publication_date=pubdate, date_precision=precision, publication_dates=dates,
                venue=venue, type=kind, language=language, abstract=abstract,
                read_range='abstract' if abstract else 'metadata', source_urls=[url],
                sources=[source], referenced_ids=references, citation_count=citations)


def normalize_crossref(work):
    doi = normalize_doi(work.get('DOI'))
    dates = []
    for field in ('published-online', 'published-print', 'published', 'issued'):
        values = work.get(field, {}).get('date-parts', [])
        value, precision = date_value(values[0] if values else [])
        if value:
            dates.append(dict(field=field, value=value, precision=precision))
    # Keep every real publication date; created/deposited/indexed are never substitutes.
    primary = min(dates, key=lambda x: x['value']) if dates else {}
    authors = [' '.join(filter(None, [a.get('given'), a.get('family')])) or a.get('name', '') for a in work.get('author', [])]
    title = (work.get('title') or [''])[0]
    identifier = doi or hashlib.sha256(json.dumps(work, sort_keys=True).encode()).hexdigest()[:20]
    refs = ['doi:' + d for r in work.get('reference', []) if (d := normalize_doi(r.get('DOI')))]
    record = base_record('crossref', identifier, doi, plain_text(title), authors,
                       primary.get('value'), primary.get('precision', 'unknown'),
                       (work.get('container-title') or [None])[0], work.get('type'), work.get('language'),
                       plain_text(work.get('abstract')), 'https://api.crossref.org/works/' + quote(identifier, safe=''),
                       refs, work.get('is-referenced-by-count'), dates)
    record.update(volume=work.get('volume'), issue=work.get('issue'), pages=work.get('page'), landing_url=work.get('URL'))
    return record


def normalize_openalex(work):
    identifier = (work.get('id') or '').rsplit('/', 1)[-1]
    doi = normalize_doi(work.get('doi'))
    value, precision = date_value(str(work['publication_date']).split('-') if work.get('publication_date') else [work.get('publication_year')])
    location = work.get('primary_location') or {}
    source = location.get('source') or {}
    record = base_record('openalex', identifier, doi, work.get('title'),
                       [a.get('author', {}).get('display_name', '') for a in work.get('authorships', [])],
                       value, precision, source.get('display_name'), work.get('type'), work.get('language'),
                       inverted_abstract(work.get('abstract_inverted_index')), 'https://api.openalex.org/works/' + identifier,
                       ['openalex:' + x.rsplit('/', 1)[-1] for x in work.get('referenced_works', [])],
                       work.get('cited_by_count'), [dict(field='publication_date', value=value, precision=precision)] if value else [])
    biblio = work.get('biblio') or {}
    record.update(volume=biblio.get('volume'), issue=biblio.get('issue'),
                  pages='-'.join(str(biblio[k]) for k in ('first_page','last_page') if biblio.get(k)) or None,
                  landing_url=location.get('landing_page_url'))
    return record


class ApiFailure(Exception):
    def __init__(self, status, code=None):
        super().__init__(status)
        self.status, self.code = status, code


class PublicClient:
    def __init__(self, interval=1.0, timeout=25):
        self.interval, self.timeout, self.last = interval, timeout, 0.0

    def get(self, source, path, params=None):
        root = {'crossref': 'https://api.crossref.org', 'openalex': 'https://api.openalex.org'}[source]
        params = dict(params or {})
        headers = {'User-Agent': 'finance-research-with-ai-academic-deepsearch', 'Accept': 'application/json'}
        if source == 'crossref' and os.getenv('CROSSREF_MAILTO'):
            params['mailto'] = os.environ['CROSSREF_MAILTO']
        if source == 'openalex' and os.getenv('OPENALEX_API_KEY'):
            headers['Authorization'] = 'Bearer ' + os.environ['OPENALEX_API_KEY']
        url = root + path + ('?' + urlencode(params) if params else '')
        for attempt in range(2):
            delay = self.interval - (time.monotonic() - self.last)
            if delay > 0:
                time.sleep(delay)
            self.last = time.monotonic()
            try:
                with urlopen(Request(url, headers=headers), timeout=self.timeout) as response:
                    result = json.load(response)
                    rate = {k.lower(): v for k, v in response.headers.items() if k.lower().startswith(('x-ratelimit', 'x-rate-limit', 'x-concurrency', 'retry-after'))}
                    return result, rate
            except HTTPError as exc:
                if exc.code in (401, 403, 404, 429):
                    raise ApiFailure({401:'authentication_required', 403:'access_restricted', 404:'not_found', 429:'quota_or_rate_limited'}[exc.code], exc.code) from None
                if exc.code < 500 or attempt:
                    raise ApiFailure('http_error', exc.code) from None
            except (URLError, TimeoutError, OSError):
                if attempt:
                    raise ApiFailure('network_error') from None
            except (ValueError, UnicodeError):
                raise ApiFailure('invalid_response') from None
        raise ApiFailure('network_error')


def normalize_id(identifier):
    value = identifier.removeprefix('openalex:').rsplit('/', 1)[-1]
    if not re.fullmatch(r'W\d+', value, re.I):
        raise ValueError('OpenAlex identifier must be W followed by digits; use lookup to resolve DOI first.')
    return value.upper()


def collect(client, source, query, start, end, size=100, cursor='*', all_pages=False, max_pages=None, citer=None):
    if not 1 <= size <= 100 or (max_pages is not None and max_pages < 1):
        raise ValueError('page-size must be 1..100 and max-pages positive')
    records, pages, seen_cursors, seen_pages = [], [], set(), set()
    status, next_cursor = 'complete', cursor
    normalizer = normalize_crossref if source == 'crossref' else normalize_openalex
    total = None
    while True:
        if next_cursor in seen_cursors:
            status = 'repeated_cursor'; break
        seen_cursors.add(next_cursor)
        params = {'cursor': next_cursor}
        if source == 'crossref':
            params.update({'query.bibliographic':query, 'rows':size, 'filter':f'from-pub-date:{start},until-pub-date:{end}'})
        else:
            params.update({'per_page':size, 'filter':f'from_publication_date:{start},to_publication_date:{end}'})
            if citer:
                params['filter'] += ',cites:' + normalize_id(citer)
            else:
                params['search'] = query
        page = dict(source=source, query=query, cursor=next_cursor, start=start, end=end)
        try:
            data, rate = client.get(source, '/works', params)
            payload = data['message'] if source == 'crossref' else data
            items = payload['items'] if source == 'crossref' else payload['results']
            new_cursor = payload.get('next-cursor') if source == 'crossref' else payload.get('meta', {}).get('next_cursor')
            total = payload.get('total-results') if source == 'crossref' else payload.get('meta', {}).get('count')
            normalized = [normalizer(x) for x in items]
        except ApiFailure as exc:
            page.update(status=exc.status, http_status=exc.code); pages.append(page)
            status = exc.status; break
        except (KeyError, TypeError, ValueError):
            page.update(status='invalid_response'); pages.append(page)
            status = 'invalid_response'; break
        fingerprint = hashlib.sha256(json.dumps([r['id'] for r in normalized]).encode()).hexdigest()
        page.update(status='ok', count=len(items), next_cursor=new_cursor, rate=rate)
        pages.append(page)
        # Retain even repeated raw results; merge is an explicit separate operation.
        for record in normalized:
            record['time_status'] = time_status(record, start, end)
        records.extend(normalized)
        if normalized and fingerprint in seen_pages:
            status, next_cursor = 'repeated_page', new_cursor; break
        seen_pages.add(fingerprint)
        next_cursor = new_cursor
        if not items or len(items) < size or not new_cursor:
            status = 'complete'; next_cursor = None; break
        if new_cursor in seen_cursors:
            status = 'repeated_cursor'; break
        if max_pages is not None and len(pages) >= max_pages:
            status = 'page_budget'; break
        if not all_pages:
            status = 'page_pending'; break
    return dict(status=status, complete=status == 'complete', records=records, pages=pages,
                next_cursor=next_cursor, total_matching=total, raw_count=len(records),
                unprocessed=[] if status == 'complete' else [dict(source=source, query=query, cursor=next_cursor, reason=status)])


def lookup(client, source, identifier):
    doi = normalize_doi(identifier.removeprefix('doi:'))
    token = ('https://doi.org/' + doi if source == 'openalex' else doi) if doi else normalize_id(identifier)
    if source == 'crossref' and not doi:
        raise ValueError('Crossref lookup needs a valid DOI')
    path = '/works/' + quote(token, safe='/:')
    try:
        data, rate = client.get(source, path)
        record = normalize_crossref(data['message']) if source == 'crossref' else normalize_openalex(data)
        return dict(status='complete', complete=True, records=[record], rate=rate)
    except ApiFailure as exc:
        return dict(status=exc.status, complete=False, records=[], http_status=exc.code, unprocessed=[identifier])
    except (KeyError, TypeError, ValueError):
        return dict(status='invalid_response', complete=False, records=[], unprocessed=[identifier])






def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('search', 'citers'):
        p = sub.add_parser(name)
        p.add_argument('--source', choices=['crossref', 'openalex'], default='openalex')
        p.add_argument('--query', required=name == 'search', default='')
        if name == 'citers':
            p.add_argument('--id', required=True)
        p.add_argument('--as-of', default=datetime.now(timezone.utc).date().isoformat(), help='Pass the task date explicitly')
        p.add_argument('--start')
        p.add_argument('--end')
        p.add_argument('--page-size', type=int, default=100)
        p.add_argument('--cursor', default='*')
        p.add_argument('--all-pages', action='store_true')
        p.add_argument('--max-pages', type=int)
    for name in ('lookup', 'references'):
        p = sub.add_parser(name)
        p.add_argument('--id', required=True)
        p.add_argument('--source', choices=['crossref', 'openalex'], default='openalex')
    args = parser.parse_args()
    try:
        client = PublicClient()
        if args.command in ('search', 'citers'):
            start, end = default_window(args.as_of)
            start, end = args.start or start, args.end or end
            if date.fromisoformat(start) > date.fromisoformat(end):
                raise ValueError('start must not follow end')
            if args.command == 'citers' and args.source != 'openalex':
                raise ValueError('citers uses OpenAlex')
            result = collect(client, args.source, args.query, start, end, args.page_size, args.cursor,
                             args.all_pages, args.max_pages, getattr(args, 'id', None))
        else:
            result = lookup(client, args.source, args.id)
            if args.command == 'references':
                result['reference_ids'] = result['records'][0]['referenced_ids'] if result['records'] else []
                result['detail_unprocessed'] = result['reference_ids']
        result['executed_at_utc'] = datetime.now(timezone.utc).isoformat()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get('complete', False) else 2
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({'status': 'input_error', 'reason': str(exc)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
