from collections import Counter
from django.contrib import admin, messages
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from catalog.models import Place, PlaceChangeAudit
from catalog.services.moderation_queue import allowed_kinds, matches_queue_type, queue_rows
from catalog.services.moderation_sla import policy_hours
from catalog.services.permanent_place_rules import copy as t


@require_GET
def queue(request):
    permitted = allowed_kinds(request.user)
    if not permitted:
        raise PermissionDenied
    now = timezone.now()
    from catalog.services.moderation_hub import kind_label
    type_filters = []
    if 'place' in permitted or 'place_revision' in permitted:
        type_filters.append(('place', t('Места', 'Məkanlar', 'Places')))
    if any(kind.endswith('_review') for kind in permitted):
        type_filters.append(('review', t('Отзывы', 'Rəylər', 'Reviews')))
    if 'place_revision' in permitted:
        type_filters.append(('proposals', t('Предложения', 'Təkliflər', 'Proposals')))
        type_filters.extend((kind, kind_label(kind)) for kind in
            ('organization', 'program', 'activity', 'offering_group'))
    if 'affiliation' in permitted:
        type_filters.append(('affiliation', kind_label('affiliation')))
    # Counts describe the destination of each filter, keeping the other filters active.
    params = request.GET
    scope = queue_rows(request.user, {key: params[key] for key in ('status', 'from', 'to') if key in params}, now=now)
    by_type = [row for row in scope if matches_queue_type(row['kind'], row['content_type'], params.get('type'))]
    selected_sla = params.get('sla_status')
    counts = Counter(row['sla'].status for row in by_type)
    by_sla = [row for row in scope if not selected_sla or row['sla'].status == selected_sla]
    rows = [row for row in by_type if not selected_sla or row['sla'].status == selected_sla]
    totals = Counter(row['content_type'] for row in by_sla)
    totals['proposals'] = sum(totals[kind] for kind in ('organization', 'program', 'activity', 'offering_group'))
    type_chips = [('', t('Все', 'Hamısı', 'All'), len(by_sla))]
    type_chips.extend((kind, label, totals[kind]) for kind, label in type_filters
                      if kind in {'place', 'review', 'proposals', 'affiliation'})
    statuses = [('', t('Все', 'Hamısı', 'All')), ('pending', t('На модерации', 'Moderasiyada', 'Pending')),
        ('needs_changes', t('Нужна доработка', 'Düzəliş lazımdır', 'Needs changes')),
        ('approved', t('Одобрено', 'Təsdiqlənib', 'Approved')), ('rejected', t('Отклонено', 'Rədd edilib', 'Rejected'))]
    sla_statuses = [('', t('Все', 'Hamısı', 'All')), ('fresh', t('В норме', 'Normada', 'On track')),
        ('warning', t('Скоро срок', 'Müddət yaxınlaşır', 'Due soon')), ('critical', t('Критично', 'Kritik', 'Critical')),
        ('breached', t('Просрочено', 'Müddət keçib', 'Overdue')),
        ('paused', t('Пауза', 'Dayandırılıb', 'Paused')), ('completed', t('Рассмотрено', 'Baxılıb', 'Completed')),
        ('unconfigured', t('Срок не задан', 'Müddət təyin edilməyib', 'No deadline configured'))]
    kinds = {'place': t('Место', 'Məkan', 'Place'), 'place_revision': t('Правки места', 'Məkan düzəlişləri', 'Place revision'),
        'place_review': t('Отзыв о месте', 'Məkan rəyi', 'Place review'), 'site_review': t('Отзыв о сайте', 'Sayt rəyi', 'Site review'),
        'specialist_review': t('Отзыв о специалисте', 'Mütəxəssis rəyi', 'Specialist review'),
        'activity_review': t('Отзыв о занятии', 'Məşğələ rəyi', 'Activity review'),
        'event_review': t('Отзыв о мероприятии', 'Tədbir rəyi', 'Event review'),
        **{kind + '_revision': kind_label(kind) for kind in ('organization', 'program', 'activity', 'offering_group')},
        'affiliation': t('Информационная связь', 'Məlumat əlaqəsi', 'Informational link')}
    for row in rows:
        row['kind_label'] = kinds[row['kind']]
        row['status_label'] = dict(statuses).get(row['status'], row['status'])
        row['sla_label'] = dict(sla_statuses).get(row['sla'].status, row['sla'].status)
    return TemplateResponse(request, 'admin/moderation_sla.html', {
        **admin.site.each_context(request), 'title': t('Сроки модерации', 'Moderasiya müddətləri', 'Moderation deadlines'),
        'page': Paginator(rows, 50).get_page(request.GET.get('page')), 'counts': dict(counts),
        'statuses': statuses[1:] + [('all', statuses[0][1])], 'sla_statuses': sla_statuses,
        'type_filters': type_filters, 'type_chips': type_chips,
        'places_count': totals['place'], 'reviews_count': totals['review'],
        'proposals_count': totals['proposals'], 'links_count': totals['affiliation'], 'params': params,
        'policy_limits': [(label, policy_hours(kind)) for kind, label in type_filters
                          if kind in {'place', 'review'}],
        'backlog_warning': bool(settings.MODERATION_QUEUE_BACKLOG_THRESHOLD and sum(row['status'] == 'pending' for row in rows) > settings.MODERATION_QUEUE_BACKLOG_THRESHOLD),
        'copy': {
            'type': t('Тип', 'Növ', 'Type'), 'status': t('Статус', 'Status', 'Status'),
            'material': t('Материал', 'Material', 'Material'), 'received': t('Поступило', 'Daxil olub', 'Received'),
            'age': t('Часов на проверке', 'Yoxlamada saat', 'Hours in review'), 'deadline': t('Дедлайн', 'Son müddət', 'Deadline'),
            'remaining': t('Осталось часов', 'Qalan saat', 'Hours remaining'), 'filter': t('Применить', 'Tətbiq et', 'Apply'),
            'places': t('Места', 'Məkanlar', 'Places'), 'reviews': t('Отзывы', 'Rəylər', 'Reviews'),
            'proposals': t('Предложения', 'Təkliflər', 'Proposals'), 'links': t('Связи', 'Əlaqələr', 'Links'),
            'all': t('Все', 'Hamısı', 'All'), 'from': t('С даты', 'Tarixdən', 'From date'), 'to': t('По дату', 'Tarixədək', 'To date'),
            'empty': t('В этой очереди нет материалов.', 'Bu növbədə material yoxdur.', 'No materials in this queue.'),
            'note': t('Календарное время. SLA — срок рассмотрения, не обещание публикации. На доработке отсчёт приостановлен; повторная отправка начинает новый срок.', 'Təqvim vaxtı. SLA baxılma müddətidir, yayımlanma vədi deyil. Düzəliş zamanı hesablanma dayanır; yenidən göndərmə yeni müddət başlayır.', 'Calendar time. SLA is a review deadline, not a publication promise. Requested changes pause the clock; resubmission starts a new period.'),
            'reason': t('Что нужно исправить', 'Nəyi düzəltməli', 'What needs changing'),
            'needs_changes': t('На доработку', 'Düzəlişə qaytar', 'Request changes'),
            'estimated': t('Дата приблизительная', 'Təxmini tarix', 'Estimated date'),
            'hours_unit': t('ч', 'saat', 'h'),
            'no_deadline': t('Срок не задан', 'Müddət təyin edilməyib', 'No deadline configured'),
            'backlog': t('Превышен порог необработанных заявок.', 'Baxılmamış müraciət həddi aşılıb.', 'Pending queue threshold exceeded.'),
        },
    })


@require_POST
@transaction.atomic
def needs_changes(request, place_id):
    if 'place' not in allowed_kinds(request.user):
        raise PermissionDenied
    reason = request.POST.get('reason', '').strip()
    if not reason:
        return HttpResponseBadRequest('A reason is required.')
    place = get_object_or_404(Place.objects.select_for_update().filter(status='pending', deleted_at__isnull=True), pk=place_id)
    if getattr(place, 'volunteer_revision', None) and place.volunteer_revision.status != 'approved':
        raise PermissionDenied  # Use version-protected volunteer review, not live Place.
    old_reason = place.rejection_reason
    place.status = 'needs_changes'
    place.is_active = False
    place.rejection_reason = reason
    place.moderated_by = request.user
    place.save(update_fields=['status', 'is_active', 'rejection_reason', 'moderated_by'])
    from catalog.repositories.django_repositories import DjangoPlaceChangeAuditRepository
    DjangoPlaceChangeAuditRepository().create_entries(place=place, changed_by=request.user,
        source=PlaceChangeAudit.SOURCE_ADMIN, changes={'status': ('pending', 'needs_changes'), 'rejection_reason': (old_reason, reason)})
    messages.success(request, t('Отправлено на доработку.', 'Düzəlişə göndərildi.', 'Changes requested.'))
    return redirect('admin:moderation_sla')


_base_urls = admin.site.get_urls
def get_urls():
    return [path('moderation-sla/', admin.site.admin_view(queue), name='moderation_sla'),
            path('moderation-sla/place/<int:place_id>/needs-changes/', admin.site.admin_view(needs_changes), name='moderation_needs_changes')] + _base_urls()
admin.site.get_urls = get_urls
