import re
import runpy
import unittest
from pathlib import Path


class GalleryRefreshTests(unittest.TestCase):
    def test_only_fixture_update_controls_are_disabled(self):
        viewer = runpy.run_path(str(Path(__file__).resolve().parents[1]
                                    / '.kilo/skills/board/scripts/board_serve.py'))
        gallery = viewer['build_gallery_html']()
        live = viewer['build_html']([], [], '2026-11-23T10:00:00', None, 10)
        for label in ('Pause', 'Refresh now'):
            with self.subTest(label=label):
                button = rf'<button\b([^>]*)>{label}</button>'
                self.assertRegex(re.search(button, gallery)[1], r'\bdisabled\b')
                self.assertNotRegex(re.search(button, live)[1], r'\bdisabled\b')
