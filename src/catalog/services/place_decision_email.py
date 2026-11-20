"""Email for a moderator's decision on a place: what was decided, why, what next.

The author asked for the moderator's reason to be in the email itself, so the
reason is included (escaped in HTML). The link leads to the login-protected
notification inbox, where the current edit link is authorized at click time.
"""
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse

DECISIONS = ('needs_changes', 'rejected')

_TONES = {
    'needs_changes': {'accent': '#a8660b', 'badge_bg': '#fdf3dc', 'badge_fg': '#7a5300', 'note_bg': '#fffaf0'},
    'rejected': {'accent': '#a3342d', 'badge_bg': '#fcebea', 'badge_fg': '#7a231e', 'note_bg': '#fff7f6'},
}


def _copy(decision, name, edits):
    common = {
        'az': {'note_label': 'Moderatorun şərhi', 'place': 'Məkan', 'button': 'Kabinetdə aç',
               'footer': 'Bu məktub KidsMap-də məkanınız üzrə moderator qərarı ilə bağlı göndərilib.'},
        'ru': {'note_label': 'Комментарий модератора', 'place': 'Место', 'button': 'Открыть в кабинете',
               'footer': 'Письмо отправлено, потому что модератор KidsMap проверил ваше место.'},
        'en': {'note_label': "Moderator's note", 'place': 'Place', 'button': 'Open your account',
               'footer': 'You received this because a KidsMap moderator reviewed your place.'},
    }
    if decision == 'needs_changes' and edits:
        text = {
            'az': {'badge': 'Düzəliş lazımdır',
                   'lead': f'«{name}» məkanına etdiyiniz dəyişikliklər düzəlişə qaytarıldı. Saytdakı hazırkı versiya dəyişmir.',
                   'next': 'Qeydə uyğun düzəliş edin və dəyişiklikləri yenidən yoxlamaya göndərin.'},
            'ru': {'badge': 'Нужна доработка',
                   'lead': f'Правки к месту «{name}» вернули на доработку. Текущая версия на сайте не меняется.',
                   'next': 'Исправьте отмеченное и отправьте правки на проверку снова.'},
            'en': {'badge': 'Changes requested',
                   'lead': f'Your edits to “{name}” were sent back for changes. The version on the site stays as is.',
                   'next': "Fix what's noted and resubmit your edits for review."},
        }
    elif decision == 'needs_changes':
        text = {
            'az': {'badge': 'Düzəliş lazımdır',
                   'lead': f'Moderator «{name}» məkanını düzəlişə qaytardı.',
                   'next': 'Qeydə uyğun düzəliş edin və kartı yenidən yoxlamaya göndərin — tezliklə baxacağıq.'},
            'ru': {'badge': 'Нужна доработка',
                   'lead': f'Модератор вернул место «{name}» на доработку.',
                   'next': 'Исправьте отмеченное и отправьте карточку на проверку снова — мы посмотрим её в ближайшее время.'},
            'en': {'badge': 'Changes requested',
                   'lead': f'A moderator sent “{name}” back for changes.',
                   'next': "Fix what's noted and resubmit the listing — we'll review it shortly."},
        }
    elif edits:
        text = {
            'az': {'badge': 'Rədd edildi',
                   'lead': f'«{name}» məkanına etdiyiniz dəyişikliklər qəbul edilmədi. Saytdakı hazırkı versiya dəyişmir.',
                   'next': 'Sualınız varsa, info@kidsmap.az ünvanına yazın.'},
            'ru': {'badge': 'Отклонено',
                   'lead': f'Правки к месту «{name}» отклонены. Текущая версия на сайте не меняется.',
                   'next': 'Если есть вопросы, напишите нам на info@kidsmap.az.'},
            'en': {'badge': 'Declined',
                   'lead': f'Your edits to “{name}” were declined. The version on the site stays as is.',
                   'next': 'If you have questions, write to info@kidsmap.az.'},
        }
    else:
        text = {
            'az': {'badge': 'Rədd edildi',
                   'lead': f'«{name}» məkanı moderasiyadan keçmədi və saytda dərc olunmayacaq.',
                   'next': 'Sualınız varsa, info@kidsmap.az ünvanına yazın.'},
            'ru': {'badge': 'Отклонено',
                   'lead': f'Место «{name}» не прошло модерацию и не будет опубликовано.',
                   'next': 'Если есть вопросы, напишите нам на info@kidsmap.az.'},
            'en': {'badge': 'Declined',
                   'lead': f'“{name}” did not pass moderation and will not be published.',
                   'next': 'If you have questions, write to info@kidsmap.az.'},
        }
    return {lang: {**common[lang], **text[lang]} for lang in ('az', 'ru', 'en')}


def is_place_decision(item):
    context = item.event_context if isinstance(item.event_context, dict) else {}
    return (item.event_kind == 'moderation_decision' and context.get('decision') in DECISIONS
            and isinstance(context.get('reason'), str) and context.get('reason').strip()
            and (item.entity_type == 'place'
                 or (item.entity_type == 'volunteer_revision' and context.get('target_type') == 'place')))


def _edits(item):
    """Edits to a public card (the live version stays) vs. a new card."""
    from catalog.models import Place, VolunteerPlaceRevision
    if item.entity_type == 'place':
        return False
    revision = VolunteerPlaceRevision.objects.filter(pk=item.entity_id).select_related('place').first()
    place = getattr(revision, 'place', None)
    return bool(place and isinstance(place, Place) and place.is_public)


def build(item):
    """(subject, text_body, html_body) for one place decision."""
    from catalog.services.workflow_email_policy import inbox_url
    context = item.event_context
    decision = context['decision']
    titles = context.get('titles') if isinstance(context.get('titles'), dict) else {}
    name = ' '.join(str(titles.get('az') or titles.get('ru') or titles.get('en') or '').split())[:120] or 'KidsMap'
    reason = context['reason'].strip()[:4000]
    copy = _copy(decision, name, _edits(item))
    url = inbox_url()
    subject = f"KidsMap: {copy['az']['badge']} / {copy['ru']['badge']} — {name}"
    langs = ('az', 'ru', 'en')
    body = '\n'.join([
        *(copy[lang]['lead'] for lang in langs), '',
        ' / '.join(copy[lang]['note_label'] for lang in langs) + ':', reason, '',
        *(copy[lang]['next'] for lang in langs), '',
        ' / '.join(copy[lang]['button'] for lang in langs) + ':', url, '',
    ])
    site_url = (settings.PUBLIC_BASE_URL or 'https://kidsmap.az').rstrip('/')
    html = render_to_string('emails/place_moderation_decision.html', {
        'subject': subject, 'preheader': copy['ru']['lead'], 'title': name, 'reason': reason,
        'copy': copy, 'tone': _TONES[decision], 'action_url': url, 'site_url': site_url,
        'languages': [{'code': lang, 'text': copy[lang]} for lang in ('az', 'ru', 'en')],
    })
    return subject, body, html
