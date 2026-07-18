from io import BytesIO
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from django.contrib.admin.sites import AdminSite
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils.datastructures import MultiValueDict
from PIL import Image

from catalog.domain_admin.place import PlaceAdmin
from catalog.models import Place, PlacePhoto


class PlaceAdminFilePondGalleryTests(TestCase):
    @staticmethod
    def _image(name, image_format, content_type):
        output = BytesIO()
        Image.new("RGB", (32, 32), color=(20, 120, 180)).save(output, format=image_format)
        return SimpleUploadedFile(name, output.getvalue(), content_type=content_type)

    def test_filepond_gallery_uploads_create_ordered_place_photos(self):
        place = Place.objects.create(
            name="FilePond Place",
            name_az="FilePond Place",
            category="EDU",
        )
        admin = PlaceAdmin(Place, AdminSite())
        request = SimpleNamespace(
            FILES=MultiValueDict(
                {
                    "gallery_uploads": [
                        self._image("first.jpg", "JPEG", "image/jpeg"),
                        self._image("second.png", "PNG", "image/png"),
                    ]
                }
            )
        )

        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            admin._save_filepond_gallery_uploads(request, place)

            photos = list(PlacePhoto.objects.filter(place=place).order_by("order", "id"))
            self.assertEqual(len(photos), 2)
            self.assertEqual([photo.order for photo in photos], [1, 2])
            self.assertTrue(photos[0].image.name.endswith(".jpg"))
            self.assertTrue(photos[1].image.name.endswith(".png"))
