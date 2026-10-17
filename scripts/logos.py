"""Conservative channel-name normalization and explicit playlist logo metadata."""
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = 'https://ignacioamigo.github.io/tv-playlist-automation'
FALLBACK = PUBLIC + '/logos/generic.png'


def channel_key(name: str) -> str:
    name = ''.join(c for c in unicodedata.normalize('NFKD', name.upper()) if not unicodedata.combining(c))
    name = re.split(r'-->|→', name)[0]
    name = re.sub(r'\.{2,}[0-9A-F]{3,40}\s*$', '', name)
    name = re.sub(r'\([^)]*\)|\[[^]]*\]', ' ', name)
    name = re.sub(r'\b(?:NEW ERA(?:\s+[IVX]+)?|NEW LOOP|ELCANO)\b', ' ', name)
    name = re.sub(r'\b(?=[0-9A-F]{4}\b)(?=[0-9A-F]*[A-F])(?=[0-9A-F]*[0-9])[0-9A-F]{4}\b', ' ', name)
    name = re.sub(r'\b(?:FHD|FULL HD|HD|SD|UHD|HDR|4K|8K|1080P?|720P?|576P?|480P?|50FPS|60FPS|MULTIAUDIO|MULTI AUDIO|SOLO EVENTOS)\b', ' ', name)
    name = re.sub(r'^M(?:\+|\.|(?=\s+(?:DEPORTES|LALIGA|LA LIGA|LIGA|VAMOS|PLUS)))\s*', 'MOVISTAR ', name)
    name = name.replace('DANZ', 'DAZN')
    name = re.sub(r'^LIGA DE CAMPEONES', 'MOVISTAR LIGA DE CAMPEONES', name)
    name = re.sub(r'^MOVISTAR LALIGA TV(?! BAR)', 'MOVISTAR LALIGA', name)
    name = re.sub(r'LA\s+LIGA', 'LALIGA', name)
    name = re.sub(r'[^\w]+', ' ', name, flags=re.UNICODE)
    name = ' '.join(name.split())
    name = name.replace('SMARTBANKTV', 'SMARTBANK TV')
    name = re.sub(r'^LALIGA SMARTBANK TV M(\d+)$', r'LALIGA SMARTBANK \1', name)
    name = re.sub(r'^LALIGA SMARTBANK TV$', 'LALIGA SMARTBANK', name)
    if name in {'DAZN LALIGA 1', 'MOVISTAR LALIGA 1'}:
        name = name[:-2]
    return name


def load_index():
    path = ROOT / 'config/logo-index.json'
    return json.loads(path.read_text()) if path.exists() else {}


def select_logo(variants: list[dict], index: dict) -> tuple[str, str]:
    for entry in variants:
        if record := index.get(channel_key(entry['name'])):
            return record['url'], 'matched'
    # Unknown identities remain explicitly generic, never guessed from their group.
    return FALLBACK, 'generic'
