from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override

from catalog.domain_admin.place import PlaceAdmin, PlaceAdminForm
from catalog.forms import OwnerPlaceCreateForm, OwnerPlaceEditForm
from catalog.models import Place
from catalog.testcases.utils import create_quality_place


User = get_user_model()


class PlaceAdultClassesModelTests(TestCase):
    def test_existing_places_default_to_children_only(self):
        place = create_quality_place(name="Children only default")

        self.assertIs(place.offers_adult_classes, False)
        self.assertEqual(place.age_display, "6–12")

    def test_adult_classes_still_require_complete_child_age_range(self):
        place = Place(
            name="Invalid adult-only place",
            category_id="EDU",
            age_from=None,
            age_to=None,
            offers_adult_classes=True,
        )

        with self.assertRaises(ValidationError) as raised:
            place.full_clean()

        self.assertIn("offers_adult_classes", raised.exception.message_dict)

    def test_adult_classes_allowed_with_open_ended_child_age_range(self):
        place = Place(
            name="Valid open ended adult place",
            category_id="EDU",
            age_from=0,
            age_to=None,
            age_open_ended=True,
            offers_adult_classes=True,
        )
        place.full_clean()
        self.assertTrue(place.offers_adult_classes)

    def test_child_age_minimum_cannot_exceed_maximum(self):
        place = Place(
            name="Invalid child ages",
            category_id="EDU",
            age_from=12,
            age_to=6,
        )

        with self.assertRaises(ValidationError) as raised:
            place.full_clean()

        self.assertIn("age_to", raised.exception.message_dict)


class PlaceAdultClassesFormTests(TestCase):
    def setUp(self):
        self.place = create_quality_place(
            name="Family classes",
            name_az="Ailə dərsləri",
            age_from=6,
            age_to=17,
            offers_adult_classes=True,
        )

    def test_owner_edit_form_exposes_and_preserves_current_value(self):
        form = OwnerPlaceEditForm(instance=self.place)

        self.assertIn("offers_adult_classes", form.fields)
        self.assertEqual(form.initial["offers_adult_classes"], "1")
        self.assertFalse(form.fields["age_from"].required)
        self.assertFalse(form.fields["age_to"].required)

        create_form = OwnerPlaceCreateForm()
        self.assertTrue(create_form.fields["age_from"].required)
        self.assertTrue(create_form.fields["age_to"].required)

        moderation_form = OwnerPlaceEditForm(instance=self.place, submit_for_moderation=True)
        self.assertTrue(moderation_form.fields["age_from"].required)
        self.assertTrue(moderation_form.fields["age_to"].required)

    def test_admin_form_and_admin_configuration_include_field(self):
        form = PlaceAdminForm(instance=self.place)

        self.assertIn("offers_adult_classes", form.fields)
        self.assertTrue(form.initial["offers_adult_classes"])
        self.assertIn("offers_adult_classes", PlaceAdmin.AUDIT_TRACKED_FIELDS)
        self.assertIn("offers_adult_classes", PlaceAdmin.list_filter)

    def test_admin_change_page_renders_adult_classes_checkbox(self):
        admin_user = User.objects.create_superuser(
            username="adult_classes_admin",
            email="adult-classes-admin@example.com",
            password="StrongPass123!!",
        )
        self.client.force_login(admin_user)

        response = self.client.get(reverse("admin:catalog_place_change", args=[self.place.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="offers_adult_classes"', html=False)

    def test_owner_create_flow_renders_simple_audience_choices(self):
        user = User.objects.create_user(
            username="adult_classes_owner",
            email="adult-classes-owner@example.com",
            password="StrongPass123!!",
        )
        self.client.force_login(user)

        with override("ru"):
            response = self.client.get(reverse("owner_place_create"), {"type": "permanent"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="offers_adult_classes"', html=False)
        self.assertContains(response, 'value="0"', html=False)
        self.assertContains(response, "checked", html=False)
        self.assertContains(response, "Кто может заниматься?")
        self.assertContains(response, "Только дети")
        self.assertContains(response, "Дети и взрослые")

    def test_owner_form_rejects_adult_flag_without_child_range(self):
        form = OwnerPlaceEditForm(
            instance=self.place,
            data={
                "category": self.place.category_id,
                "age_from": "",
                "age_to": "",
                "offers_adult_classes": "1",
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("offers_adult_classes", form.errors)

    def test_owner_edit_form_saves_checked_and_unchecked_values(self):
        base_data = {
            "category": self.place.category_id,
            "age_from": "6",
            "age_to": "17",
        }
        checked_form = OwnerPlaceEditForm(
            instance=self.place,
            data={**base_data, "offers_adult_classes": "1"},
        )
        self.assertTrue(checked_form.is_valid(), checked_form.errors)
        checked_form.save()
        self.place.refresh_from_db()
        self.assertTrue(self.place.offers_adult_classes)

        unchecked_form = OwnerPlaceEditForm(
            instance=self.place,
            data={**base_data, "offers_adult_classes": "0"},
        )
        self.assertTrue(unchecked_form.is_valid(), unchecked_form.errors)
        unchecked_form.save()
        self.place.refresh_from_db()
        self.assertFalse(self.place.offers_adult_classes)

    def test_owner_form_rejects_unknown_audience_value(self):
        form = OwnerPlaceEditForm(
            instance=self.place,
            data={
                "category": self.place.category_id,
                "age_from": "6",
                "age_to": "17",
                "offers_adult_classes": "adults-only",
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("offers_adult_classes", form.errors)


class PlaceAdultClassesPublicTests(TestCase):
    def setUp(self):
        self.children_only = create_quality_place(
            name="Children Only Club",
            name_az="Yalnız uşaqlar üçün klub",
            name_ru="Только детский клуб",
            name_en="Children Only Club",
            age_from=6,
            age_to=17,
            offers_adult_classes=False,
        )
        self.family_place = create_quality_place(
            name="Family Club",
            name_az="Ailə klubu",
            name_ru="Семейный клуб",
            name_en="Family Club",
            age_from=6,
            age_to=17,
            offers_adult_classes=True,
        )

    def test_catalog_has_no_adult_filter_and_renders_compact_audience(self):
        with override("ru"):
            response = self.client.get(reverse("place_list"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="adult_classes"', html=False)
        self.assertContains(response, "Семейный клуб")
        self.assertContains(response, "Только детский клуб")
        self.assertContains(response, "6–17 лет")
        self.assertContains(response, "Взрослые группы")
        self.assertNotContains(response, "Для детей")

    def test_place_detail_renders_children_only_and_mixed_audience(self):
        with override("ru"):
            family_response = self.client.get(self.family_place.get_absolute_url())
            children_response = self.client.get(self.children_only.get_absolute_url())

        self.assertContains(family_response, "6–17 лет")
        self.assertContains(family_response, "Взрослые группы")
        self.assertNotContains(children_response, "Взрослые группы")
        self.assertNotContains(children_response, "Для детей")

    def test_owner_form_label_is_available_in_all_supported_languages(self):
        expected = {
            "az": "Kim məşğul ola bilər?",
            "ru": "Кто может заниматься?",
            "en": "Who can attend?",
        }

        for language, label in expected.items():
            with self.subTest(language=language), override(language):
                self.assertEqual(str(OwnerPlaceEditForm().fields["offers_adult_classes"].label), label)
