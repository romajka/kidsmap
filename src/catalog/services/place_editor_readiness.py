"""Presentation groups for the existing publication verdict, shared by editors."""
from catalog.services.permanent_place_rules import submission_readiness


def field_section(field):
    if field in {'name', 'name_az', 'name_ru', 'name_en', 'description', 'description_az', 'description_ru', 'description_en', 'category', 'subcategory'}:
        return 1
    if field in {'region', 'district', 'metro', 'address', 'lat', 'lng', 'phone1', 'phone2', 'phone3', 'whatsapp_mode', 'whatsapp_number', 'website', 'instagram', 'public_links', 'schedule', 'schedule_mode', 'structured_schedule'} or field.startswith('schedule_note'):
        return 2
    if field in {'age_from', 'age_to', 'age_open_ended', 'offers_adult_classes', 'price_mode', 'pricing_plans', 'nested_pricing'}:
        return 3
    return 4


def editor_readiness(form):
    result = submission_readiness(form)
    sections = {number: {'id': number, 'required_count': 0, 'completed_count': 0, 'error_count': 0} for number in range(1, 5)}
    for item in result['items']:
        section = sections[field_section(item['field'])]
        item['section'] = section['id']
        section['required_count'] += 1
        section['completed_count'] += int(item['complete'])
    errors = getattr(form, 'errors', {})
    # Missing requirements are amber. Invalid entered values are red; optional
    # fields must not inflate the denominator, but can still block submission.
    for field in errors:
        if field == '__all__':
            continue
        value = form.data.get(field) if form.is_bound else None
        if isinstance(value, str):
            value = value.strip()
            if field in {'pricing_plans', 'nested_pricing', 'structured_schedule', 'public_links'}:
                import json
                try: value = json.loads(value or 'null')
                except (ValueError, TypeError): pass
        if field == 'structured_schedule' and isinstance(value, list) and not getattr(form, 'schedule_editor_errors', {}):
            # The editor serializes seven closed days even before any entry.
            # Missing opening hours are incomplete, not an invalid user value.
            if all(isinstance(day, dict) and day.get('is_closed') is True and not day.get('intervals') for day in value):
                continue
        if value not in (None, '', [], False) or field in getattr(form, 'files', {}):
            sections[field_section(field)]['error_count'] += 1
    for section in sections.values():
        section['is_complete'] = section['completed_count'] == section['required_count'] and not section['error_count']
    result['sections'] = list(sections.values())
    result['error_count'] = sum(section['error_count'] for section in sections.values())
    result['is_ready'] = result['is_ready'] and not bool(errors)
    return result
