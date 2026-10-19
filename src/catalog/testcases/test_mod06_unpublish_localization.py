"""The changelist must supply localized unpublish copy to the row dialog.

Regression: missing labels, untranslated catalogs or ignoring the selected
admin locale would send Russian confirmation copy to AZ/EN users.
"""
from html.parser import HTMLParser

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase


class _UnpublishLabels(HTMLParser):
    def __init__(self):
        super().__init__()
        self.labels = {}

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("id") == "km-changelist-i18n":
            self.labels = {
                key.removeprefix("data-unpublish-"): value
                for key, value in attrs
                if key.startswith("data-unpublish-")
            }


class UnpublishConfirmationLocalizationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(
            username="mod06_localization_admin",
            email="mod06@example.invalid",
            password=None,
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def assert_labels(self, path, cookie, language, expected):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = cookie
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.LANGUAGE_CODE, language)
        parser = _UnpublishLabels()
        parser.feed(response.content.decode("utf-8"))
        self.assertEqual(parser.labels, expected)

    def test_ru_prefix_supplies_russian_confirmation_despite_en_cookie(self):
        self.assert_labels("/ru/admin/catalog/place/", "en", "ru", {
            "title": "Снять с публикации?",
            "message": "Карточка «%(name)s» перестанет отображаться на сайте и перейдёт в черновики.",
            "confirm": "Да, снять",
            "cancel": "Отмена",
            "fallback": "Снять карточку «%(name)s» с публикации?",
        })

    def test_en_prefix_supplies_english_confirmation_despite_ru_cookie(self):
        self.assert_labels("/en/admin/catalog/place/", "ru", "en", {
            "title": "Unpublish?",
            "message": "The “%(name)s” listing will no longer appear on the site and will move to drafts.",
            "confirm": "Yes, unpublish",
            "cancel": "Cancel",
            "fallback": "Unpublish the “%(name)s” listing?",
        })

    def test_unprefixed_admin_uses_cookie_selected_azerbaijani_confirmation(self):
        self.assert_labels("/admin/catalog/place/", "az", "az", {
            "title": "Nəşrdən çıxarılsın?",
            "message": "«%(name)s» kartı saytda göstərilməyəcək və qaralamalara keçiriləcək.",
            "confirm": "Bəli, nəşrdən çıxar",
            "cancel": "Ləğv et",
            "fallback": "«%(name)s» kartı nəşrdən çıxarılsın?",
        })
