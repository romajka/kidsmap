"""Public wording for explicit stored tariff terms; never infer or rewrite them."""

_UNITS = {
    'ru': {
        'entry': ('вход', 'входа', 'входов'), 'visit': ('посещение', 'посещения', 'посещений'),
        'lesson': ('занятие', 'занятия', 'занятий'), 'minute': ('минута', 'минуты', 'минут'),
        'hour': ('час', 'часа', 'часов'), 'day': ('день', 'дня', 'дней'),
        'week': ('неделя', 'недели', 'недель'), 'month': ('месяц', 'месяца', 'месяцев'),
        'year': ('год', 'года', 'лет'), 'course': ('курс', 'курса', 'курсов'),
        'event': ('мероприятие', 'мероприятия', 'мероприятий'), 'camp_shift': ('смена', 'смены', 'смен'),
        'person': ('человек', 'человека', 'человек'), 'family': ('семья', 'семьи', 'семей'),
        'group': ('группа', 'группы', 'групп'),
    },
    'az': {
        'entry': 'giriş', 'visit': 'ziyarət', 'lesson': 'dərs', 'minute': 'dəqiqə',
        'hour': 'saat', 'day': 'gün', 'week': 'həftə', 'month': 'ay', 'year': 'il',
        'course': 'kurs', 'event': 'tədbir', 'camp_shift': 'düşərgə növbəsi',
        'person': 'nəfər', 'family': 'ailə', 'group': 'qrup',
    },
    'en': {
        'entry': ('entry', 'entries'), 'visit': ('visit', 'visits'), 'lesson': ('lesson', 'lessons'),
        'minute': ('minute', 'minutes'), 'hour': ('hour', 'hours'), 'day': ('day', 'days'),
        'week': ('week', 'weeks'), 'month': ('month', 'months'), 'year': ('year', 'years'),
        'course': ('course', 'courses'), 'event': ('event', 'events'),
        'camp_shift': ('camp session', 'camp sessions'), 'person': ('person', 'people'),
        'family': ('family', 'families'), 'group': ('group', 'groups'),
    },
}


def _counted(count, unit, language):
    count = int(count)
    forms = _UNITS[language].get(unit)
    if not forms:
        return ''
    if language == 'ru':
        index = 2 if count % 100 in (11, 12, 13, 14) else 0 if count % 10 == 1 else 1 if count % 10 in (2, 3, 4) else 2
        word = forms[index]
    elif language == 'en':
        word = forms[0 if count == 1 else 1]
    else:
        word = forms
    return f'{count} {word}'


def public_tariff_terms(plan, language):
    """Keep payment frequency, included quantity and usage validity separate."""
    language = language if language in _UNITS else 'ru'
    if not plan.get('product_type'):
        # Free-form historical frequency is evidence, not an inferred enum.
        return [plan['payment_label']] if not plan.get('payment_type') and plan.get('payment_label') else []
    copy = {
        'ru': {'once': 'Разовая оплата', 'every': 'Оплата: раз в ', 'installment': 'Рассрочка: ', 'included': 'Включено: ', 'unlimited': 'Безлимит посещений', 'validity': 'Срок использования: ', 'from': 'Предложение с ', 'until': 'Предложение до '},
        'az': {'once': 'Birdəfəlik ödəniş', 'every': 'Ödəniş: hər ', 'installment': 'Hissə-hissə ödəniş: ', 'included': 'Daxildir: ', 'unlimited': 'Limitsiz ziyarətlər', 'validity': 'İstifadə müddəti: ', 'from': 'Təklifin başlanğıcı: ', 'until': 'Təklifin sonu: '},
        'en': {'once': 'One payment', 'every': 'Payment: every ', 'installment': 'Instalments: ', 'included': 'Includes: ', 'unlimited': 'Unlimited visits', 'validity': 'Use within: ', 'from': 'Offer starts: ', 'until': 'Offer ends: '},
    }[language]
    terms = []
    mode = plan.get('billing_mode')
    if mode == 'recurring' and plan.get('billing_interval'):
        count = plan.get('billing_interval_count') or 1
        unit = plan['billing_interval']
        period = _counted(count, unit, language)
        if count == 1:
            if language == 'ru':
                period = {'day': 'день', 'week': 'неделю', 'month': 'месяц', 'year': 'год'}[unit]
            elif language == 'en':
                period = _UNITS['en'][unit][0]
            else:
                period = _UNITS['az'][unit]
        terms.append(copy['every'] + period)
    elif mode == 'installment' and plan.get('billing_cycles'):
        count = int(plan['billing_cycles'])
        if language == 'ru':
            suffix = 'платежей' if count % 100 in (11,12,13,14) or count % 10 not in (1,2,3,4) else 'платёж' if count % 10 == 1 else 'платежа'
        else:
            suffix = 'ödəniş' if language == 'az' else 'payment' if count == 1 else 'payments'
        terms.append(copy['installment'] + f'{count} {suffix}')
    elif mode == 'one_time' and plan.get('price_kind') != 'free':
        terms.append(copy['once'])
    if plan.get('is_unlimited'):
        terms.append(copy['unlimited'])
    elif plan.get('quantity') and plan.get('quantity_unit'):
        # Package quantity is already included by the compatibility formatter.
        if not (plan.get('quantity_unit') == 'lesson' and plan.get('quantity') == plan.get('package_sessions')):
            terms.append(copy['included'] + _counted(plan['quantity'], plan['quantity_unit'], language))
    if plan.get('validity_interval') and plan.get('validity_interval_count'):
        terms.append(copy['validity'] + _counted(plan['validity_interval_count'], plan['validity_interval'], language))
    for field, label in (('valid_from', 'from'), ('valid_until', 'until')):
        if plan.get(field):
            terms.append(copy[label] + str(plan[field]))
    return terms
