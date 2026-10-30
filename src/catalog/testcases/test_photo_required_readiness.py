from django.test import SimpleTestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from catalog.services.place_readiness import PlaceReadinessData, evaluate_readiness


class RequiredPhotoReadinessTests(SimpleTestCase):
    def test_photo_is_a_blocking_twelfth_requirement(self):
        result = evaluate_readiness(PlaceReadinessData())
        photo = next((item for item in result.items if item.code == 'photo'), None)
        self.assertIsNotNone(photo)
        self.assertFalse(photo.is_complete)
        self.assertTrue(photo.issue.blocking)
        self.assertEqual(result.required_count, 12)

    def test_main_photo_satisfies_the_photo_requirement(self):
        result = evaluate_readiness(PlaceReadinessData(has_main_photo=True))
        self.assertTrue(next(item for item in result.items if item.code == 'photo').is_complete)


class PhotoPublicationTests(TestCase):
    def test_publication_rejects_missing_photo_and_accepts_added_photo(self):
        from catalog.services.publication import publish
        from catalog.testcases.utils import create_ready_place

        staff = get_user_model().objects.create_superuser(username='photo-reviewer', password='test')
        place = create_ready_place(status='draft', is_active=False, photo='', cover_photo='')
        with self.assertRaises(ValidationError):
            publish(actor=staff, place_id=place.pk, expected_version=place.content_version)
        place.photo = 'places/test-main.jpg'
        place.save(update_fields=['photo'])
        result = publish(actor=staff, place_id=place.pk, expected_version=place.content_version)
        self.assertEqual(result.status, 'published')

    def test_existing_published_place_is_not_hidden_by_new_requirement(self):
        from catalog.models import Place
        from catalog.services.content_quality import public_place_queryset
        from catalog.testcases.utils import create_ready_place

        place = create_ready_place(photo='', cover_photo='')
        self.assertTrue(public_place_queryset(Place.objects.filter(pk=place.pk)).exists())
