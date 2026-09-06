"""Static landing-video contract; behavior is exercised by browser_hero.py."""
import hashlib
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Elements(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.elements = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class HeroVideo(unittest.TestCase):
    def test_both_pages_use_local_accessible_progressive_video(self):
        for path, label in [('nl/index.html', 'Clanky, bel mij nu!'),
                            ('index.html', 'Clanky, call me now!')]:
            with self.subTest(path=path):
                source = (ROOT / path).read_text()
                elements = Elements(source).elements
                videos = [a for tag, a in elements if tag == 'video']
                self.assertEqual(len(videos), 1)
                video = videos[0]
                for attr in ['autoplay', 'muted', 'playsinline', 'hidden']:
                    self.assertIn(attr, video)
                self.assertNotIn('loop', video)
                self.assertNotIn('src', video, 'No-JS / reduced motion must not fetch video')
                self.assertEqual(video['preload'], 'auto')
                self.assertEqual((video['width'], video['height']), ('960', '960'))
                self.assertTrue(video['aria-label'])
                for key in ['poster', 'data-src']:
                    self.assertTrue(video[key].startswith('/assets/'))
                    self.assertTrue((ROOT / video[key].lstrip('/')).is_file())
                cta = [a for tag, a in elements if 'hero-call' in a.get('class', '').split()]
                self.assertEqual(len(cta), 1)
                self.assertEqual(cta[0]['href'], '#call')
                self.assertIn('>' + label + '</a>', source)
                self.assertIn(('div', {'class': 'hero-finale'}), elements)
                self.assertIn(('script', {'src': '/assets/hero-video-v1.js', 'defer': None}), elements)
                self.assertIn(('link', {'rel': 'stylesheet', 'href': '/assets/hero-video-v1.css'}), elements)

    def test_owner_video_is_unchanged(self):
        video = (ROOT / 'assets/clanky-intro-v1.mp4').read_bytes()
        self.assertEqual(hashlib.sha256(video).hexdigest(),
                         'bba38f93fe3b04873576250cf16d53deb265ecb31b82d68d36c2c4d77e776f93')
        self.assertLess(len(video), 2_000_000)


if __name__ == '__main__':
    unittest.main()
