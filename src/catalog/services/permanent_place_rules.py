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
    from catalog.services.place_readiness import inherited_contact_for_form, readiness_data_from_form
    from catalog.services.contact_policy import contact_optional, contact_client_config
    snapshot = readiness_presentation_snapshot(form)
    data = readiness_data_from_form(snapshot)
    inherited = bool(inherited_contact_for_form(snapshot))
    policy = contact_client_config(form.instance, original_taxonomy=getattr(form, 'contact_original_taxonomy', None), approved_nature=getattr(form, 'contact_approved_nature', None))
    policy['inherited'] = inherited
    contact_required = not contact_optional(category_code=data.category_code, subcategory_code=data.subcategory_code,
        subcategory_category_code=data.subcategory_category_code, nature=data.nature) and not inherited
    return {
        'required': [name for name in REQUIRED if name != 'phone1'], 'contact_any': ['phone1','phone2','phone3','website','whatsapp_number'], 'contact_required': bool(contact_required), 'contact_policy': policy, 'names': ['name_az'],
        'descriptions': list(DESCRIPTION_FIELDS), 'description_min': 1,
        'max_plans': 12, 'max_gallery': MAX_GALLERY_IMAGES,
        'existing_price_label': summary['label'], 'custom_price': summary['source'] == 'custom_override',
        'legacy_price': bool(form.instance.pk and not form.instance.pricing_plans and any(getattr(form.instance, key) is not None for key in ('price_from', 'price_to', 'price_per_lesson', 'price_per_month', 'price_per_8_lessons'))),
    }


def readiness_presentation_snapshot(form):
    """Read displayed values without validating or changing the instance."""
    import copy as object_copy
    import json
    from types import SimpleNamespace

    if form.is_bound and hasattr(form, 'cleaned_data'):
        snapshot = form
    else:
        values = {name: form[name].value() for name in form.fields}
        for name in ('pricing_plans', 'nested_pricing', 'structured_schedule'):
            if isinstance(values.get(name), str):
                try:
                    values[name] = json.loads(values[name] or 'null')
                except (ValueError, TypeError):
                    values[name] = None
        # This is a display projection before full_clean. Normalize hostile
        # schedule shapes here, while retaining raw input for field validation.
        from catalog.services.place_schedule import validate_schedule_payload
        schedule_days = validate_schedule_payload(values.get('structured_schedule')).days
        instance = object_copy.copy(form.instance)
        if 'nested_pricing' in values and not values['nested_pricing'] and instance.pk:
            from catalog.services.pricing_plans import serialize_nested_pricing
            values['nested_pricing'] = serialize_nested_pricing(instance)
        instance.nature = values.get('nature') or instance.nature
        snapshot = SimpleNamespace(
            instance=instance, cleaned_data=values,
            contact_original_taxonomy=getattr(form, 'contact_original_taxonomy', (str(instance.category_id or ''), str(instance.subcategory_id or ''))),
            contact_approved_nature=getattr(form, 'contact_approved_nature', getattr(instance, 'nature', '') or ''),
            cleaned_schedule_days=schedule_days,
        )
    return snapshot


def submission_readiness(form):
    """Present the existing server verdict; do not validate or save the form."""
    from catalog.services.place_readiness import evaluate_form_readiness
    snapshot = readiness_presentation_snapshot(form)
    readiness = evaluate_form_readiness(snapshot, snapshot.instance)
    items = []
    for item in readiness.items:
        requirement = item.requirement
        config = dict(requirement.client_config)
        if item.code == 'phone':
            from catalog.services.contact_policy import contact_client_config
            config.update(contact_client_config(form.instance, original_taxonomy=getattr(form, 'contact_original_taxonomy', None), approved_nature=getattr(form, 'contact_approved_nature', None)))
            mode = snapshot.cleaned_data.get('whatsapp_mode', getattr(snapshot.instance, 'whatsapp_mode', 'legacy'))
            config['inherited'] = config.get('inherited_by_mode', {}).get(mode, config.get('inherited', False))
        items.append(dict(code=item.code, label=str(requirement.label),
                          field=requirement.field, anchor=requirement.anchor,
                          config=config, complete=item.is_complete,
                          message=str(item.issue.message) if item.issue else ''))
    return dict(items=items, required_count=readiness.required_count,
                completed_count=readiness.completed_count, is_ready=readiness.is_ready,
                issues=[item for item in items if not item['complete']],
                advice=[dict(label=issue.label, message=issue.message) for issue in readiness.advice])
