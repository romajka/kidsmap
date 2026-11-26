from django.test import TestCase
from django.test.html import Element, parse_html
from django.urls import reverse
from django.utils.translation import override

from catalog.models import SiteSettings, Specialist
from catalog.testcases.utils import create_quality_place


def walk(node, wrapping_label=None):
    yield node, wrapping_label
    if node.name == "label" and "for" not in dict(node.attributes):
        wrapping_label = node
    for child in node.children:
        if isinstance(child, Element):
            yield from walk(child, wrapping_label)


def label_text(node):
    if isinstance(node, str):
        return node
    # Text from the control itself (e.g. its options) is not its label.
    if node.name in {"input", "select", "textarea"} or dict(node.attributes).get("aria-hidden") == "true":
        return ""
    return " ".join(label_text(child) for child in node.children).strip()


def unnamed_fields(nodes):
    by_id = {}
    labels = {}
    for node, _ in nodes:
        attrs = dict(node.attributes)
        if attrs.get("id"):
            by_id[attrs["id"]] = node
        if node.name == "label" and attrs.get("for"):
            labels[attrs["for"]] = label_text(node)

    for field, wrapping_label in nodes:
        attrs = dict(field.attributes)
        if field.name not in {"input", "select", "textarea"} or attrs.get("type") == "hidden":
            continue
        # Include the native selects behind the custom filters as well.
        refs = [by_id[key] for key in attrs.get("aria-labelledby", "").split() if key in by_id]
        if refs:
            if not any(label_text(ref) for ref in refs):
                yield (field.name, attrs.get("name"), attrs.get("id"))
            continue
        if attrs.get("aria-label", "").strip() or labels.get(attrs.get("id")):
            continue
        if wrapping_label is None or not label_text(wrapping_label):
            yield (field.name, attrs.get("name"), attrs.get("id"))


class PublicAccessibilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        settings = SiteSettings.get_solo()
        settings.events_section_enabled = True
        settings.save()
        create_quality_place(with_pricing_plan=True)
        Specialist.objects.create(name="Synthetic tutor", status="published", is_active=True, lesson_price=35)

    def assert_skip_link(self, nodes, text):
        body = next(node for node, _ in nodes if node.name == "body")
        first = next(child for child in body.children if isinstance(child, Element))
        links = [node for node, _ in nodes if "skip-link" in dict(node.attributes).get("class", "").split()]
        self.assertEqual(len(links), 1)
        self.assertIs(first, links[0])
        self.assertEqual((first.name, dict(first.attributes).get("href"), label_text(first)), ("a", "#main", text))

        mains = [node for node, _ in nodes if node.name == "main"]
        targets = [node for node, _ in nodes if dict(node.attributes).get("id") == "main"]
        self.assertEqual(len(mains), 1)
        self.assertEqual(targets, mains)
        self.assertEqual(dict(mains[0].attributes).get("tabindex"), "-1")

    def test_skip_link_and_field_names_in_each_language(self):
        routes = ("home", "place_list", "events_landing", "specialist_list", "place_new", "organization_list")
        languages = (("az", "Əsas məzmuna keç"), ("ru", "Перейти к содержанию"), ("en", "Skip to main content"))
        for language, link_text in languages:
            for route in routes:
                with override(language):
                    path = reverse(route)
                with self.subTest(path=path):
                    response = self.client.get(path)
                    self.assertEqual(response.status_code, 200)
                    # Django's parse_html uses html.parser.HTMLParser to build this tree.
                    nodes = list(walk(parse_html(response.content.decode())))
                    with self.subTest(check="fields"):
                        self.assertEqual(list(unnamed_fields(nodes)), [])
                    self.assert_skip_link(nodes, link_text)
