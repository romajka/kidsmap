from django.test import SimpleTestCase
from django.utils.translation import gettext, ngettext, override


class ListingMessageCopyTests(SimpleTestCase):
    def test_listing_messages_distinguish_unavailable_deleted_and_rejected(self):
        messages = (
            ("Карточка не найдена или не привязана к вашему аккаунту.",
             "The listing was not found or is not linked to your account.",
             "Kart tapılmadı və ya hesabınıza bağlı deyil."),
            ("Карточка удалена и не показывается на сайте.",
             "The listing has been deleted and is no longer visible on the site.",
             "Kart silinib və saytda göstərilmir."),
            ("Карточка отклонена и не показывается на сайте.",
             "The listing has been rejected and is not visible on the site.",
             "Kart rədd edilib və saytda göstərilmir."),
        )
        for source, en, az in messages:
            for language, expected in (("en", en), ("az", az)):
                with self.subTest(source=source, language=language), override(language):
                    self.assertEqual(gettext(source), expected)

    def test_region_language_summary_preserves_both_values(self):
        source = "Азербайджанский: %(az)s · Английский: %(en)s"
        for language, expected in (
            ("en", "Azerbaijani: Bakı · English: Baku"),
            ("az", "Azərbaycanca: Bakı · İngiliscə: Baku"),
        ):
            with self.subTest(language=language), override(language):
                self.assertEqual(gettext(source) % {"az": "Bakı", "en": "Baku"}, expected)

    def test_active_events_count_is_localized_for_one_and_many(self):
        singular = "%(total)s активное мероприятие"
        plural = "%(total)s активных мероприятий"
        for language, noun in (("en", "event"), ("az", "tədbir")):
            for count in (1, 5):
                with self.subTest(language=language, count=count), override(language):
                    text = ngettext(singular, plural, count) % {"total": count}
                    self.assertIn(str(count), text)
                    self.assertIn(noun, text.lower())


class AdminFieldCopyTests(SimpleTestCase):
    def test_description_and_empty_results_labels_identify_the_edited_fields(self):
        from catalog.domain_admin.place_admin.forms import PlaceAdminForm
        from catalog.models import SiteSettings

        for language, description, text, contacts in (
            ("en", "Description (English)", "No-results text", "Contacts"),
            ("az", "Təsvir (ingilis dili)", "Nəticə tapılmadıqda göstərilən mətn", "Əlaqə"),
        ):
            with self.subTest(language=language), override(language):
                self.assertEqual(str(PlaceAdminForm.base_fields["description_en"].label), description)
                for code in ("ru", "az", "en"):
                    empty_field = SiteSettings._meta.get_field(f"empty_results_text_{code}")
                    contact_field = SiteSettings._meta.get_field(f"contacts_text_{code}")
                    self.assertEqual(str(empty_field.verbose_name), f"{text} ({code.upper()})")
                    self.assertEqual(str(contact_field.verbose_name), f"{contacts} ({code.upper()})")


class AdminErrorSummaryCopyTests(SimpleTestCase):
    @override("ru")
    def test_russian_error_count_uses_all_three_plural_forms(self):
        singular = "Карточка не сохранена — %(counter)s проблема"
        plural = "Карточка не сохранена — %(counter)s проблем(ы)"
        for count, expected in (
            (1, "Карточка не сохранена — 1 проблема"),
            (2, "Карточка не сохранена — 2 проблемы"),
            (18, "Карточка не сохранена — 18 проблем"),
        ):
            with self.subTest(count=count):
                self.assertEqual(ngettext(singular, plural, count) % {"counter": count}, expected)
