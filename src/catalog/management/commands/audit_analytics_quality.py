from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Count, Q, Sum

from catalog.models import AnalyticsActorExclusion, AnalyticsIngressDaily, FunnelEvent, Place, PlaceLike
from catalog.services.favorite_metrics import eligible_favorites_queryset


class Command(BaseCommand):
    help = "Print aggregate-only analytics quality indicators."

    def handle(self, *args, **options):
        v2 = FunnelEvent.objects.filter(schema_version=2)
        unknown_subjects = v2.filter(~Q(subject_type="place") | Q(subject_id__isnull=True)).count()
        empty_identity = v2.filter(Q(visitor_key_hash="") | Q(session_key_hash="")).count()
        place_ids = list(Place.objects.values_list("pk", flat=True))
        eligible_by_place = dict(
            eligible_favorites_queryset(place_ids=place_ids)
            .values("place_id").annotate(total=Count("user_id", distinct=True))
            .values_list("place_id", "total")
        )
        drift = sum(1 for pk, cached in Place.objects.values_list("pk", "likes_count") if cached != eligible_by_place.get(pk, 0))
        excluded_favorite_rows = max(PlaceLike.objects.count() - sum(eligible_by_place.values()), 0)
        ingress = AnalyticsIngressDaily.objects.aggregate(
            accepted=Sum("accepted_count"),
            rejected=Sum("rejected_count"),
            rate_limited=Sum("rate_limited_count"),
        )
        self.stdout.write(
            " ".join([
                f"accepted_events={int(ingress['accepted'] or 0)}", f"rejected_events={int(ingress['rejected'] or 0)}",
                f"unknown_subjects={unknown_subjects}", f"empty_identity_hashes={empty_identity}",
                f"rate_limited={int(ingress['rate_limited'] or 0)}", f"favorite_cache_drift={drift}",
                f"active_exclusions={AnalyticsActorExclusion.objects.count()}",
                f"excluded_favorite_rows={excluded_favorite_rows}",
                f"collection_enabled={bool(getattr(settings, 'LOCAL_ANALYTICS_STORAGE_ENABLED', False))}",
                f"collection_start_configured={bool(getattr(settings, 'ANALYTICS_COLLECTION_STARTED_AT', ''))}",
            ])
        )
