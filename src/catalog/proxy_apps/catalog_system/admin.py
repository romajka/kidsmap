from django.contrib import admin

from catalog.domain_admin.site import (
    SiteSettingsCompatAdmin, SiteBrandingSettingsAdmin, SiteAboutSettingsAdmin,
    SiteContactsSettingsAdmin, SiteFooterSettingsAdmin, SiteEmptyStateSettingsAdmin,
    SiteAnalyticsAdmin
)
from catalog.domain_admin.owner import PlaceChangeAuditAdmin, PlaceOwnershipRequestAuditAdmin

from catalog.models.site import (
    SiteSettings, SiteBrandingSettings, SiteAboutSettings, 
    SiteContactsSettings, SiteFooterSettings, SiteEmptyStateSettings,
    SiteAnalytics
)
from catalog.models.owner import PlaceChangeAudit, PlaceOwnershipRequestAudit

from .models import (
    SystemSiteSettings, SystemSiteBranding, SystemSiteAbout, 
    SystemSiteContacts, SystemSiteFooter, SystemSiteEmptyState,
    SystemSiteAnalytics,
    SystemPlaceChangeAudit, SystemPlaceOwnershipRequestAudit
)

try:
    admin.site.unregister(SiteSettings)
    admin.site.unregister(SiteBrandingSettings)
    admin.site.unregister(SiteAboutSettings)
    admin.site.unregister(SiteContactsSettings)
    admin.site.unregister(SiteFooterSettings)
    admin.site.unregister(SiteEmptyStateSettings)
    admin.site.unregister(SiteAnalytics)
    admin.site.unregister(PlaceChangeAudit)
    admin.site.unregister(PlaceOwnershipRequestAudit)
except admin.sites.NotRegistered:
    pass

admin.site.register(SystemSiteSettings, SiteSettingsCompatAdmin)
admin.site.register(SystemSiteBranding, SiteBrandingSettingsAdmin)
admin.site.register(SystemSiteAbout, SiteAboutSettingsAdmin)
admin.site.register(SystemSiteContacts, SiteContactsSettingsAdmin)
admin.site.register(SystemSiteFooter, SiteFooterSettingsAdmin)
admin.site.register(SystemSiteEmptyState, SiteEmptyStateSettingsAdmin)
admin.site.register(SystemSiteAnalytics, SiteAnalyticsAdmin)
admin.site.register(SystemPlaceChangeAudit, PlaceChangeAuditAdmin)
admin.site.register(SystemPlaceOwnershipRequestAudit, PlaceOwnershipRequestAuditAdmin)
