#!/usr/bin/env python3
"""Download and validate channel logos, keeping serving URLs on our own Pages."""
from concurrent.futures import ThreadPoolExecutor
import argparse
from datetime import datetime, timezone
import hashlib
import http.client
import zlib
import json
from pathlib import Path
import re
import ssl
import struct
import threading
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from build_playlist import atomic_write
from logos import ROOT, PUBLIC, channel_key, select_logo
from playlist import parse, Entry
from remote_transport import PublicHTTPS, approved_url

BLOCKED_HOSTS = set()
HOST_LOCK = threading.Lock()


def validate_png(body):
    if not body.startswith(b'\x89PNG\r\n\x1a\n') or len(body) < 33:
        raise ValueError('expected PNG')
    width, height = struct.unpack('>II', body[16:24])
    if not (16 <= width <= 8192 and 16 <= height <= 8192):
        raise ValueError('invalid logo dimensions')
    offset = 8
    image_data = False
    while offset + 12 <= len(body):
        length = struct.unpack('>I', body[offset:offset + 4])[0]
        end = offset + length + 12
        if end > len(body):
            raise ValueError('truncated PNG chunk')
        kind = body[offset + 4:offset + 8]
        payload = body[offset + 4:end - 4]
        expected = struct.unpack('>I', body[end - 4:end])[0]
        if zlib.crc32(payload) & 0xffffffff != expected:
            raise ValueError('PNG checksum failure')
        image_data = image_data or kind == b'IDAT'
        if kind == b'IEND':
            if not image_data:
                raise ValueError('missing PNG image data')
            return
        offset = end
    raise ValueError('missing PNG end chunk')


def image_bytes(url: str):
    host = urlsplit(url).hostname
    approved_url(url, [host])
    with HOST_LOCK:
        if host in BLOCKED_HOSTS:
            raise ValueError('image host rate limited')
    parts = urlsplit(url)
    conn = PublicHTTPS(host, timeout=8, context=ssl.create_default_context())
    try:
        conn.request('GET', parts.path, headers={'User-Agent': 'tv-playlist-logo-check/1.0', 'Accept-Encoding': 'identity'})
        response = conn.getresponse()
        if response.status == 429:
            with HOST_LOCK:
                BLOCKED_HOSTS.add(host)
        if response.status != 200:
            raise ValueError('image HTTP failure')
        body = response.read(1048577)
        if len(body) > 1048576:
            raise ValueError('image too large')
        validate_png(body)
        return body
    finally:
        conn.close()


def get_json(url, cache, reuse=False):
    if reuse and cache.exists():
        return json.loads(cache.read_text())
    try:
        with urlopen(Request(url, headers={'User-Agent': 'tv-playlist-logo-check/1.0'}), timeout=20) as response:
            data = response.read(15 * 1024 * 1024)
        result = json.loads(data)
        atomic_write(cache, json.dumps(result, ensure_ascii=False))
        return result
    except (OSError, ValueError):
        if cache.exists():
            return json.loads(cache.read_text())
        return {'sha': None, 'tree': []} if cache.name == 'picons-tree.json' else []


def sync(reuse_verified=False):
    work = ROOT / '.research'
    entries = json.loads((work / 'extracted.json').read_text())
    names = {channel_key(e['name']) for e in entries}
    compact_names = {}
    for name in names:
        compact_names.setdefault(name.replace(' ', ''), set()).add(name)
    choices = {}
    tree = get_json('https://api.github.com/repos/davidmuma/picons_dobleM/git/trees/master?recursive=1', work / 'picons-tree.json', reuse_verified)
    revision = tree['sha']
    for item in tree['tree']:
        path = item['path']
        if path.startswith('icon/') and path.endswith('.png'):
            key = channel_key(Path(path).stem)
            for target_key in compact_names.get(key.replace(' ', ''), []):
                choices.setdefault(target_key, []).append({'source': 'picons_dobleM', 'url': 'https://raw.githubusercontent.com/davidmuma/picons_dobleM/' + revision + '/' + quote(path, safe='/'), 'channel': Path(path).stem})
    channels = get_json('https://iptv-org.github.io/api/channels.json', work / 'channels.json', reuse_verified)
    logos = get_json('https://iptv-org.github.io/api/logos.json', work / 'logos.json', reuse_verified)
    by_channel = {}
    for logo in logos:
        if logo.get('in_use') and logo.get('format') == 'PNG' and logo['url'].startswith('https://'):
            by_channel.setdefault(logo['channel'], []).append(logo['url'])
    key_channels = {}
    for channel in channels:
        if channel.get('closed') or channel['id'] not in by_channel:
            continue
        for alias in [channel['name'], channel['id'].rsplit('.', 1)[0], *channel.get('alt_names', [])]:
            key = channel_key(alias)
            for target_key in compact_names.get(key.replace(' ', ''), []):
                key_channels.setdefault(target_key, {})[channel['id']] = channel
    for key, matches in key_channels.items():
        if len(matches) != 1:
            continue
        cid = next(iter(matches))
        for url in sorted(set(by_channel[cid]))[:2]:
            choices.setdefault(key, []).append({'source': 'iptv-org', 'url': url, 'channel': cid})
    for entry in entries:
        if entry.get('logo'):
            choices.setdefault(channel_key(entry['name']), []).append({
                'source': 'playlist_metadata', 'url': entry['logo'], 'channel': entry['name']})
    for options in choices.values():
        options.sort(key=lambda o: (o['source'] != 'picons_dobleM', bool(re.search(r'\b(HDR|UHD|4K)\b', o['channel'])), len(o['channel'])))
    old = json.loads((ROOT / 'config/logo-index.json').read_text()) if (ROOT / 'config/logo-index.json').exists() else {}
    destination = ROOT / 'docs/logos'
    destination.mkdir(parents=True, exist_ok=True)
    # Code-drawn neutral TV icon; never presented as an identified channel brand.
    width, height = 256, 160
    pixels = bytearray()
    for y in range(height):
        pixels.append(0)
        for x in range(width):
            rim = (28 <= x < 228 and 20 <= y < 130 and not (36 <= x < 220 and 28 <= y < 122))
            stand = 90 <= x < 166 and 141 <= y < 149
            pixels.extend((169, 183, 200) if rim or stand else (22, 32, 45))
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    generic = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(bytes(pixels))) + chunk(b'IEND', b'')
    (destination / 'generic.png').write_bytes(generic)
    def usable_previous(record):
        if not record:
            return False
        try:
            validate_png((destination / record['url'].rsplit('/', 1)[-1]).read_bytes())
            return True
        except (OSError, ValueError):
            return False
    def check(item):
        key, options = item
        prior = old.get(key)
        if reuse_verified and usable_previous(prior):
            return key, prior, None
        for option in options[:4]:
            try:
                body = image_bytes(option['url'])
                filename = hashlib.sha256(body).hexdigest()[:24] + '.png'
                (destination / filename).write_bytes(body)
                return key, dict(option, original_url=option['url'], url=PUBLIC + '/logos/' + filename), None
            except (OSError, ValueError, http.client.HTTPException) as exc:
                error = type(exc).__name__
        prior = old.get(key)
        if prior:
            filename = prior['url'].rsplit('/', 1)[-1]
            if usable_previous(prior):
                return key, prior, 'retained_previous'
        return key, None, 'unavailable'
    index = {key: value for key, value in old.items() if key in names and usable_previous(value)}
    errors = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        for key, record, error in pool.map(check, choices.items()):
            if record:
                index[key] = record
            if error:
                errors[key] = error
    atomic_write(ROOT / 'config/logo-index.json', json.dumps(index, ensure_ascii=False, indent=2) + '\n')
    aliases = {}
    for entry in entries:
        aliases.setdefault(entry['url'], []).append(entry)
    def decorate(path):
        if not path.exists():
            return {}
        original = path.read_text()
        result = [original.splitlines()[0]]
        counts = {'entries': 0, 'channel_logo': 0, 'generic_logo': 0}
        unresolved = set()
        previous_group = None
        for entry in parse(original):
            attrs = dict(entry.attributes)
            group = attrs.get('group-title', '')
            if group != previous_group:
                result.extend(['', f'# ===== {group} ====='])
                previous_group = group
            url, kind = select_logo([{'name': entry.name}] + aliases.get(entry.url, []), index)
            attrs['tvg-logo'] = url
            result.extend([Entry(entry.name, tuple(sorted(attrs.items())), entry.url).extinf(), entry.url])
            counts['entries'] += 1
            counts['channel_logo' if kind == 'matched' else 'generic_logo'] += 1
            if kind == 'generic':
                unresolved.add(entry.name)
        output = '\n'.join(result) + '\n'
        parse(output)
        atomic_write(path, output)
        counts['unresolved_names'] = sorted(unresolved)
        return counts
    coverage = decorate(ROOT / 'docs/canales.m3u')
    decorate(ROOT / '.research/canales-candidatos.m3u')
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'channel_name_keys': len(names),
              'matched_keys': len(index), 'image_failures': errors, 'picons_revision': revision, 'coverage': coverage}
    atomic_write(ROOT / 'docs/logo-status.json', json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    status_path = ROOT / 'docs/status.json'
    if status_path.exists():
        status = json.loads(status_path.read_text())
        status['logos'] = {k: v for k, v in coverage.items() if k != 'unresolved_names'}
        status['sha256'] = hashlib.sha256((ROOT / 'docs/canales.m3u').read_bytes()).hexdigest()
        atomic_write(status_path, json.dumps(status, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'matched_keys': len(index), 'coverage': {k: v for k, v in coverage.items() if k != 'unresolved_names'},
                      'image_failures': len(errors)}, ensure_ascii=False))


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--reuse-verified', action='store_true', help='Reuse images and catalogues already checked locally')
    sync(cli.parse_args().reuse_verified)
