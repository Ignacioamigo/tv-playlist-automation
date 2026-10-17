from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_transport import check_one, parameters, validate_engine, engine_state
from playlist import Entry


class TransportTests(unittest.TestCase):
    def test_offline_engine_is_not_confused_with_invalid_channels(self):
        def getter(url, timeout):
            return {'result': {'version': '3.2.17'}} if 'get_version' in url else {'result': {'connected': False}}
        version, connected = engine_state('http://localhost:6878', getter)
        self.assertEqual(version['version'], '3.2.17')
        self.assertIs(connected, False)
    def test_identifiers_are_not_interchanged(self):
        self.assertEqual(parameters('acestream://' + 'a'*40), {'content_id': 'a'*40})
        self.assertEqual(parameters('http://127.0.0.1:6878/ace/getstream?infohash=' + 'b'*40), {'infohash': 'b'*40})

    def test_control_endpoint_is_loopback_only(self):
        self.assertEqual(validate_engine('http://127.0.0.1:16878'), 'http://127.0.0.1:16878')
        for base in ['http://192.168.1.2:6878', 'https://public.example:443', 'http://localhost:6878/control', 'http://user:pass@localhost:6878']:
            with self.subTest(base=base), self.assertRaises(ValueError): validate_engine(base)

    def test_resolution_is_not_marked_as_playback_success(self):
        entry = Entry('Test', (), 'acestream://'+'a'*40)
        def getter(url, timeout):
            self.assertIn('method=get_media_files', url)
            self.assertIn('content_id=', url)
            self.assertNotIn('/ace/getstream', url)
            return {'result': {'files': [{'index': 0}], 'name': 'Test', 'transport_type': 'bt'}}
        result = check_one(entry, 'http://localhost:6878', getter=getter)
        self.assertTrue(result['transport_resolved'])
        self.assertFalse(result['playback_tested'])

    def test_engine_error_is_preserved_as_diagnostic(self):
        entry = Entry('Test', (), 'acestream://'+'a'*40)
        result = check_one(entry, 'http://localhost:6878', getter=lambda *_: {'error': {'message': 'cannot get transport file'}})
        self.assertFalse(result['transport_resolved'])
        self.assertEqual(result['error'], 'cannot get transport file')


if __name__ == '__main__': unittest.main()
