"""Public approved Organization and concrete Place Activity pages."""
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET
from catalog.models import Organization, Activity, PlaceReview, ActivityReview
from catalog.services.content_quality import published_place_queryset, public_review_queryset
from catalog.services.public_presentation import present, current_organization, translated
from catalog.services.tracking import track_subject_view
from catalog.services.seo import build_public_entity_seo_payload


def _language(request):
    return getattr(request, 'LANGUAGE_CODE', 'az')


@require_GET
def organization_detail(request, public_id):
    entity = get_object_or_404(Organization, public_id=public_id)
    data = present(entity, _language(request))
    if not data['visible']:
        raise Http404
    request._seo_entity = entity
    branch_objects = [p for p in published_place_queryset(entity.places.all()).select_related('category','organization')
        if current_organization(p) is not None]
    branches = []
    for place in branch_objects:
        branch = present(place, _language(request))
        branch.update(age=place.age_display, address=translated(place, 'address', _language(request))[0],
            activities=[present(activity, _language(request)) for activity in place.activities.filter(
                status='published', archived_at__isnull=True).select_related('place__organization', 'place__category', 'program__organization')])
        branches.append(branch)
    programs = [present(p, _language(request)) for p in entity.programs.filter(status='published', approved_at__isnull=False, archived_at__isnull=True)]
    feed = []
    for review in public_review_queryset(PlaceReview.objects.filter(place_id__in=[p.pk for p in branch_objects])).select_related('place').order_by('-created_at')[:30]:
        target = present(review.place, _language(request))
        feed.append({'target_name':target['name'], 'target_url':target['url']+'#reviews', 'text':review.text, 'rating':review.rating})
    for review in public_review_queryset(ActivityReview.objects.filter(activity__place_id__in=[p.pk for p in branch_objects],
            activity__status='published', activity__archived_at__isnull=True)).select_related('activity__place__category', 'activity__program__organization').order_by('-created_at')[:30]:
        target = present(review.activity, _language(request))
        if target['visible']:
            feed.append({'target_name':target['name'], 'target_url':target['url']+'#reviews', 'text':review.text, 'rating':review.rating})
    track_subject_view(request=request, subject=entity)
    return render(request,'catalog/public_entity_detail.html',{
        'entity':entity,'presentation':data,'branches':branches,'programs':programs,'review_feed':feed,
        **build_public_entity_seo_payload(entity, request, _language(request))})


@require_GET
def activity_detail(request, pk):
    entity = get_object_or_404(Activity.objects.select_related('place__category','place__organization','program__organization'), pk=pk)
    data = present(entity, _language(request))
    if not data['visible']:
        raise Http404
    request._seo_entity = entity
    feed = [{'target_name':data['name'], 'target_url':data['url']+'#reviews', 'text':review.text, 'rating':review.rating}
        for review in public_review_queryset(ActivityReview.objects.filter(activity=entity)).order_by('-created_at')[:30]]
    track_subject_view(request=request, subject=entity)
    return render(request,'catalog/public_entity_detail.html',{
        'entity':entity,'presentation':data,'place':entity.place,'place_presentation':present(entity.place,_language(request)),
        'review_feed':feed, **build_public_entity_seo_payload(entity, request, _language(request))})
