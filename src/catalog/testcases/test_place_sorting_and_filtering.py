from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from catalog.models import Category, Place

User = get_user_model()


class PlaceSortingAndFilteringTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin_tester",
            email="admin@example.com",
            password="admin-password",
        )
        self.client.force_login(self.admin_user)
        self.category_art, _ = Category.objects.get_or_create(code="ART", defaults={"name": "Art"})
        self.category_sport, _ = Category.objects.get_or_create(code="SPORT", defaults={"name": "Sport"})

        now = timezone.now()

        # Place 1: Created 100 days ago, updated yesterday
        self.place_old = Place.objects.create(
            name="Old Place",
            name_ru="Старое место",
            name_az="Köhnə məkan",
            category=self.category_art,
            created_by=self.admin_user,
        )
        Place.objects.filter(pk=self.place_old.pk).update(
            created_at=now - timedelta(days=100),
            updated_at=now - timedelta(days=1),
        )

        # Place 2: Created today, updated today
        self.place_new = Place.objects.create(
            name="New Place",
            name_ru="Новое место",
            name_az="Yeni məkan",
            category=self.category_sport,
            created_by=self.admin_user,
        )
        Place.objects.filter(pk=self.place_new.pk).update(
            created_at=now - timedelta(hours=2),
            updated_at=now - timedelta(hours=2),
        )

    def test_sorting_by_created_desc(self):
        url = reverse("admin:catalog_place_changelist")
        response = self.client.get(url, {"sort": "created_desc"})
        self.assertEqual(response.status_code, 200)
        places = list(response.context["cl"].result_list)
        self.assertEqual(places[0].pk, self.place_new.pk)
        self.assertEqual(places[1].pk, self.place_old.pk)
        self.assertContains(response, "Создано: новые")

    def test_sorting_by_created_asc(self):
        url = reverse("admin:catalog_place_changelist")
        response = self.client.get(url, {"sort": "created_asc"})
        self.assertEqual(response.status_code, 200)
        places = list(response.context["cl"].result_list)
        self.assertEqual(places[0].pk, self.place_old.pk)
        self.assertEqual(places[1].pk, self.place_new.pk)
        self.assertContains(response, "Создано: старые")

    def test_filtering_by_created_date_7d(self):
        url = reverse("admin:catalog_place_changelist")
        response = self.client.get(url, {"created_date": "7d"})
        self.assertEqual(response.status_code, 200)
        places = list(response.context["cl"].result_list)
        self.assertEqual(len(places), 1)
        self.assertEqual(places[0].pk, self.place_new.pk)

    def test_filtering_by_created_date_older_90d(self):
        url = reverse("admin:catalog_place_changelist")
        response = self.client.get(url, {"created_date": "older_90d"})
        self.assertEqual(response.status_code, 200)
        places = list(response.context["cl"].result_list)
        self.assertEqual(len(places), 1)
        self.assertEqual(places[0].pk, self.place_old.pk)

    def test_table_renders_created_date_and_category_link(self):
        url = reverse("admin:catalog_place_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "category__id__exact=")
        self.assertContains(response, "km-col-tag-link")
        self.assertContains(response, "km-col-upd-created")

    def test_sorting_by_name_asc(self):
        url = reverse("admin:catalog_place_changelist")
        response = self.client.get(url, {"sort": "name_asc"})
        self.assertEqual(response.status_code, 200)
        places = list(response.context["cl"].result_list)
        # "Новое место" vs "Старое место" (Н comes before С in Russian alphabet)
        self.assertEqual(places[0].pk, self.place_new.pk)
        self.assertEqual(places[1].pk, self.place_old.pk)
        self.assertContains(response, "По названию (А → Я)")
        self.assertContains(response, "km-col-sort-badge is-active")

    def test_sorting_by_name_desc(self):
        url = reverse("admin:catalog_place_changelist")
        response = self.client.get(url, {"sort": "name_desc"})
        self.assertEqual(response.status_code, 200)
        places = list(response.context["cl"].result_list)
        # "Старое место" vs "Новое место" (С comes after Н, so reversed С first)
        self.assertEqual(places[0].pk, self.place_old.pk)
        self.assertEqual(places[1].pk, self.place_new.pk)
        self.assertContains(response, "По названию (Я → А)")

    def test_sorting_by_updated_asc_and_desc(self):
        url = reverse("admin:catalog_place_changelist")
        # updated_asc: place_old (updated yesterday) before place_new (updated today)
        response_asc = self.client.get(url, {"sort": "updated_asc"})
        self.assertEqual(response_asc.status_code, 200)
        places_asc = list(response_asc.context["cl"].result_list)
        self.assertEqual(places_asc[0].pk, self.place_old.pk)
        self.assertEqual(places_asc[1].pk, self.place_new.pk)

        # updated_desc: place_new (updated today) before place_old (updated yesterday)
        response_desc = self.client.get(url, {"sort": "updated_desc"})
        self.assertEqual(response_desc.status_code, 200)
        places_desc = list(response_desc.context["cl"].result_list)
        self.assertEqual(places_desc[0].pk, self.place_new.pk)
        self.assertEqual(places_desc[1].pk, self.place_old.pk)

    def test_table_headers_render_clean_sort_links_without_broken_fa_icons(self):
        url = reverse("admin:catalog_place_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Toolbar sort button
        self.assertContains(response, "km-btn-sort")
        self.assertContains(response, "km-sort-dropdown")
        # Column headers
        self.assertContains(response, "km-th-sortable")
        self.assertContains(response, "km-th-sort-link")
        # Ensure broken Jazzmin glyph elements are not present
        self.assertNotContains(response, "fa fa-times")
        self.assertNotContains(response, "fa-sort-alpha-down")
        self.assertNotContains(response, "fa-sort-alpha-up")

