from django.contrib import admin
from catalog.domain_admin.user import SiteRegisteredUserAdmin, StaffAccessUserAdmin, UserEmailVerificationAdmin
from catalog.domain_admin.owner import OwnerTeamMembershipAdmin

from catalog.models.user import SiteRegisteredUser, StaffAccessUser, UserEmailVerification
from catalog.models.owner import OwnerTeamMembership

from .models import (
    UsersSiteRegisteredUser,
    UsersStaffAccessUser,
    UsersEmailVerification,
    UsersOwnerTeamMembership
)

try:
    admin.site.unregister(SiteRegisteredUser)
    admin.site.unregister(StaffAccessUser)
    admin.site.unregister(UserEmailVerification)
    admin.site.unregister(OwnerTeamMembership)
except admin.sites.NotRegistered:
    pass

admin.site.register(UsersSiteRegisteredUser, SiteRegisteredUserAdmin)
admin.site.register(UsersStaffAccessUser, StaffAccessUserAdmin)
admin.site.register(UsersEmailVerification, UserEmailVerificationAdmin)
admin.site.register(UsersOwnerTeamMembership, OwnerTeamMembershipAdmin)
