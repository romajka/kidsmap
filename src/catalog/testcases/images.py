from io import BytesIO
from io import StringIO
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import SimpleTestCase, TransactionTestCase, override_settings
from PIL import Image

from catalog.services.images import generate_image_variants, image_variant_url, validate_uploaded_image, variant_name
from catalog.models import Category, Place


def make_image_bytes(*, size=(1200, 800), image_format="JPEG") -> bytes:
    output = BytesIO()
    Image.new("RGB", size, color=(38, 132, 181)).save(output, format=image_format, quality=90)
    return output.getvalue()


class ImageOptimizationTests(SimpleTestCase):
    def test_validation_decodes_actual_image_contents(self):
        invalid = SimpleUploadedFile("fake.jpg", b"not-an-image", content_type="image/jpeg")
        with self.assertRaises(ValidationError):
            validate_uploaded_image(invalid)

    def test_validation_accepts_supported_raster_image(self):
        upload = SimpleUploadedFile("photo.jpg", make_image_bytes(), content_type="image/jpeg")
        validate_uploaded_image(upload)
        self.assertEqual(upload.tell(), 0)

    def test_validation_rejects_gif_even_when_it_is_a_real_image(self):
        upload = SimpleUploadedFile(
            "animated.gif",
            make_image_bytes(size=(32, 32), image_format="GIF"),
            content_type="image/gif",
        )
        with self.assertRaises(ValidationError):
            validate_uploaded_image(upload)

    def test_listing_profile_generates_responsive_webp_variants(self):
        with TemporaryDirectory() as media_root:
            storage = FileSystemStorage(location=media_root, base_url="/media/")
            name = storage.save("places/source.jpg", ContentFile(make_image_bytes()))
            field_file = SimpleNamespace(name=name, storage=storage)

            generated = generate_image_variants(field_file, "listing")

            self.assertEqual(len(generated), 4)
            card_name = variant_name(name, "card-480")
            self.assertTrue(storage.exists(card_name))
            with storage.open(card_name, "rb") as generated_file:
                with Image.open(generated_file) as card:
                    self.assertEqual(card.format, "WEBP")
                    self.assertEqual(card.size, (480, 480))
            self.assertEqual(image_variant_url(field_file, "card-480"), storage.url(card_name))


class ImageLifecycleTests(TransactionTestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_directory.name)
        self.settings_override.enable()
        Category.objects.get_or_create(code="EDU", defaults={"name": "Education", "name_az": "Education"})

    def tearDown(self):
        self.settings_override.disable()
        self.media_directory.cleanup()

    def test_model_save_replace_and_delete_manage_original_and_variants(self):
        place = Place.objects.create(
            name="Optimized place",
            name_az="Optimized place",
            category="EDU",
            photo=SimpleUploadedFile("photo.jpg", make_image_bytes(), content_type="image/jpeg"),
        )
        first_name = place.photo.name
        first_variant = variant_name(first_name, "card-480")
        storage = place.photo.storage
        self.assertTrue(storage.exists(first_variant))

        place.photo = SimpleUploadedFile("photo.jpg", make_image_bytes(size=(900, 900)), content_type="image/jpeg")
        place.save(update_fields=["photo", "updated_at"])
        second_name = place.photo.name

        self.assertNotEqual(first_name, second_name)
        self.assertFalse(storage.exists(first_name))
        self.assertFalse(storage.exists(first_variant))
        self.assertTrue(storage.exists(variant_name(second_name, "card-480")))

        place.delete()
        self.assertFalse(storage.exists(second_name))
        self.assertFalse(storage.exists(variant_name(second_name, "card-480")))

    def test_backfill_command_recreates_missing_variant(self):
        place = Place.objects.create(
            name="Backfill place",
            name_az="Backfill place",
            category="EDU",
            photo=SimpleUploadedFile("backfill.jpg", make_image_bytes(), content_type="image/jpeg"),
        )
        target = variant_name(place.photo.name, "card-480")
        place.photo.storage.delete(target)
        self.assertFalse(place.photo.storage.exists(target))

        call_command("optimize_images", models=["catalog.Place"], stdout=StringIO())

        self.assertTrue(place.photo.storage.exists(target))
