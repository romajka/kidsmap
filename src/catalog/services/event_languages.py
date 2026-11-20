"""Languages an event is held in, stored on Event.languages as "az,ru" (fixed order).

One plain text column keeps filtering portable (SQLite tests, PostgreSQL prod):
a regex on whole codes, never a substring match.
"""
from django import forms
from django.utils.translation import get_language

CODES = ('az', 'ru', 'en', 'tr')

NAMES = {
    'az': {'az': 'Azərbaycan dili', 'ru': 'Rus dili', 'en': 'İngilis dili', 'tr': 'Türk dili'},
    'ru': {'az': 'Азербайджанский', 'ru': 'Русский', 'en': 'Английский', 'tr': 'Турецкий'},
    'en': {'az': 'Azerbaijani', 'ru': 'Russian', 'en': 'English', 'tr': 'Turkish'},
}
FLAGS = {'az': '🇦🇿', 'ru': '🇷🇺', 'en': '🇬🇧', 'tr': '🇹🇷'}


def _ui(language=None):
    code = (language or get_language() or 'az').split('-')[0]
    return code if code in NAMES else 'az'


def normalize(values):
    """Any iterable or "ru, az" string -> "az,ru" with only known codes, in CODES order."""
    if isinstance(values, str):
        values = values.split(',')
    picked = {str(value).strip().lower() for value in (values or ())}
    return ','.join(code for code in CODES if code in picked)


def split(value):
    return [code for code in normalize(value).split(',') if code]


def choices(language=None):
    names = NAMES[_ui(language)]
    return [(code, names[code]) for code in CODES]


def present(value, language=None):
    """[{'code': 'ru', 'short': 'RU', 'name': 'Русский', 'flag': '🇷🇺'}, …] for templates and JSON."""
    names = NAMES[_ui(language)]
    return [{'code': code, 'short': code.upper(), 'name': names[code], 'flag': FLAGS[code]} for code in split(value)]


def regex_for(code):
    """Database regex that matches one whole code inside the stored list."""
    return rf'(^|,){code}(,|$)' if code in CODES else None


class EventLanguagesField(forms.MultipleChoiceField):
    """Checkboxes in the form, "az,ru" on the model."""
    widget = forms.CheckboxSelectMultiple

    def __init__(self, **kwargs):
        kwargs.setdefault('choices', choices)
        super().__init__(**kwargs)

    def prepare_value(self, value):
        return split(value) if isinstance(value, str) else (value or [])

    def has_changed(self, initial, data):
        return normalize(initial or '') != normalize(data or [])

    def clean(self, value):
        return normalize(super().clean(value) or [])
