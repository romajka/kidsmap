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
from catalog.services.moderation_queue import allowed_kinds, queue_rows
from catalog.services.permanent_place_rules import copy as t


@require_GET
def queue(request):
    if not allowed_kinds(request.user):
        raise PermissionDenied
    now = timezone.now()
    rows = queue_rows(request.user, request.GET, now=now)
    counts = Counter(row['sla'].status for row in rows)
    statuses = [('', t('Все', 'Hamısı', 'All')), ('pending', t('На модерации', 'Moderasiyada', 'Pending')),
        ('needs_changes', t('Нужна доработка', 'Düzəliş lazımdır', 'Needs changes')),
        ('approved', t('Одобрено', 'Təsdiqlənib', 'Approved')), ('rejected', t('Отклонено', 'Rədd edilib', 'Rejected'))]
    sla_statuses = [('', t('Все', 'Hamısı', 'All')), ('fresh', t('Свежая', 'Yeni', 'Fresh')),
        ('warning', 'SLA warning'), ('critical', 'SLA critical'), ('breached', 'SLA breached'),
        ('paused', t('Пауза', 'Dayandırılıb', 'Paused')), ('completed', t('Рассмотрено', 'Baxılıb', 'Completed'))]
    kinds = {'place': t('Место', 'Məkan', 'Place'), 'place_revision': t('Правки места', 'Məkan düzəlişləri', 'Place revision'),
        'place_review': t('Отзыв о месте', 'Məkan rəyi', 'Place review'), 'site_review': t('Отзыв о сайте', 'Sayt rəyi', 'Site review'),
        'specialist_review': t('Отзыв о специалисте', 'Mütəxəssis rəyi', 'Specialist review')}
    for row in rows:
        row['kind_label'] = kinds[row['kind']]
        row['status_label'] = dict(statuses).get(row['status'], row['status'])
        row['sla_label'] = dict(sla_statuses).get(row['sla'].status, row['sla'].status)
    return TemplateResponse(request, 'admin/moderation_sla.html', {
        **admin.site.each_context(request), 'title': t('Сроки модерации', 'Moderasiya müddətləri', 'Moderation deadlines'),
        'page': Paginator(rows, 50).get_page(request.GET.get('page')), 'counts': dict(counts),
        'statuses': statuses[1:] + [('all', statuses[0][1])], 'sla_statuses': sla_statuses,
        'places_count': sum(row['content_type'] == 'place' for row in rows),
        'reviews_count': sum(row['content_type'] == 'review' for row in rows), 'params': request.GET,
        'backlog_warning': bool(settings.MODERATION_QUEUE_BACKLOG_THRESHOLD and sum(row['status'] == 'pending' for row in rows) > settings.MODERATION_QUEUE_BACKLOG_THRESHOLD),
        'copy': {
            'type': t('Тип', 'Növ', 'Type'), 'status': t('Статус', 'Status', 'Status'),
            'material': t('Материал', 'Material', 'Material'), 'received': t('Поступило', 'Daxil olub', 'Received'),
            'age': t('Часов на проверке', 'Yoxlamada saat', 'Hours in review'), 'deadline': t('Дедлайн', 'Son müddət', 'Deadline'),
            'remaining': t('Осталось часов', 'Qalan saat', 'Hours remaining'), 'filter': t('Применить', 'Tətbiq et', 'Apply'),
            'places': t('Места', 'Məkanlar', 'Places'), 'reviews': t('Отзывы', 'Rəylər', 'Reviews'),
            'all': t('Все', 'Hamısı', 'All'), 'from': t('С даты', 'Tarixdən', 'From date'), 'to': t('По дату', 'Tarixədək', 'To date'),
            'empty': t('В этой очереди нет материалов.', 'Bu növbədə material yoxdur.', 'No materials in this queue.'),
            'note': t('Календарное время. SLA — срок рассмотрения, не обещание публикации. На доработке отсчёт приостановлен; повторная отправка начинает новый срок.', 'Təqvim vaxtı. SLA baxılma müddətidir, yayımlanma vədi deyil. Düzəliş zamanı hesablanma dayanır; yenidən göndərmə yeni müddət başlayır.', 'Calendar time. SLA is a review deadline, not a publication promise. Requested changes pause the clock; resubmission starts a new period.'),
            'reason': t('Что нужно исправить', 'Nəyi düzəltməli', 'What needs changing'),
            'needs_changes': t('На доработку', 'Düzəlişə qaytar', 'Request changes'),
            'estimated': t('Дата приблизительная', 'Təxmini tarix', 'Estimated date'),
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
