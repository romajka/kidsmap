"""Read-only review cues. Never interprets a visual diff as permission to publish."""
import json
import re
from difflib import SequenceMatcher
from django.core.exceptions import FieldDoesNotExist
from catalog.services.permanent_place_rules import copy as t


def review_copy():
    return {
        'title': t('Что изменено', 'Nə dəyişib', 'What changed'),
        'pending': t('Правки ждут проверки', 'Dəyişikliklər yoxlama gözləyir', 'Changes awaiting review'),
        'fields': t('Полей в предложении', 'Təklifdəki sahələr', 'Fields in this proposal'),
        'help': t('Сравните выделенные фрагменты. На сайте изменения появятся только после одобрения.',
                  'Vurğulanmış hissələri müqayisə edin. Dəyişikliklər yalnız təsdiqdən sonra saytda görünəcək.',
                  'Compare the highlighted parts. Changes appear on the site only after approval.'),
        'draft': t('Это сохранённый черновик. Он ещё не отправлен на проверку.', 'Bu saxlanılmış qaralamadır. Hələ yoxlamaya göndərilməyib.', 'This is a saved draft. It has not been submitted for review yet.'),
        'history': t('Сравнение с текущими данными. Решение по этой заявке уже принято.',
                     'Cari məlumatlarla müqayisə. Bu təklif üzrə qərar artıq verilib.',
                     'Comparison with current data. This proposal already has a decision.'),
        'review': t('Сравнить и проверить', 'Müqayisə et və yoxla', 'Compare and review'),
        'attention': t('На что обратить внимание', 'Nəyə diqqət yetirməli', 'What to check'),
        'empty': t('В предложении нет изменённых полей.', 'Təklifdə dəyişdirilmiş sahə yoxdur.', 'No changed fields in this proposal.'),
        'now': t('Сейчас', 'Hazırda', 'Current'),
        'proposed': t('Предложено', 'Təklif olunur', 'Proposed'),
        'new': t('Новая карточка: проверьте все данные перед первой публикацией.',
                 'Yeni kart: ilk dərcdən əvvəl bütün məlumatları yoxlayın.',
                 'New entry: check all information before its first publication.'),
    }


def review_hint(key):
    if key in {'district', 'region', 'metro', 'address', 'lat', 'lng', 'location_override'}:
        return t('Сверьте адрес, район и точку на карте.', 'Ünvanı, rayonu və xəritədəki nöqtəni yoxlayın.', 'Check the address, district and map pin.')
    if key.startswith(('price', 'custom_price')) or key in {'pricing_plans', 'nested_pricing', 'payment_type'}:
        return t('Проверьте сумму, период оплаты и условия тарифа.', 'Məbləği, ödəniş dövrünü və tarif şərtlərini yoxlayın.', 'Check the amount, billing period and pricing conditions.')
    if key.startswith('phone') or key in {'website', 'instagram', 'whatsapp_number', 'contact_email'}:
        return t('Проверьте, что контакт принадлежит этому месту и работает.', 'Əlaqənin bu məkana aid olduğunu və işlədiyini yoxlayın.', 'Check that the contact works and belongs to this place.')
    if key in {'photo', 'cover_photo', 'gallery'}:
        return t('Сверьте место на фото, качество и права на использование.', 'Şəkildəki məkanı, keyfiyyəti və istifadə hüquqlarını yoxlayın.', 'Check the location shown, image quality and usage rights.')
    if 'schedule' in key or key in {'start_datetime', 'end_datetime'}:
        return t('Проверьте дни, время и исключения в расписании.', 'Günləri, saatları və cədvəldəki istisnaları yoxlayın.', 'Check the days, times and schedule exceptions.')
    return t('Сверьте новые данные с источником; проверьте, не удалено ли важное.',
             'Yeni məlumatları mənbə ilə tutuşdurun; vacib məlumatların silinmədiyini yoxlayın.',
             'Verify the new information against its source and check for important removals.')


def _empty(value):
    return value is None or value == '' or value == [] or value == {}


def _text(value, target=None, key=''):
    if _empty(value):
        return t('Не указано', 'Göstərilməyib', 'Not specified')
    if isinstance(value, bool):
        return t('Да', 'Bəli', 'Yes') if value else t('Нет', 'Xeyr', 'No')
    if isinstance(value, str) and key in {'district', 'region', 'metro'}:
        from catalog.services.locations import get_location_translation, get_metro_translation
        return str(get_metro_translation(value) if key == 'metro' else get_location_translation(value))
    if target is not None:
        try:
            field = target._meta.get_field(key)
        except FieldDoesNotExist:
            field = None
        if field is not None and field.auto_created and not field.concrete:
            # Reverse relations (e.g. ``gallery``) carry structured payloads,
            # not a column value: they have no choices and no target field.
            field = None
        if field is not None and field.choices:
            return str(dict(field.flatchoices).get(value, value))
        if field is not None and field.is_relation and not isinstance(value, (dict, list)):
            related = field.remote_field.model.objects.filter(**{field.target_field.name: value}).first()
            return str(related) if related else str(value)
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=2)
    return str(value)


def describe_change(key, before, after, target=None):
    """Plain segments stay autoescaped in templates; bounded work for long text."""
    before_text, after_text = _text(before, target, key), _text(after, target, key)
    kind = 'unchanged' if before == after else 'added' if _empty(before) else 'removed' if _empty(after) else 'changed'
    labels = {
        'added': t('Добавлено', 'Əlavə edilib', 'Added'),
        'removed': t('Удалено', 'Silinib', 'Removed'),
        'changed': t('Изменено', 'Dəyişdirilib', 'Changed'),
        'unchanged': t('Совпадает с текущим', 'Cari dəyərlə eynidir', 'Matches current value'),
    }
    old, new = [], []
    a, b = re.findall(r'\s+|[^\s]+', before_text), re.findall(r'\s+|[^\s]+', after_text)
    if len(a) + len(b) <= 2000 and len(before_text) + len(after_text) <= 20000:
        for op, i, j, k, l in SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
            if j > i: old.append({'text': ''.join(a[i:j]), 'changed': op != 'equal'})
            if l > k: new.append({'text': ''.join(b[k:l]), 'changed': op != 'equal'})
    else:
        old = [{'text': before_text, 'changed': kind != 'unchanged'}]
        new = [{'text': after_text, 'changed': kind != 'unchanged'}]
    return {'key': key, 'change_type': kind, 'change_label': labels[kind], 'hint': review_hint(key),
            'before_text': before_text, 'after_text': after_text, 'before_parts': old, 'after_parts': new}
