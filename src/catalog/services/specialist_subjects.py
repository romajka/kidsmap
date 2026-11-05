"""Tutoring taxonomy shared by entry, validation, discovery and presentation.

Subjects retain their existing specialization codes and M2M storage, including
legacy profiles with only a precise subject and no generic tutor selection.
"""
from django.utils.translation import get_language


SUBJECTS = {
    'english_teacher': ('Английский язык', 'İngilis dili', 'English', 'translate'),
    'math_tutor': ('Математика', 'Riyaziyyat', 'Mathematics', 'calculate'),
    'azerbaijani_teacher': ('Азербайджанский язык', 'Azərbaycan dili', 'Azerbaijani', 'translate'),
    'russian_teacher': ('Русский язык', 'Rus dili', 'Russian', 'translate'),
    'physics_tutor': ('Физика', 'Fizika', 'Physics', 'science'),
    'chemistry_tutor': ('Химия', 'Kimya', 'Chemistry', 'experiment'),
    'biology_tutor': ('Биология', 'Biologiya', 'Biology', 'eco'),
    'history_tutor': ('История', 'Tarix', 'History', 'history_edu'),
    'geography_tutor': ('География', 'Coğrafiya', 'Geography', 'public'),
    'informatics_tutor': ('Информатика', 'İnformatika', 'Computer science', 'computer'),
    'french_teacher': ('Французский язык', 'Fransız dili', 'French', 'translate'),
    'german_teacher': ('Немецкий язык', 'Alman dili', 'German', 'translate'),
}
REQUIRES_SUBJECT = frozenset({'tutor', 'exam_prep_tutor'})
TUTOR_CODES = REQUIRES_SUBJECT | SUBJECTS.keys()


def subject_item(code, language=None):
    language = (language or get_language() or 'az').split('-')[0]
    item = SUBJECTS[code]
    return {'value': code, 'label': item[{'ru': 0, 'az': 1, 'en': 2}.get(language, 1)], 'icon': item[3]}


def subject_required(specializations):
    codes = {spec.code for spec in specializations}
    return bool(codes & REQUIRES_SUBJECT and not codes & SUBJECTS.keys())


def subject_error():
    language = (get_language() or 'az').split('-')[0]
    return {
        'ru': 'Выберите хотя бы один предмет для репетитора или подготовки к экзаменам.',
        'az': 'Repetitor və ya imtahana hazırlıq üçün ən azı bir fənn seçin.',
        'en': 'Choose at least one subject for tutoring or exam preparation.',
    }.get(language, 'Choose at least one subject for tutoring or exam preparation.')


def profile_subjects(specialist, language=None):
    codes = {s.code for s in specialist.specializations.all()}
    return [subject_item(code, language) for code in SUBJECTS if code in codes]


def form_subject_options(form):
    specs = {str(spec.pk): spec for spec in form.fields['specializations'].queryset}
    widgets = {str(widget.data['value']): widget for widget in form['specializations']}
    by_code = {spec.code: (pk, spec) for pk, spec in specs.items()}
    return [dict(subject_item(code), widget=widgets[by_code[code][0]])
            for code in SUBJECTS if code in by_code]


def form_subject_rules(form):
    specs = list(form.fields['specializations'].queryset)
    return {
        'requires': [str(s.pk) for s in specs if s.code in REQUIRES_SUBJECT],
        'subjects': [str(s.pk) for s in specs if s.code in SUBJECTS],
    }
