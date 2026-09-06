"""Publication requirements shared by the admin and the public place wizard."""
from catalog.services.image_uploads import MAX_GALLERY_IMAGES
from django.utils.translation import get_language


def copy(ru, az, en):
    return {'ru': ru, 'az': az, 'en': en}.get((get_language() or 'az').split('-')[0], ru)


REQUIRED = ('name_az', 'subcategory', 'category', 'description_az', 'age_from', 'address', 'region', 'phone1', 'photo', 'lat', 'lng')
NAME_FIELDS = ('name_az', 'name_ru', 'name_en')
DESCRIPTION_FIELDS = ('description_az', 'description_ru', 'description_en')


def publication_errors(data, *, instance=None, schedule_days=()):
    from catalog.services.place_schedule import is_meaningful_schedule
    from catalog.services.content_quality import _mapping_has_public_price, contains_test_content
    errors = {}
    for name in (*NAME_FIELDS, *DESCRIPTION_FIELDS, 'address', 'schedule'):
        if contains_test_content(data.get(name)):
            errors[name] = copy('Удалите тестовый текст.', 'Sınaq mətnini silin.', 'Remove placeholder text.')
    missing = copy('Заполните это поле перед отправкой.', 'Göndərməzdən əvvəl bu sahəni doldurun.', 'Complete this field before submitting.')
    for name in REQUIRED:
        if data.get(name) is None or data.get(name) == '' or data.get(name) is False:
            errors[name] = missing
    if not any(str(data.get(name) or '').strip() for name in NAME_FIELDS):
        errors['name_az'] = copy('Укажите название хотя бы на одном языке.', 'Adı ən azı bir dildə daxil edin.', 'Enter a name in at least one language.')
    if max(len(str(data.get(name) or '').strip()) for name in DESCRIPTION_FIELDS) < 120:
        errors['description_az'] = copy('Описание хотя бы на одном языке — не менее 120 символов.', 'Ən azı bir dildə təsvir 120 simvoldan az olmamalıdır.', 'Provide at least 120 characters in one description.')
    if not data.get('age_open_ended') and data.get('age_to') is None:
        errors['age_to'] = missing
    if data.get('region') == 'baku' and not data.get('district'):
        errors['district'] = missing
    if data.get('schedule_mode', 'regular') == 'regular' and not (str(data.get('schedule') or '').strip() or is_meaningful_schedule(schedule_days)):
        errors['structured_schedule'] = copy('Укажите дни и время работы или текстовое расписание.', 'İş günlərini və saatlarını və ya mətn cədvəlini daxil edin.', 'Enter opening days and hours or a text schedule.')
    plans = data.get('pricing_plans') or []
    # Existing scalar-only cards can still be edited without deleting their prices.
    legacy = instance is not None and instance.pk and not plans and not instance.pricing_plan_records.exists() and any(
        getattr(instance, field, None) is not None for field in ('price_from', 'price_to', 'price_per_lesson', 'price_per_month', 'price_per_8_lessons')
    )
    if not legacy and not any(_mapping_has_public_price(plan) for plan in plans):
        errors['pricing_plans'] = copy('Добавьте активный основной тариф, в том числе «бесплатно» или «по запросу».', 'Aktiv əsas tarif əlavə edin: pulsuz və ya sorğu ilə də mümkündür.', 'Add an active primary plan; free and on request are accepted.')
    return errors


def client_rules(form):
    from catalog.services.pricing_plans import build_public_price_summary
    summary = build_public_price_summary(form.instance, get_language())
    return {
        'required': list(REQUIRED), 'names': ['name_az'],
        'descriptions': list(DESCRIPTION_FIELDS), 'description_min': 120,
        'max_plans': 12, 'max_gallery': MAX_GALLERY_IMAGES,
        'existing_price_label': summary['label'], 'custom_price': summary['source'] == 'custom_override',
        'legacy_price': bool(form.instance.pk and not form.instance.pricing_plans and any(getattr(form.instance, key) is not None for key in ('price_from', 'price_to', 'price_per_lesson', 'price_per_month', 'price_per_8_lessons'))),
    }
