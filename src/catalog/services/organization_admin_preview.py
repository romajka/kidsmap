"""Render an organization candidate using the public detail page."""
from base64 import b64encode
from copy import copy

from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import UploadedFile
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.cache import add_never_cache_headers
from django.utils.translation import gettext as _, override

from catalog.controllers.public_details import organization_detail_context
from catalog.models import Organization, VolunteerPlaceRevision
from catalog.services import publication
from catalog.services.public_presentation import language_code


def render_organization_preview(request, organization, *, form_class):
    submitted = request.method == 'POST'
    language = language_code(
        request.POST.get('preview_language') if submitted else
        request.GET.get('lang') or request.LANGUAGE_CODE,
    )
    form = (
        form_class(request.POST, request.FILES, instance=copy(organization))
        if submitted else None
    )
    candidate = copy(organization) if organization else Organization()
    revision = getattr(organization, 'content_revision', None)
    fields = publication.fields_for('organization')
    has_candidate = revision and revision.status in {
        VolunteerPlaceRevision.Status.DRAFT,
        VolunteerPlaceRevision.Status.PENDING,
        VolunteerPlaceRevision.Status.REJECTED,
    }
    if has_candidate:
        for name in fields.intersection(revision.payload):
            setattr(candidate, name, revision.payload[name])

    visitor = copy(request)
    visitor.user = AnonymousUser()
    visitor.LANGUAGE_CODE = language
    visitor.site_preview = True
    candidate._public_batch = True
    candidate._public_visible = True

    with override(language):
        media = {}
        if form is not None:
            form.is_valid()
            for name in fields.intersection(form.cleaned_data):
                value = form.cleaned_data[name]
                if isinstance(value, UploadedFile):
                    value.seek(0)
                    encoded = b64encode(value.read()).decode('ascii')
                    mime = {'PNG': 'png', 'JPEG': 'jpeg', 'WEBP': 'webp'}[value.image.format]
                    media[name] = f'data:image/{mime};base64,{encoded}'
                else:
                    setattr(candidate, name, value or '')

        for name in ('logo', 'cover_photo'):
            if name not in media:
                file = getattr(candidate, name)
                media[name] = file.url if file else ''

        editor_url = (
            reverse('admin:catalog_organization_change', args=[organization.pk])
            if organization else reverse('admin:catalog_organization_add')
        )
        context = organization_detail_context(candidate, language, preview_media=media)
        context.update({
            'organization_preview': True,
            'organization_preview_submitted': submitted,
            'organization_preview_editor': editor_url,
            'organization_preview_form': form,
            'organization_preview_languages': (
                [(code, f'{request.path}?lang={code}') for code in ('az', 'ru', 'en')]
                if not submitted else []
            ),
            'site_preview': True,
            'site_preview_page_class': 'page-organization_detail',
            'organization_reviewed': bool(organization and organization.is_public and not has_candidate and not submitted),
            'seo_title': _('Предпросмотр организации'),
        })
        response = TemplateResponse(visitor, 'catalog/public_entity_detail.html', context)
        response.render()
    add_never_cache_headers(response)
    response['X-Robots-Tag'] = 'noindex, nofollow, noarchive'
    response['Content-Language'] = language
    response['Referrer-Policy'] = 'no-referrer'
    return response
