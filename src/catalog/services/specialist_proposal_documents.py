"""Working-copy credentials follow the applicant, until their identity is confirmed."""
from pathlib import Path

from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseFormSet, formset_factory
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from catalog.models import SpecialistDocument, SpecialistProposalDocument
from catalog.services.specialist_document_validation import validate_document_upload

MAX_DOCUMENT_BYTES = 10 * 1024 * 1024
MAX_BATCH_BYTES = 20 * 1024 * 1024
MAX_DOCUMENTS = 10


class QualificationForm(forms.Form):
    id = forms.UUIDField(required=False, widget=forms.HiddenInput)
    type = forms.ChoiceField(required=False, choices=SpecialistDocument.QUALIFICATION_TYPES, initial='diploma')
    name = forms.CharField(required=False, max_length=255)
    file = forms.FileField(required=False, widget=forms.FileInput(attrs={'accept': '.pdf,.png,.jpg,.jpeg'}))
    publish = forms.BooleanField(required=False)

    def __init__(self, *args, saved_document=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.saved_document = saved_document

    def clean(self):
        data = super().clean()
        if not data or data.get('DELETE'):
            return data
        upload = data.get('file')
        saved = self.saved_document
        if saved and upload:
            self.add_error('file', _('Чтобы заменить файл, уберите документ и добавьте новый.'))
        if not upload and not saved:
            if data.get('name') or data.get('publish') or data.get('type') == 'certificate':
                self.add_error('file', _('Выберите файл диплома или сертификата.'))
            return data
        data['type'] = data.get('type') or 'diploma'
        data['name'] = data.get('name') or (saved.name if saved else Path(upload.name).stem[:255]) or str(_('Документ'))
        if upload:
            if not 0 < upload.size <= MAX_DOCUMENT_BYTES or Path(upload.name).suffix.lower() not in {'.pdf', '.png', '.jpg', '.jpeg'}:
                self.add_error('file', _('Выберите JPG, PNG или PDF до 10 МБ.'))
        return data


class BaseQualificationFormSet(BaseFormSet):
    max_upload_bytes = MAX_DOCUMENT_BYTES
    max_batch_bytes = MAX_BATCH_BYTES

    def __init__(self, *, draft=None, allow_upload=True, **kwargs):
        self.saved = list(draft.qualification_documents.all()) if draft else []
        self.allow_upload = allow_upload
        initial = [{'id': row.pk, 'type': row.document_type, 'name': row.name, 'publish': row.publish}
                   for row in self.saved]
        super().__init__(initial=initial, prefix='qual', **kwargs)

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        if index is not None and index < len(self.saved):
            kwargs['saved_document'] = self.saved[index]
        return kwargs

    def clean(self):
        super().clean()
        if not self.management_form.is_valid():
            return
        if self.initial_form_count() != len(self.saved) or self.total_form_count() < len(self.saved):
            raise ValidationError(_('Список документов изменился. Обновите страницу.'))
        file_fields = {form.add_prefix('file') for form in self.forms}
        for key in self.files:
            if key.startswith('qual-') and (key not in file_fields or (
                    hasattr(self.files, 'getlist') and len(self.files.getlist(key)) != 1)):
                raise ValidationError(_('Список документов изменился. Обновите страницу.'))
        inputs = []
        for form in self.forms:
            fields = form.cleaned_data
            expected_id = form.saved_document.pk if form.saved_document else None
            if fields.get('id') != expected_id:
                raise ValidationError(_('Список документов изменился. Обновите страницу.'))
            if fields.get('DELETE'):
                continue
            if not self.allow_upload and (fields.get('file') or fields.get('name') or fields.get('publish')):
                raise ValidationError(_('Документы можно приложить только к своей анкете.'))
            if fields.get('file'):
                inputs.append((form, fields['file']))
        if sum(upload.size for _, upload in inputs) > self.max_batch_bytes:
            raise ValidationError(_('За одно сохранение можно добавить до 20 МБ. Остальные файлы добавьте следующим сохранением.'))
        if not any(self.errors):
            for form, upload in inputs:
                try:
                    validate_document_upload(upload)
                except ValidationError as exc:
                    form.add_error('file', exc)


QualificationFormSet = formset_factory(QualificationForm, formset=BaseQualificationFormSet, extra=1, can_delete=True,
                                        max_num=MAX_DOCUMENTS, validate_max=True, absolute_max=MAX_DOCUMENTS * 2)


def qualification_formset(*, draft, subject, data=None, files=None):
    # Older clients have no qualification fields. A missing section preserves all saved files.
    has_section = data is not None and any(key.startswith('qual-') for items in (data, files or {}) for key in items)
    return QualificationFormSet(draft=draft, allow_upload=subject == 'self',
                                data=data if has_section else None, files=files if has_section else None)


def save_qualifications(*, draft, formset, created_paths):
    """The caller holds the author and draft locks and cleans new files on rollback."""
    if not formset.is_bound:
        return
    for form in formset:
        fields = form.cleaned_data
        row = form.saved_document
        if fields.get('DELETE'):
            if row:
                row.delete()
            continue
        if row is None:
            upload = fields.get('file')
            if not upload:
                continue
            row = SpecialistProposalDocument(draft=draft)
            upload.seek(0)
            row.file.save(upload.name, upload, save=False)
            created_paths.append(row.file.name)
        row.name = fields['name']
        row.document_type = fields['type']
        row.publish = fields.get('publish', False)
        row.opted_in_at = (row.opted_in_at or timezone.now()) if row.publish else None
        row.save()


def transfer_confirmed_qualifications(person):
    """The confirmed author and specialist are locked; transfer ownership of private paths atomically."""
    if not person.verified_person_user_id or not person.person_verified_at:
        return
    rows = SpecialistProposalDocument.objects.filter(draft__actor_id=person.verified_person_user_id,
            draft__submitted_specialist_id=person.pk, draft__submitted_at__isnull=False)
    records = list(rows.select_for_update(of=('self',)))
    if not records:
        return
    SpecialistDocument.objects.bulk_create([
        SpecialistDocument(specialist=person, name=row.name, document_type=row.document_type, file=row.file.name,
                           uploaded_by_id=person.verified_person_user_id, verified_at_upload=person.person_verified_at,
                           is_published=row.publish, opted_in_at=row.opted_in_at,
                           opted_in_by_id=person.verified_person_user_id if row.publish else None)
        for row in records
    ])
    # One storage file changes owner without a byte copy. Clearing the old reference keeps
    # cascade cleanup for abandoned draft rows from deleting the newly owned file.
    transferred = SpecialistProposalDocument.objects.filter(pk__in=[row.pk for row in records])
    transferred.update(file='')
    transferred.delete()
