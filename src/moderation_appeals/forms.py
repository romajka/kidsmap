from django import forms
from django.core.validators import URLValidator
from django.utils.functional import lazy

from catalog.services.permanent_place_rules import copy

tr = lazy(copy, str)


class AppealForm(forms.Form):
    explanation = forms.CharField(
        label=tr("Почему вы не согласны?", "Nə üçün razı deyilsiniz?", "Why do you disagree?"),
        max_length=4000, widget=forms.Textarea(attrs={"rows": 4}),
    )
    evidence_url = forms.CharField(
        label=tr("Ссылка на материалы", "Materiallara keçid", "Supporting link"),
        max_length=2000, required=False,
        validators=[URLValidator(schemes=["http", "https"])],
        widget=forms.URLInput(attrs={"placeholder": "https://", "dir": "ltr"}),
    )


class DecisionForm(forms.Form):
    reason = forms.CharField(
        label=tr("Обоснование решения", "Qərarın əsaslandırılması", "Reason for the decision"),
        max_length=4000, widget=forms.Textarea(attrs={"rows": 4}),
    )
