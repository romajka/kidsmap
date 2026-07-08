from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalog.models import Category, Subcategory


class PlaceAdminTaxonomyPickerTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="taxonomy_admin",
            email="taxonomy-admin@example.com",
            password="password",
        )
        self.client.force_login(self.admin_user)

    def test_place_add_form_exposes_taxonomy_picker_config(self):
        category = Category.objects.create(
            code="TAXUX",
            name="Taxonomy UX",
            name_ru="Категория UX",
            icon="icons/categories/beach.svg",
            color_bg="#CCFBF1",
            color_text="#0F766E",
            order=1,
        )
        Subcategory.objects.create(
            category=category,
            code="taxux-subcategory",
            name="Subcategory UX",
            name_ru="Подкатегория UX",
            order=1,
        )

        response = self.client.get(reverse("admin:catalog_place_add"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "km-place-taxonomy-config")
        self.assertContains(response, "admin/css/pages/kidsmap_place_form.css")
        self.assertContains(response, "admin/js/kidsmap_place_form.js")
        config = response.context["km_place_taxonomy_picker"]
        category_config = next(item for item in config["categories"] if item["code"] == "TAXUX")
        self.assertEqual(category_config["label"], "Категория UX")
        self.assertEqual(category_config["color_bg"], "#CCFBF1")
        self.assertEqual(category_config["color_text"], "#0F766E")
        self.assertEqual(category_config["subcategory_count"], 1)
        self.assertIn(
            {"id": str(category.subcategories.get().pk), "category": "TAXUX", "label": "Подкатегория UX"},
            config["subcategories"],
        )
