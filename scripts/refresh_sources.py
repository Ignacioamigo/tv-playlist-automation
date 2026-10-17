#!/usr/bin/env python3
"""Refresh current remote catalogues and publish enabled sources."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
from urllib.parse import urljoin

from build_playlist import atomic_write
from extract_candidates import extract
from inspect_sources import References
from playlist import parse
from remote_transport import approved_url, download
from sections import render_sections

ROOT = Path(__file__).resolve().parents[1]


class IPFS:
    def __init__(self, binary: str):
        self.binary = shutil.which(binary)
        self.temporary = None
        self.daemon = None
        self.log = None

    def command(self, args, timeout=30):
        result = subprocess.run([self.binary, *args], env=self.env, capture_output=True,
                                timeout=timeout, check=True)
        return result.stdout

    def start(self):
        if not self.binary:
            raise ValueError('Kubo executable missing')
        self.temporary = tempfile.TemporaryDirectory(prefix='tv-playlist-ipfs-')
        self.env = dict(os.environ, IPFS_PATH=str(Path(self.temporary.name) / 'repo'))
        self.command(['init', '--profile=lowpower'])
        for key, value in [('Addresses.Swarm', '[]'), ('Addresses.API', '"/ip4/127.0.0.1/tcp/0"'),
                           ('Addresses.Gateway', '"/ip4/127.0.0.1/tcp/0"')]:
            self.command(['config', '--json', key, value])
        self.log = open(Path(self.temporary.name) / 'daemon.log', 'wb')
        self.daemon = subprocess.Popen([self.binary, 'daemon', '--migrate=false'], env=self.env,
                                       stdout=self.log, stderr=subprocess.STDOUT)
        for _ in range(60):
            if self.daemon.poll() is not None:
                raise ValueError('Kubo startup failed')
            if (Path(self.env['IPFS_PATH']) / 'api').exists():
                return
            time.sleep(.25)
        raise TimeoutError('Kubo startup deadline')

    def read(self, source, limit, timeout):
        path = source['path']
        if any(piece in {'', '.', '..'} for piece in path.split('/')) or not re.fullmatch(r'[a-zA-Z0-9_./-]+', path):
            raise ValueError('invalid IPFS file path')
        # Alternatives refer to one logical source; never combine stale snapshots.
        for name in source['names']:
            if not re.fullmatch(r'[a-zA-Z0-9]{40,100}', name):
                raise ValueError('invalid IPNS name')
            try:
                resolved = self.command([f'--timeout={timeout}s', 'name', 'resolve', '/ipns/' + name], timeout + 5).decode().strip()
                if not re.fullmatch(r'/ipfs/[a-zA-Z0-9]+', resolved):
                    raise ValueError('unexpected IPNS target')
                body = self.command([f'--timeout={timeout}s', 'cat', f'--length={limit + 1}', resolved + '/' + path], timeout + 5)
                if len(body) > limit:
                    raise ValueError('IPFS source size limit')
                return body.decode('utf-8-sig')
            except (subprocess.SubprocessError, ValueError, UnicodeError):
                continue
        raise ValueError('IPNS source unavailable')

    def close(self):
        if self.daemon is not None:
            self.daemon.terminate()
            try:
                self.daemon.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.daemon.kill()
                self.daemon.wait()
        if self.log is not None:
            self.log.close()
        if self.temporary is not None:
            self.temporary.cleanup()


def collect(source, limit, timeout, ipfs=None, downloader=download):
    name = source['name']
    if source['type'] == 'ipns_m3u':
        text = ipfs.read(source, limit, timeout)
        entries = extract(text, name)
    else:
        hosts = source['allowed_hosts']
        text = downloader(source['url'], hosts, limit, timeout)
        if source['type'] == 'gist':
            files = json.loads(text)['files']
            entries = []
            for file in files.values():
                if not file['filename'].lower().endswith(('.m3u', '.m3u8', '.txt')):
                    continue
                body = downloader(file['raw_url'], hosts, limit, timeout)
                entries.extend(extract(body, name))
        elif source['type'] == 'web_catalog':
            parser = References()
            parser.feed(text)
            bundles = [urljoin(source['url'], url) for url in parser.scripts
                       if re.search(r'/static/js/main\.[a-zA-Z0-9]+\.js$', url)]
            if len(bundles) != 1:
                raise ValueError('expected one current application bundle')
            approved_url(bundles[0], hosts)
            entries = extract(downloader(bundles[0], hosts, limit, timeout), name)
        elif source['type'] == 'https_catalog':
            entries = extract(text, name)
        else:
            raise ValueError('unsupported source type')
    if not entries:
        raise ValueError('empty catalogue')
    return entries


def refresh(root: Path, config: Path, ipfs_bin='ipfs', collector=collect, ipfs_factory=IPFS):
    cfg = json.loads(config.read_text())
    limit, timeout = cfg['max_source_bytes'], cfg['timeout_seconds']
    if type(limit) is not int or not 1 <= limit <= 8388608 or type(timeout) is not int or not 1 <= timeout <= 60:
        raise ValueError('invalid source limits')
    sources = [s for s in cfg['sources'] if s.get('enabled') is True]
    ids = set()
    for source in sources:
        if (not re.fullmatch(r'[a-z0-9_-]+', source['id']) or source['id'] in ids
                or type(source.get('publish')) is not bool):
            raise ValueError('invalid source configuration')
        ids.add(source['id'])
    ipfs = ipfs_factory(ipfs_bin)
    ipfs_ready = False
    entries, publishable, reports = [], [], []
    cache = root / '.research/source-cache'
    cache.mkdir(parents=True, exist_ok=True)
    try:
        if any(s['type'] == 'ipns_m3u' for s in sources):
            try:
                ipfs.start()
                ipfs_ready = True
            except (OSError, ValueError, subprocess.SubprocessError):
                pass
        def fetch_one(source):
            try:
                if source['type'] == 'ipns_m3u' and not ipfs_ready:
                    raise ValueError('Kubo unavailable')
                items = collector(source, limit, timeout, ipfs)
                if not items:
                    raise ValueError('empty source')
                parse(render_sections(items)[0])
                atomic_write(cache / (source['id'] + '.json'), json.dumps(items, ensure_ascii=False) + '\n')
                return source, items, None, False
            except (OSError, ValueError, KeyError, http.client.HTTPException, subprocess.SubprocessError) as exc:
                reason = str(exc) if re.fullmatch(r'HTTP \d{3}', str(exc)) else type(exc).__name__
                for backup in [cache / (source['id'] + '.json'), root / 'data/source-snapshots' / (source['id'] + '.json')]:
                    try:
                        items = json.loads(backup.read_text())
                        if not items:
                            continue
                        parse(render_sections(items)[0])
                        return source, items, reason, True
                    except (OSError, ValueError, TypeError, KeyError):
                        continue
                return source, [], reason, False
        with ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(fetch_one, sources))
        for source, items, error, cached in results:
            entries.extend(items)
            if source['publish']:
                publishable.extend(items)
            reports.append({'id': source['id'], 'ok': error is None, 'entries': len(items),
                            'publish': source['publish'], 'cached': cached, 'error': error})
            print(f"{source['id']}: {'OK' if error is None else 'BACKUP' if cached else 'ERROR'}; {len(items)} entradas")
    finally:
        ipfs.close()
    target = root / '.research'
    target.mkdir(parents=True, exist_ok=True)
    status = {'attempted_at': datetime.now(timezone.utc).isoformat(), 'sources': reports,
              'complete': bool(reports) and all(r['ok'] for r in reports),
              'published': False, 'candidate_entries': 0, 'publication_entries': 0}
    if entries:
        text, counts = render_sections(entries)
        status['candidate_entries'] = len(parse(text))
        status['sections'] = counts
        atomic_write(target / 'canales-candidatos.m3u', text)
        atomic_write(target / 'extracted.json', json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
    failed_publish = any(r['publish'] and not r['ok'] and not r['cached'] for r in reports)
    no_fresh_sources = not any(r['ok'] for r in reports)
    if publishable and not failed_publish and not no_fresh_sources:
        text, counts = render_sections(publishable)
        status['publication_entries'] = len(parse(text))
        status['publication_sections'] = counts
        status['sha256'] = hashlib.sha256(text.encode()).hexdigest()
        atomic_write(root / 'docs/canales.m3u', text)
        status['published'] = True
        atomic_write(root / 'docs/status.json', json.dumps(status, indent=2) + '\n')
    atomic_write(target / 'refresh-status.json', json.dumps(status, indent=2) + '\n')
    if failed_publish or not entries or no_fresh_sources:
        raise ValueError('refresh incomplete; published playlist preserved')
    return status


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--config', type=Path, default=ROOT / 'config/remote-sources.json')
    cli.add_argument('--ipfs-bin', default='ipfs')
    args = cli.parse_args()
    try:
        status = refresh(ROOT, args.config, args.ipfs_bin)
    except (OSError, ValueError, KeyError, TypeError):
        print('ERROR: no se publica una lista incompleta o inválida.')
        return 1
    print(f"Candidatos únicos: {status['candidate_entries']}; publicados: {status['publication_entries']}")
    if not status['complete']:
        print('WARN: recopilación parcial; consultar refresh-report para las fuentes fallidas.')
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as handle:
            handle.write(f"published={str(status['published']).lower()}\n")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
