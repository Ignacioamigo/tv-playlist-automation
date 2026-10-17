"""Strict, deterministic M3U processing. Standard library only."""
from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import re
import unicodedata
from urllib.parse import unquote, urlsplit

ACE = re.compile(r'acestream://([0-9a-fA-F]{40})')
ENGINE_INFOHASH = re.compile(r'http://127\.0\.0\.1:6878/ace/getstream\?infohash=([0-9a-fA-F]{40})')
ATTRIBUTE = re.compile(r'\s+([a-z][a-z0-9-]*)="([^"\r\n]*)"')
ALLOWED_ATTRIBUTES = {'tvg-id', 'tvg-name', 'tvg-logo', 'group-title'}


def clean(value: str) -> str:
    if any(unicodedata.category(c).startswith('C') for c in value):
        raise ValueError('control character')
    return ' '.join(unicodedata.normalize('NFC', value).split())


def https_url(value: str, hosts: set[str] | None = None) -> str:
    """Public, credential-free HTTPS subset; never fetches stream URLs."""
    try:
        decoded = unquote(value)
        parts = urlsplit(value)
        host = parts.hostname
        if (parts.scheme != 'https' or not host or parts.username is not None
                or parts.password is not None or parts.port not in (None, 443)
                or parts.query or parts.fragment or '%' in parts.netloc
                or any(c.isspace() or ord(c) < 32 for c in decoded)
                or any(c in decoded for c in '\\|@')
                or host == 'localhost' or '.' not in host):
            raise ValueError
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            raise ValueError
        if not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?', host):
            raise ValueError
        if hosts is not None and host not in hosts:
            raise ValueError
    except ValueError:
        raise ValueError('HTTPS URL rejected by public URL policy') from None
    return value


def stream_url(value: str, hosts: set[str] | None = None) -> str:
    if match := ACE.fullmatch(value):
        return 'acestream://' + match[1].lower()
    if match := ENGINE_INFOHASH.fullmatch(value):
        # Playback happens on the TV; never fetch this control endpoint in CI.
        return 'http://127.0.0.1:6878/ace/getstream?infohash=' + match[1].lower()
    return https_url(value, hosts)


@dataclass(frozen=True)
class Entry:
    name: str
    attributes: tuple[tuple[str, str], ...]
    url: str

    def extinf(self) -> str:
        attrs = ''.join(f' {key}="{value}"' for key, value in self.attributes)
        return f'#EXTINF:-1{attrs},{self.name}'


def parse(text: str, hosts: set[str] | None = None) -> list[Entry]:
    lines = [line.strip() for line in text.lstrip('\ufeff').splitlines() if line.strip()]
    if not lines or not re.fullmatch(r'#EXTM3U(?: refresh="(?:[1-9]|1[0-9]|2[0-3])")?', lines[0]):
        raise ValueError('invalid M3U header')
    entries = []
    pending = None
    for number, line in enumerate(lines[1:], 2):
        if line.startswith('#EXTINF:'):
            if pending is not None:
                raise ValueError(f'line {number}: previous entry has no URL')
            # Find the separator outside quoted attributes (values may contain commas).
            quoted = False
            separator = None
            for pos, char in enumerate(line):
                if char == '"':
                    quoted = not quoted
                elif char == ',' and not quoted:
                    separator = pos
                    break
            if separator is None:
                raise ValueError(f'line {number}: invalid EXTINF')
            metadata, name = line[8:separator], clean(line[separator + 1:])
            duration = re.match(r'-?\d+(?:\.\d+)?', metadata)
            if not duration or not name or '@' in name:
                raise ValueError(f'line {number}: missing duration or name')
            tail = metadata[duration.end():]
            attributes = {}
            while tail:
                match = ATTRIBUTE.match(tail)
                if not match or match[1] not in ALLOWED_ATTRIBUTES or match[1] in attributes:
                    raise ValueError(f'line {number}: unsupported or invalid attribute')
                value = clean(match[2])
                if match[1] == 'tvg-logo':
                    https_url(value, hosts)
                if '@' in value or '@' in name:
                    raise ValueError(f'line {number}: personal data marker')
                attributes[match[1]] = value
                tail = tail[match.end():]
            pending = (name, tuple(sorted(attributes.items())))
        elif line.startswith('#'):
            # Plain comments allowed; unknown directives must not be silently lost.
            if line.upper().startswith(('#EXT', '#KODI', '#VLC')):
                raise ValueError(f'line {number}: unsupported directive')
        else:
            if pending is None:
                raise ValueError(f'line {number}: URL without EXTINF')
            entries.append(Entry(*pending, stream_url(line, hosts)))
            pending = None
    if pending is not None or not entries:
        raise ValueError('empty playlist or missing final URL')
    return entries


def render(entries: list[Entry], hours: int) -> str:
    if type(hours) is not int or not 1 <= hours <= 23:
        raise ValueError('refresh_hours must be an integer in 1..23')
    unique = sorted(set(entries), key=lambda e: (dict(e.attributes).get('group-title', '').casefold(), e.name.casefold(), e.url, e.attributes))
    return '\n'.join([f'#EXTM3U refresh="{hours}"'] + [line for e in unique for line in (e.extinf(), e.url)]) + '\n'
