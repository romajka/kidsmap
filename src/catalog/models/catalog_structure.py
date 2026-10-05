"""Additive business hierarchy. Publication readers are switched in later stages."""
import uuid

from django.conf import settings
from django.db import models, transaction
from django.db.models import F, Q
from django.db.models.deletion import ProtectedError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class PublicationState(models.TextChoices):
    DRAFT = 'draft', _('Черновик')
    PENDING = 'pending', _('На проверке')
    PUBLISHED = 'published', _('Опубликовано')
    REJECTED = 'rejected', _('Отклонено')


class PlaceNature(models.TextChoices):
    BUSINESS = 'business', _('Бизнес')
    PUBLIC_SPACE = 'public_space', _('Общественное место')


class OperatingState(models.TextChoices):
    OPEN = 'open', _('Открыто')
    CLOSED = 'closed', _('Закрыто')


class RequestState(models.TextChoices):
    PENDING = 'pending', _('На проверке')
    APPROVED = 'approved', _('Одобрено')
    REJECTED = 'rejected', _('Отклонено')
    CANCELED = 'canceled', _('Отменено')


class ArchiveQuerySet(models.QuerySet):
    def delete(self):
        raise ProtectedError('Business/venue records must be archived, not deleted.', [])


class ArchivedEntity(models.Model):
    content_version = models.PositiveBigIntegerField(default=1, editable=False)
    archived_at = models.DateTimeField(null=True, blank=True, db_index=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = ArchiveQuerySet.as_manager()

    class Meta:
        abstract = True
        constraints = [models.CheckConstraint(condition=Q(content_version__gte=1), name='%(class)s_content_positive')]

    def delete(self, *args, **kwargs):
        raise ProtectedError('Business/venue records must be archived, not deleted.', [self])

    def archive(self):
        if self.pk is None:
            raise ValueError('Cannot archive an unsaved record.')
        with transaction.atomic(using=self._state.db):
            now = timezone.now()
            type(self).objects.using(self._state.db).filter(pk=self.pk, archived_at__isnull=True).update(
                archived_at=now, content_version=F('content_version') + 1, updated_at=now)
            self.refresh_from_db()
            if isinstance(self, Activity) and self.status == PublicationState.PUBLISHED and self.offering_groups.filter(pricing_plan_records__isnull=False).exists():
                from catalog.services.pricing_plans import sync_legacy_price_fields
                sync_legacy_price_fields(self.place_id)
            elif isinstance(self, OfferingGroup) and self.activity.status == PublicationState.PUBLISHED and self.pricing_plan_records.exists():
                from catalog.services.pricing_plans import sync_legacy_price_fields
                sync_legacy_price_fields(self.activity.place_id)


class TranslatedContent(ArchivedEntity):
    name_az = models.CharField(max_length=255, blank=True, default='')
    name_ru = models.CharField(max_length=255, blank=True, default='')
    name_en = models.CharField(max_length=255, blank=True, default='')
    description_az = models.TextField(blank=True, default='')
    description_ru = models.TextField(blank=True, default='')
    description_en = models.TextField(blank=True, default='')
    status = models.CharField(max_length=16, choices=PublicationState.choices, default=PublicationState.DRAFT, db_index=True)
    approved_at = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta(ArchivedEntity.Meta):
        abstract = True
        constraints = ArchivedEntity.Meta.constraints + [
            models.CheckConstraint(condition=Q(status__in=PublicationState.values), name='%(class)s_publication_state')]


class Organization(TranslatedContent):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='managed_organizations')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_organizations')
    ownership_version = models.PositiveBigIntegerField(default=1, editable=False)
    ownership_verified_at = models.DateTimeField(null=True, blank=True, editable=False)
    ownership_verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='verified_organizations', editable=False)
    phone = models.CharField(max_length=50, blank=True, default='')
    whatsapp = models.CharField(max_length=50, blank=True, default='')
    website = models.URLField(blank=True, default='')

    class Meta(TranslatedContent.Meta):
        abstract = False
        constraints = TranslatedContent.Meta.constraints + [
            models.CheckConstraint(condition=Q(ownership_version__gte=1), name='organization_ownership_positive')]


    def save(self, *args, **kwargs):
        from catalog.services.organization_ownership import save_organization
        return save_organization(self, *args, **kwargs)


class Program(TranslatedContent):
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name='programs')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_programs')
    category = models.ForeignKey('catalog.Category', null=True, blank=True, on_delete=models.PROTECT, related_name='programs')
    subcategory = models.ForeignKey('catalog.Subcategory', null=True, blank=True, on_delete=models.PROTECT, related_name='programs')

    class Meta(TranslatedContent.Meta):
        abstract = False

    def save(self, *args, **kwargs):
        from catalog.services.catalog_structure import save_program
        return save_program(self, *args, **kwargs)

    def clean(self):
        super().clean()
        from catalog.services.catalog_structure import validate_taxonomy
        validate_taxonomy(self.category_id,self.subcategory_id,using=self._state.db or 'default')


class Activity(ArchivedEntity):
    place = models.ForeignKey('catalog.Place', on_delete=models.PROTECT, related_name='activities')
    program = models.ForeignKey(Program, null=True, blank=True, on_delete=models.PROTECT, related_name='activities')
    category = models.ForeignKey('catalog.Category', null=True, blank=True, on_delete=models.PROTECT, related_name='activities')
    subcategory = models.ForeignKey('catalog.Subcategory', null=True, blank=True, on_delete=models.PROTECT, related_name='activities')
    name_az = models.CharField(max_length=255, blank=True, default='')
    name_ru = models.CharField(max_length=255, blank=True, default='')
    name_en = models.CharField(max_length=255, blank=True, default='')
    description_az = models.TextField(blank=True, default='')
    description_ru = models.TextField(blank=True, default='')
    description_en = models.TextField(blank=True, default='')
    supplement_az = models.TextField(blank=True, default='')
    supplement_ru = models.TextField(blank=True, default='')
    supplement_en = models.TextField(blank=True, default='')
    status = models.CharField(max_length=16, choices=PublicationState.choices, default=PublicationState.DRAFT, db_index=True)
    source_program = models.ForeignKey(Program, null=True, blank=True, on_delete=models.PROTECT, related_name='snapshot_activities')
    source_program_version = models.PositiveBigIntegerField(null=True, blank=True)
    program_snapshot = models.JSONField(default=dict, blank=True)

    class Meta(ArchivedEntity.Meta):
        abstract = False
        constraints = ArchivedEntity.Meta.constraints + [
            models.CheckConstraint(condition=Q(status__in=PublicationState.values), name='activity_publication_state'),
            models.CheckConstraint(condition=(Q(source_program__isnull=True, source_program_version__isnull=True)
                                             | Q(source_program__isnull=False, source_program_version__isnull=False, source_program_version__gte=1)), name='activity_provenance_pair')]

    def save(self, *args, **kwargs):
        from catalog.services.catalog_structure import save_activity
        return save_activity(self, *args, **kwargs)

    def clean(self):
        super().clean()
        from catalog.services.catalog_structure import validate_taxonomy
        validate_taxonomy(self.category_id,self.subcategory_id,using=self._state.db or 'default')


class OfferingGroup(ArchivedEntity):
    activity = models.ForeignKey(Activity, on_delete=models.PROTECT, related_name='offering_groups')
    name_az = models.CharField(max_length=255, blank=True, default='')
    name_ru = models.CharField(max_length=255, blank=True, default='')
    name_en = models.CharField(max_length=255, blank=True, default='')
    age_from = models.PositiveSmallIntegerField(null=True, blank=True)
    age_to = models.PositiveSmallIntegerField(null=True, blank=True)
    lesson_format = models.CharField(max_length=16, choices=[('group', _('Групповой')), ('individual', _('Индивидуальный'))], blank=True, default='')
    language = models.CharField(max_length=100, blank=True, default='')
    schedule_text = models.TextField(blank=True, default='')
    teachers_text = models.TextField(blank=True, default='')
    conditions_az = models.TextField(blank=True, default='')
    conditions_ru = models.TextField(blank=True, default='')
    conditions_en = models.TextField(blank=True, default='')
    conditions_verified_at = models.DateTimeField(null=True, blank=True)

    class Meta(ArchivedEntity.Meta):
        abstract = False
        constraints = ArchivedEntity.Meta.constraints + [
            models.CheckConstraint(condition=Q(age_from__isnull=True) | Q(age_to__isnull=True) | Q(age_from__lte=F('age_to')), name='offering_group_age_order'),
            models.CheckConstraint(condition=Q(lesson_format__in=('', 'group', 'individual')), name='offering_group_format_known')]

    def save(self, *args, **kwargs):
        from catalog.services.pricing_plans import validate_group_plan_ages
        using = kwargs.get('using') or self._state.db or 'default'
        with transaction.atomic(using=using):
            if self.pk:
                previous = type(self).objects.using(using).select_for_update().filter(pk=self.pk).values(
                    'conditions_az', 'conditions_ru', 'conditions_en').first()
                fields = kwargs.get('update_fields')
                changed = previous and any(
                    (fields is None or name in fields) and getattr(self, name) != previous[name]
                    for name in ('conditions_az', 'conditions_ru', 'conditions_en'))
                if changed:
                    self.conditions_verified_at = None
                    if fields is not None:
                        kwargs['update_fields'] = set(fields) | {'conditions_verified_at'}
            validate_group_plan_ages(self, self.age_from, self.age_to)
            return super().save(*args, **kwargs)


class Location(ArchivedEntity):
    """A confirmed physical location; neither an Organization nor a Place owner."""
    name_az = models.CharField(max_length=255, blank=True, default='')
    address = models.CharField(max_length=255, blank=True, default='')
    lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    confirmed_at = models.DateTimeField()
    confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='confirmed_physical_locations')

    class Meta(ArchivedEntity.Meta):
        abstract = False
        constraints = ArchivedEntity.Meta.constraints + [
            models.CheckConstraint(condition=(Q(lat__isnull=True, lng__isnull=True) | Q(lat__isnull=False, lng__isnull=False, lat__gte=-90, lat__lte=90, lng__gte=-180, lng__lte=180)), name='location_coordinates_valid'),
            models.CheckConstraint(condition=~Q(address='') | Q(lat__isnull=False, lng__isnull=False), name='location_physical_identity')]


class RelationshipRequest(models.Model):
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='%(class)s_requests')
    status = models.CharField(max_length=16, choices=RequestState.choices, default=RequestState.PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='%(class)s_decisions')
    note = models.TextField(blank=True, default='')

    class Meta:
        abstract = True
        constraints = [models.CheckConstraint(condition=(Q(status=RequestState.PENDING, decided_at__isnull=True)
                                                       | Q(status__in=(RequestState.APPROVED, RequestState.REJECTED, RequestState.CANCELED), decided_at__isnull=False)), name='%(class)s_decision_pair')]


class OrganizationPlaceRequest(RelationshipRequest):
    place = models.ForeignKey('catalog.Place', on_delete=models.PROTECT, related_name='organization_requests')
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name='place_requests')
    relationship_kind = models.CharField(max_length=16, choices=[('business', _('Бизнес')), ('informational', _('Информационная связь'))], default='business')
    base_place_ownership_version = models.PositiveBigIntegerField(default=1)
    base_organization_ownership_version = models.PositiveBigIntegerField(default=1)
    base_place_content_version = models.PositiveBigIntegerField(default=1)
    base_place_owner_id = models.PositiveBigIntegerField(null=True, blank=True, editable=False)
    base_organization_owner_id = models.PositiveBigIntegerField(null=True, blank=True, editable=False)
    place_owner_confirmed_at = models.DateTimeField(null=True, blank=True)
    organization_owner_confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta(RelationshipRequest.Meta):
        abstract = False
        constraints = RelationshipRequest.Meta.constraints + [
            models.UniqueConstraint(fields=('place', 'organization'), condition=Q(status=RequestState.PENDING), name='organization_place_pending_unique'),
            models.CheckConstraint(condition=Q(relationship_kind__in=('business', 'informational')), name='organization_place_kind_known'),
            models.CheckConstraint(condition=Q(base_place_ownership_version__gte=1, base_organization_ownership_version__gte=1, base_place_content_version__gte=1), name='organization_place_base_positive')]


class PlaceVenueRequest(RelationshipRequest):
    place = models.ForeignKey('catalog.Place', on_delete=models.PROTECT, related_name='venue_requests')
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='place_requests')
    base_place_content_version = models.PositiveBigIntegerField(default=1)
    base_location_content_version = models.PositiveBigIntegerField(default=1)

    class Meta(RelationshipRequest.Meta):
        abstract = False
        constraints = RelationshipRequest.Meta.constraints + [
            models.UniqueConstraint(fields=('place',), condition=Q(status=RequestState.PENDING), name='place_venue_pending_unique'),
            models.CheckConstraint(condition=Q(base_place_content_version__gte=1, base_location_content_version__gte=1), name='place_venue_base_positive')]
