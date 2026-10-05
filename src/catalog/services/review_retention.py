"""Apply the existing account-deletion policy to all explicit review versions."""
from django.db.models import Q
from catalog.services.review_versions import review_types


def dispose_typed_reviews(*, user_id, disposition):
    deleted = anonymized = 0
    for kind, (targets, heads, revisions, reactions) in review_types().items():
        voted_ids = set(reactions.objects.filter(user_id=user_id).values_list('review_id', flat=True))
        reactions.objects.filter(user_id=user_id).delete()
        # Moderation actors are not the review author; remove their FK everywhere.
        revisions.objects.filter(moderated_by_id=user_id).update(moderated_by=None)
        authored = heads.objects.filter(user_id=user_id)
        target_ids = set(authored.values_list(kind + '_id', flat=True))
        if disposition == 'delete_all':
            deleted += authored.count()
            authored.delete()
        else:
            approved = authored.filter(status='approved', is_approved=True)
            ids = list(approved.values_list('pk', flat=True))
            revisions.objects.filter(review_id__in=ids, status='approved').update(author_name='', is_anonymous=True)
            heads.objects.filter(pk__in=ids).update(candidate_revision=None)
            revisions.objects.filter(review_id__in=ids).exclude(status='approved').delete()
            anonymized += heads.objects.filter(pk__in=ids).update(user=None, author_name='', is_anonymous=True, session_key='')
            deleted += authored.count()
            authored.delete()
        for target in targets.objects.filter(pk__in=target_ids):
            if hasattr(target, 'refresh_rating_stats'):
                target.refresh_rating_stats()
        from catalog.services.review_versions import refresh_reactions
        for voted_head in heads.objects.filter(pk__in=voted_ids):
            refresh_reactions(voted_head)
    return deleted, anonymized
