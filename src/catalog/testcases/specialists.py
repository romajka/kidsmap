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
            key="yasamal",
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
        self.assertContains(response, "Psixoloq")
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
        response = self.client.get(url, {"region": "baku", "district": "yasamal"})
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
