import re
import uuid
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Avg, Count, Q
from django.db.models.signals import post_delete, post_save
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language, override
from django.utils.text import slugify
from django.urls import reverse
from django.utils import timezone
from django.dispatch import receiver

from .place import Place


def _get_solo_site_settings():
    obj = SiteSettings.objects.order_by("id").first()
    if obj:
        return obj
    return SiteSettings.objects.create(
        brand_name="KidsMap",
        contacts_text_ru="Свяжитесь с нами по почте: kidsmap.az@gmail.com",
        contacts_text_en="Contact us by email: kidsmap.az@gmail.com",
        contacts_text_az="Bizimlə e-poçt vasitəsilə əlaqə saxlayın: kidsmap.az@gmail.com",
        about_text_ru="KidsMap — каталог детских кружков и секций по Азербайджану.",
        about_text_en="KidsMap is a catalog of kids clubs and courses across Azerbaijan.",
        about_text_az="KidsMap Azərbaycanda uşaqlar üçün dərnək və kurs kataloqudur.",
        home_title_ru="Найдите подходящее занятие для ребёнка",
        home_title_en="Find the right activity for your child",
        home_title_az="Uşağınız üçün uyğun məşğələni tapın",
        home_subtitle_ru="Кружки, курсы и события рядом — всё в одном месте.",
        home_subtitle_en="Nearby clubs, classes and events — all in one place.",
        home_subtitle_az="Yaxınlıqdakı dərnək, kurs və tədbirlər — hamısı bir yerdə.",
        home_search_label_ru="Найти занятие",
        home_search_label_en="Find activities",
        home_search_label_az="Məşğələ tap",
        home_search_placeholder_ru="например шахматы, футбол, рисование",
        home_search_placeholder_en="for example chess, football, drawing",
        home_search_placeholder_az="məsələn şahmat, futbol, rəsm",
        home_cta_text_ru="Начать поиск",
        home_cta_text_en="Start searching",
        home_cta_text_az="Axtarışa başla",
        empty_results_text_ru="Ничего не найдено.",
        empty_results_text_en="Nothing found.",
        empty_results_text_az="Heç nə tapılmadı.",
        footer_phone="+994 50 540 66 39",
        footer_email="kidsmap.az@gmail.com",
        footer_instagram="https://www.instagram.com/kidsmap.az/",
        footer_telegram="https://t.me/KidsMap_az",
        footer_youtube="https://www.youtube.com/@KidsMap_az",
        footer_tiktok="https://www.tiktok.com/@kidsmap.az?lang=ru-RU",
        footer_facebook="https://www.facebook.com/people/KidsMap/61583913364027/",
        footer_linkedin="https://www.linkedin.com/company/kidsmap-az/",
    )


def _get_solo_catalog_content_settings():
    obj = CatalogContentSettings.objects.order_by("id").first()
    if obj:
        return obj
    return CatalogContentSettings.objects.create()


def clear_singleton_caches() -> None:
    if hasattr(_get_solo_site_settings, "cache_clear"):
        _get_solo_site_settings.cache_clear()
    if hasattr(_get_solo_catalog_content_settings, "cache_clear"):
        _get_solo_catalog_content_settings.cache_clear()


class SiteSettings(models.Model):
    brand_name = models.CharField(_("Название бренда"), max_length=120, default="KidsMap")
    logo = models.FileField(
        _("Логотип"),
        upload_to="site/",
        blank=True,
        null=True,
        help_text=_("Рекомендуется SVG или PNG, размер 256x256 px (минимум 128x128), до 500 KB."),
    )
    site_background_image = models.FileField(
        _("Фон сайта"),
        upload_to="site/",
        blank=True,
        null=True,
        help_text=_("Рекомендуется JPG/WebP 1920x1080 px, до 2 MB."),
    )
    home_hero_image = models.FileField(
        _("Фон главного баннера"),
        upload_to="site/",
        blank=True,
        null=True,
        help_text=_("Рекомендуется JPG/WebP 1600x500 px, до 1 MB."),
    )
    home_map_image = models.FileField(
        _("Фон блока карты"),
        upload_to="site/",
        blank=True,
        null=True,
        help_text=_("Рекомендуется JPG/WebP 1600x600 px, до 1 MB."),
    )
    home_recommended_image = models.FileField(
        _("Фон блока рекомендаций"),
        upload_to="site/",
        blank=True,
        null=True,
        help_text=_("Рекомендуется JPG/WebP 1600x600 px, до 1 MB."),
    )
    home_categories_image = models.FileField(
        _("Фон блока категорий"),
        upload_to="site/",
        blank=True,
        null=True,
        help_text=_("Рекомендуется JPG/WebP 1600x600 px, до 1 MB."),
    )
    home_steps_image = models.FileField(
        _("Фон блока 'Как это работает'"),
        upload_to="site/",
        blank=True,
        null=True,
        help_text=_("Рекомендуется JPG/WebP 1600x600 px, до 1 MB."),
    )
    home_trust_image = models.FileField(
        _("Фон блока преимуществ"),
        upload_to="site/",
        blank=True,
        null=True,
        help_text=_("Рекомендуется JPG/WebP 1600x600 px, до 1 MB."),
    )
    home_cta_image = models.FileField(
        _("Фон нижнего призыва (CTA)"),
        upload_to="site/",
        blank=True,
        null=True,
        help_text=_("Рекомендуется JPG/WebP 1600x500 px, до 1 MB."),
    )
    home_hero_show_decor = models.BooleanField(_("Показывать декор в hero"), default=True)
    home_title_ru = models.CharField(_("Hero заголовок (RU)"), max_length=220, blank=True, default="")
    home_title_en = models.CharField(_("Hero заголовок (EN)"), max_length=220, blank=True, default="")
    home_title_az = models.CharField(_("Hero заголовок (AZ)"), max_length=220, blank=True, default="")
    home_subtitle_ru = models.CharField(_("Hero подзаголовок (RU)"), max_length=260, blank=True, default="")
    home_subtitle_en = models.CharField(_("Hero подзаголовок (EN)"), max_length=260, blank=True, default="")
    home_subtitle_az = models.CharField(_("Hero подзаголовок (AZ)"), max_length=260, blank=True, default="")
    home_search_label_ru = models.CharField(_("Hero подпись поиска (RU)"), max_length=220, blank=True, default="")
    home_search_label_en = models.CharField(_("Hero подпись поиска (EN)"), max_length=220, blank=True, default="")
    home_search_label_az = models.CharField(_("Hero подпись поиска (AZ)"), max_length=220, blank=True, default="")
    home_search_placeholder_ru = models.CharField(_("Hero placeholder поиска (RU)"), max_length=220, blank=True, default="")
    home_search_placeholder_en = models.CharField(_("Hero placeholder поиска (EN)"), max_length=220, blank=True, default="")
    home_search_placeholder_az = models.CharField(_("Hero placeholder поиска (AZ)"), max_length=220, blank=True, default="")
    home_cta_text_ru = models.CharField(_("Hero кнопка (RU)"), max_length=120, blank=True, default="")
    home_cta_text_en = models.CharField(_("Hero кнопка (EN)"), max_length=120, blank=True, default="")
    home_cta_text_az = models.CharField(_("Hero кнопка (AZ)"), max_length=120, blank=True, default="")
    contacts_text_ru = models.TextField(_("Контакты (RU)"), blank=True, default="")
    contacts_text_en = models.TextField(_("Контакты (EN)"), blank=True, default="")
    contacts_text_az = models.TextField(_("Контакты (AZ)"), blank=True, default="")
    about_text_ru = models.TextField(_("О проекте (RU)"), blank=True, default="")
    about_text_en = models.TextField(_("О проекте (EN)"), blank=True, default="")
    about_text_az = models.TextField(_("О проекте (AZ)"), blank=True, default="")
    empty_results_text_ru = models.CharField(_("Текст пустого результата (RU)"), max_length=255, blank=True, default="")
    empty_results_text_en = models.CharField(_("Текст пустого результата (EN)"), max_length=255, blank=True, default="")
    empty_results_text_az = models.CharField(_("Текст пустого результата (AZ)"), max_length=255, blank=True, default="")
    empty_results_image = models.FileField(
        _("Картинка пустого результата"),
        upload_to="site/",
        blank=True,
        null=True,
        help_text=_("Рекомендуется PNG/WebP 600x400 px, до 500 KB."),
    )
    catalog_hero_image = models.FileField(
        _("Баннер каталога"),
        upload_to="site/",
        blank=True,
        null=True,
        help_text=_("Рекомендуется JPG/WebP 1600x500 px, до 1 MB. Используется в каталоге."),
    )
    about_hero_image = models.FileField(
        _("Баннер страницы 'О проекте'"),
        upload_to="site/",
        blank=True,
        null=True,
        help_text=_("Рекомендуется JPG/WebP 1600x500 px, до 1 MB. Используется на странице О проекте."),
    )
    reviews_hero_image = models.FileField(
        _("Баннер страницы отзывов"),
        upload_to="site/",
        blank=True,
        null=True,
        help_text=_("Рекомендуется JPG/WebP 1600x500 px, до 1 MB. Используется на странице отзывов."),
    )
    for_business_hero_image = models.FileField(
        _("Баннер страницы владельцам"),
        upload_to="site/",
        blank=True,
        null=True,
        help_text=_("Рекомендуется JPG/WebP 1600x500 px, до 1 MB. Используется на странице владельцев."),
    )
    dashboard_hero_image = models.FileField(
        _("Баннер личного кабинета"),
        upload_to="site/",
        blank=True,
        null=True,
        help_text=_("Рекомендуется JPG/WebP 1600x500 px, до 1 MB. Используется в личном кабинете."),
    )
    specialists_section_enabled = models.BooleanField(
        _("Показывать раздел «Педагоги и специалисты»"),
        default=True,
        help_text=_("Скрывает публичный каталог, ссылки в навигации и owner-формы. Данные и админка специалистов сохраняются."),
    )
    events_section_enabled = models.BooleanField(
        _("Показывать раздел «Временные мероприятия»"),
        default=True,
        help_text=_("Скрывает афишу, временные карточки, ссылки в навигации и owner-формы. Данные и админка мероприятий сохраняются."),
    )
    footer_phone = models.CharField(_("Телефон в футере"), max_length=60, blank=True, default="")
    footer_email = models.EmailField(_("Email в футере"), blank=True, default="")
    footer_instagram = models.CharField(_("Instagram в футере"), max_length=255, blank=True, default="")
    footer_telegram = models.URLField(_("Telegram в футере"), blank=True, default="")
    footer_youtube = models.URLField(_("YouTube в футере"), blank=True, default="")
    footer_tiktok = models.URLField(_("TikTok в футере"), blank=True, default="")
    footer_facebook = models.URLField(_("Facebook в футере"), blank=True, default="")
    footer_linkedin = models.URLField(_("LinkedIn в футере"), blank=True, default="")
    footer_whatsapp = models.CharField(_("WhatsApp ссылка в футере"), max_length=255, blank=True, default="")
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    def _normalize_lang(self, lang):
        if not lang:
            lang = get_language() or settings.LANGUAGE_CODE or "az"
        return lang.split("-")[0]

    def _i18n_text(self, prefix, lang):
        lang = self._normalize_lang(lang)
        return (getattr(self, f"{prefix}_{lang}", "") or "").strip()

    def contacts_text_i18n(self, lang=None):
        return self._i18n_text("contacts_text", lang)

    def about_text_i18n(self, lang=None):
        return self._i18n_text("about_text", lang)

    def empty_results_text_i18n(self, lang=None):
        return self._i18n_text("empty_results_text", lang)

    def home_title_i18n(self, lang=None):
        return self._i18n_text("home_title", lang)

    def home_subtitle_i18n(self, lang=None):
        return self._i18n_text("home_subtitle", lang)

    def home_search_label_i18n(self, lang=None):
        return self._i18n_text("home_search_label", lang)

    def home_search_placeholder_i18n(self, lang=None):
        return self._i18n_text("home_search_placeholder", lang)

    def home_cta_text_i18n(self, lang=None):
        return self._i18n_text("home_cta_text", lang)

    def footer_instagram_url(self):
        value = (self.footer_instagram or "").strip()
        if not value:
            return ""
        if value.startswith(("http://", "https://")):
            return value
        if value.startswith(("instagram.com/", "www.instagram.com/")):
            return f"https://{value}"
        if "instagram.com/" in value:
            return f"https://{value.lstrip('/')}"
        return f"https://instagram.com/{value.lstrip('@')}"

    @staticmethod
    def _footer_external_url(value):
        return (value or "").strip()

    def footer_telegram_url(self):
        return self._footer_external_url(self.footer_telegram)

    def footer_youtube_url(self):
        return self._footer_external_url(self.footer_youtube)

    def footer_tiktok_url(self):
        return self._footer_external_url(self.footer_tiktok)

    def footer_facebook_url(self):
        return self._footer_external_url(self.footer_facebook)

    def footer_linkedin_url(self):
        return self._footer_external_url(self.footer_linkedin)

    @classmethod
    def get_solo(cls):
        return _get_solo_site_settings()

    def save(self, *args, **kwargs):
        result = super().save(*args, **kwargs)
        # Admin sections use proxy models, whose saves do not emit a
        # post_save signal with SiteSettings as the sender.
        clear_singleton_caches()
        return result

    def delete(self, *args, **kwargs):
        result = super().delete(*args, **kwargs)
        clear_singleton_caches()
        return result

    class Meta:
        verbose_name = _("Настройка сайта")
        verbose_name_plural = _("Настройка сайта")

    def __str__(self):
        return self.brand_name or "Site settings"


class SiteGalleryImage(models.Model):
    PLACEMENT_HOME_HERO = "HOME_HERO"
    PLACEMENT_HOME_PARTNERS = "HOME_PARTNERS"

    PLACEMENT_CHOICES = (
        (PLACEMENT_HOME_HERO, _("Главная: hero-слайдер")),
        (PLACEMENT_HOME_PARTNERS, _("Главная: партнёры")),
    )

    placement = models.CharField(
        _("Где показывать"),
        max_length=32,
        choices=PLACEMENT_CHOICES,
        default=PLACEMENT_HOME_HERO,
        db_index=True,
    )
    image = models.FileField(
        _("Изображение"),
        upload_to="site/gallery/",
        help_text=_("Загрузите JPG/WebP/PNG. Для hero лучше 1200x900 или 900x1200, до 2 MB."),
    )
    category = models.CharField(
        _("Категория"),
        max_length=50,
        choices=Place.CATEGORY_CHOICES,
        blank=True,
        default="",
        help_text=_("Нужно для подписи фото в hero или будущих подборок."),
    )
    title_ru = models.CharField(_("Подпись (RU)"), max_length=120, blank=True, default="")
    title_en = models.CharField(_("Подпись (EN)"), max_length=120, blank=True, default="")
    title_az = models.CharField(_("Подпись (AZ)"), max_length=120, blank=True, default="")
    order = models.PositiveIntegerField(_("Порядок"), default=0, db_index=True)
    is_active = models.BooleanField(_("Показывать"), default=True, db_index=True)
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    def _normalize_lang(self, lang):
        if not lang:
            lang = get_language() or settings.LANGUAGE_CODE or "az"
        return lang.split("-")[0]

    def title_i18n(self, lang=None):
        lang = self._normalize_lang(lang)
        title = (getattr(self, f"title_{lang}", "") or "").strip()
        if title:
            return title
        with override(lang):
            return str(self.get_category_display()).strip()

    class Meta:
        ordering = ("placement", "order", "id")
        verbose_name = _("Фото для блоков сайта")
        verbose_name_plural = _("Фото для блоков сайта")

    def __str__(self):
        return f"{self.get_placement_display()} · {self.title_i18n() or self.pk}"


class SiteBrandingSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = _("Лого и бренд")
        verbose_name_plural = _("Лого и бренд")


class SiteAboutSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = _("О проекте")
        verbose_name_plural = _("О проекте")


class SiteContactsSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = _("Контакты")
        verbose_name_plural = _("Контакты")


class SiteFooterSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = _("Футер и соцсети")
        verbose_name_plural = _("Футер и соцсети")


class SiteEmptyStateSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = _("Пустой результат")
        verbose_name_plural = _("Пустой результат")


class SiteVisibilitySettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = _("Разделы сайта")
        verbose_name_plural = _("Разделы сайта")


class SiteAnalytics(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = _("Статистика")
        verbose_name_plural = _("Статистика")


class SiteVisit(models.Model):
    day = models.DateField(_("День"), db_index=True)
    session_key = models.CharField(_("Сессия"), max_length=64, db_index=True)
    hits = models.PositiveIntegerField(_("Просмотры"), default=1)
    first_path = models.CharField(_("Первый путь"), max_length=255, blank=True, default="")
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    class Meta:
        verbose_name = _("Посещение")
        verbose_name_plural = _("Посещения")
        constraints = [
            models.UniqueConstraint(
                fields=("day", "session_key"),
                name="unique_site_visit_per_day_session",
            ),
        ]
        ordering = ("-day", "-hits")

    def __str__(self):
        return f"{self.day} / {self.session_key} / {self.hits}"

    @classmethod
    def today(cls):
        return timezone.localdate()


class FunnelEvent(models.Model):
    EVENT_CATALOG_SEARCH = "catalog_search"
    EVENT_CATALOG_FILTER = "catalog_filter"
    EVENT_PLACE_OPEN = "place_open"
    EVENT_CTA_CALL = "cta_call"
    EVENT_CTA_WHATSAPP = "cta_whatsapp"
    EVENT_CTA_INSTAGRAM = "cta_instagram"
    EVENT_FAVORITE_TOGGLE = "favorite_toggle"
    EVENT_REVIEW_SUBMIT = "review_submit"
    EVENT_CLAIM_PLACE_START = "claim_place_start"
    EVENT_CLAIM_PLACE_SUBMIT = "claim_place_submit"
    EVENT_OWNER_SIGNUP_START = "owner_signup_start"
    EVENT_OWNER_SIGNUP_COMPLETE = "owner_signup_complete"
    EVENT_AI_REFERRAL_VISIT = "ai_referral_visit"

    EVENT_CHOICES = (
        (EVENT_CATALOG_SEARCH, _("Поиск в каталоге")),
        (EVENT_CATALOG_FILTER, _("Применение фильтров")),
        (EVENT_PLACE_OPEN, _("Открытие карточки")),
        (EVENT_CTA_CALL, _("Клик: Позвонить")),
        (EVENT_CTA_WHATSAPP, _("Клик: WhatsApp")),
        (EVENT_CTA_INSTAGRAM, _("Клик: Instagram")),
        (EVENT_FAVORITE_TOGGLE, _("Добавление в избранное")),
        (EVENT_REVIEW_SUBMIT, _("Отправка отзыва")),
        (EVENT_CLAIM_PLACE_START, _("Начало заявки на управление")),
        (EVENT_CLAIM_PLACE_SUBMIT, _("Отправка заявки на управление")),
        (EVENT_OWNER_SIGNUP_START, _("Начало регистрации владельца")),
        (EVENT_OWNER_SIGNUP_COMPLETE, _("Завершение регистрации владельца")),
        (EVENT_AI_REFERRAL_VISIT, _("Переход из AI-сервиса")),
    )

    event_type = models.CharField(_("Событие"), max_length=32, choices=EVENT_CHOICES, db_index=True)
    day = models.DateField(_("День"), default=timezone.localdate, db_index=True)
    path = models.CharField(_("Путь"), max_length=255, blank=True, default="")
    place = models.ForeignKey(
        Place,
        on_delete=models.SET_NULL,
        related_name="funnel_events",
        verbose_name=_("Кружок/курс"),
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="funnel_events",
        verbose_name=_("Пользователь"),
        null=True,
        blank=True,
    )
    session_key = models.CharField(_("Сессия"), max_length=64, blank=True, default="", db_index=True)
    event_meta = models.JSONField(_("Данные"), default=dict, blank=True)
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _("Событие воронки")
        verbose_name_plural = _("События воронки")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("day", "event_type")),
            models.Index(fields=("event_type", "created_at")),
        ]

    def __str__(self):
        return f"{self.day} / {self.event_type}"


class CatalogContentSettings(models.Model):
    districts_json = models.JSONField(_("Регионы / районы (JSON)"), default=list, blank=True)
    metro_stations_json = models.JSONField(_("Станции метро (JSON)"), default=list, blank=True)
    seo_pages_json = models.JSONField(_("SEO страницы (JSON)"), default=dict, blank=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    @classmethod
    def get_solo(cls):
        return _get_solo_catalog_content_settings()

    def districts(self):
        raw_list = self.districts_json
        if not raw_list:
            from catalog.services.locations import get_all_districts_flat_choices
            return [k for k, _ in get_all_districts_flat_choices()]

        flat_keys = []
        for item in raw_list:
            if isinstance(item, dict):
                key = item.get("key")
                if key:
                    flat_keys.append(key)
                for sub in item.get("districts") or []:
                    if isinstance(sub, dict):
                        sub_key = sub.get("key")
                        if sub_key:
                            flat_keys.append(sub_key)
                    elif isinstance(sub, str):
                        flat_keys.append(sub)
            elif isinstance(item, str):
                flat_keys.append(item)
        return flat_keys

    def metro_stations(self):
        if isinstance(self.metro_stations_json, list) and self.metro_stations_json:
            return self.metro_stations_json
        from catalog.content_data import BAKU_METRO_STATIONS

        return BAKU_METRO_STATIONS

    def seo_pages(self, language_code=None):
        from catalog.content_data import seo_landing_pages
        from django.utils.translation import get_language

        language_code = (language_code or get_language() or "az").split("-")[0]
        if isinstance(self.seo_pages_json, dict) and self.seo_pages_json:
            localized_pages = self.seo_pages_json.get(language_code)
            if isinstance(localized_pages, dict):
                return localized_pages
            if language_code == "az" and not any(
                key in self.seo_pages_json for key in {"az", "ru", "en"}
            ):
                return self.seo_pages_json
        return seo_landing_pages(language_code)

    class Meta:
        verbose_name = _("Контент каталога")
        verbose_name_plural = _("Контент каталога")

    def __str__(self):
        return _("Контент каталога")


@receiver(post_save, sender=SiteSettings)
@receiver(post_delete, sender=SiteSettings)
def _clear_site_settings_cache(*_args, **_kwargs) -> None:
    clear_singleton_caches()


@receiver(post_save, sender=CatalogContentSettings)
@receiver(post_delete, sender=CatalogContentSettings)
def _clear_catalog_content_settings_cache(*_args, **_kwargs) -> None:
    clear_singleton_caches()
