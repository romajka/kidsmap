"""Explicit typed review histories; shared fields do not mix target identities."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class VersionedReview(models.Model):
    is_current = models.BooleanField(default=True, db_index=True)
    archive_head = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='legacy_sources')

    class Meta:
        abstract = True


class ReviewRevision(models.Model):
    author_name = models.CharField(max_length=80, blank=True)
    is_anonymous = models.BooleanField(default=False)
    rating = models.PositiveSmallIntegerField()
    text = models.TextField()
    contains_profanity = models.BooleanField(default=False)
    status = models.CharField(max_length=16, default='pending', choices=[('pending', _('На модерации')), ('approved', _('Одобрен')), ('rejected', _('Отклонен'))])
    submitted_at = models.DateTimeField(null=True, blank=True)
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_baseline = models.BooleanField(default=False)
    source_is_approved = models.BooleanField(null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ('created_at', 'pk')
        constraints = [
            models.CheckConstraint(condition=Q(is_baseline=True) | Q(rating__gte=1, rating__lte=5), name='%(class)s_rating_range'),
            models.UniqueConstraint(fields=['review'], condition=Q(is_baseline=True), name='%(class)s_one_baseline'),
        ]


class PlaceReviewRevision(ReviewRevision):
    review = models.ForeignKey('catalog.PlaceReview', on_delete=models.CASCADE, related_name='revisions')


class SpecialistReviewRevision(ReviewRevision):
    review = models.ForeignKey('catalog.SpecialistReview', on_delete=models.CASCADE, related_name='revisions')


class ActivityReviewRevision(ReviewRevision):
    review = models.ForeignKey('catalog.ActivityReview', on_delete=models.CASCADE, related_name='revisions')


class EventReviewRevision(ReviewRevision):
    review = models.ForeignKey('catalog.EventReview', on_delete=models.CASCADE, related_name='revisions')


class NewTargetReview(VersionedReview):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='%(class)ss')
    author_name = models.CharField(max_length=80, blank=True)
    is_anonymous = models.BooleanField(default=False)
    rating = models.PositiveSmallIntegerField(default=5)
    text = models.TextField()
    contains_profanity = models.BooleanField(default=False)
    likes_count = models.PositiveIntegerField(default=0)
    dislikes_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=16, default='pending', choices=ReviewRevision._meta.get_field('status').choices, db_index=True)
    is_approved = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    rejection_reason = models.TextField(blank=True)
    session_key = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ('-created_at',)

    def save(self, *args, **kwargs):
        self.is_approved = self.status == 'approved'
        from catalog.services.review_versions import save_legacy_source
        save_legacy_source(self, lambda: super(NewTargetReview, self).save(*args, **kwargs))

    @property
    def author_name_i18n(self):
        return str(_('Аноним')) if self.is_anonymous else self.author_name or str(_('Гость'))

    @property
    def text_i18n(self):
        return self.text


class ActivityReview(NewTargetReview):
    current_revision = models.ForeignKey(ActivityReviewRevision, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    candidate_revision = models.ForeignKey(ActivityReviewRevision, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    activity = models.ForeignKey('catalog.Activity', on_delete=models.CASCADE, related_name='reviews')
    class Meta(NewTargetReview.Meta):
        constraints = [models.UniqueConstraint(fields=['activity', 'user'], condition=Q(is_current=True, user__isnull=False), name='activityreview_current_user')]


class EventReview(NewTargetReview):
    current_revision = models.ForeignKey(EventReviewRevision, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    candidate_revision = models.ForeignKey(EventReviewRevision, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    event = models.ForeignKey('catalog.Event', on_delete=models.CASCADE, related_name='reviews')
    class Meta(NewTargetReview.Meta):
        constraints = [models.UniqueConstraint(fields=['event', 'user'], condition=Q(is_current=True, user__isnull=False), name='eventreview_current_user')]


class TypedReaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name='+')
    session_key = models.CharField(max_length=64, blank=True)
    value = models.SmallIntegerField(choices=[(1, _('Лайк')), (-1, _('Дизлайк'))])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(fields=['revision', 'user'], condition=Q(user__isnull=False), name='%(class)s_user'),
            models.UniqueConstraint(fields=['revision', 'session_key'], condition=Q(user__isnull=True) & ~Q(session_key=''), name='%(class)s_session'),
            models.CheckConstraint(condition=Q(value__in=[-1, 1]), name='%(class)s_value'),
        ]

    def clean(self):
        if self.revision_id and self.revision.review_id != self.review_id:
            raise ValidationError('Reaction revision belongs to another review.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class SpecialistReviewReaction(TypedReaction):
    review = models.ForeignKey('catalog.SpecialistReview', on_delete=models.CASCADE, related_name='reactions')
    revision = models.ForeignKey(SpecialistReviewRevision, on_delete=models.CASCADE, related_name='reactions')


class ActivityReviewReaction(TypedReaction):
    review = models.ForeignKey(ActivityReview, on_delete=models.CASCADE, related_name='reactions')
    revision = models.ForeignKey(ActivityReviewRevision, on_delete=models.CASCADE, related_name='reactions')


class EventReviewReaction(TypedReaction):
    review = models.ForeignKey(EventReview, on_delete=models.CASCADE, related_name='reactions')
    revision = models.ForeignKey(EventReviewRevision, on_delete=models.CASCADE, related_name='reactions')


class ReviewResponse(models.Model):
    """Business reply is public; report is private to KidsMap reviewers."""
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='+')
    kind = models.CharField(max_length=8, choices=[('reply', 'Reply'), ('report', 'Report')])
    text = models.TextField(max_length=5000)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        abstract = True
        ordering = ('created_at', 'pk')


class PlaceReviewResponse(ReviewResponse):
    revision = models.ForeignKey(PlaceReviewRevision, on_delete=models.CASCADE, related_name='responses')


class SpecialistReviewResponse(ReviewResponse):
    revision = models.ForeignKey(SpecialistReviewRevision, on_delete=models.CASCADE, related_name='responses')


class ActivityReviewResponse(ReviewResponse):
    revision = models.ForeignKey(ActivityReviewRevision, on_delete=models.CASCADE, related_name='responses')


class EventReviewResponse(ReviewResponse):
    revision = models.ForeignKey(EventReviewRevision, on_delete=models.CASCADE, related_name='responses')
