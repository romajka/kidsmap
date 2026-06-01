from catalog.models.site import (
    SiteSettings, SiteBrandingSettings, SiteAboutSettings, 
    SiteContactsSettings, SiteFooterSettings, SiteEmptyStateSettings,
    SiteAnalytics
)
from catalog.models.owner import PlaceChangeAudit, PlaceOwnershipRequestAudit

class SystemSiteSettings(SiteSettings):
    class Meta:
        proxy = True
        app_label = 'catalog_system'
        verbose_name = 'Настройки сайта'
        verbose_name_plural = 'Настройки сайта'

class SystemSiteBranding(SiteBrandingSettings):
    class Meta:
        proxy = True
        app_label = 'catalog_system'
        verbose_name = 'Брендинг'
        verbose_name_plural = 'Брендинг'

class SystemSiteAbout(SiteAboutSettings):
    class Meta:
        proxy = True
        app_label = 'catalog_system'
        verbose_name = 'О нас'
        verbose_name_plural = 'О нас'

class SystemSiteContacts(SiteContactsSettings):
    class Meta:
        proxy = True
        app_label = 'catalog_system'
        verbose_name = 'Контакты'
        verbose_name_plural = 'Контакты'

class SystemSiteFooter(SiteFooterSettings):
    class Meta:
        proxy = True
        app_label = 'catalog_system'
        verbose_name = 'Подвал сайта'
        verbose_name_plural = 'Подвал сайта'

class SystemSiteEmptyState(SiteEmptyStateSettings):
    class Meta:
        proxy = True
        app_label = 'catalog_system'
        verbose_name = 'Пустые состояния'
        verbose_name_plural = 'Пустые состояния'

class SystemSiteAnalytics(SiteAnalytics):
    class Meta:
        proxy = True
        app_label = 'catalog_system'
        verbose_name = 'Аналитика (настройки)'
        verbose_name_plural = 'Аналитика (настройки)'

class SystemPlaceChangeAudit(PlaceChangeAudit):
    class Meta:
        proxy = True
        app_label = 'catalog_system'
        verbose_name = 'История изменений мест'
        verbose_name_plural = 'История изменений мест'

class SystemPlaceOwnershipRequestAudit(PlaceOwnershipRequestAudit):
    class Meta:
        proxy = True
        app_label = 'catalog_system'
        verbose_name = 'Логи заявок владельцев'
        verbose_name_plural = 'Логи заявок владельцев'
