import json
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from refresh_sources import collect, refresh
from remote_transport import approved_url, PublicHTTPS


class RefreshTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / 'docs').mkdir()
        (self.root / 'docs/canales.m3u').write_text('previous valid publication')
        self.sources = [{'id': 'one', 'name': 'One', 'type': 'https_catalog', 'enabled': True, 'publish': False}]

    def run_refresh(self, collector):
        config = self.root / 'config.json'
        config.write_text(json.dumps({'timeout_seconds': 5, 'max_source_bytes': 1000, 'sources': self.sources}))
        return refresh(self.root, config, collector=collector)

    def items(self, source, *args):
        return [{'name': 'DAZN LaLiga', 'url': 'acestream://' + 'a' * 40, 'source': source['name']}]

    def test_unpublish_catalogue_remains_local(self):
        status = self.run_refresh(self.items)
        self.assertFalse(status['published'])
        self.assertEqual(status['candidate_entries'], 1)
        self.assertEqual((self.root / 'docs/canales.m3u').read_text(), 'previous valid publication')
        self.assertIn('group-title="LA LIGA"', (self.root / '.research/canales-candidatos.m3u').read_text())

    def test_publish_source_can_publish(self):
        self.sources[0]['publish'] = True
        status = self.run_refresh(self.items)
        self.assertTrue(status['published'])
        self.assertEqual(status['publication_entries'], 1)

    def test_partial_publish_failure_preserves_publication(self):
        self.sources[0]['publish'] = True
        self.sources.append(dict(self.sources[0], id='two'))
        def collector(source, *args):
            if source['id'] == 'two': raise ValueError('unavailable')
            return self.items(source)
        with self.assertRaises(ValueError): self.run_refresh(collector)
        self.assertEqual((self.root / 'docs/canales.m3u').read_text(), 'previous valid publication')
        report = json.loads((self.root / '.research/refresh-status.json').read_text())
        self.assertFalse(report['published'])

    def test_no_sources_does_not_replace_candidate_or_publication(self):
        (self.root / '.research').mkdir()
        output = self.root / '.research/canales-candidatos.m3u'
        output.write_text('previous candidates')
        def collector(*args): raise ValueError('failed')
        with self.assertRaises(ValueError): self.run_refresh(collector)
        self.assertEqual(output.read_text(), 'previous candidates')

    def test_seed_backup_keeps_unavailable_source_in_publication(self):
        self.sources[0]['publish'] = True
        self.sources.append(dict(self.sources[0], id='two'))
        backups = self.root / 'data/source-snapshots'
        backups.mkdir(parents=True)
        backup = [{'name': 'Eurosport', 'url': 'acestream://' + 'b' * 40, 'source': 'Two'}]
        (backups / 'two.json').write_text(json.dumps(backup))
        def collector(source, *args):
            if source['id'] == 'two': raise ValueError('HTTP 403')
            return self.items(source)
        status = self.run_refresh(collector)
        self.assertTrue(status['published'])
        self.assertEqual(status['publication_entries'], 2)
        self.assertTrue(status['sources'][1]['cached'])
        self.assertFalse(status['complete'])

    def test_total_outage_preserves_publication_even_with_cache(self):
        self.sources[0]['publish'] = True
        self.run_refresh(self.items)
        original = (self.root / 'docs/canales.m3u').read_bytes()
        def collector(*args): raise ValueError('unavailable')
        with self.assertRaises(ValueError): self.run_refresh(collector)
        self.assertEqual((self.root / 'docs/canales.m3u').read_bytes(), original)

    def test_dynamic_bundle_discovery(self):
        source = {'name': 'UI', 'type': 'web_catalog', 'url': 'https://source.example/', 'allowed_hosts': ['source.example']}
        calls = []
        def downloader(url, *args):
            calls.append(url)
            if len(calls) == 1: return '<script src="/static/js/main.newhash.js"></script>'
            return '{infohash:"' + 'a' * 40 + '",name:"Canal"}'
        entries = collect(source, 1000, 5, downloader=downloader)
        self.assertEqual(len(entries), 1)
        self.assertTrue(calls[1].endswith('main.newhash.js'))

    def test_gist_fetches_current_revision(self):
        source = {'name': 'Gist', 'type': 'gist', 'url': 'https://api.github.com/gists/id', 'allowed_hosts': ['api.github.com', 'gist.githubusercontent.com']}
        def downloader(url, *args):
            if 'api.github.com' in url:
                return json.dumps({'files': {'channels': {'filename': 'channels.m3u', 'raw_url': 'https://gist.githubusercontent.com/current/raw/file.m3u'}}})
            return '#EXTM3U\n#EXTINF:-1,Canal\nacestream://' + 'b' * 40 + '\n'
        self.assertEqual(len(collect(source, 1000, 5, downloader=downloader)), 1)


class NetworkPolicyTests(unittest.TestCase):
    def test_unapproved_urls(self):
        for url in ['http://source.example/a', 'https://private.example/a', 'https://u:p@source.example/a',
                    'https://source.example/a?token=x', 'https://source.example:99/a']:
            with self.subTest(url=url), self.assertRaises(ValueError): approved_url(url, ['source.example'])

    def test_private_dns_rejected_before_connecting(self):
        with patch('remote_transport.socket.getaddrinfo', return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 443))]), patch('remote_transport.socket.create_connection') as connect:
            with self.assertRaises(ValueError): PublicHTTPS('source.example').connect()
            connect.assert_not_called()


if __name__ == '__main__': unittest.main()
