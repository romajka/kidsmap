from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalog.models import District, Place, Region, Specialist, SpecialistPracticeLocation

User = get_user_model()


class RegionAdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin_test",
            email="admin_test@kidsmap.az",
            password="password123",
        )
        self.client.force_login(self.admin)

        # Setup test regions
        self.reg_baku, _ = Region.objects.update_or_create(
            key="baku",
            defaults={"name_ru": "Баку", "name_az": "Bakı", "name_en": "Baku"},
        )
        self.reg_sumgait, _ = Region.objects.update_or_create(
            key="sumgait",
            defaults={"name_ru": "Сумгаит", "name_az": "Sumqayıt", "name_en": "Sumgait"},
        )
        self.reg_empty, _ = Region.objects.update_or_create(
            key="empty_region",
            defaults={"name_ru": "Пустой Регион", "name_az": "Boş Region", "name_en": "Empty Region"},
        )

        # Create districts for Baku
        self.dist_nasimi, _ = District.objects.update_or_create(
            key="baku_nasimi",
            defaults={
                "region": self.reg_baku,
                "name_ru": "Насиминский",
                "name_az": "Nəsimi",
                "name_en": "Nasimi",
            },
        )
        self.dist_yasamal, _ = District.objects.update_or_create(
            key="baku_yasamal",
            defaults={
                "region": self.reg_baku,
                "name_ru": "Ясамальский",
                "name_az": "Yasamal",
                "name_en": "Yasamal",
            },
        )

        # Category
        from catalog.models import Category
        self.cat, _ = Category.objects.get_or_create(
            code="test_cat",
            defaults={"name_ru": "Категория", "name_az": "Kateqoriya", "name_en": "Category", "is_active": True},
        )

        # Create places in regions
        self.place_baku = Place.objects.create(
            name="Детский центр в Баку",
            name_ru="Детский центр в Баку",
            district="baku_nasimi",
            category=self.cat,
            is_temporary=False,
            is_active=True,
        )
        self.place_sumgait = Place.objects.create(
            name="Клуб в Сумгаите",
            name_ru="Клуб в Сумгаите",
            district="sumgait",
            category=self.cat,
            is_temporary=False,
            is_active=True,
        )

        # Create event in Baku
        self.event_baku = Place.objects.create(
            name="Фестиваль в Баку",
            name_ru="Фестиваль в Баку",
            district="baku",
            category=self.cat,
            is_temporary=True,
            is_active=True,
        )

    def test_changelist_view_renders_successfully(self):
        url = reverse("admin:catalog_region_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Check that dashboard metrics and quick filters are in context
        self.assertIn("region_dashboard_stats", response.context)
        self.assertIn("km_primary_quick_filters", response.context)
        self.assertIn("region_bulk_actions", response.context)

        # Check KPI cards
        stats = {item["label"]: item["count"] for item in response.context["region_dashboard_stats"]}
        self.assertIn("Всего регионов", stats)
        self.assertEqual(stats["Всего регионов"], Region.objects.count())
        self.assertEqual(stats["Районов городов"], District.objects.count())

    def test_quick_filter_with_objects(self):
        url = reverse("admin:catalog_region_changelist")
        response = self.client.get(url, {"content_status": "with_objects"})
        self.assertEqual(response.status_code, 200)
        results = list(response.context["cl"].queryset)
        keys = [r.key for r in results]
        self.assertIn("baku", keys)
        self.assertIn("sumgait", keys)
        self.assertNotIn("empty_region", keys)

    def test_quick_filter_with_districts(self):
        url = reverse("admin:catalog_region_changelist")
        response = self.client.get(url, {"content_status": "with_districts"})
        self.assertEqual(response.status_code, 200)
        results = list(response.context["cl"].queryset)
        keys = [r.key for r in results]
        self.assertIn("baku", keys)
        self.assertNotIn("sumgait", keys)
        self.assertNotIn("empty_region", keys)

    def test_quick_filter_empty(self):
        url = reverse("admin:catalog_region_changelist")
        response = self.client.get(url, {"content_status": "empty"})
        self.assertEqual(response.status_code, 200)
        results = list(response.context["cl"].queryset)
        keys = [r.key for r in results]
        self.assertNotIn("baku", keys)
        self.assertNotIn("sumgait", keys)
        self.assertIn("empty_region", keys)

    def test_search_cyrillic_case_insensitive(self):
        url = reverse("admin:catalog_region_changelist")
        # Search lower-case cyrillic "баку"
        response_lower = self.client.get(url, {"q": "баку"})
        self.assertEqual(response_lower.status_code, 200)
        keys = [r.key for r in response_lower.context["cl"].queryset]
        self.assertEqual(keys, ["baku"])

        # Search capitalized cyrillic "Баку"
        response_cap = self.client.get(url, {"q": "Баку"})
        self.assertEqual(response_cap.status_code, 200)
        keys_cap = [r.key for r in response_cap.context["cl"].queryset]
        self.assertEqual(keys_cap, ["baku"])

    def test_search_by_az_and_en_and_key(self):
        url = reverse("admin:catalog_region_changelist")
        # Search AZ
        response = self.client.get(url, {"q": "Sumqayıt"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([r.key for r in response.context["cl"].queryset], ["sumgait"])

        # Search EN
        response = self.client.get(url, {"q": "Sumgait"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([r.key for r in response.context["cl"].queryset], ["sumgait"])

        # Search Key
        response = self.client.get(url, {"q": "sumgait"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([r.key for r in response.context["cl"].queryset], ["sumgait"])

    def test_change_form_renders_hero_and_inlines(self):
        url = reverse("admin:catalog_region_change", args=[self.reg_baku.key])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Region summary in context
        self.assertIn("km_region_summary", response.context)
        summary = response.context["km_region_summary"]
        self.assertEqual(summary["key"], "baku")
        self.assertEqual(summary["districts_count"], self.reg_baku.districts.count())
        self.assertEqual(summary["places_count"], 1)
        self.assertEqual(summary["events_count"], 1)

        # Readonly fields include key on edit
        admin_form = response.context["adminform"]
        self.assertIn("key", admin_form.readonly_fields)

        # Inlines include DistrictInline
        inline_formsets = response.context["inline_admin_formsets"]
        self.assertEqual(len(inline_formsets), 1)
        self.assertEqual(inline_formsets[0].opts.model, District)

    def test_add_form_key_is_editable(self):
        url = reverse("admin:catalog_region_add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        admin_form = response.context["adminform"]
        self.assertNotIn("key", admin_form.readonly_fields)

    def test_metrics_refresh_after_district_added_between_requests(self):
        url = reverse("admin:catalog_region_change", args=[self.reg_baku.key])
        before = self.client.get(url).context["km_region_summary"]["districts_count"]
        District.objects.create(
            key="release_added", region=self.reg_baku,
            name_ru="Новый район", name_az="Yeni rayon", name_en="New district",
        )
        after = self.client.get(url).context["km_region_summary"]["districts_count"]
        self.assertEqual(after, before + 1)

    def test_search_preserves_content_filter(self):
        response = self.client.get(
            reverse("admin:catalog_region_changelist"),
            {"content_status": "empty", "q": "baku"},
        )
        self.assertEqual(list(response.context["cl"].queryset), [])
