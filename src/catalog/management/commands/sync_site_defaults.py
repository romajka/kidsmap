from django.core.management.base import BaseCommand

from catalog.models import SiteSettings


SITE_DEFAULTS = {
    "brand_name": "KidsMap",
    "contacts_text_ru": "Свяжитесь с нами по почте: info@kidsmap.az",
    "contacts_text_en": "Contact us by email: info@kidsmap.az",
    "contacts_text_az": "Bizimlə e-poçt vasitəsilə əlaqə saxlayın: info@kidsmap.az",
    "about_text_ru": "KidsMap — каталог детских кружков и секций по Азербайджану.",
    "about_text_en": "KidsMap is a catalog of kids clubs and courses across Azerbaijan.",
    "about_text_az": "KidsMap Azərbaycanda uşaqlar üçün dərnək və kurs kataloqudur.",
    "home_title_ru": "Найдите подходящее занятие для ребёнка",
    "home_title_en": "Find the right activity for your child",
    "home_title_az": "Uşağınız üçün uyğun məşğələni tapın",
    "home_subtitle_ru": "Кружки, курсы и события рядом — всё в одном месте.",
    "home_subtitle_en": "Nearby clubs, classes and events — all in one place.",
    "home_subtitle_az": "Yaxınlıqdakı dərnək, kurs və tədbirlər — hamısı bir yerdə.",
    "home_search_label_ru": "Найти занятие",
    "home_search_label_en": "Find activities",
    "home_search_label_az": "Məşğələ tap",
    "home_search_placeholder_ru": "например шахматы, футбол, рисование",
    "home_search_placeholder_en": "for example chess, football, drawing",
    "home_search_placeholder_az": "məsələn şahmat, futbol, rəsm",
    "home_cta_text_ru": "Начать поиск",
    "home_cta_text_en": "Start searching",
    "home_cta_text_az": "Axtarışa başla",
    "empty_results_text_ru": "Ничего не найдено.",
    "empty_results_text_en": "Nothing found.",
    "empty_results_text_az": "Heç nə tapılmadı.",
    "footer_phone": "+994 50 540 66 39",
    "footer_email": "info@kidsmap.az",
    "footer_instagram": "https://www.instagram.com/kidsmap.az/",
    "footer_telegram": "https://t.me/KidsMap_az",
    "footer_youtube": "https://www.youtube.com/@KidsMap_az",
    "footer_tiktok": "https://www.tiktok.com/@kidsmap.az?lang=ru-RU",
    "footer_facebook": "https://www.facebook.com/people/KidsMap/61583913364027/",
    "footer_linkedin": "https://www.linkedin.com/company/kidsmap-az/",
}


class Command(BaseCommand):
    help = "Fill blank SiteSettings fields with code defaults without overwriting non-empty production content."

    def handle(self, *args, **options):
        site = SiteSettings.get_solo()
        changed_fields = []

        for field_name, default_value in SITE_DEFAULTS.items():
            current_value = getattr(site, field_name, "")
            if isinstance(current_value, str) and not current_value.strip():
                setattr(site, field_name, default_value)
                changed_fields.append(field_name)

        if changed_fields:
            site.save(update_fields=[*changed_fields, "updated_at"])
            self.stdout.write(
                self.style.SUCCESS(
                    f"Updated SiteSettings defaults for: {', '.join(changed_fields)}"
                )
            )
            return

        self.stdout.write("SiteSettings defaults already in sync.")
