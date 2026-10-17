#!/usr/bin/env python3
"""Inspect declared public pages and their same-origin scripts without executing them.

Produces metadata and candidate URLs only, never a playback playlist. No retries,
proxy rotation, credential handling or access-control bypasses.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 2 * 1024 * 1024


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and attrs.get('href'):
            self.links.append(attrs['href'])
        if tag == 'script' and attrs.get('src'):
            self.scripts.append(attrs['src'])


def candidates(text: str, base: str) -> list[str]:
    parser = References()
    parser.feed(text)
    # Only explicit resource references; no guessing filenames or endpoints.
    quoted = re.findall(r'''["']([^"'<>\s]+\.(?:m3u8?|json|txt)(?:\?[^"'<>\s]*)?)["']''', text, re.I)
    found = set()
    for reference in parser.links + quoted:
        url = urllib.parse.urljoin(base, unescape(reference))
        parts = urllib.parse.urlsplit(url)
        if (parts.scheme == 'https' and not parts.username and not parts.password
                and not parts.query and not parts.fragment
                and re.search(r'\.(m3u8?|json|txt)$', parts.path, re.I)):
            found.add(url)
    return sorted(found)


def fetch(url: str) -> tuple[dict, str]:
    request = urllib.request.Request(url, headers={'User-Agent': 'tv-playlist-source-inspection/1.0'})
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            data = response.read(LIMIT + 1)
            if len(data) > LIMIT:
                return {'url': url, 'error': 'size_limit'}, ''
            text = data.decode('utf-8-sig', errors='replace')
            header = text.lstrip()
            kind = 'm3u' if header.startswith('#EXTM3U') else 'html' if re.search(r'<(?:!doctype|html|head|body)', header[:1000], re.I) else 'text'
            return {'url': url, 'final_url': response.url, 'http': response.status,
                    'content_type': response.headers.get('Content-Type'), 'bytes': len(data),
                    'format': kind, 'extinf_count': text.count('#EXTINF:'),
                    'unique_acestream_ids': len(set(re.findall(r'acestream://([a-fA-F0-9]{40})(?![a-fA-F0-9])', text)))}, text
    except urllib.error.HTTPError as exc:
        return {'url': url, 'http': exc.code, 'error': 'http_error', 'retry_after': exc.headers.get('Retry-After')}, ''
    except (OSError, ValueError) as exc:
        return {'url': url, 'error': type(exc).__name__}, ''


def inspect(source: dict) -> dict:
    result, text = fetch(source['url'])
    result['name'] = source['name']
    result['candidates'] = candidates(text, result.get('final_url', source['url'])) if text else []
    parser = References()
    parser.feed(text)
    scripts = []
    base = result.get('final_url', source['url'])
    for relative in parser.scripts:
        url = urllib.parse.urljoin(base, relative)
        if urllib.parse.urlsplit(url).netloc == urllib.parse.urlsplit(base).netloc and url.startswith('https://'):
            scripts.append(url)
    result['assets'] = []
    for url in list(dict.fromkeys(scripts))[:2]:
        asset, code = fetch(url)
        asset['candidates'] = candidates(code, asset.get('final_url', url)) if code else []
        result['candidates'].extend(asset['candidates'])
        result['assets'].append(asset)
    result['candidates'] = sorted(set(result['candidates']))
    return result


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--inventory', type=Path, default=ROOT / 'research/sources.json')
    cli.add_argument('--output', type=Path, default=ROOT / 'research/inspection.json')
    args = cli.parse_args()
    sources = json.loads(args.inventory.read_text())
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(inspect, sources))
    # Fetch each unique explicit candidate at most once; retain no body or IDs.
    urls = sorted({url for item in results for url in item['candidates']})[:40]
    with ThreadPoolExecutor(max_workers=3) as pool:
        checked = [item[0] for item in pool.map(fetch, urls)]
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'sources': results, 'candidate_checks': checked,
              'note': 'Structural counts only. No playback availability or redistribution rights verified.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    for item in results:
        print(f"{item['name']}: HTTP {item.get('http', '-')} {item.get('format', item.get('error'))}; {item.get('unique_acestream_ids', 0)} IDs; {len(item['candidates'])} candidatos")
    print(f'Informe: {args.output}; {len(checked)} candidatos comprobados')


if __name__ == '__main__':
    main()
