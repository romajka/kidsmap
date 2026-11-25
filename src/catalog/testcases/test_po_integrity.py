import re
import unicodedata
from collections import Counter
from string import Formatter

import polib
from django.conf import settings
from django.test import SimpleTestCase
from django.utils.translation import gettext, override


# Only complete proper names may stay in Cyrillic. Neither catalog needs one today.
CYRILLIC_PROPER_NAMES = frozenset()

PERCENT_FIELDS = re.compile(r"%%|%(?:\([^)]+\))?[-+#0]*(?:\d+|\*)?(?:\.(?:\d+|\*))?[diouxXeEfFgGcrsa]")


def placeholders(text):
    fields = Counter(token for token in PERCENT_FIELDS.findall(text) if token != "%%")
    for _, field, spec, conversion in Formatter().parse(text):
        if field is not None:
            fields[(field, spec, conversion)] += 1
    # Historical template messages also contain Django variables such as {{ counter }}.
    fields.update(re.findall(r"\{\{\s*\w+\s*\}\}", text))
    return fields


class PoIntegrityTests(SimpleTestCase):
    def test_all_az_en_entries_preserve_content_and_placeholders(self):
        for language in ("az", "en"):
            catalog = polib.pofile(settings.BASE_DIR / "locale" / language / "LC_MESSAGES" / "django.po")
            for entry in catalog:
                if entry.msgid_plural:
                    with self.subTest(language=language, msgid=entry.msgid):
                        self.assertEqual(set(entry.msgstr_plural), {0, 1})
                    forms = entry.msgstr_plural.items()
                else:
                    forms = [(0, entry.msgstr)]
                for index, text in forms:
                    with self.subTest(language=language, msgid=entry.msgid, form=index):
                        self.assertTrue(text.strip(), "Empty translation")
                        source = entry.msgid_plural if index else entry.msgid
                        self.assertEqual(placeholders(text), placeholders(source))
                        cyrillic = {
                            word for word in re.findall(r"\w+|\W", text)
                            if any("CYRILLIC" in unicodedata.name(char, "") for char in word)
                        }
                        self.assertFalse(cyrillic - CYRILLIC_PROPER_NAMES, cyrillic)

    def test_placeholder_counts_include_anonymous_fields_and_ignore_literal_percents(self):
        self.assertEqual(
            placeholders("%s, %s, %%(ignored)s, %(lat).6f, {}, {count}, {{ total }}"),
            Counter({"%s": 2, "%(lat).6f": 1, ("", "", None): 1, ("count", "", None): 1, "{{ total }}": 1}),
        )

    def test_category_example_unlink_confirmation_and_sla_heading(self):
        for source, az, en in (
            ("Например: Образование", "Məsələn: Təhsil", "For example: Education"),
            ("Отсоединение подтверждено", "Əlaqənin kəsilməsi təsdiqləndi", "Unlinking confirmed"),
            ("Контроль регламентных сроков рассмотрения (Service Level Agreement)",
             "Xidmət səviyyəsi sazişində (SLA) müəyyən edilmiş baxılma müddətlərinə nəzarət",
             "Monitoring review deadlines under the service level agreement (SLA)"),
        ):
            for language, expected in (("az", az), ("en", en)):
                with self.subTest(language=language, source=source), override(language):
                    self.assertEqual(gettext(source), expected)
