"""Configurable grouping for local candidate playlists."""
from collections import Counter
import json
from pathlib import Path
import re
import unicodedata

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / 'config/sections.json'


def normalized(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', text.upper()) if not unicodedata.combining(c)).replace('.', ' ')


def natural_key(text: str) -> tuple:
    return tuple((0, int(part)) if part.isdigit() else (1, part) for part in re.split(r'(\d+)', normalized(text)))


def render_sections(entries: list[dict], config: Path = DEFAULT_CONFIG) -> tuple[str, dict]:
    cfg = json.loads(config.read_text())
    rules = [(section['name'], re.compile(section['pattern'])) for section in cfg['sections']]
    fallback = cfg['fallback']
    aliases = {}
    for entry in entries:
        aliases.setdefault(entry['url'], []).append(entry)
    grouped = {}
    for url, variants in aliases.items():
        # Keep a descriptive channel name ahead of extraction fallback labels.
        variants = sorted(variants, key=lambda e: (' · ' in e['name'], len(e['name']), natural_key(e['name']), e['source']))
        selected, group = variants[0], fallback
        for section, pattern in rules:
            matches = [entry for entry in variants if pattern.search(normalized(entry['name']))]
            if matches:
                selected, group = matches[0], section
                break
        grouped.setdefault(group, []).append(dict(selected, url=url))
    lines = ['#EXTM3U refresh="3"']
    counts = Counter()
    for group in cfg['order']:
        items = grouped.pop(group, [])
        if not items:
            continue
        lines.extend(['', f'# ===== {group} ====='])
        for entry in sorted(items, key=lambda e: (natural_key(e['name']), e['url'])):
            name = ' '.join(entry['name'].split())
            lines.extend([f'#EXTINF:-1 group-title="{group}",{name}', entry['url']])
        counts[group] = len(items)
    if grouped:
        raise ValueError('section missing from configured order')
    return '\n'.join(lines) + '\n', dict(counts)
