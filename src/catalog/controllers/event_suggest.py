"""«Есть мероприятие?» — organisers send an event to the KidsMap team.

No data is stored: the request becomes an e-mail to the site inbox with the
sender as Reply-To, so the team answers from their usual mailbox. Spam guards:
a hidden honeypot field, a minimum fill time and a per-address hourly limit.
"""
import time

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

RATE_LIMIT = 5             # requests per address
RATE_WINDOW = 60 * 60      # seconds
MIN_FILL_SECONDS = 3

COPY = {
    'ru': {
        'name': 'Ваше имя', 'contact': 'Телефон или WhatsApp', 'email': 'E-mail',
        'organization': 'Организация или площадка', 'title': 'Название мероприятия',
        'when': 'Когда пройдёт', 'link': 'Ссылка (Instagram, сайт, билеты)', 'message': 'Коротко о мероприятии',
        'need_contact': 'Оставьте телефон или e-mail — иначе мы не сможем ответить.',
        'ok': 'Спасибо! Заявка отправлена. Мы свяжемся с вами в ближайшее время.',
        'slow': 'Слишком много заявок с этого адреса. Попробуйте позже или напишите нам в WhatsApp.',
        'fail': 'Не удалось отправить письмо. Напишите нам в WhatsApp или на e-mail — мы ответим.',
        'subject': 'Новое мероприятие для афиши',
    },
    'az': {
        'name': 'Adınız', 'contact': 'Telefon və ya WhatsApp', 'email': 'E-poçt',
        'organization': 'Təşkilat və ya məkan', 'title': 'Tədbirin adı',
        'when': 'Nə vaxt keçiriləcək', 'link': 'Link (Instagram, sayt, biletlər)', 'message': 'Tədbir haqqında qısaca',
        'need_contact': 'Telefon və ya e-poçt yazın — əks halda cavab verə bilmərik.',
        'ok': 'Təşəkkür edirik! Müraciət göndərildi. Tezliklə sizinlə əlaqə saxlayacağıq.',
        'slow': 'Bu ünvandan çox müraciət gəlib. Bir az sonra yenidən cəhd edin və ya WhatsApp-da yazın.',
        'fail': 'Məktubu göndərmək alınmadı. WhatsApp və ya e-poçt ilə yazın — cavab verəcəyik.',
        'subject': 'Afişa üçün yeni tədbir',
    },
    'en': {
        'name': 'Your name', 'contact': 'Phone or WhatsApp', 'email': 'E-mail',
        'organization': 'Organisation or venue', 'title': 'Event name',
        'when': 'When is it', 'link': 'Link (Instagram, website, tickets)', 'message': 'A few words about the event',
        'need_contact': 'Leave a phone number or e-mail so we can reply.',
        'ok': 'Thank you! Your request has been sent. We will get back to you soon.',
        'slow': 'Too many requests from this address. Please try later or message us on WhatsApp.',
        'fail': 'The e-mail could not be sent. Please message us on WhatsApp or by e-mail.',
        'subject': 'New event for the afisha',
    },
}


def _copy(request):
    return COPY.get((getattr(request, 'LANGUAGE_CODE', '') or 'ru').split('-')[0], COPY['ru'])


class EventSuggestionForm(forms.Form):
    name = forms.CharField(max_length=80)
    contact = forms.CharField(max_length=40, required=False)
    email = forms.EmailField(max_length=120, required=False)
    organization = forms.CharField(max_length=120, required=False)
    title = forms.CharField(max_length=160)
    when = forms.CharField(max_length=80, required=False)
    link = forms.URLField(max_length=300, required=False, assume_scheme='https')
    message = forms.CharField(max_length=1500, required=False, widget=forms.Textarea)
    website = forms.CharField(required=False)          # honeypot: people never see it
    started = forms.FloatField(required=False)           # page render time (epoch seconds)

    def __init__(self, *args, copy=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.copy = copy or COPY['ru']

    def clean(self):
        data = super().clean()
        if not (data.get('contact') or '').strip() and not data.get('email'):
            raise forms.ValidationError(self.copy['need_contact'], code='contact')
        return data

    def is_bot(self):
        data = self.cleaned_data
        if (data.get('website') or '').strip():
            return True
        started = data.get('started')
        return bool(started) and time.time() - started < MIN_FILL_SECONDS


def _client_address(request):
    return (request.META.get('REMOTE_ADDR') or 'unknown').strip()


def _rate_limited(request):
    key = f'event-suggest:{_client_address(request)}'
    if cache.add(key, 1, timeout=RATE_WINDOW):
        return False
    try:
        return cache.incr(key) > RATE_LIMIT
    except ValueError:
        cache.set(key, 1, timeout=RATE_WINDOW)
        return False


def _recipient():
    explicit = getattr(settings, 'EVENT_SUGGESTIONS_EMAIL', '')
    if explicit:
        return explicit
    from django.db import OperationalError, ProgrammingError
    from catalog.context_processors import DEFAULT_FOOTER_EMAIL
    from catalog.models import SiteSettings
    try:
        email = (SiteSettings.get_solo().footer_email or '').strip()
    except (OperationalError, ProgrammingError):  # settings table unavailable: use the public address
        email = ''
    return email if email and email.lower() != 'kidsmap@example.com' else DEFAULT_FOOTER_EMAIL


def _send(form, request, copy):
    data = form.cleaned_data
    labels = COPY['ru']  # the team reads Russian
    lines = [f"{labels[field]}: {str(data.get(field) or '—').strip()}"
             for field in ('title', 'when', 'organization', 'name', 'contact', 'email', 'link')]
    lines += ['', labels['message'] + ':', (data.get('message') or '—').strip(), '',
              f"Язык сайта: {getattr(request, 'LANGUAGE_CODE', '')}",
              f"Страница: {request.META.get('HTTP_REFERER', '—')}"]
    email = EmailMessage(
        subject=f"[KidsMap] {labels['subject']}: {data['title']}"[:180],
        body='\n'.join(lines),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[_recipient()],
        reply_to=[data['email']] if data.get('email') else None,
    )
    email.send(fail_silently=False)


def _wants_json(request):
    return request.headers.get('X-Requested-With') == 'fetch' or 'application/json' in request.headers.get('Accept', '')


@require_http_methods(['GET', 'POST'])
def event_suggest(request):
    from catalog.services.afisha_urls import localized_route_paths
    request._seo_localized_paths = localized_route_paths('event_suggest')
    copy = _copy(request)
    status, message, form = 200, '', EventSuggestionForm(copy=copy)
    if request.method == 'POST':
        form = EventSuggestionForm(request.POST, copy=copy)
        if not form.is_valid():
            status = 400
        elif form.is_bot():
            message = copy['ok']   # look successful; send nothing
        elif _rate_limited(request):
            status, message = 429, copy['slow']
        else:
            try:
                _send(form, request, copy)
                message = copy['ok']
            except Exception:  # SMTP outage: tell the visitor and offer the other channels
                status, message = 502, copy['fail']
        if _wants_json(request):
            errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()} if status == 400 else {}
            return JsonResponse({'ok': status == 200, 'message': message, 'errors': errors}, status=status)
        if status == 200:
            form = EventSuggestionForm(copy=copy)
    return render(request, 'pages/event_suggest.html', {
        'suggest_form': form, 'suggest_message': message, 'suggest_ok': request.method == 'POST' and status == 200,
        'suggest_started': int(time.time()), 'language': (request.LANGUAGE_CODE or 'ru').split('-')[0],
    }, status=status)
