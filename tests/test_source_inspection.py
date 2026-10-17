import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from inspect_sources import candidates
from extract_candidates import extract
from playlist import parse, stream_url
from sections import render_sections


class ResearchTests(unittest.TestCase):
    def test_infohash_is_not_a_content_id_even_if_hex_matches(self):
        sid = 'a' * 40
        text = '{infohash:"' + sid + '",name:"Infohash channel"}\nacestream://' + sid
        entries = extract(text, 'Test')
        self.assertEqual(len(entries), 2)
        urls = {entry['url'] for entry in entries}
        self.assertIn('acestream://' + sid, urls)
        self.assertIn('http://127.0.0.1:6878/ace/getstream?infohash=' + sid, urls)
        self.assertEqual(len(parse(render_sections(entries)[0])), 2)

    def test_only_exact_engine_infohash_endpoint_is_allowed(self):
        valid = 'http://127.0.0.1:6878/ace/getstream?infohash=' + 'a' * 40
        self.assertEqual(stream_url(valid), valid)
        for invalid in [valid + '&token=x', valid.replace('6878', '80'),
                        valid.replace('/ace/getstream', '/server/api'), valid.replace('127.0.0.1', '192.168.1.2')]:
            with self.subTest(url=invalid), self.assertRaises(ValueError):
                stream_url(invalid)
    def test_explicit_candidates_only(self):
        text = '<a href="/list.m3u">Lista</a><a href="https://bad.example/list.m3u?token=x">Private</a><script src="app.js"></script>'
        self.assertEqual(candidates(text,'https://source.example/page'),['https://source.example/list.m3u'])

    def test_extract_formats_and_dedup(self):
        sid='a'*40
        other='b'*40
        text=f'#EXTM3U\n#EXTINF:-1 group-title="TV, ES",Mi canal, HD\nacestream://{sid}\n'+f'{{infohash:"{other}",name:"Otro canal"}}'+f'{{"url":"acestream:\\/\\/{sid}"}}'
        items=extract(text,'Test')
        self.assertEqual(len(items),2)
        self.assertEqual({e['name'] for e in items},{'Mi canal, HD','Otro canal'})

    def test_reject_bad_id_and_keep_json_ids(self):
        text='acestream://'+'a'*41+' '+ '{"url":"acestream://'+'b'*40+'"}'
        items=extract(text,'Test')
        self.assertEqual(len(items),1)
        self.assertEqual(items[0]['url'],'acestream://'+'b'*40)

    def test_engine_and_kodi_representations(self):
        sid = 'c' * 40
        for url in (f'http://127.0.0.1:6878/ace/getstream?id={sid}',
                    f'plugin://script.module.horus?action=play&id={sid}'):
            entries = extract(f'#EXTM3U\n#EXTINF:-1,Canal\n{url}\n', 'Test')
            self.assertEqual(entries[0]['url'], 'acestream://' + sid)
            self.assertEqual(entries[0]['name'], 'Canal')


if __name__=='__main__':
    unittest.main()
