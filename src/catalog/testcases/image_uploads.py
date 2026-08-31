from __future__ import annotations

from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.datastructures import MultiValueDict
from PIL import Image

from catalog.controllers.owner_places_controller import OwnerPlacesController
from catalog.models import Place, PlacePhoto, UserProfile
from catalog.services.image_uploads import normalize_uploaded_image


User = get_user_model()


def build_image_upload(
    name="photo.png",
    *,
    image_format="PNG",
    size=(48, 32),
    color="#2f8f5b",
    exif=None,
    content_type="image/png",
):
    output = BytesIO()
    image = Image.new("RGB", size, color)
    save_kwargs = {"format": image_format}
    if exif is not None:
        save_kwargs["exif"] = exif
    image.save(output, **save_kwargs)
    return SimpleUploadedFile(name, output.getvalue(), content_type=content_type)


class TestOwnerImageNormalization(TestCase):
    def test_png_is_decoded_and_saved_as_webp(self):
        normalized = normalize_uploaded_image(build_image_upload("кружок photo.PNG"))

        self.assertTrue(normalized.name.endswith(".webp"))
        self.assertEqual(normalized.content_type, "image/webp")
        self.assertLessEqual(normalized.size, 2 * 1024 * 1024)
        with Image.open(normalized) as image:
            self.assertEqual(image.format, "WEBP")
            self.assertEqual(image.size, (48, 32))

    def test_exif_orientation_is_applied(self):
        exif = Image.Exif()
        exif[274] = 6
        upload = build_image_upload(
            "iphone.jpg",
            image_format="JPEG",
            size=(40, 20),
            exif=exif,
            content_type="image/jpeg",
        )

        normalized = normalize_uploaded_image(upload)

        with Image.open(normalized) as image:
            self.assertEqual(image.size, (20, 40))
            self.assertEqual(image.getexif().get(274, 1), 1)

    def test_heic_is_converted_to_webp(self):
        upload = build_image_upload(
            "IMG_1234.HEIC",
            image_format="HEIF",
            size=(60, 45),
            content_type="image/heic",
        )

        normalized = normalize_uploaded_image(upload)

        self.assertEqual(normalized.name, "IMG_1234.webp")
        with Image.open(normalized) as image:
            self.assertEqual(image.format, "WEBP")
            self.assertEqual(image.size, (60, 45))

    def test_corrupt_image_has_clear_validation_error(self):
        upload = SimpleUploadedFile("broken.jpg", b"not-an-image", content_type="image/jpeg")

        with self.assertRaisesMessage(ValidationError, "Не удалось прочитать"):
            normalize_uploaded_image(upload)

    def test_mime_mismatch_has_clear_validation_error_and_is_logged(self):
        upload = build_image_upload("wrong.jpg", image_format="PNG", content_type="image/jpeg")

        with self.assertLogs("catalog.services.image_uploads", level="WARNING") as logs:
            with self.assertRaisesMessage(ValidationError, "объявлен как image/jpeg"):
                normalize_uploaded_image(upload)

        self.assertIn("wrong.jpg", " ".join(logs.output))

    def test_progressive_cmyk_jpeg_is_normalized(self):
        output = BytesIO()
        Image.new("CMYK", (64, 48), (10, 20, 30, 5)).save(
            output,
            format="JPEG",
            progressive=True,
        )
        upload = SimpleUploadedFile("print-profile.jpg", output.getvalue(), content_type="image/jpeg")

        normalized = normalize_uploaded_image(upload)

        with Image.open(normalized) as image:
            self.assertEqual(image.format, "WEBP")
            self.assertEqual(image.mode, "RGB")
            self.assertEqual(image.size, (64, 48))

    def test_non_heic_source_larger_than_two_mb_is_rejected(self):
        upload = SimpleUploadedFile(
            "huge.png",
            b"x" * (2 * 1024 * 1024 + 1),
            content_type="image/png",
        )

        with self.assertRaisesMessage(ValidationError, "Обычные изображения — до 2 МБ"):
            normalize_uploaded_image(upload)


class TestOwnerImagePersistenceFailures(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="photo_owner", password="StrongPass123!!")
        UserProfile.objects.create(user=self.user)
        self.request = RequestFactory().post("/account/places/create/")
        self.request.user = self.user
        self.controller = OwnerPlacesController.build_default()

    def test_card_is_not_created_when_main_photo_storage_fails(self):
        photo = build_image_upload()
        data = {"name_az": "Foto qaralama", "category": "EDU"}
        files = MultiValueDict({"photo": [photo]})
        storage = Place._meta.get_field("photo").storage

        with patch.object(storage, "save", side_effect=RuntimeError("storage unavailable")):
            result = self.controller.create_place(
                request=self.request,
                data=data,
                files=files,
                draft_save_only=True,
            )

        self.assertFalse(result.ok)
        self.assertIn("photo", result.form.errors)
        self.assertFalse(Place.objects.filter(owner=self.user).exists())

    def test_card_changes_are_not_saved_when_gallery_storage_fails(self):
        place = Place.objects.create(
            name="Existing name",
            name_az="Mövcud ad",
            category="EDU",
            owner=self.user,
            status=Place.STATUS_DRAFT,
            is_active=False,
        )
        gallery_storage = PlacePhoto._meta.get_field("image").storage

        with patch.object(gallery_storage, "save", side_effect=RuntimeError("storage unavailable")):
            result = self.controller.save_edit_form(
                request=self.request,
                place_id=place.id,
                data={"name_az": "Dəyişdirilmiş ad", "category": "EDU"},
                files=MultiValueDict(
                    {"gallery_images": [build_image_upload("gallery.png")]}
                ),
                draft_save_only=True,
            )

        self.assertFalse(result.ok)
        self.assertIn("gallery_images", result.form.errors)
        place.refresh_from_db()
        self.assertEqual(place.name_az, "Mövcud ad")
        self.assertFalse(place.gallery.exists())

    def test_corrupt_photo_does_not_create_draft(self):
        files = MultiValueDict(
            {
                "photo": [
                    SimpleUploadedFile("broken.png", b"broken", content_type="image/png")
                ]
            }
        )

        result = self.controller.create_place(
            request=self.request,
            data={"name_az": "Broken photo", "category": "EDU"},
            files=files,
            draft_save_only=True,
        )

        self.assertFalse(result.ok)
        self.assertIn("photo", result.form.errors)
        self.assertFalse(Place.objects.filter(owner=self.user).exists())

    def test_main_photo_can_be_replaced_and_then_removed(self):
        place = Place.objects.create(
            name="Photo lifecycle",
            name_az="Foto həyat dövrü",
            category="EDU",
            owner=self.user,
            status=Place.STATUS_DRAFT,
            is_active=False,
            photo=build_image_upload("old.png", color="#cc3344"),
        )
        old_name = place.photo.name
        storage = place.photo.storage

        with self.captureOnCommitCallbacks(execute=True):
            replace_result = self.controller.save_edit_form(
                request=self.request,
                place_id=place.id,
                data={"name_az": place.name_az, "category": "EDU"},
                files=MultiValueDict(
                    {"photo": [build_image_upload("new.webp", color="#3366cc")]}
                ),
                draft_save_only=True,
            )

        self.assertTrue(replace_result.ok)
        place.refresh_from_db()
        replacement_name = place.photo.name
        self.assertNotEqual(replacement_name, old_name)
        self.assertTrue(replacement_name.endswith(".webp"))
        self.assertTrue(storage.exists(replacement_name))
        self.assertFalse(storage.exists(old_name))

        with self.captureOnCommitCallbacks(execute=True):
            remove_result = self.controller.save_edit_form(
                request=self.request,
                place_id=place.id,
                data={
                    "name_az": place.name_az,
                    "category": "EDU",
                    "photo-clear": "on",
                },
                files=MultiValueDict(),
                draft_save_only=True,
            )

        self.assertTrue(remove_result.ok)
        place.refresh_from_db()
        self.assertFalse(place.photo)
        self.assertFalse(storage.exists(replacement_name))

    def test_gallery_can_be_added_and_owner_can_delete_a_photo(self):
        place = Place.objects.create(
            name="Gallery lifecycle",
            name_az="Qalereya həyat dövrü",
            category="EDU",
            owner=self.user,
            status=Place.STATUS_DRAFT,
            is_active=False,
            photo=build_image_upload("main.png"),
        )

        save_result = self.controller.save_edit_form(
            request=self.request,
            place_id=place.id,
            data={"name_az": place.name_az, "category": "EDU"},
            files=MultiValueDict(
                {
                    "gallery_images": [
                        build_image_upload("gallery-one.png", color="#cc8844"),
                        build_image_upload("gallery-two.webp", color="#5588cc"),
                    ]
                }
            ),
            draft_save_only=True,
        )

        self.assertTrue(save_result.ok, save_result.form.errors)
        gallery_photos = list(place.gallery.order_by("order"))
        self.assertEqual(len(gallery_photos), 2)
        for gallery_photo in gallery_photos:
            self.assertTrue(gallery_photo.image.name.endswith(".webp"))
            self.assertTrue(gallery_photo.image.storage.exists(gallery_photo.image.name))

        deleted_photo = gallery_photos[0]
        deleted_name = deleted_photo.image.name
        storage = deleted_photo.image.storage
        with self.captureOnCommitCallbacks(execute=True):
            delete_result = self.controller.delete_gallery_photo(
                request=self.request,
                place_id=place.id,
                photo_id=deleted_photo.id,
            )

        self.assertTrue(delete_result.ok)
        self.assertFalse(place.gallery.filter(pk=deleted_photo.id).exists())
        self.assertFalse(storage.exists(deleted_name))

    def test_user_cannot_delete_photo_from_another_users_card(self):
        place = Place.objects.create(
            name="Protected gallery",
            name_az="Qorunan qalereya",
            category="EDU",
            owner=self.user,
            status=Place.STATUS_DRAFT,
            is_active=False,
        )
        gallery_photo = place.gallery.create(image=build_image_upload("protected.png"))
        other_user = User.objects.create_user(username="other_photo_owner", password="StrongPass123!!")
        UserProfile.objects.create(user=other_user)
        other_request = RequestFactory().post("/account/places/1/photos/1/delete/")
        other_request.user = other_user

        result = self.controller.delete_gallery_photo(
            request=other_request,
            place_id=place.id,
            photo_id=gallery_photo.id,
        )

        self.assertFalse(result.ok)
        self.assertTrue(place.gallery.filter(pk=gallery_photo.id).exists())

    def test_edit_page_shows_saved_gallery_preview_and_delete_action(self):
        place = Place.objects.create(
            name="Gallery preview",
            name_az="Qalereya önizləməsi",
            category="EDU",
            owner=self.user,
            status=Place.STATUS_DRAFT,
            is_active=False,
        )
        gallery_photo = place.gallery.create(image=build_image_upload("preview.png"))
        self.client.force_login(self.user)

        response = self.client.get(reverse("owner_place_edit", args=[place.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, gallery_photo.image.url)
        self.assertContains(
            response,
            reverse("owner_place_gallery_photo_delete", args=[place.id, gallery_photo.id]),
        )
