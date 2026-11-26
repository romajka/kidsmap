from pathlib import Path

from django.contrib.staticfiles import finders
from django.test import SimpleTestCase


class PublicScriptDeliveryTests(SimpleTestCase):
    def test_development_and_collectstatic_resolve_the_same_bundles(self):
        for name, markers in {
            "js/public_shell.js": (b"kidsMapEmitAnalyticsEvent", b"IntersectionObserver"),
            "js/map_tools.js": (b"KidsMapPaging", b"KidsMap"),
        }.items():
            with self.subTest(name=name):
                path = finders.find(name)
                self.assertIsNotNone(path)
                source = Path(path).read_bytes()
                for marker in markers:
                    self.assertIn(marker, source)
                copies = []
                for finder in finders.get_finders():
                    for relative, storage in finder.list([]):
                        if relative == name:
                            with storage.open(name) as item:
                                copies.append(item.read())
                self.assertEqual(copies, [source])
