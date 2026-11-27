import json
from datetime import datetime, timedelta
from decimal import Decimal
from urllib.parse import quote
from zoneinfo import ZoneInfo

from django.test import RequestFactory, SimpleTestCase, TestCase
from django.utils.html import format_html
from django.utils.translation import override

from catalog.models import Category, Event, Place, SiteSettings
from catalog.services.seo import build_event_seo_payload


class EventSearchRulesTests(SimpleTestCase):
    def setUp(self):
        self.start = datetime(2099, 11, 28, 18, tzinfo=ZoneInfo("Asia/Baku"))
        self.venue = {"label": "Puppet Theatre", "address": "Neftçilər 36", "district": "baku_sabail"}
        self.event = Event(
            slug="duymecik", name_az="Düyməcik", name_ru="Дюймовочка", name_en="Thumbelina",
            start_datetime=self.start, end_datetime=self.start + timedelta(minutes=50),
            price_mode="fixed", price_amount=Decimal("5.00"), price_currency="AZN",
            registration_method="link", registration_url="https://tickets.example/show",
            languages="ru", age_from=4, age_to=10,
        )

    def payload(self, language="ru", *, venue=None):
        with override(language):
            request = RequestFactory().get(self.event.get_absolute_url())
            result = build_event_seo_payload(self.event, request, language, public_context={
                "event_online": self.event.event_format == "online",
                "event_venue": self.venue if venue is None else venue,
                "event_reviews": [], "event_rating": {"count": 0},
            })
        return result, json.loads(result["event_schema_json"])

    def test_title_and_summary_distinguish_each_local_session_in_all_languages(self):
        for lang, name, city, month, spoken in (
            ("az", "Düyməcik", "Bakı", "noyabr", "rus dili"),
            ("ru", "Дюймовочка", "Баку", "ноября", "русский"),
            ("en", "Thumbelina", "Baku", "November", "Russian"),
        ):
            with self.subTest(lang=lang):
                result, schema = self.payload(lang)
                for token in (name, city, "28", "18:00"):
                    self.assertIn(token, result["seo_title"])
                for token in ("Puppet Theatre", "5 AZN", spoken, month):
                    self.assertIn(token, result["meta_description"])
                self.assertEqual(schema["location"]["address"]["addressCountry"], "AZ")
                self.assertEqual(schema["location"]["address"]["addressLocality"], city)
                self.assertEqual(schema["inLanguage"], ["ru"])
                self.assertEqual(schema["typicalAgeRange"], "4-10")
                offer = schema["offers"]
                self.assertEqual(offer["url"], "https://tickets.example/show")
                self.assertEqual(Decimal(str(offer["price"])), Decimal("5.00"))
                self.assertEqual(offer["priceCurrency"], "AZN")
                self.assertNotIn("availability", offer)

    def test_minimum_and_range_prices_keep_qualifiers_and_unknown_admission_has_no_offer(self):
        for mode in ("from", "range"):
            with self.subTest(mode=mode):
                self.event.price_mode = mode
                self.event.price_amount_max = Decimal("12") if mode == "range" else None
                _, schema = self.payload()
                self.assertIn("offers", schema)
                spec = schema["offers"]["priceSpecification"]
                self.assertEqual(Decimal(str(spec["minPrice"])), Decimal("5"))
                if mode == "range":
                    self.assertEqual(Decimal(str(spec["maxPrice"])), Decimal("12"))
                else:
                    self.assertNotIn("maxPrice", spec)
        self.event.price_mode = "free"
        _, schema = self.payload()
        self.assertIs(schema.get("isAccessibleForFree"), True)
        self.assertEqual(Decimal(str(schema["offers"]["price"])), 0)
        for mode in ("legacy", "unknown"):
            self.event.price_mode = mode
            self.event.price_text = "ask about tickets"
            _, schema = self.payload()
            self.assertNotIn("offers", schema)
            self.assertNotIn("isAccessibleForFree", schema)

    def test_online_and_unknown_or_non_baku_venues_do_not_inherit_baku(self):
        self.event.event_format = "online"
        result, schema = self.payload("en")
        self.assertIn("online", result["seo_title"].lower())
        self.assertNotIn("Baku", result["seo_title"])
        self.assertEqual(schema["location"], {"@type": "VirtualLocation"})
        self.event.event_format = "physical"
        result, schema = self.payload("en", venue={"label": "Baku Club", "address": "Baku Street"})
        self.assertNotIn("in Baku", result["seo_title"])
        self.assertNotIn("addressCountry", schema["location"]["address"])
        result, schema = self.payload("en", venue={"label": "Arts Hall", "district": "ganja"})
        self.assertIn("Ganja", result["seo_title"])
        self.assertNotIn("Baku", result["seo_title"])

    def test_known_city_in_legacy_address_supports_all_translations(self):
        for address in ("Баку город, Neftçilər prospekti 36", "Bakı, Zərifə Əliyeva küçəsi 8", "Baku city, Neftchilar Ave"):
            with self.subTest(address=address):
                result, schema = self.payload("en", venue={"address": address})
                self.assertIn("in Baku", result["seo_title"])
                self.assertEqual(schema["location"]["address"]["addressLocality"], "Baku")

    def test_reschedule_uses_current_date_and_keeps_original_status(self):
        self.event.occurrence_state = "rescheduled"
        result, schema = self.payload("az")
        self.assertIn("dəyiş", result["meta_description"].lower())
        self.assertEqual(schema["eventStatus"], "https://schema.org/EventRescheduled")
        self.assertNotIn("previousStartDate", schema)

    def test_only_the_public_registration_link_can_be_a_ticket_url(self):
        self.event.registration_method = "phone"
        self.event.phone = "+994501234567"
        _, schema = self.payload()
        self.assertNotIn("url", schema.get("offers", {}))
        self.event.registration_method = "link"
        self.event.registration_url = "https://staff:private@tickets.example/not-public"
        _, schema = self.payload()
        self.assertNotIn("url", schema.get("offers", {}))
        self.assertNotIn("private", str(schema))

    def test_cancelled_and_ended_pages_do_not_advertise_ticket_sales(self):
        self.event.occurrence_state = "cancelled"
        result, schema = self.payload()
        self.assertIn("отмен", result["meta_description"].lower())
        self.assertNotIn("offers", schema)
        self.event.occurrence_state = "scheduled"
        self.event.start_datetime = self.start.replace(year=2010)
        self.event.end_datetime = self.start.replace(year=2010, day=30)
        result, schema = self.payload("en")
        self.assertIn("ended", result["meta_description"].lower())
        for token in ("28", "30", "2010"):
            self.assertIn(token, result["meta_description"])
        self.assertNotIn("offers", schema)

    def test_bare_street_name_shared_with_a_baku_district_cannot_locate_an_event(self):
        for address in ("Nizami, 10", "Nizami, Main Street"):
            with self.subTest(address=address):
                result, schema = self.payload("en", venue={"address": address})
                self.assertNotIn("in Baku", result["seo_title"])
                self.assertNotIn("addressCountry", schema["location"]["address"])

    def test_overnight_session_has_both_clock_times_and_dates(self):
        self.event.start_datetime = self.start.replace(hour=23)
        self.event.end_datetime = self.event.start_datetime + timedelta(hours=3)
        result, _ = self.payload("ru")
        for value in ("28 ноября", "23:00", "29 ноября", "02:00"):
            self.assertIn(value, result["event_search_summary"])

    def test_same_name_date_and_time_remain_distinct_at_two_venues(self):
        first, _ = self.payload(venue=dict(self.venue, label="Первый театр"))
        second, _ = self.payload(venue=dict(self.venue, label="Второй театр"))
        self.assertIn("Первый театр", first["seo_title"])
        self.assertIn("Второй театр", second["seo_title"])
        self.assertNotEqual(first["seo_title"], second["seo_title"])

    def test_long_names_retain_date_and_time_across_showtimes(self):
        self.event.name_ru = "Дюймовочка и " + "очень длинное название " * 5
        first, _ = self.payload()
        self.event.start_datetime += timedelta(hours=1)
        self.event.end_datetime += timedelta(hours=1)
        second, _ = self.payload()
        self.assertIn("18:00", first["seo_title"])
        self.assertIn("19:00", second["seo_title"])
        self.assertTrue(second["seo_title"].startswith(self.event.name_ru.strip()))
        self.assertIn(self.event.name_ru.strip(), second["event_search_summary"])

    def test_full_production_and_venue_names_in_titles_in_every_language(self):
        self.event.name_ru = "«Девичья башня» Айдан Салаховой"
        self.event.name_az = "Aydan Salahovanın «Qız qalası» sərgisi"
        self.event.name_en = "Maiden Tower by Aidan Salakhova"
        names = {"ru": "Баку", "az": "Bakı", "en": "Baku"}
        venue = {"district": "baku_sabail", "label": "Azerbaijan National Museum of Art, Main Building and Exhibition Gallery"}
        for lang, city in names.items():
            with self.subTest(lang=lang):
                details, _ = self.payload(lang, venue=venue)
                title = details["seo_title"]
                self.assertTrue(title.startswith(self.event.name_i18n(lang)))
                for value in (venue["label"], city, "2099", "18:00"):
                    self.assertIn(value, title)
                self.assertNotIn("…", title)

    def test_russian_age_summary_handles_open_ranges_and_year_endings(self):
        for low, high, wording in (
            (3, None, "от 3 лет"), (1, None, "от 1 года"), (21, None, "от 21 года"),
            (11, None, "от 11 лет"), (0, None, "с рождения"),
            (None, 3, "до 3 лет"), (None, 1, "до 1 года"),
            (4, 10, "4–10 лет"), (1, 2, "1–2 года"), (3, 3, "3 года"),
        ):
            with self.subTest(low=low, high=high):
                self.event.age_from, self.event.age_to = low, high
                details, schema = self.payload("ru")
                self.assertIn("Возраст — " + wording + ".", details["event_search_summary"])
                self.assertNotIn("+ лет", details["event_search_summary"])
                self.assertEqual(schema["typicalAgeRange"], f"{low if low is not None else ''}-{high if high is not None else ''}")
        self.event.age_from, self.event.age_to = None, None
        details, schema = self.payload("ru")
        self.assertNotIn("Возраст", details["event_search_summary"])
        self.assertNotIn("typicalAgeRange", schema)


class RenderedEventSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        settings = SiteSettings.get_solo()
        settings.events_section_enabled = True
        settings.save()
        start = datetime(2099, 12, 31, 19, 30, tzinfo=ZoneInfo("Asia/Baku"))
        cls.event = Event.objects.create(
            status="published", category=Category.objects.create(code="science-event", name_az="Elm"),
            slug="science-lab", name_az="Elm gecəsi", name_ru="Ночь науки", name_en="Science Night",
            description_az="Elmi təcrübə.", description_ru="Научный опыт.", description_en="A science experiment.",
            start_datetime=start, end_datetime=start + timedelta(days=1, hours=2),
            venue_label="Science Hall", address="Bakı şəhəri, Nizami 10",
            price_mode="fixed", price_amount=Decimal("7"), price_currency="AZN", languages="tr",
            registration_method="link", registration_url="https://tickets.example/lab",
        )

    def test_visible_local_summary_matches_event_data_on_all_three_public_urls(self):
        for lang, name in (("az", "Elm gecəsi"), ("ru", "Ночь науки"), ("en", "Science Night")):
            with self.subTest(lang=lang), override(lang):
                response = self.client.get(self.event.get_absolute_url())
                self.assertEqual(response.status_code, 200)
                summary = response.context["event_search_summary"]
                schema = json.loads(response.context["event_schema_json"])
                self.assertContains(response, format_html(
                    '<p class="event-story__paragraph" data-event-search-summary lang="{}">{}</p>', lang, summary
                ), html=True)
                for token in (name, "2099", "2100", schema["location"]["name"], "7 AZN"):
                    self.assertIn(token, summary)
                self.assertIn(schema["location"]["name"], response.context["seo_title"])
                self.assertEqual(schema["inLanguage"], ["tr"])
                self.assertEqual(schema["offers"]["priceCurrency"], "AZN")
                self.assertEqual(schema["offers"]["url"], "https://tickets.example/lab")

    def detail_with_venue(self, status, snapshot):
        place = Place.objects.create(
            status=status, category_id=self.event.category_id, name="Kukla teatrı", name_az="Kukla teatrı",
            name_ru="Театр кукол", name_en="Puppet Theatre", address="Bakı şəhəri, Nizami 10",
            district="baku_sabail", is_active=True,
        )
        Event.objects.filter(pk=self.event.pk).update(
            related_place=place, venue_snapshot=snapshot, venue_label="Unpublished raw label",
            address="Unpublished raw address", district="ganja",
        )
        with override("ru"):
            response = self.client.get(self.event.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        return response, json.loads(response.context["event_schema_json"])

    def test_public_translation_for_the_same_venue_matches_visible_name_and_schema(self):
        snapshot = {"label": "Kukla teatrı", "address": "Bakı şəhəri, Nizami 10", "district": "baku_sabail"}
        response, schema = self.detail_with_venue("published", snapshot)
        visible = response.context["related_place_presentation"]["name"]
        self.assertEqual(visible, "Театр кукол")
        self.assertEqual(schema["location"]["name"], visible)
        self.assertIn(visible, response.context["seo_title"])
        self.assertIn(visible, response.context["event_search_summary"])
        self.assertEqual(schema["location"]["address"]["addressLocality"], "Баку")

    def test_empty_legacy_snapshot_uses_only_the_publicly_rendered_venue_name(self):
        response, schema = self.detail_with_venue("published", {})
        self.assertIn("Театр кукол", response.context["event_search_summary"])
        self.assertEqual(schema["location"], {"@type": "Place", "name": "Театр кукол"})
        self.assertNotIn("Баку", response.context["seo_title"])
        self.assertNotIn("Unpublished raw", response.context["event_search_summary"])

    def test_unpublished_linked_place_and_raw_fields_do_not_fill_an_empty_snapshot(self):
        response, schema = self.detail_with_venue("draft", {})
        self.assertIsNone(response.context["related_place_presentation"])
        self.assertNotIn("location", schema)
        self.assertNotIn("Театр кукол", response.context["event_search_summary"])
        self.assertNotIn("Unpublished raw", response.context["event_search_summary"])

    def test_different_venue_or_historical_address_retains_snapshot_identity(self):
        archived = self.event.start_datetime.replace(year=2020)
        Event.objects.filter(pk=self.event.pk).update(start_datetime=archived, end_datetime=archived + timedelta(hours=1))
        for label, address in (("Another theatre", "Bakı şəhəri, Nizami 10"), ("Kukla teatrı", "Gəncə, Street 4")):
            with self.subTest(label=label, address=address):
                response, schema = self.detail_with_venue("published", {"label": label, "address": address})
                self.assertEqual(schema["location"]["name"], label)
                self.assertIn(label, response.context["event_search_summary"])
                self.assertNotIn("Театр кукол", response.context["seo_title"])
                self.assertIsNone(response.context["related_place_presentation"])
                self.assertNotContains(response, "Театр кукол")
                self.assertContains(response, format_html("<strong>{}</strong>", label), html=True)
                self.assertContains(response, format_html("<h3>{}</h3>", label), html=True)
                street = schema["location"]["address"]["streetAddress"]
                self.assertContains(response, format_html('<span class="event-poster-address">{}</span>', street), html=True)
                self.assertContains(response, "maps/search/?api=1&amp;query=" + quote(street))
                self.assertNotContains(response, 'class="event-venue-link"')
