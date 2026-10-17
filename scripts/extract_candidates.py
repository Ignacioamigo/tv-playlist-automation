#!/usr/bin/env python3
"""Extract local research candidates from explicit public resources. Never deploy."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, urlsplit
from inspect_sources import fetch

ROOT = Path(__file__).resolve().parents[1]
ACE = re.compile(r'acestream://([a-fA-F0-9]{40})(?![a-fA-F0-9])', re.I)
STATIC = re.compile(r'\{infohash:"([0-9a-fA-F]{40})",name:("(?:[^"\\]|\\.)*")\}')


def entry_id(line: str) -> str | None:
    if match := ACE.fullmatch(line):
        return match[1].lower()
    parts = urlsplit(line)
    if ((parts.scheme in {'http', 'https'} and parts.path == '/ace/getstream')
            or (parts.scheme == 'plugin' and parts.netloc == 'script.module.horus')):
        values = parse_qs(parts.query).get('id', [])
        if len(values) == 1 and re.fullmatch(r'[a-fA-F0-9]{40}', values[0]):
            return values[0].lower()
    return None


def extract(text: str, source: str) -> list[dict]:
    found = {}
    for sid, encoded_name in STATIC.findall(text):
        try:
            name = json.loads(encoded_name)
        except ValueError:
            continue
        found[sid.lower()] = {'name': name, 'url': 'acestream://' + sid.lower(), 'source': source}
    pending = None
    for line in text.splitlines():
        if line.startswith('#EXTINF:'):
            quoted = False
            pending = None
            for index, char in enumerate(line):
                if char == '"': quoted = not quoted
                elif char == ',' and not quoted:
                    pending = line[index + 1:].strip()
                    break
        elif sid := entry_id(line.strip()):
            found.setdefault(sid, {'name': pending or f'{source} · {sid[:8]}', 'url': 'acestream://' + sid, 'source': source})
            pending = None
    # Also retain IDs embedded in JSON, HTML and escaped links.
    for sid in ACE.findall(text.replace('\\/', '/')):
        sid = sid.lower()
        found.setdefault(sid, {'name': f'{source} · {sid[:8]}', 'url': 'acestream://' + sid, 'source': source})
    return list(found.values())


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--merge-ipfs', action='store_true', help='Merge downloaded IPFS files into the existing local catalogue without HTTP requests')
    args = cli.parse_args()
    sources = json.loads((ROOT / 'research/extraction-sources.json').read_text())
    entries, reports = [], []
    if args.merge_ipfs:
        entries = [e for e in json.loads((ROOT / '.research/extracted.json').read_text()) if not e['source'].startswith('IPFS ')]
        reports = [r for r in json.loads((ROOT / 'research/extraction-summary.json').read_text())['sources'] if not r['name'].startswith('IPFS ')]
    else:
        with ThreadPoolExecutor(max_workers=3) as pool:
            fetched = list(pool.map(fetch, [s['url'] for s in sources]))
        for source, (metadata, text) in zip(sources, fetched):
            items = extract(text, source['name'])
            entries.extend(items)
            reports.append(dict(metadata, name=source['name'], unique_ids=len(items)))
    for path in sorted((ROOT / '.research/ipfs').glob('*')):
        if path.suffix.lower() not in {'.m3u', '.m3u8', '.html'}:
            continue
        source = 'IPFS ' + path.name
        items = extract(path.read_text(), source)
        entries.extend(items)
        reports.append({'name': source, 'file': str(path.relative_to(ROOT)), 'unique_ids': len(items)})
    unique = {}
    for entry in entries:
        unique.setdefault(entry['url'], entry)
    target = ROOT / '.research'
    target.mkdir(exist_ok=True)
    (target / 'extracted.json').write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
    lines = ['#EXTM3U refresh="3"']
    for entry in sorted(unique.values(), key=lambda e: (e['name'].casefold(), e['url'])):
        name = ' '.join(entry['name'].split())
        lines.extend([f'#EXTINF:-1 group-title="Candidatos sin verificar",{name}', entry['url']])
    (target / 'canales-candidatos.m3u').write_text('\n'.join(lines) + '\n')
    summary = {'checked_at': datetime.now(timezone.utc).isoformat(), 'source_entries': len(entries),
               'unique_ids': len(unique), 'duplicates_removed': len(entries) - len(unique),
               'sources': reports, 'playback_verified': False, 'redistribution_rights_verified': False,
               'output': '.research/canales-candidatos.m3u'}
    (ROOT / 'research/extraction-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'sources'}, indent=2))
    for report in reports:
        print(f"{report['name']}: {report['unique_ids']} identificadores; HTTP {report.get('http', '-')}")


if __name__ == '__main__':
    main()
