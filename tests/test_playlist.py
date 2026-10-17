import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from playlist import parse, render, stream_url
from build_playlist import build

URL = 'https://example.org/live.m3u8'
VALID = '#EXTM3U\n#EXTINF:-1 group-title="TV", Canal   uno\n' + URL + '\n'


class ParserTests(unittest.TestCase):
    def test_normalization_and_bom(self):
        entries = parse('\ufeff' + VALID)
        self.assertEqual(entries[0].name, 'Canal uno')
        self.assertEqual(parse(render(entries, 3)), entries)
        self.assertTrue(render(entries, 3).startswith('#EXTM3U refresh="3"\n'))

    def test_comma_in_attribute_and_name(self):
        entry = parse(VALID.replace('group-title="TV"', 'group-title="TV, España"').replace('Canal   uno', 'Uno, HD'))[0]
        self.assertEqual(entry.name, 'Uno, HD')
        self.assertIn(('group-title', 'TV, España'), entry.attributes)

    def test_deterministic_exact_dedup_and_variants(self):
        one = parse(VALID)[0]
        two = parse(VALID.replace('live.m3u8', 'alternative.m3u8'))[0]
        self.assertEqual(render([two, one, one], 3), render([one, two], 3))
        self.assertEqual(len(parse(render([two, one, one], 3))), 2)

    def test_invalid_structure(self):
        cases = ['<html>oops</html>', '#EXTM3U\n', '#EXTM3U\n' + URL,
                 VALID.rsplit('\n', 2)[0], VALID.replace('#EXTINF:-1', '#EXTINF:bad'),
                 VALID.replace(URL, '#EXTINF:-1,Otra\n' + URL),
                 VALID.replace(URL, '#EXTVLCOPT:http-referrer=secret\n' + URL),
                 VALID.replace('group-title="TV"', 'unknown="x"'),
                 VALID.replace('group-title="TV"', 'group-title="TV" group-title="other"')]
        for text in cases:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse(text)

    def test_url_policy(self):
        invalid = ['http://example.org/live', 'https://u:p@example.org/a',
                   'https://example.org/a?token=secret', 'https://localhost/a',
                   'https://127.0.0.1/a', 'https://[::1]/a', 'https://example.org:99/a',
                   'https://example.org/a#secret', 'https://example.org/a%0Ab',
                   'https://example.org/a|User-Agent=x', 'file:///etc/passwd',
                   'acestream://abc', 'https://evil.org/a']
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                stream_url(value, {'example.org'})
        self.assertEqual(stream_url('acestream://' + 'A' * 40), 'acestream://' + 'a' * 40)

    def test_refresh_limits(self):
        for hours in (0, 24, True, '3', 3.5):
            with self.subTest(hours=hours), self.assertRaises(ValueError):
                render(parse(VALID), hours)


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'input.m3u').write_text(VALID)
        self.cfg = {'allowed_stream_hosts': ['example.org'], 'sources': [
            {'id': 'one', 'enabled': True, 'authorized': True, 'type': 'local_m3u', 'path': 'input.m3u'}]}
        self.config = self.root / 'sources.json'

    def run_build(self):
        self.config.write_text(json.dumps(self.cfg))
        return build(self.root, self.config)

    def test_build_and_no_rewrite(self):
        first = self.run_build()
        output = self.root / 'docs/canales.m3u'
        mtime = output.stat().st_mtime_ns
        second = self.run_build()
        self.assertTrue(first['changed'])
        self.assertFalse(second['changed'])
        self.assertEqual(output.stat().st_mtime_ns, mtime)
        self.assertEqual(first['sha256'], second['sha256'])

    def test_failure_preserves_last_good(self):
        self.run_build()
        output = self.root / 'docs/canales.m3u'
        original = output.read_bytes()
        for data in ('bad', '#EXTM3U', VALID + '#EXTINF:-1,Broken\n'):
            (self.root / 'input.m3u').write_text(data)
            with self.assertRaises(ValueError):
                self.run_build()
            self.assertEqual(output.read_bytes(), original)
            self.assertFalse(json.loads((self.root / 'docs/status.json').read_text())['ok'])
        (self.root / 'input.m3u').unlink()
        with self.assertRaises(ValueError):
            self.run_build()
        self.assertEqual(output.read_bytes(), original)

    def test_partial_failure_preserves(self):
        self.run_build()
        original = (self.root / 'docs/canales.m3u').read_bytes()
        self.cfg['sources'].append(dict(self.cfg['sources'][0], id='missing', path='missing.m3u'))
        with self.assertRaises(ValueError):
            self.run_build()
        self.assertEqual((self.root / 'docs/canales.m3u').read_bytes(), original)

    def test_invalid_config(self):
        for changes in ({'authorized': False}, {'authorized': 'true'}, {'type': 'remote_m3u'}, {'path': '../outside'}, {'enabled': 'true'}):
            self.cfg['sources'][0].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.run_build()
            self.cfg['sources'][0] = {'id': 'one', 'enabled': True, 'authorized': True, 'type': 'local_m3u', 'path': 'input.m3u'}

    def test_symlink_escape(self):
        with tempfile.TemporaryDirectory() as outside:
            path = Path(outside) / 'secret'
            path.write_text(VALID)
            (self.root / 'link').symlink_to(path)
            self.cfg['sources'][0]['path'] = 'link'
            with self.assertRaises(ValueError):
                self.run_build()

    def test_size_limit_and_unapproved_origin(self):
        self.cfg['max_source_bytes'] = 5
        with self.assertRaises(ValueError):
            self.run_build()
        self.cfg.pop('max_source_bytes')
        self.cfg['allowed_stream_hosts'] = []
        with self.assertRaises(ValueError):
            self.run_build()

    def test_cli(self):
        self.run_build()
        script = Path(__file__).resolve().parents[1] / 'scripts/validate_playlist.py'
        result = subprocess.run([sys.executable, str(script), str(self.root / 'docs/canales.m3u')], capture_output=True)
        self.assertEqual(result.returncode, 0)
        (self.root / 'docs/canales.m3u').write_text('invalid')
        result = subprocess.run([sys.executable, str(script), str(self.root / 'docs/canales.m3u')], capture_output=True)
        self.assertEqual(result.returncode, 1)


if __name__ == '__main__':
    unittest.main()
