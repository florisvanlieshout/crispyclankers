"""Offline checks for the actual HTML and image assets; stdlib only."""
import struct
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]

class Head(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.meta = {}
        self.canonical = []
        self.in_head = False
        self.feed(source)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "head": self.in_head = True
        if not self.in_head: return
        if tag == "meta":
            key = attrs.get("property") or attrs.get("name")
            if key: self.meta.setdefault(key, []).append(attrs.get("content", ""))
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical.append(attrs.get("href"))
    def handle_endtag(self, tag):
        if tag == "head": self.in_head = False

class SocialPreviews(unittest.TestCase):
    def test_both_pages_have_complete_static_metadata(self):
        for locale, path in [("nl", "nl/index.html"), ("en", "index.html")]:
            with self.subTest(locale=locale):
                head = Head((ROOT / path).read_text())
                required = ["og:title", "og:description", "og:url", "og:type", "og:site_name",
                            "og:locale", "og:image", "og:image:secure_url", "og:image:type",
                            "og:image:width", "og:image:height", "og:image:alt", "twitter:card",
                            "twitter:title", "twitter:description", "twitter:image", "twitter:image:alt"]
                for key in required:
                    self.assertEqual(len(head.meta.get(key, [])), 1, key)
                    self.assertTrue(head.meta[key][0].strip(), key)
                m = {k: v[0] for k, v in head.meta.items()}
                url = "https://crispyclankers.com/" + ("nl/" if locale == "nl" else "")
                self.assertEqual(m["og:url"], url)
                self.assertEqual(head.canonical, [url])
                self.assertEqual(m["og:type"], "website")
                self.assertEqual(m["og:locale"], "nl_NL" if locale == "nl" else "en_US")
                self.assertEqual(m["twitter:card"], "summary_large_image")
                self.assertEqual(m["twitter:image"], m["og:image"])
                self.assertEqual(m["og:image:secure_url"], m["og:image"])
                self.assertEqual(m["og:image:type"], "image/png")
                image_url = urlparse(m["og:image"])
                self.assertEqual((image_url.scheme, image_url.netloc), ("https", "crispyclankers.com"))
                image = (ROOT / image_url.path.lstrip("/")).read_bytes()
                self.assertEqual(image[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(image[12:16], b"IHDR")
                size = struct.unpack(">II", image[16:24])
                self.assertEqual(size, (1200, 630))
                self.assertEqual(size, (int(m["og:image:width"]), int(m["og:image:height"])))
                self.assertLess(len(image), 300_000, "Keep crawler downloads small")

if __name__ == "__main__":
    unittest.main()
