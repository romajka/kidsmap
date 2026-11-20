from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from catalog.interfaces.geocoding import GeocodingPoint
from catalog.models import Category, Place, VolunteerPlaceRevision


@override_settings(GOOGLE_MAPS_API_KEY="local-test")
class PlaceAdminGeocodingRevisionTests(TestCase):
    old_point = (40.409264, 49.867092)
    new_point = (40.366667, 49.833333)
    new_address = "ичери шяхяр"

    @classmethod
    def setUpTestData(cls):
        cls.editor = get_user_model().objects.create_superuser("coordinate-editor", password=None)
        cls.category, _ = Category.objects.get_or_create(code="EDU", defaults={"name": "QA"})

    def setUp(self):
        self.client.force_login(self.editor)

    def place(self, published=False):
        return Place.objects.create(name="QA old place", name_az="QA old place", category=self.category,
                                    address="Нариманов", lat=self.old_point[0], lng=self.old_point[1],
                                    status="published" if published else "draft", is_active=published)

    def form_data(self, url, **values):
        page = self.client.get(url)
        form = page.context["adminform"].form
        data = {"name_az": "QA Geo", "category": self.category.pk, "status": "draft",
                "address": self.new_address, "region": "baku", "district": "baku_narimanov",
                "publication_token": form.initial["publication_token"], **values}
        for inline in page.context["inline_admin_formsets"]:
            for field in inline.formset.management_form:
                if field.value() is not None:
                    data[field.html_name] = field.value()
        return data

    def post(self, url, data):
        response = self.client.post(url, data)
        errors = response.context["adminform"].form.errors if response.context else None
        self.assertEqual(response.status_code, 302, errors)

    def reopened_point(self, place):
        url = reverse("admin:catalog_place_change", args=[place.pk])
        form = self.client.get(url).context["adminform"].form
        self.assertEqual(form["address"].value(), self.new_address)
        return form["lat"].value(), form["lng"].value(), form["district"].value()

    def check_recalculation(self, place=None):
        url = (reverse("admin:catalog_place_change", args=[place.pk]) if place else
               reverse("admin:catalog_place_add") + "?type=permanent")
        fields = dict(zip(("lat", "lng"), self.old_point)) if place else {}
        data = self.form_data(url, **fields, _refresh_coordinates_from_address="1")
        point = GeocodingPoint(*self.new_point)
        with patch("catalog.repositories.geocoding_repositories.GoogleMapsGeocodingRepository.geocode",
                   return_value=point) as geocode:
            self.post(url, data)
        geocode.assert_called_once()
        query = geocode.call_args.kwargs["query"]
        self.assertIn(self.new_address, query)
        self.assertNotIn("narimanov", query.lower())
        if place:
            place.refresh_from_db()
            self.assertEqual((place.address, place.lat, place.lng), ("Нариманов", *self.old_point))
        else:
            place = Place.objects.get(created_by=self.editor)
            self.assertEqual((place.lat, place.lng), (None, None))
        self.assertEqual(self.reopened_point(place), (*self.new_point, "baku_sabail"))
        self.assertEqual(VolunteerPlaceRevision.objects.get(place=place).status, "draft")

    def test_new_card_geocodes_submitted_address_in_first_revision(self):
        self.check_recalculation()

    def test_existing_draft_geocodes_submitted_address_in_revision(self):
        self.check_recalculation(self.place())

    def test_published_place_preserves_approved_address_and_point(self):
        self.check_recalculation(self.place(published=True))

    def test_changed_address_discards_stale_pin_without_javascript(self):
        place = self.place()
        url = reverse("admin:catalog_place_change", args=[place.pk])
        data = self.form_data(url, lat=place.lat, lng=place.lng, _save_draft="1")
        self.post(url, data)
        self.assertEqual(self.reopened_point(place), (None, None, ""))
        place.refresh_from_db()
        self.assertEqual((place.lat, place.lng), self.old_point)

    def test_same_point_explicitly_confirmed_for_changed_address_is_kept(self):
        place = self.place()
        url = reverse("admin:catalog_place_change", args=[place.pk])
        data = self.form_data(url, lat=place.lat, lng=place.lng, _save_draft="1",
                              _location_point_confirmed="1")
        self.post(url, data)
        self.assertEqual(self.reopened_point(place), (*self.old_point, "baku_narimanov"))

    def test_changed_address_clears_legacy_district_after_it_was_resolved_on_screen(self):
        place = self.place()
        Place.objects.filter(pk=place.pk).update(district="Нариманов", location_resolution_status="legacy")
        url = reverse("admin:catalog_place_change", args=[place.pk])
        data = self.form_data(url, lat=place.lat, lng=place.lng, _save_draft="1")
        self.post(url, data)
        self.assertEqual(self.reopened_point(place), (None, None, ""))

    def test_changed_address_clears_old_coordinates_rounded_by_map_control(self):
        place = self.place()
        place.lat += 0.0000001
        place.lng -= 0.0000001
        place.save(update_fields=["lat", "lng"])
        url = reverse("admin:catalog_place_change", args=[place.pk])
        data = self.form_data(url, lat=f"{place.lat:.6f}", lng=f"{place.lng:.6f}", _save_draft="1")
        self.post(url, data)
        self.assertEqual(self.reopened_point(place), (None, None, ""))

    def test_failed_lookup_on_changed_address_saves_no_coordinates_in_candidate(self):
        place = self.place(published=True)
        url = reverse("admin:catalog_place_change", args=[place.pk])
        data = self.form_data(url, lat=place.lat, lng=place.lng, _refresh_coordinates_from_address="1")
        with patch("catalog.repositories.geocoding_repositories.GoogleMapsGeocodingRepository.geocode",
                   return_value=None):
            self.post(url, data)
        self.assertEqual(self.reopened_point(place), (None, None, ""))

    def test_changed_pending_address_discards_its_old_pin_without_javascript(self):
        place = self.place(published=True)
        url = reverse("admin:catalog_place_change", args=[place.pk])
        data = self.form_data(url, address="Первая редакция", lat=self.new_point[0],
                              lng=self.new_point[1], _save_draft="1")
        self.post(url, data)
        again = self.form_data(url, district="baku_sabail", lat=self.new_point[0],
                               lng=self.new_point[1], _save_draft="1")
        self.post(url, again)
        self.assertEqual(self.reopened_point(place), (None, None, ""))

    def test_stale_refresh_cannot_replace_another_editors_revision(self):
        place = self.place(published=True)
        url = reverse("admin:catalog_place_change", args=[place.pk])
        stale = self.form_data(url, address="Устаревший адрес", _refresh_coordinates_from_address="1")
        current = self.form_data(url, district="baku_sabail", lat=self.new_point[0],
                                 lng=self.new_point[1], _save_draft="1")
        self.post(url, current)
        with patch("catalog.repositories.geocoding_repositories.GoogleMapsGeocodingRepository.geocode",
                   return_value=GeocodingPoint(*self.old_point)):
            response = self.client.post(url, stale)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["km_place_candidate_conflict"])
        self.assertEqual(self.reopened_point(place), (*self.new_point, "baku_sabail"))
        place.refresh_from_db()
        self.assertEqual((place.address, place.lat, place.lng), ("Нариманов", *self.old_point))

    def test_precise_ganja_point_is_saved_in_draft_without_claiming_a_district(self):
        self.new_address = "Nizami Gəncəvi küçəsi 12"
        place = self.place()
        url = reverse("admin:catalog_place_change", args=[place.pk])
        data = self.form_data(url, region="ganja", district="", lat="", lng="",
                              _refresh_coordinates_from_address="1")
        point = GeocodingPoint(40.6821, 46.3606)
        with patch("catalog.repositories.geocoding_repositories.GoogleMapsGeocodingRepository.geocode",
                   return_value=point) as geocode:
            self.post(url, data)
        self.assertIn("Гянджа", geocode.call_args.kwargs["query"])
        self.assertEqual(self.reopened_point(place), (point.lat, point.lng, ""))

    def test_existing_confirmed_ganja_override_survives_identical_geocoded_point(self):
        from catalog.services.location_assignment import set_location_override

        self.new_address = "Nizami Gəncəvi küçəsi 12"
        place = self.place(published=True)
        point = GeocodingPoint(40.6821, 46.3606)
        place.address, place.lat, place.lng = self.new_address, point.lat, point.lng
        set_location_override(place, actor=self.editor, city="ganja", district="ganja", reason="QA")
        place.save()
        url = reverse("admin:catalog_place_change", args=[place.pk])
        data = self.form_data(url, region="ganja", district="", lat=point.lat, lng=point.lng,
                              _refresh_coordinates_from_address="1")
        with patch("catalog.repositories.geocoding_repositories.GoogleMapsGeocodingRepository.geocode",
                   return_value=point):
            response = self.client.post(url, data, follow=True)
        self.assertContains(response, "Координаты уже актуальны.")
        form = response.context["adminform"].form
        self.assertEqual((form["lat"].value(), form["lng"].value(), form["region"].value()),
                         (point.lat, point.lng, "ganja"))
        self.assertTrue(place.location_overrides.filter(is_current=True).exists())
