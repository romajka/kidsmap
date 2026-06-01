from catalog.models.user import SiteRegisteredUser, StaffAccessUser, UserEmailVerification
from catalog.models.owner import OwnerTeamMembership

class UsersSiteRegisteredUser(SiteRegisteredUser):
    class Meta:
        proxy = True
        app_label = 'catalog_users'
        verbose_name = 'Пользователи сайта'
        verbose_name_plural = 'Пользователи сайта'

class UsersStaffAccessUser(StaffAccessUser):
    class Meta:
        proxy = True
        app_label = 'catalog_users'
        verbose_name = 'Сотрудники админки'
        verbose_name_plural = 'Сотрудники админки'

class UsersEmailVerification(UserEmailVerification):
    class Meta:
        proxy = True
        app_label = 'catalog_users'
        verbose_name = 'Подтверждения E-mail'
        verbose_name_plural = 'Подтверждения E-mail'

class UsersOwnerTeamMembership(OwnerTeamMembership):
    class Meta:
        proxy = True
        app_label = 'catalog_users'
        verbose_name = 'Представители мест'
        verbose_name_plural = 'Представители мест'
