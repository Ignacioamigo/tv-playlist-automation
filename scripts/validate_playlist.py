#!/usr/bin/env python3
"""Validate structure, supported public URLs and duplicate entries (no network)."""
import argparse
from pathlib import Path
import sys
from playlist import parse


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('path', type=Path)
    args = cli.parse_args()
    try:
        entries = parse(args.path.read_text(encoding='utf-8-sig'))
        if len(entries) != len(set(entries)):
            raise ValueError('duplicate entries')
    except (OSError, UnicodeError, ValueError):
        print('ERROR: lista inválida (estructura, URL o duplicados).', file=sys.stderr)
        return 1
    print(f'OK: {len(entries)} entradas válidas; disponibilidad de vídeo no comprobada.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
