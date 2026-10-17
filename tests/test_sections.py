import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from sections import render_sections
from playlist import parse


class SectionsTests(unittest.TestCase):
    def test_direct_catalogue_is_first_without_dropping_archive_links(self):
        current = dict(self.entry('DAZN Z', 'a'), catalog_priority=0)
        archive = dict(self.entry('DAZN A', 'b'), catalog_priority=1)
        text, counts = render_sections([archive, current])
        rows = parse(text)
        self.assertEqual([row.name for row in rows], ['DAZN Z', 'DAZN A'])
        self.assertEqual({row.url for row in rows}, {current['url'], archive['url']})
    def entry(self, name, digit):
        return {'name': name, 'url': 'acestream://' + digit * 40, 'source': 'Test'}

    def test_specific_sections_before_broad_brands(self):
        entries = [self.entry('DAZN LaLiga', 'a'), self.entry('LaLiga Hypermotion', 'b'),
                   self.entry('M+ Liga de Campeones', 'c'), self.entry('DAZN 1', 'd')]
        text, counts = render_sections(entries)
        self.assertEqual(counts, {'LA LIGA': 1, 'HYPERMOTION': 1, 'LIGA DE CAMPEONES': 1, 'DAZN': 1})
        self.assertEqual(len(parse(text)), 4)
        self.assertIn('# ===== LA LIGA =====', text)

    def test_dedup_aliases_unknown_and_determinism(self):
        entries = [self.entry('Sin identificar', 'a'), self.entry('LaLiga 1', 'a'), self.entry('Unknown channel', 'b')]
        text, counts = render_sections(entries)
        self.assertEqual(text, render_sections(list(reversed(entries)))[0])
        self.assertEqual(counts, {'LA LIGA': 1, 'OTROS / SIN CLASIFICAR': 1})
        self.assertEqual({e.url for e in parse(text)}, {e['url'] for e in entries})

    def test_numeric_order(self):
        entries = [self.entry('DAZN 10', 'a'), self.entry('DAZN 2', 'b')]
        self.assertEqual([e.name for e in parse(render_sections(entries)[0])], ['DAZN 2', 'DAZN 10'])
