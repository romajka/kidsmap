from django.test import SimpleTestCase, TestCase
from django.utils.translation import gettext, override


class SeoLandingCopyTests(TestCase):
    def test_collection_label_in_each_language(self):
        old_labels = ("Yoxlanılmış seçim", "Проверенная подборка", "Verified selection")
        for prefix, label in (
            ("", "KidsMap seçimi"), ("/ru", "Подборка KidsMap"), ("/en", "KidsMap selection"),
        ):
            with self.subTest(prefix=prefix):
                page = self.client.get(f"{prefix}/catalog/dzudo-dlya-detey-v-baku/")
                self.assertEqual(page.status_code, 200)
                self.assertContains(page, f"<span>{label}</span>", html=True)
                for old in old_labels:
                    self.assertNotContains(page, old)


class ListingMessageCopyTests(SimpleTestCase):
    def test_homepage_recommendation_confirmation(self):
        for language, expected in (
            ("en", "The listing was added to homepage recommendations."),
            ("az", "Kart ana səhifədə tövsiyə olunanlar siyahısına əlavə edildi."),
        ):
            with self.subTest(language=language), override(language):
                self.assertEqual(gettext("Карточка добавлена в рекомендуемые на главной."), expected)
