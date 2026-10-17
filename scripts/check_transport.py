#!/usr/bin/env python3
"""Check Ace Stream transport metadata locally without starting video playback.

A resolved transport is not proof that video is currently available or stable.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from urllib.parse import urlencode, urlsplit, parse_qs
from urllib.request import Request, build_opener, HTTPRedirectHandler

from playlist import ACE, ENGINE_INFOHASH, parse

ROOT = Path(__file__).resolve().parents[1]


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_engine(base):
    parts = urlsplit(base)
    if (parts.scheme != 'http' or parts.hostname not in {'127.0.0.1', 'localhost', '::1'}
            or parts.username is not None or parts.password is not None
            or parts.path not in {'', '/'} or parts.query or parts.fragment):
        raise ValueError('Engine API must be on loopback; do not expose it publicly')
    if parts.port is None:
        raise ValueError('Specify the local engine port')
    return base.rstrip('/')


def parameters(url):
    if match := ACE.fullmatch(url):
        return {'content_id': match[1].lower()}
    if match := ENGINE_INFOHASH.fullmatch(url):
        return {'infohash': match[1].lower()}
    raise ValueError('unsupported stream identifier')


def read_json(url, timeout):
    request = Request(url, headers={'Accept': 'application/json'})
    with build_opener(NoRedirect).open(request, timeout=timeout) as response:
        body = response.read(1048577)
    if len(body) > 1048576:
        raise ValueError('engine response too large')
    return json.loads(body)


def engine_state(engine, getter=read_json):
    version = getter(engine + '/webui/api/service?method=get_version', 10)
    if not version.get('result'):
        raise ValueError('Engine version could not be confirmed')
    try:
        network = getter(engine + '/server/api?api_version=3&method=get_network_connection_status', 10)
        connected = network.get('result', {}).get('connected')
    except (OSError, ValueError, AttributeError):
        connected = None
    return version['result'], connected


def check_one(entry, engine, timeout=15, getter=read_json):
    params = parameters(entry.url)
    endpoint = engine + '/server/api?' + urlencode({'api_version': 3, 'method': 'get_media_files', **params})
    started = time.monotonic()
    record = {'name': entry.name, 'url': entry.url, 'identifier_type': next(iter(params)),
              'transport_resolved': False, 'playback_tested': False}
    try:
        response = getter(endpoint, timeout)
        if response.get('error'):
            error = response['error']
            record['error'] = str(error.get('message', 'engine error') if isinstance(error, dict) else error)[:200]
        elif isinstance(response.get('result'), dict) and response['result'].get('files'):
            record['transport_resolved'] = True
            record['transport_type'] = response['result'].get('transport_type')
            record['engine_title'] = response['result'].get('name')
        else:
            record['error'] = 'engine returned no transport files'
    except (OSError, ValueError) as exc:
        record['error'] = type(exc).__name__
    record['seconds'] = round(time.monotonic() - started, 2)
    return record


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--engine', default='http://127.0.0.1:6878')
    cli.add_argument('--playlist', type=Path, default=ROOT / 'docs/canales.m3u')
    cli.add_argument('--output', type=Path, default=ROOT / '.research/transport-check.json')
    cli.add_argument('--max-items', type=int, default=12)
    cli.add_argument('--timeout', type=int, default=15)
    cli.add_argument('--match', help='Case-insensitive substring of the channel name')
    args = cli.parse_args()
    engine = validate_engine(args.engine)
    if not 1 <= args.max_items <= 100 or not 1 <= args.timeout <= 60:
        cli.error('max-items must be 1..100; timeout must be 1..60')
    # Fail once if the engine is absent; do not mislabel all channels as unavailable.
    version, connected = engine_state(engine)
    if connected is False:
        report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'engine_version': version,
                  'engine_connected': False, 'results': [], 'conclusion': 'engine_reports_offline; links not classified'}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        print('El motor informa connected=false; se detiene la prueba sin marcar los canales como caídos.')
        return 1
    entries = parse(args.playlist.read_text())
    if args.match:
        entries = [e for e in entries if args.match.casefold() in e.name.casefold()]
    # Spread probes through the selected list rather than testing only its first group.
    stride = max(1, len(entries) // args.max_items)
    selected = entries[::stride][:args.max_items]
    results = []
    for entry in selected:
        record = check_one(entry, engine, args.timeout)
        results.append(record)
        print(f"{'RESOLVED' if record['transport_resolved'] else 'FAILED'} {entry.name}: {record.get('error', '')} ({record['seconds']} s)", flush=True)
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'engine_version': version,
              'engine_connected': connected,
              'scope': 'transport metadata only; no playback, peer or video quality claim',
              'results': results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(f"Resolved {sum(r['transport_resolved'] for r in results)}/{len(results)}; report: {args.output}")


if __name__ == '__main__':
    raise SystemExit(main())
