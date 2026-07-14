from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from catalog.models import (
    Specialist,
    SpecialistSpecialization,
    SpecialistReview,
    SpecialistDocument,
    SpecialistPracticeLocation,
    Region,
    District,
    MetroStation
)

User = get_user_model()

class TestSpecialistFlows(TestCase):
    def setUp(self):
        # Setup location test data
        self.region, _ = Region.objects.get_or_create(key="baku", defaults={"name_ru": "Баку", "name_az": "Bakı", "name_en": "Baku"})
        self.district, _ = District.objects.get_or_create(
            key="baku_yasamal",
            defaults={
                "region": self.region,
                "name_ru": "Ясамал",
                "name_az": "Yasamal",
                "name_en": "Yasamal"
            }
        )
        self.metro, _ = MetroStation.objects.get_or_create(
            key="elmlar",
            defaults={
                "name_ru": "Эльмляр Академиясы",
                "name_az": "Elmlər Akademiyası",
                "name_en": "Elmlar Akademiyasi"
            }
        )

        # Setup Specializations
        self.spec_psych, _ = SpecialistSpecialization.objects.get_or_create(
            code="psych",
            defaults={
                "name_ru": "Психолог",
                "name_az": "Psixoloq",
                "name_en": "Psychologist"
            }
        )
        self.spec_speech, _ = SpecialistSpecialization.objects.get_or_create(
            code="speech",
            defaults={
                "name_ru": "Логопед",
                "name_az": "Loqoped",
                "name_en": "Speech Therapist"
            }
        )

        # Create owners/users
        self.owner = User.objects.create_user(username="owner1", email="owner1@example.com", password="password")
        self.user = User.objects.create_user(username="user1", email="user1@example.com", password="password")
        self.staff = User.objects.create_superuser(username="admin", email="admin@example.com", password="password")

        # Create Specialist
        self.specialist = Specialist.objects.create(
            name="Иван Иванов",
            name_alt="Dr. Ivan Ivanov",
            slug="ivan-ivanov",
            owner=self.owner,
            consultation_format=Specialist.FORMAT_BOTH,
            experience_years=10,
            age_from=5,
            age_to=15,
            bio_ru="Опытный детский психолог.",
            bio_az="Təcrübəli uşaq psixoloqu.",
            bio_en="Experienced child psychologist.",
            status=Specialist.STATUS_PUBLISHED,
            is_active=True,
            is_verified=True
        )
        self.specialist.specializations.add(self.spec_psych)

        # Add practice location
        self.practice_loc = SpecialistPracticeLocation.objects.create(
            specialist=self.specialist,
            region=self.region,
            district=self.district,
            metro=self.metro,
            address="ул. Мира, 15",
            price_per_session=50
        )

        # Add Documents
        self.diploma = SpecialistDocument.objects.create(
            specialist=self.specialist,
            name="Диплом МГУ",
            document_type=SpecialistDocument.TYPE_DIPLOMA,
            file=SimpleUploadedFile("diploma.pdf", b"pdfcontent", content_type="application/pdf"),
            status=SpecialistDocument.STATUS_APPROVED,
            is_published=True
        )

        self.passport = SpecialistDocument.objects.create(
            specialist=self.specialist,
            name="Паспорт",
            document_type=SpecialistDocument.TYPE_IDENTITY,
            file=SimpleUploadedFile("passport.pdf", b"pdfcontent", content_type="application/pdf"),
            status=SpecialistDocument.STATUS_APPROVED,
            is_published=False
        )

    def test_specialist_list_opens(self):
        url = reverse("specialist_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Иван Иванов")
        self.assertContains(response, "50 AZN")

    def test_specialist_list_filtering(self):
        url = reverse("specialist_list")
        
        # Filter by specialization
        response = self.client.get(url, {"specialization": "psych"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Иван Иванов")

        response = self.client.get(url, {"specialization": "speech"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Иван Иванов")

        # Filter by location
        response = self.client.get(url, {"region": "baku", "district": "baku_yasamal"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Иван Иванов")

        response = self.client.get(url, {"region": "sumgayit"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Иван Иванов")

        # Filter by age
        response = self.client.get(url, {"age": "8"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Иван Иванов")

        response = self.client.get(url, {"age": "20"})
        self.assertNotContains(response, "Иван Иванов")

        # Filter by price
        response = self.client.get(url, {"price_from": "40", "price_to": "60"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Иван Иванов")

        response = self.client.get(url, {"price_from": "60"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Иван Иванов")

    def test_specialist_detail_opens(self):
        url = reverse("specialist_detail", kwargs={"slug": self.specialist.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Иван Иванов")
        self.assertContains(response, "Диплом МГУ")
        # Passport is not published to public, should not be visible
        self.assertNotContains(response, "Паспорт")

    def test_document_download_authorization(self):
        url_diploma = reverse("serve_specialist_document", kwargs={"document_id": self.diploma.id})
        url_passport = reverse("serve_specialist_document", kwargs={"document_id": self.passport.id})

        # 1. Anonymous user can download approved diploma
        response = self.client.get(url_diploma)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"pdfcontent")

        # 2. Anonymous user cannot download passport (identity)
        response = self.client.get(url_passport)
        self.assertEqual(response.status_code, 404)

        # 3. Regular logged in user cannot download passport
        self.client.login(username="user1", password="password")
        response = self.client.get(url_passport)
        self.assertEqual(response.status_code, 404)
        self.client.logout()

        # 4. Specialist owner can download passport
        self.client.login(username="owner1", password="password")
        response = self.client.get(url_passport)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"pdfcontent")
        self.client.logout()

        # 5. Admin can download passport
        self.client.login(username="admin", password="password")
        response = self.client.get(url_passport)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"pdfcontent")
        self.client.logout()

    def test_submit_specialist_review(self):
        url = reverse("add_specialist_review", kwargs={"pk": self.specialist.pk})
        
        # Submitting review when login required (anonymous client)
        response = self.client.post(url, {"rating": "5", "text": "Прекрасный специалист!"})
        # Check login redirect (redirects to accounts login page with next param)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login/", response.url)

        # Logged in client review submission
        self.client.login(username="user1", password="password")
        response = self.client.post(url, {"rating": "5", "text": "Прекрасный специалист!"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.specialist.get_absolute_url() + "#reviews")
        
        # Check review is created in pending status
        review = SpecialistReview.objects.get(specialist=self.specialist, user=self.user)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.text, "Прекрасный специалист!")
        self.assertEqual(review.status, SpecialistReview.STATUS_PENDING)
        self.assertFalse(review.is_approved)


class TestOwnerSpecialistManagement(TestCase):
    def setUp(self):
        self.region, _ = Region.objects.get_or_create(
            key="baku",
            defaults={"name_ru": "Баку", "name_az": "Bakı", "name_en": "Baku"},
        )
        self.spec, _ = SpecialistSpecialization.objects.get_or_create(
            code="tutor",
            defaults={
                "name": "Tutor",
                "name_ru": "Репетитор",
                "name_az": "Repetitor",
                "name_en": "Tutor",
            },
        )
        self.owner = User.objects.create_user(username="spec_owner", email="spec-owner@example.com", password="password")
        self.other = User.objects.create_user(username="spec_other", email="spec-other@example.com", password="password")

    def _valid_payload(self, **overrides):
        payload = {
            "name": "Анна Петрова",
            "bio_ru": "Помогаю детям с математикой и подготовкой к школе.",
            "specializations": [str(self.spec.pk)],
            "consultation_format": Specialist.FORMAT_ONLINE,
            "language_ru": "on",
            "phone": "+994 50 123 45 67",
            "form_action": "submit",
        }
        payload.update(overrides)
        return payload

    def test_owner_can_create_online_profile_without_location(self):
        self.client.login(username="spec_owner", password="password")
        response = self.client.post(reverse("owner_specialist_create"), data=self._valid_payload())

        self.assertEqual(response.status_code, 302)
        specialist = Specialist.objects.get(owner=self.owner)
        self.assertEqual(specialist.status, Specialist.STATUS_PENDING)
        self.assertEqual(specialist.consultation_format, Specialist.FORMAT_ONLINE)
        self.assertFalse(specialist.practice_locations.exists())

    def test_owner_can_create_offline_profile_with_location(self):
        self.client.login(username="spec_owner", password="password")
        response = self.client.post(
            reverse("owner_specialist_create"),
            data=self._valid_payload(
                consultation_format=Specialist.FORMAT_OFFLINE,
                location_address="Баку, ул. Низами 10",
                location_region=self.region.pk,
            ),
        )

        self.assertEqual(response.status_code, 302)
        specialist = Specialist.objects.get(owner=self.owner)
        location = specialist.practice_locations.get()
        self.assertEqual(specialist.status, Specialist.STATUS_PENDING)
        self.assertEqual(location.region, self.region)
        self.assertEqual(location.address, "Баку, ул. Низами 10")

    def test_owner_can_save_incomplete_draft(self):
        self.client.login(username="spec_owner", password="password")
        response = self.client.post(
            reverse("owner_specialist_create"),
            data={"name": "Черновик профиля", "form_action": "save_draft"},
        )

        self.assertEqual(response.status_code, 302)
        specialist = Specialist.objects.get(owner=self.owner)
        self.assertEqual(specialist.status, Specialist.STATUS_DRAFT)

    def test_owner_uploads_documents_as_pending_private_certificates(self):
        self.client.login(username="spec_owner", password="password")
        response = self.client.post(
            reverse("owner_specialist_create"),
            data={
                **self._valid_payload(),
                "documents": [SimpleUploadedFile("certificate.pdf", b"pdf", content_type="application/pdf")],
            },
        )

        self.assertEqual(response.status_code, 302)
        document = SpecialistDocument.objects.get(specialist__owner=self.owner)
        self.assertEqual(document.status, SpecialistDocument.STATUS_PENDING)
        self.assertEqual(document.document_type, SpecialistDocument.TYPE_CERTIFICATE)
        self.assertFalse(document.is_published)

    def test_owner_cannot_edit_other_profile(self):
        specialist = Specialist.objects.create(
            owner=self.owner,
            name="Чужой профиль",
            consultation_format=Specialist.FORMAT_ONLINE,
            status=Specialist.STATUS_DRAFT,
        )
        self.client.login(username="spec_other", password="password")
        response = self.client.get(reverse("owner_specialist_edit", kwargs={"pk": specialist.pk}))

        self.assertEqual(response.status_code, 404)

    def test_owner_dashboard_button_points_to_owner_form(self):
        self.client.login(username="spec_owner", password="password")
        response = self.client.get(reverse("owner_places_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("owner_specialist_create"))
        self.assertNotContains(response, "/admin/catalog/specialist/add/")

    def test_specialist_language_pages_open(self):
        specialist = Specialist.objects.create(
            owner=self.owner,
            name="Публичный педагог",
            bio_ru="Описание профиля.",
            consultation_format=Specialist.FORMAT_ONLINE,
            language_ru=True,
            phone="+994 50 123 45 67",
            status=Specialist.STATUS_PUBLISHED,
            is_active=True,
        )
        specialist.specializations.add(self.spec)

        for path in ("/specialists/", "/ru/specialists/", "/en/specialists/"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)

from unittest.mock import patch

class TestSpecialistsFeatureFlag(TestCase):
    def setUp(self):
        from catalog.models.site import SiteSettings
        self.settings = SiteSettings.get_solo()
        self.owner = User.objects.create_user(username="owner_flag", email="flag@example.com", password="password")
        self.specialist = Specialist.objects.create(
            name="Test Specialist",
            slug="test-specialist",
            owner=self.owner,
            consultation_format=Specialist.FORMAT_ONLINE,
            status=Specialist.STATUS_PUBLISHED,
            is_active=True,
        )

    def test_feature_enabled_by_default(self):
        self.settings.specialists_section_enabled = True
        self.settings.save()

        # Public endpoints
        response = self.client.get(reverse("specialist_list"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("specialist_detail", kwargs={"slug": self.specialist.slug}))
        self.assertEqual(response.status_code, 200)

        # Owner endpoints
        self.client.login(username="owner_flag", password="password")
        response = self.client.get(reverse("owner_specialist_create"))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("owner_specialist_create"), data={"name": "test"})
        self.assertNotEqual(response.status_code, 404)

        # Review POST
        response = self.client.post(reverse("add_specialist_review", kwargs={"pk": self.specialist.pk}), data={"rating": 5, "text": "Good"})
        self.assertNotEqual(response.status_code, 404)

    def test_feature_disabled_returns_404(self):
        self.settings.specialists_section_enabled = False
        self.settings.save()

        # Public endpoints
        response = self.client.get(reverse("specialist_list"))
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse("specialist_detail", kwargs={"slug": self.specialist.slug}))
        self.assertEqual(response.status_code, 404)

        # Owner endpoints
        self.client.login(username="owner_flag", password="password")
        response = self.client.get(reverse("owner_specialist_create"))
        self.assertEqual(response.status_code, 404)

        response = self.client.post(reverse("owner_specialist_create"), data={"name": "test"})
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse("owner_specialist_edit", kwargs={"pk": self.specialist.pk}))
        self.assertEqual(response.status_code, 404)

        response = self.client.post(reverse("owner_specialist_edit", kwargs={"pk": self.specialist.pk}), data={"name": "test"})
        self.assertEqual(response.status_code, 404)

        # Review POST
        response = self.client.post(reverse("add_specialist_review", kwargs={"pk": self.specialist.pk}), data={"rating": 5, "text": "Good"})
        self.assertEqual(response.status_code, 404)

    @patch("catalog.models.site.SiteSettings.get_solo")
    def test_feature_disabled_on_db_error(self, mock_get_solo):
        from django.db.utils import OperationalError
        mock_get_solo.side_effect = OperationalError("no such table")

        response = self.client.get(reverse("specialist_list"))
        self.assertEqual(response.status_code, 404)

    def test_proxy_admin_save_invalidates_cached_feature_flag(self):
        from catalog.models.site import SiteVisibilitySettings
        from catalog.services.features import is_specialists_section_enabled

        self.settings.specialists_section_enabled = True
        self.settings.save()
        self.assertTrue(is_specialists_section_enabled())

        visibility_settings = SiteVisibilitySettings.objects.get(pk=self.settings.pk)
        visibility_settings.specialists_section_enabled = False
        visibility_settings.save()

        self.assertFalse(is_specialists_section_enabled())
