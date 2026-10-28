"""Public age bounds and parent notes must retain their meaning and credits."""
from datetime import timedelta
from types import SimpleNamespace

from django.template import Context, Template
from django.template.loader import render_to_string
from django.test import SimpleTestCase
from django.utils import timezone
from django.utils.translation import override

from catalog.models import Place, PricingPlan
from catalog.services.public_presentation import activity_groups, price_rows, schema_offers
from catalog.templatetags.catalog_i18n import clean_public_note


class PublicAgeNotesTests(SimpleTestCase):
    def test_upper_only_age_remains_an_upper_bound_in_each_language(self):
        for lang, expected in (("ru", "до 7"), ("az", "ən çox 7"), ("en", "up to 7")):
            with self.subTest(lang=lang), override(lang):
                self.assertEqual(Place(age_from=None, age_to=7).age_display, expected)

    def test_other_age_bounds_keep_zero_and_open_ended_meaning(self):
        for low, high, expected in ((0, 7, "0–7"), (5, None, "5+"), (None, None, "")):
            with self.subTest(low=low, high=high):
                self.assertEqual(Place(age_from=low, age_to=high).age_display, expected)

    def test_option_and_group_age_bounds_use_the_same_localized_label(self):
        for lang, low, high, expected in (("ru", 5, None, "5+"), ("en", None, 7, "up to 7"), ("az", 0, 7, "0–7")):
            with self.subTest(lang=lang), override(lang):
                html = Template("{% load catalog_i18n %}{% age_range low high %}").render(Context({"low": low, "high": high}))
                self.assertEqual(html, expected)
                group = SimpleNamespace(pk=1, age_from=low, age_to=high, name_az="Group", conditions_az="", language="", schedule_text="", teachers_text="", _public_plans=[])
                self.assertEqual(activity_groups(SimpleNamespace(_public_groups=[group]), lang)[0]["age"], expected)

    def test_parent_note_excludes_credits_and_internal_markers(self):
        text = "Запишитесь заранее.\nФото: Alice / CC BY 4.0 https://creativecommons.org/licenses/by/4.0/\nseed:internal\nПроверено по источнику."
        self.assertEqual(clean_public_note(text), "Запишитесь заранее.")

    def test_photo_credits_are_preserved_separately_with_safe_links(self):
        with override("ru"):
            place = Place(additional_info_ru="Приходите за 10 минут.\nФото: Alice <script>bad</script> https://commons.wikimedia.org/wiki/File:Park.jpg\nЛицензия: CC BY 4.0 https://creativecommons.org/licenses/by/4.0/")
            html = render_to_string("catalog/includes/pricing_notes.html", {"place": place, "pricing_summary": {}})
        self.assertIn('class="detail-photo-credits"', html)
        useful, credits = html.split('class="detail-photo-credits"', 1)
        self.assertIn("Приходите за 10 минут.", useful)
        self.assertNotIn("Alice", useful)
        self.assertIn("Alice", credits)
        self.assertIn("CC BY 4.0", credits)
        self.assertIn('href="https://commons.wikimedia.org/wiki/File:Park.jpg"', credits)
        self.assertIn("&lt;script&gt;", credits)
        self.assertNotIn("<script>", html)

    def test_parent_rules_about_photos_are_not_treated_as_credits(self):
        self.assertEqual(clean_public_note("Фотосъёмка разрешена без вспышки.\nФото на документы делают у входа."), "Фотосъёмка разрешена без вспышки.\nФото на документы делают у входа.")

    def test_real_multiline_archive_credits_stay_out_of_parent_conditions(self):
        text = "По вопросам посещения: info@example.invalid.\nАрхивные фото, 2013–2014: Samral, Urmen19; ретушь: Sefer azeri. Источник: https://commons.wikimedia.org/wiki/Category:Baku_Puppet_Theatre\nCC BY-SA 4.0: https://creativecommons.org/licenses/by-sa/4.0/\nФото спектакля и кукол: Tapdiq Abdullayev / PhotoStock.az, 2026."
        self.assertEqual(clean_public_note(text), "По вопросам посещения: info@example.invalid.")
        with override("ru"):
            html = render_to_string("catalog/includes/pricing_notes.html", {"place": Place(additional_info_ru=text), "pricing_summary": {}})
        credits = html.split('class="detail-photo-credits"', 1)[1]
        for text in ("Samral", "Urmen19", "Sefer azeri", "CC BY-SA 4.0", "Tapdiq Abdullayev", "PhotoStock.az"):
            self.assertIn(text, credits)

    def test_missing_note_translation_does_not_drop_photo_attribution(self):
        place = Place(additional_info_ru="Запись заранее.\nФото: Alice, CC BY-SA 4.0")
        with override("en"):
            html = render_to_string("catalog/includes/pricing_notes.html", {"place": place, "pricing_summary": {}})
        self.assertIn("Alice, CC BY-SA 4.0", html)
        self.assertNotIn("Запись заранее", html)

    def test_translated_archival_credits_are_separated_in_all_locales(self):
        for line in ("Archive photos, 2013–2014: Alice.", "Arxiv fotoşəkillər, 2013–2014: Alice.", "Photos of the show: Alice."):
            with self.subTest(line=line):
                self.assertEqual(clean_public_note("Book ahead.\n" + line), "Book ahead.")


class CurrentPublicTariffTests(SimpleTestCase):
    def setUp(self):
        today = timezone.localdate()
        self.plans = [
            PricingPlan(pk=1, price=5, price_kind="exact", title_az="Expired", valid_until=today-timedelta(days=1)),
            PricingPlan(pk=2, price=20, price_kind="exact", title_az="Future", valid_from=today+timedelta(days=1)),
            PricingPlan(pk=3, price=10, price_kind="exact", title_az="Current", valid_from=today, valid_until=today),
        ]

    def test_activity_prices_ignore_noncurrent_cached_tariffs(self):
        rows = price_rows(SimpleNamespace(_public_plans=self.plans), "en")
        self.assertEqual([row["id"] for row in rows], [3])

    def test_schema_ignores_noncurrent_cached_tariffs(self):
        place = Place(price_mode="tariffs")
        place._pricing_records_cache = self.plans
        offer = schema_offers(place, "en")
        self.assertIsInstance(offer, dict)
        self.assertEqual(offer["price"], "10.00")
