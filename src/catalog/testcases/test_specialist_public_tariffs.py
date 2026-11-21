from decimal import Decimal

from django.test import TestCase
from django.utils.translation import override

from catalog.controllers.home_controller import HomeController
from catalog.models import SiteSettings, Specialist, SpecialistPracticeLocation
from catalog.services.specialist_presentation import public_profile_context


class SpecialistPublicTariffTests(TestCase):
    def setUp(self):
        site = SiteSettings.get_solo()
        site.specialists_section_enabled = True
        site.save()

    def profile(self, name, **fields):
        return Specialist.objects.create(
            name=name, status=Specialist.STATUS_PUBLISHED, is_active=True, **fields,
        )

    def test_detail_shows_base_monthly_and_package_price_per_lesson_in_all_locales(self):
        person = self.profile(
            "Lesson tariffs", lesson_type="group", lesson_price=Decimal("32.50"),
            pricing_packages=[
                {"period": "month", "amount": "100.00", "sessions": 8},
                {"period": "package", "amount": "2.01", "sessions": 2},
            ],
        )
        for lang, month, package, lesson_type in [
            ("ru", "Месячный абонемент", "Пакет занятий", "Групповое занятие"),
            ("az", "Aylıq abunəlik", "Dərs paketi", "Qrup dərsi"),
            ("en", "Monthly subscription", "Lesson package", "Group lesson"),
        ]:
            with self.subTest(language=lang), override(lang):
                page = self.client.get(person.get_absolute_url())
                self.assertEqual(page.status_code, 200)
                self.assertContains(page, month)
                self.assertContains(page, package)
                for value in ("32.50", "12.50", "1.01", "100"):
                    localized = value if lang == "en" else value.replace(".", ",")
                    self.assertContains(page, f"{localized} ₼")
                self.assertNotContains(page, 'data-fact="duration"')
                self.assertContains(page, f'<span data-fact="lesson-type">{lesson_type}</span>', html=True)

    def test_catalog_matches_only_independently_bookable_prices_and_sorts_them(self):
        base = self.profile("New pricing", lesson_type="group", lesson_price=Decimal("32.50"),
                            price_from=2, price_to=999,
                            pricing_packages=[{"period": "month", "amount": "200", "sessions": 8}])
        middle = self.profile("Legacy pricing", price_from=27, price_to=27)
        free = self.profile("New free lesson", lesson_type="individual", lesson_price=Decimal("0"))
        self.profile("Unknown price")
        path = "/ru/specialists/"
        def result(**query):
            response = self.client.get(path, query)
            self.assertEqual(response.status_code, 200)
            return response.context

        self.assertEqual(result()["specialist_price_max"], 33)
        self.assertEqual([x.pk for x in result(price_from=24, price_to=25)["specialists"]], [])
        self.assertEqual([x.pk for x in result(price_from=32, price_to=33)["specialists"]], [base.pk])
        self.assertEqual([x.pk for x in result(price_to=0)["specialists"]], [free.pk])
        self.assertEqual([x.pk for x in result(sort="price_asc")["specialists"]][:3],
                         [free.pk, middle.pk, base.pk])
        active = SpecialistPracticeLocation.objects.create(
            specialist=base, address="Synthetic branch", price_per_session=20, is_active=True,
        )
        self.assertEqual([x.pk for x in result(price_to=20, price_from=20)["specialists"]], [base.pk])
        self.assertEqual([x.pk for x in result(sort="price_asc")["specialists"]][:3],
                         [free.pk, base.pk, middle.pk])
        sorted_card = next(x for x in result(sort="price_asc")["specialists"] if x.pk == base.pk)
        self.assertIn("20 ₼", sorted_card.card_price)
        filtered = result(price_from=25, sort="price_asc")["specialists"]
        self.assertEqual([x.pk for x in filtered], [middle.pk, base.pk])
        self.assertIn("32,50 ₼", list(filtered)[1].card_price)
        active.is_active = False
        active.save()
        self.assertEqual([x.pk for x in result(sort="price_desc")["specialists"]][:3],
                         [base.pk, middle.pk, free.pk])

    def test_zero_price_is_visible_and_public_home_card_uses_the_base_price(self):
        person = self.profile("Free profile", lesson_type="pair", lesson_price=Decimal("0"),
                              price_from=60, photo="synthetic-profile.jpg")
        with override("ru"):
            self.assertEqual(public_profile_context(person)["specialist_public"]["price_label"], "Бесплатно")
            people = HomeController._specialists_block("ru")["people"]
            self.assertEqual(people[0]["price_label"], "Бесплатно")


class SpecialistPricingCardTests(TestCase):
    """The public pricing card: single lesson first, then plans with savings."""

    def setUp(self):
        site = SiteSettings.get_solo()
        site.specialists_section_enabled = True
        site.save()

    def test_card_lists_single_lesson_and_plan_savings(self):
        person = Specialist.objects.create(
            name="Pricing card", status=Specialist.STATUS_PUBLISHED, is_active=True,
            lesson_type="individual", lesson_price=Decimal("30"), duration_minutes=45,
            pricing_packages=[
                {"period": "month", "amount": "200", "sessions": 8},
                {"period": "package", "amount": "140", "sessions": 4},
                {"period": "package", "amount": "28", "sessions": 1},
            ],
        )
        with override("ru"):
            page = self.client.get(person.get_absolute_url())
        self.assertContains(page, "Стоимость занятий")
        self.assertContains(page, "Разовое занятие")
        self.assertContains(page, "Индивидуальное занятие · 45 мин")
        self.assertContains(page, "Месячный абонемент")
        self.assertContains(page, "8 занятий в месяц")
        # 25 ₼ against 30 ₼ is a 16.67% discount, rounded to the nearest percent.
        self.assertContains(page, "выгода 17%", count=1)
        self.assertContains(page, "выгода 7%", count=1)
        # A pricier package gets no badge.
        self.assertContains(page, "35 ₼ за занятие")
        self.assertNotContains(page, "выгода -")
        # A one-lesson package does not repeat its total as a per-lesson price.
        self.assertNotContains(page, "28 ₼ за занятие")

    def test_card_shows_single_lesson_without_plans_and_free_lesson(self):
        person = Specialist.objects.create(
            name="Free card", status=Specialist.STATUS_PUBLISHED, is_active=True,
            lesson_type="consultation", lesson_price=Decimal("0"),
            pricing_packages=[{"period": "package", "amount": "50", "sessions": 5}],
        )
        with override("en"):
            page = self.client.get(person.get_absolute_url())
        self.assertContains(page, "Lesson prices")
        self.assertContains(page, "is-free")
        self.assertContains(page, "10 ₼ per lesson")
        self.assertNotContains(page, "sp-tariff__saving")

    def test_card_is_hidden_without_new_prices(self):
        person = Specialist.objects.create(
            name="Legacy card", status=Specialist.STATUS_PUBLISHED, is_active=True, price_from=20,
        )
        with override("ru"):
            page = self.client.get(person.get_absolute_url())
        self.assertNotContains(page, 'id="specialist-pricing"')
