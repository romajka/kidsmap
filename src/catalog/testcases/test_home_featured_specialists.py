from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalog.controllers.home_controller import HomeController
from catalog.models import SiteSettings, Specialist


class HomeFeaturedSpecialistsTests(TestCase):
    """Specialists picked by hand in admin replace the automatic home block."""

    @classmethod
    def setUpTestData(cls):
        site = SiteSettings.get_solo()
        site.specialists_section_enabled = True
        site.save()

    def person(self, name, **fields):
        fields.setdefault("status", Specialist.STATUS_PUBLISHED)
        fields.setdefault("is_active", True)
        return Specialist.objects.create(name=name, **fields)

    def test_without_featured_people_the_automatic_teaser_stays(self):
        self.person("Auto One", photo="public/a.jpg")
        block = HomeController._specialists_block("ru")
        self.assertEqual(block["mode"], "teaser")

    def test_featured_people_follow_admin_order_and_skip_hidden_profiles(self):
        third = self.person("Third", is_home_featured=True, home_featured_order=3)
        first = self.person("First", is_home_featured=True, home_featured_order=1, photo="public/f.jpg")
        self.person("Draft", status=Specialist.STATUS_DRAFT, is_home_featured=True, home_featured_order=0)
        self.person("Inactive", is_active=False, is_home_featured=True, home_featured_order=0)
        self.person("Not picked", photo="public/n.jpg")

        block = HomeController._specialists_block("ru")

        self.assertEqual(block["mode"], "featured")
        self.assertEqual([p["name"] for p in block["people"]], [first.name, third.name])
        self.assertEqual(block["total"], 3)
        self.assertEqual(block["total_label"], "3 специалиста")
        self.assertEqual(block["people"][1]["initials"], "T")
        self.assertEqual(block["people"][1]["photo"], "")

    def test_card_facts_are_localized(self):
        self.person(
            "Aynur Mammadova", is_home_featured=True, experience_years=5, age_from=3, age_to=10,
            price_from=30, bio_ru="Работаю с детьми. " * 20,
        )
        ru = HomeController._specialists_block("ru")["people"][0]
        self.assertEqual(ru["experience"], "Стаж 5 лет")
        self.assertEqual(ru["ages"], "Возраст 3–10")
        self.assertLessEqual(len(ru["bio"]), 130)
        self.assertEqual(HomeController._specialists_block("az")["people"][0]["experience"], "5 il təcrübə")
        self.assertEqual(HomeController._specialists_block("en")["people"][0]["ages"], "Ages 3–10")

    def test_home_page_renders_large_cards_and_all_card(self):
        person = self.person("Leyla Aliyeva", is_home_featured=True, price_from=25)
        page = self.client.get("/ru/")
        self.assertContains(page, "data-spx")
        self.assertContains(page, person.get_absolute_url())
        self.assertContains(page, "от 25 ₼")
        self.assertContains(page, "home-spx-card--all")
        self.assertContains(page, "js/home_specialists.js")
        self.assertNotContains(page, "home-specialists--band")

    def test_filter_tabs_come_from_picked_people_and_whatsapp_is_offered(self):
        from catalog.models import SpecialistSpecialization

        speech = SpecialistSpecialization.objects.create(code="spx-speech", name_ru="Логопед")
        psych = SpecialistSpecialization.objects.create(code="spx-psych", name_ru="Психолог")
        first = self.person("One", is_home_featured=True, whatsapp="+994 50 123 45 67")
        first.specializations.add(speech)
        second = self.person("Two", is_home_featured=True)
        second.specializations.add(speech, psych)

        block = HomeController._specialists_block("ru")

        self.assertEqual([tab["code"] for tab in block["tabs"]], ["spx-speech", "spx-psych"])
        self.assertEqual(block["tabs"][0]["count"], 2)
        cards = {card["name"]: card for card in block["people"]}
        self.assertEqual(cards["One"]["whatsapp_url"], "https://wa.me/994501234567")
        self.assertEqual(cards["Two"]["whatsapp_url"], "")
        self.assertEqual(cards["Two"]["specialty_codes"], "spx-speech spx-psych")
        page = self.client.get("/ru/")
        self.assertContains(page, 'data-spx-tab="spx-psych"')
        self.assertContains(page, 'data-spx-codes="spx-speech spx-psych"')

    def test_one_specialty_shows_no_tabs(self):
        self.person("Solo", is_home_featured=True)
        self.assertEqual(HomeController._specialists_block("ru")["tabs"], [])

    def test_admin_actions_toggle_the_flag(self):
        admin_user = get_user_model().objects.create_superuser("featured-admin", "a@example.com", "pw-12345")
        self.client.force_login(admin_user)
        person = self.person("Toggle Me")
        url = reverse("admin:catalog_specialist_changelist")
        self.client.post(url, {"action": "feature_on_home", "_selected_action": [person.pk]})
        person.refresh_from_db()
        self.assertTrue(person.is_home_featured)
        self.client.post(url, {"action": "unfeature_on_home", "_selected_action": [person.pk]})
        person.refresh_from_db()
        self.assertFalse(person.is_home_featured)

    def test_admin_change_form_shows_the_home_controls(self):
        admin_user = get_user_model().objects.create_superuser("featured-admin2", "b@example.com", "pw-12345")
        self.client.force_login(admin_user)
        person = self.person("Form Person")
        page = self.client.get(reverse("admin:catalog_specialist_change", args=[person.pk]))
        self.assertContains(page, 'name="is_home_featured"')
        self.assertContains(page, 'name="home_featured_order"')
