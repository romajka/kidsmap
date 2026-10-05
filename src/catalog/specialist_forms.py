"""Workspace inputs: domain services remain the final authority."""
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from catalog.models import Specialist, SpecialistDocument


class EmploymentProposalForm(forms.Form):
    specialist = forms.ModelChoiceField(label=_("Специалист"), queryset=Specialist.objects.none())
    role = forms.CharField(label=_("Роль"), max_length=255)
    start_date = forms.DateField(label=_("Начало сотрудничества"), widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(label=_("Окончание сотрудничества"), required=False,
                              widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['specialist'].queryset = Specialist.objects.filter(
            verified_person_user__is_active=True, person_verified_at__isnull=False,
            is_active=True, status=Specialist.STATUS_PUBLISHED).order_by('name', 'pk')

    def clean(self):
        data = super().clean()
        if data.get('end_date') and data.get('start_date') and data['end_date'] < data['start_date']:
            self.add_error('end_date', _("Окончание не может быть раньше начала."))
        return data


class SpecialistDocumentUploadForm(forms.Form):
    document_type = forms.ChoiceField(label=_("Тип документа"), choices=SpecialistDocument.TYPE_CHOICES)
    name = forms.CharField(label=_("Название документа"), max_length=255)
    file = forms.FileField(label=_("Файл документа"), help_text=_("PDF, PNG или JPEG. Максимум 10 МБ."),
        widget=forms.ClearableFileInput(
        attrs={'accept': '.pdf,.png,.jpg,.jpeg'}))
    publish = forms.BooleanField(label=_("Показывать после проверки"), required=False)

    def clean(self):
        data = super().clean()
        if data.get('publish') and data.get('document_type') == SpecialistDocument.TYPE_IDENTITY:
            self.add_error('publish', _("Удостоверение личности всегда приватно."))
        return data
