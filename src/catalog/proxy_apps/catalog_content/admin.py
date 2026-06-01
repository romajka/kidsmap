from django.contrib import admin
from catalog.domain_admin.site import CatalogContentSettingsAdmin, SiteGalleryImageAdmin
from catalog.domain_admin.review import SiteReviewAdmin

from catalog.models.site import CatalogContentSettings, SiteGalleryImage
from catalog.models.review import SiteReview

from .models import (
    ContentCatalogSettings,
    ContentSiteGallery,
    ContentSiteReview
)

try:
    admin.site.unregister(CatalogContentSettings)
    admin.site.unregister(SiteGalleryImage)
    admin.site.unregister(SiteReview)
except admin.sites.NotRegistered:
    pass

admin.site.register(ContentCatalogSettings, CatalogContentSettingsAdmin)
admin.site.register(ContentSiteGallery, SiteGalleryImageAdmin)
admin.site.register(ContentSiteReview, SiteReviewAdmin)
