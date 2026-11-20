from django.http import Http404, HttpResponse, HttpResponseNotFound
from django.shortcuts import render
from django.urls import reverse
from django.utils.cache import patch_vary_headers
from django.views.decorators.http import require_safe

from catalog.models import SpecialistDocument
from catalog.services.features import require_specialists_section_enabled
from catalog.services.specialist_document_raster import PageNotFound, PreviewUnavailable, render_document_page
from catalog.services.specialist_documents import can_download_document


def _qualification(request, document_id):
    require_specialists_section_enabled()
    doc = SpecialistDocument.objects.select_related('specialist__verified_person_user').filter(
        pk=document_id, document_type__in=['diploma', 'certificate'],
        file__startswith='specialist-documents/',
    ).first()
    if doc is None or not can_download_document(request.user, doc):
        raise Http404
    return doc


def _private(response):
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    response['X-Robots-Tag'] = 'noindex, noarchive'
    patch_vary_headers(response, ['Cookie'])
    return response


def document_reader_response(request, document, *, page_route, route_args, download_url=''):
    """Serve an already-authorized qualification from the public or private workspace."""
    raw_page = request.GET.get('page', '1')
    if len(raw_page) > 8 or not raw_page.isascii() or not raw_page.isdecimal() or int(raw_page) < 1:
        return _private(HttpResponseNotFound())
    page = int(raw_page)
    try:
        count, _ = render_document_page(document.file, page)
    except PageNotFound:
        return _private(HttpResponseNotFound())
    except PreviewUnavailable:
        count = 0
    context = {
        'document': document, 'page': page, 'page_count': count, 'download_url': download_url,
        'image_url': reverse(page_route, args=[*route_args, page]),
    }
    return _private(render(request, 'catalog/specialist_document_preview.html', context))


def document_image_response(request, document, page):
    if page < 1 or page > 99_999_999:
        return _private(HttpResponseNotFound())
    try:
        _, jpeg = render_document_page(document.file, page, thumbnail=request.GET.get('thumb') == '1')
    except (PageNotFound, PreviewUnavailable):
        return _private(HttpResponseNotFound())
    return _private(HttpResponse(jpeg, content_type='image/jpeg'))


@require_safe
def specialist_document_preview(request, document_id):
    try:
        doc = _qualification(request, document_id)
    except Http404:
        return _private(HttpResponseNotFound())
    return document_reader_response(
        request, doc, page_route='specialist_document_page', route_args=[doc.pk],
        download_url=reverse('serve_specialist_document', args=[doc.pk]),
    )


@require_safe
def specialist_document_page(request, document_id, page):
    try:
        doc = _qualification(request, document_id)
    except Http404:
        return _private(HttpResponseNotFound())
    return document_image_response(request, doc, page)
