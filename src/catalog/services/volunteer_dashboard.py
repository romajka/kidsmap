"""Read-only presentation of the existing volunteer proposal/live-place workflow."""
from dataclasses import replace
from django.core.paginator import Paginator
from django.db.models import Case, CharField, Count, F, Q, Value, When
from django.db.models.functions import Coalesce, Greatest
from django.urls import reverse
from django.utils.translation import pgettext_lazy, get_language
from catalog.models import Category, Subcategory
from catalog.services.volunteer_places import own_places, candidate_from_payload, content_snapshot
from catalog.services.place_readiness import evaluate_readiness, readiness_data_from_place
from catalog.services.place_schedule import is_meaningful_schedule, build_schedule_summary

def _(message):
    return pgettext_lazy("volunteer dashboard", message)


STATES = {
    'draft': (_('Черновик'), _('Карточка ещё не отправлена на проверку.'), _('Продолжить заполнение')),
    'pending': (_('На модерации'), _('Карточка отправлена администратору и ожидает проверки.'), _('Посмотреть')),
    'rejected': (_('Нужна доработка'), _('Исправьте замечания администратора и отправьте карточку повторно.'), _('Исправить')),
    'published': (_('Опубликовано'), _('Карточка опубликована на KidsMap.'), _('Редактировать')),
    'unpublished': (_('Снято с публикации'), _('Карточка сейчас не показывается на сайте.'), _('Редактировать')),
}


def workspace_places(user):
    return own_places(user).annotate(workflow_state=Case(
        When(volunteer_revision__status__in=['draft', 'pending', 'rejected'], then=F('volunteer_revision__status')),
        When(status='published', is_active=True, then=Value('published')),
        When(status='pending', then=Value('pending')),
        When(status='rejected', then=Value('rejected')),
        When(status='published', is_active=False, then=Value('unpublished')),
        default=Value('draft'), output_field=CharField(),
    ), activity_at=Greatest('updated_at', Coalesce('volunteer_revision__updated_at', 'updated_at')))


def display_card(place):
    revision = getattr(place, 'volunteer_revision', None)
    proposed = bool(revision and revision.status != 'approved')
    payload = revision.payload if proposed else content_snapshot(place)
    candidate = candidate_from_payload(place, payload)
    # A removed reference in an old proposal is a readiness issue, not a 500.
    candidate.category = Category.objects.filter(pk=candidate.category_id).first()
    candidate.subcategory = Subcategory.objects.select_related('category').filter(pk=candidate.subcategory_id).first()
    data = readiness_data_from_place(candidate)
    readiness = evaluate_readiness(replace(data, schedule_has_structured=is_meaningful_schedule(payload.get('structured_schedule', []))))
    state = place.workflow_state
    label, explanation, action = STATES[state]
    language = (get_language() or 'az').split('-')[0]
    name = getattr(candidate, f'name_{language}', '') or candidate.name_az or candidate.name_ru or candidate.name_en or place.name
    public = place.status == 'published' and place.is_active
    note = revision.review_note if proposed and revision.review_note else place.rejection_reason if state == 'rejected' else ''
    return dict(place=place, candidate=candidate, name=name, state=state, status=label, explanation=explanation,
        action=action, action_url=reverse('admin:volunteer_detail' if state=='pending' else 'admin:volunteer_edit', args=[place.pk]),
        detail_url=reverse('admin:volunteer_detail',args=[place.pk]), edit_url=reverse('admin:volunteer_edit',args=[place.pk]),
        photo_url=reverse('admin:volunteer_photo',args=[place.pk,'main']) if candidate.photo or candidate.cover_photo else '',
        public_url=place.get_absolute_url() if public else '', public=public, proposed=proposed, note=note,
        readiness=readiness, readiness_issues=[replace(issue, field="district") if issue.field == "region" else issue for issue in readiness.issues], updated_at=place.activity_at, description=getattr(candidate,f'description_{language}', '') or candidate.description_az or candidate.description_ru or candidate.description_en,
        schedule=build_schedule_summary(payload.get('structured_schedule', [])) or candidate.schedule,
    )


def dashboard_context(user, params):
    places = workspace_places(user)
    counts = places.aggregate(all=Count('pk'), **{state:Count('pk',filter=Q(workflow_state=state)) for state in STATES})
    state = params.get('status','all')
    if state not in STATES:
        state='all'
    query = params.get('q','').strip()[:200]
    selected=places
    if state!='all':
        selected=selected.filter(workflow_state=state)
    if query:
        search=Q(name__icontains=query)
        for language in ('az','ru','en'):
            search |= Q(**{f'name_{language}__icontains':query}) | Q(**{f'volunteer_revision__payload__name_{language}__icontains':query})
        selected=selected.filter(search)
    page=Paginator(selected.select_related('volunteer_revision','category','subcategory').prefetch_related('pricing_plan_records','schedule_days__intervals').order_by('-activity_at','-pk'),12).get_page(params.get('page'))
    filters=[dict(key='all',label=_('Все мои места'),count=counts['all'])]
    filters += [dict(key=key,label=value[0],count=counts[key]) for key,value in STATES.items() if key!='unpublished' or counts[key]]
    return dict(page=page,cards=[display_card(place) for place in page],counts=counts,filters=filters,
                selected_status=state,query=query,is_empty=not counts['all'])
