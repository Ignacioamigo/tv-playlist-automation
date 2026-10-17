import sys
from pathlib import Path
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from logos import channel_key, select_logo, FALLBACK
from sections import render_sections
from playlist import parse
from extract_candidates import extract
from sync_logos import validate_png


class LogoTests(unittest.TestCase):
    def test_truncated_or_corrupt_png_is_rejected(self):
        image = (Path(__file__).resolve().parents[1] / 'docs/logos/generic.png').read_bytes()
        validate_png(image)
        for invalid in [b'<html>404</html>', image[:-10], image[:40] + bytes([image[40] ^ 1]) + image[41:]]:
            with self.assertRaises(ValueError): validate_png(invalid)

    def test_movistar_and_dazn_are_distinct(self):
        self.assertEqual(channel_key('M+ LaLiga FHD --> NEW ERA'), channel_key('Movistar LaLiga'))
        self.assertEqual(channel_key('DAZN LA LIGA 1 FHD f0bc --> NEW ERA VI'), channel_key('DAZN LaLiga'))
        self.assertNotEqual(channel_key('DAZN LaLiga'), channel_key('Movistar LaLiga'))
        self.assertNotEqual(channel_key('DAZN LaLiga'), channel_key('DAZN LaLiga 2'))

    def test_source_logo_is_preserved(self):
        text = '#EXTM3U\n#EXTINF:-1 tvg-logo="https://source.example/logo.png",Canal\nacestream://' + 'a' * 40
        self.assertEqual(extract(text, 'Test')[0]['logo'], 'https://source.example/logo.png')

    def test_unidentified_does_not_get_a_guessed_brand(self):
        logo, status = select_logo([{'name': 'Canal no identificado'}], {'DAZN': {'url': 'https://source.example/dazn.png'}})
        self.assertEqual((logo, status), (FALLBACK, 'generic'))

    def test_render_has_explicit_logo_without_altering_playback_url(self):
        url = 'acestream://' + 'a' * 40
        index = {'DAZN LALIGA': {'url': 'https://source.example/dazn.png'}}
        with patch('sections.load_index', return_value=index):
            text, counts = render_sections([{'name': 'DAZN LaLiga 1080p', 'url': url, 'source': 'Test'}])
        entry = parse(text)[0]
        self.assertEqual(dict(entry.attributes)['tvg-logo'], index['DAZN LALIGA']['url'])
        self.assertEqual(entry.url, url)


if __name__ == '__main__': unittest.main()
