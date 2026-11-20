from django import forms
from django.utils.functional import cached_property
from django.utils.translation import get_language

from .services import StaleOffer, offer, validate_offer


STALE_MESSAGE = {
    "az": "Sənədlərin cari versiyalarını nəzərdən keçirin və razılığınızı yenidən təsdiqləyin.",
    "ru": "Ознакомьтесь с текущими версиями документов и подтвердите согласие ещё раз.",
    "en": "Review the current versions of the documents and confirm your agreement again.",
}
REQUIRED_MESSAGE = {
    "az": "Davam etmək üçün sənədlərlə razı olduğunuzu təsdiqləyin.",
    "ru": "Чтобы продолжить, подтвердите согласие с документами.",
    "en": "Confirm your agreement with the documents to continue.",
}


class AgreementCheckbox(forms.CheckboxInput):
    def value_from_datadict(self, data, files, name):
        # Native checkbox submits "on". Arbitrary nonempty values aren't consent.
        return data.get(name) in ("on", "true", "1", True)


class LegalAgreementMixin:
    """Bind the checked field to the exact documents displayed by this form."""

    def __init__(self, *args, language=None, **kwargs):
        super().__init__(*args, **kwargs)
        language = (language or get_language() or "az").split("-")[0]
        self.consent_language = language if language in STALE_MESSAGE else "az"
        self.fields["agreement"].error_messages["required"] = REQUIRED_MESSAGE[self.consent_language]

    @cached_property
    def legal_offer(self):
        return offer(self.consent_language)

    def clear_agreement(self):
        self.data = self.data.copy()
        self.data.pop(self.add_prefix("agreement"), None)

    def clean_agreement(self):
        try:
            validate_offer(self.consent_language, self.data.get("legal_offer"), current=self.legal_offer)
        except StaleOffer:
            self.clear_agreement()
            raise forms.ValidationError(STALE_MESSAGE[self.consent_language], code="stale_offer") from None
        return self.cleaned_data["agreement"]


class ConsentForm(LegalAgreementMixin, forms.Form):
    agreement = forms.BooleanField(widget=AgreementCheckbox)
