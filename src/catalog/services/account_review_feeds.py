"""Page across place and specialist reviews without loading their entire histories."""
from django.core.paginator import Paginator
from django.db.models import F, Value, OuterRef, Subquery
from django.db.models.functions import Coalesce

from catalog.services.public_review_replies import REVIEW_MODELS


def written_queries(user):
    return {kind: model.objects.filter(user=user, is_current=True) for kind, model in REVIEW_MODELS.items()}


def review_page(queries, page_number=1, *, page_size=12, by_publication=False):
    """Page a combined timeline of small keys, then load only the selected cards."""
    keys = []
    for kind, query in queries.items():
        date = Coalesce("current_revision__moderated_at", "moderated_at", "created_at") if by_publication else F("created_at")
        keys.append(query.order_by().annotate(review_kind=Value(kind), sort_date=date)
                    .values_list("pk", "review_kind", "sort_date"))
    timeline = keys[0].union(*keys[1:], all=True).order_by("-sort_date", "review_kind", "-pk")
    page = Paginator(timeline, page_size).get_page(page_number)
    selected = list(page.object_list)
    cards = {}
    for kind, query in queries.items():
        ids = [pk for pk, review_kind, _ in selected if review_kind == kind]
        if not ids:
            continue
        rows = query.filter(pk__in=ids).select_related(kind, "user__profile")
        if not by_publication:
            revisions = query.model._meta.get_field("current_revision").related_model
            latest = revisions.objects.filter(review_id=OuterRef("pk")).order_by("-created_at", "-pk")
            rows = rows.annotate(latest_status=Subquery(latest.values("status")[:1]),
                                 latest_reason=Subquery(latest.values("rejection_reason")[:1]))
        for row in rows:
            row.review_kind = kind
            row.target = getattr(row, kind)
            row.target_name = row.target.name_i18n() if kind == "place" else row.target.name
            cards[(kind, row.pk)] = row
    page.object_list = [cards[(kind, pk)] for pk, kind, _ in selected if (kind, pk) in cards]
    return page
