#!/usr/bin/env python3
"""Build from explicitly authorized local sources, preserving output on failure."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile

from playlist import parse, render

ROOT = Path(__file__).resolve().parents[1]


def atomic_write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(data)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def build(root: Path, config: Path) -> dict:
    root = root.resolve()
    cfg = json.loads(config.read_text(encoding='utf-8'))
    hours = cfg.get('refresh_hours', 3)
    render([], hours)
    limit = cfg.get('max_source_bytes', 2097152)
    if type(limit) is not int or not 1 <= limit <= 20 * 1024 * 1024:
        raise ValueError('invalid max_source_bytes')
    sources = cfg.get('sources')
    if not isinstance(sources, list) or not sources:
        raise ValueError('sources must be a nonempty array')
    hosts = cfg.get('allowed_stream_hosts', [])
    if not isinstance(hosts, list) or not all(isinstance(h, str) and h for h in hosts):
        raise ValueError('invalid allowed_stream_hosts')
    # Configuration errors abort before processing any source.
    active = []
    ids = set()
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError('source must be an object')
        sid = source.get('id')
        if not isinstance(sid, str) or not sid or not sid.replace('_', '').replace('-', '').isalnum() or sid in ids:
            raise ValueError('source IDs must be unique simple names')
        ids.add(sid)
        if type(source.get('enabled')) is not bool:
            raise ValueError('enabled must be boolean')
        if not source['enabled']:
            continue
        if source.get('authorized') is not True or source.get('type') != 'local_m3u':
            raise ValueError('only explicitly authorized local_m3u sources are supported')
        path = (root / source['path']).resolve()
        if not path.is_relative_to(root):
            raise ValueError('source path escapes repository')
        active.append((sid, path))
    entries, reports = [], []
    for sid, path in active:
        try:
            with path.open('rb') as handle:
                data = handle.read(limit + 1)
            if len(data) > limit:
                raise ValueError('source exceeds size limit')
            items = parse(data.decode('utf-8-sig'), set(hosts))
            entries.extend(items)
            reports.append({'id': sid, 'ok': True, 'entries': len(items)})
        except (OSError, UnicodeError, ValueError) as exc:
            # Do not log source contents, paths or exception messages containing URLs.
            reports.append({'id': sid, 'ok': False, 'error': type(exc).__name__})
            print(f'ERROR fuente {sid}: {type(exc).__name__}; revisar archivo local.', file=sys.stderr)
    status = {'attempted_at': datetime.now(timezone.utc).isoformat(), 'sources': reports}
    if not entries:
        status.update(ok=False, published=False, entries=0)
        atomic_write(root / 'docs/status.json', json.dumps(status, indent=2) + '\n')
        raise ValueError('no valid entries; previous playlist preserved')
    # Fail closed for partial outages too: keep the complete last-known-good list.
    if any(not report['ok'] for report in reports):
        status.update(ok=False, published=False, entries=0)
        atomic_write(root / 'docs/status.json', json.dumps(status, indent=2) + '\n')
        raise ValueError('source failure; previous playlist preserved')
    text = render(entries, hours)
    parsed = parse(text, set(hosts))
    output = root / 'docs/canales.m3u'
    changed = not output.exists() or output.read_bytes() != text.encode('utf-8')
    if changed:
        atomic_write(output, text)
    status.update(ok=True, published=True, changed=changed, entries=len(parsed), duplicates_removed=len(entries) - len(parsed), sha256=hashlib.sha256(text.encode()).hexdigest())
    atomic_write(root / 'docs/status.json', json.dumps(status, indent=2) + '\n')
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'config/sources.json')
    args = parser.parse_args()
    try:
        result = build(ROOT, args.config)
    except (OSError, ValueError, TypeError, KeyError):
        print('ERROR: configuración o fuente inválida; playlist anterior conservada.', file=sys.stderr)
        return 1
    print(f"OK: {result['entries']} entradas; {result['duplicates_removed']} duplicados; cambios={result['changed']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
