from catalog.models.site import CatalogContentSettings, SiteGalleryImage
from catalog.models.review import SiteReview

class ContentCatalogSettings(CatalogContentSettings):
    class Meta:
        proxy = True
        app_label = 'catalog_content'
        verbose_name = 'Блоки главной страницы'
        verbose_name_plural = 'Блоки главной страницы'

class ContentSiteGallery(SiteGalleryImage):
    class Meta:
        proxy = True
        app_label = 'catalog_content'
        verbose_name = 'Фото для блоков сайта'
        verbose_name_plural = 'Фото для блоков сайта'

class ContentSiteReview(SiteReview):
    class Meta:
        proxy = True
        app_label = 'catalog_content'
        verbose_name = 'Отзывы о сервисе'
        verbose_name_plural = 'Отзывы о сервисе'
