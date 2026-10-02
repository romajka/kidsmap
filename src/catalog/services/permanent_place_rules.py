"""Publication requirements shared by the admin and the public place wizard."""
from catalog.services.image_uploads import MAX_GALLERY_IMAGES
from django.utils.translation import get_language


def copy(ru, az, en):
    return {'ru': ru, 'az': az, 'en': en}.get((get_language() or 'az').split('-')[0], ru)


REQUIRED = ('name_az', 'subcategory', 'category', 'description_az', 'age_from', 'address', 'region', 'phone1')
NAME_FIELDS = ('name_az', 'name_ru', 'name_en')
DESCRIPTION_FIELDS = ('description_az', 'description_ru', 'description_en')


def publication_errors(data, *, instance=None, schedule_days=()):
    from types import SimpleNamespace
    from catalog.services.place_readiness import evaluate_form_readiness
    form=SimpleNamespace(cleaned_data=data,instance=instance,cleaned_schedule_days=schedule_days)
    return {issue.field:issue.message for issue in evaluate_form_readiness(form,instance).issues}


def client_rules(form):
    from catalog.services.pricing_plans import build_public_price_summary
    summary = build_public_price_summary(form.instance, get_language())
    from catalog.services.place_readiness import inherited_contact
    contact_required = getattr(form.instance, 'nature', '') != 'public_space' and not inherited_contact(form.instance)
    return {
        'required': [name for name in REQUIRED if name != 'phone1'], 'contact_any': ['phone1','phone2','phone3','website'], 'contact_required': bool(contact_required), 'names': ['name_az'],
        'descriptions': list(DESCRIPTION_FIELDS), 'description_min': 1,
        'max_plans': 12, 'max_gallery': MAX_GALLERY_IMAGES,
        'existing_price_label': summary['label'], 'custom_price': summary['source'] == 'custom_override',
        'legacy_price': bool(form.instance.pk and not form.instance.pricing_plans and any(getattr(form.instance, key) is not None for key in ('price_from', 'price_to', 'price_per_lesson', 'price_per_month', 'price_per_8_lessons'))),
    }
