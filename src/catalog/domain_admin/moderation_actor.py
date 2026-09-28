class ModerationActorAdminMixin:
    """Attribute decisions made through ordinary admin change forms."""
    def save_model(self, request, obj, form, change):
        old_status = type(obj).objects.filter(pk=obj.pk).values_list('status', flat=True).first() if obj.pk else None
        if old_status != obj.status:
            obj.moderated_by = request.user if obj.status in {'approved', 'rejected', 'published', 'needs_changes'} else None
        super().save_model(request, obj, form, change)
