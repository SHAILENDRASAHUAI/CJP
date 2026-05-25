import re
import unittest
from html.parser import HTMLParser
from pathlib import Path


class LinkAndImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.internal_links = []
        self.images = []

    def handle_starttag(self, tag, attrs):
        attr_map = dict(attrs)
        element_id = attr_map.get("id")
        if element_id:
            self.ids.add(element_id)

        if tag == "a":
            href = attr_map.get("href", "")
            if href.startswith("#"):
                self.internal_links.append(href[1:])

        if tag == "img":
            self.images.append(attr_map)


class TestIndexHtml(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index_path = Path(__file__).resolve().parents[1] / "index.html"
        cls.content = cls.index_path.read_text(encoding="utf-8")

        cls.parser = LinkAndImageParser()
        cls.parser.feed(cls.content)

    def test_document_metadata(self):
        self.assertIn("<!doctype html>", self.content.lower())
        self.assertRegex(self.content, r'<html\\s+lang="en">')
        self.assertIn("<meta charset=\"UTF-8\" />", self.content)
        self.assertIn(
            "<title>Cockroach Janata Party | Janata Ka Sankalp</title>",
            self.content,
        )

    def test_internal_links_point_to_existing_ids(self):
        missing_targets = sorted(
            target for target in self.parser.internal_links if target and target not in self.parser.ids
        )
        self.assertEqual(missing_targets, [])

    def test_expected_sections_are_present(self):
        expected_ids = {"home", "vision", "agenda", "movement", "roadmap", "join", "hero-title", "join-title"}
        self.assertTrue(expected_ids.issubset(self.parser.ids))

    def test_policy_content_counts(self):
        self.assertEqual(len(re.findall(r'<article class="metric">', self.content)), 4)
        self.assertEqual(len(re.findall(r'<article class="card">', self.content)), 10)
        self.assertEqual(len(re.findall(r'<article class="step">', self.content)), 4)
        self.assertEqual(len(re.findall(r'<figure class="shot">', self.content)), 3)

    def test_navigation_menu_links(self):
        self.assertIn('<nav class="menu" aria-label="Primary navigation">', self.content)
        for anchor in ["#vision", "#agenda", "#movement", "#roadmap", "#join"]:
            self.assertIn(f'href="{anchor}"', self.content)

    def test_images_have_alt_and_lazy_loading(self):
        self.assertGreaterEqual(len(self.parser.images), 4)
        for image in self.parser.images:
            self.assertTrue(image.get("alt", "").strip())
            self.assertEqual(image.get("loading"), "lazy")


if __name__ == "__main__":
    unittest.main()
